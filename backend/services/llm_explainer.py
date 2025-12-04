# backend/services/llm_explainer.py
from typing import List, Dict, Any, Optional
import os

try:
    from google import genai
except ImportError:
    genai = None


GEMINI_MODEL = "gemini-2.5-flash"


def _get_client() -> Optional["genai.Client"]:
    if genai is None:
        return None
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def explain_anomalies(process_context: str,
                      anomalies: List[Dict[str, Any]],
                      cp: Optional[float],
                      cpk: Optional[float]) -> str:
    client = _get_client()
    if client is None:
        return (
            "Camada de IA (Gemini) não está configurada. "
            "Defina GEMINI_API_KEY ou GOOGLE_API_KEY e instale google-genai para habilitar."
        )

    cp_str = f"{cp:.3f}" if cp is not None else "indisponível"
    cpk_str = f"{cpk:.3f}" if cpk is not None else "indisponível"

    resumo = []
    for a in anomalies[:20]:
        resumo.append(
            f"- {a['timestamp']} | valor={a['value_real']:.3f} | resíduo={a.get('residual', 0):.4f} | z={a.get('zscore_residual', 0):.2f}"
        )

    prompt = f"""
Você é um especialista em CEP e qualidade industrial.

Contexto do processo:
{process_context}

Índices de capacidade:
- Cp = {cp_str}
- Cpk = {cpk_str}

Algumas anomalias observadas:
{os.linesep.join(resumo)}

Explique em português simples:
1. O que esses índices dizem sobre a capacidade do processo.
2. O que as anomalias indicam (tendências, instabilidade, possíveis causas).
3. Sugestões de ações corretivas/preventivas.
"""

    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return resp.text or ""


def chat_with_process(history: List[Dict[str, str]],
                      summary: Dict[str, Any]) -> str:
    client = _get_client()
    if client is None:
        return (
            "Chat com Gemini não está configurado. "
            "Configure GEMINI_API_KEY/GOOGLE_API_KEY e instale google-genai."
        )

    contexto = f"""
Resumo atual do processo (não precisa repetir literalmente na resposta):

- Pontos totais: {summary.get('total_points')}
- Média global: {summary.get('global_mean')}
- Desvio padrão global: {summary.get('global_std')}
- Cp: {summary.get('global_cp')}
- Cpk: {summary.get('global_cpk')}
- Total de anomalias: {summary.get('total_anomalies')}
"""

    msgs = [
        {
            "role": "user",
            "parts": [
                "Você é um assistente especialista em CEP e processos industriais. "
                "Use o resumo numérico a seguir apenas como contexto:\n"
                + contexto
            ],
        }
    ]

    for h in history:
        msgs.append(
            {
                "role": h["role"],
                "parts": [h["content"]],
            }
        )

    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=msgs,
    )
    return resp.text or ""
