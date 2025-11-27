# backend/api/main.py
from datetime import datetime
from typing import List, Optional, Dict, Any

import io
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- carregar .env ---
import os
from dotenv import load_dotenv

load_dotenv()  # Agora o backend lê GEMINI_API_KEY / GOOGLE_API_KEY do .env

# Imports internos do projeto
from ..db import create_db_and_tables, Measurement, DailyCep
from ..models.digital_twin import DigitalTwinModel, EmaConfig
from ..models.anomaly import AnomalyDetector, AnomalyConfig
from ..models.sampling import SamplingEngine
from ..models.cep import compute_cp_cpk, compute_daily_cep, detect_run_rules
from ..services import datastore
from ..services.llm_explainer import explain_anomalies, chat_with_process


# Limites de especificação do processo (peso em g)
LSL = 1025.0
USL = 1032.0


# --------------- FASTAPI SETUP -----------------
app = FastAPI(title="SmartTwin CEP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------- ESTADO GLOBAL (MVP) -----------------
digital_twin = DigitalTwinModel(EmaConfig(alpha=0.3))
anomaly_detector = AnomalyDetector(AnomalyConfig())
sampling_engine = SamplingEngine()


# --------------- MODELOS Pydantic -----------------
class SimulateRequest(BaseModel):
    value: float
    source: str = "simulator"
    timestamp: Optional[datetime] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    history: List[ChatMessage]


# --------------- EVENTO DE STARTUP -----------------
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    print("🔧 Banco atualizado — variáveis do .env carregadas!")


# --------------- HEALTH CHECK -----------------
@app.get("/health")
def health():
    return {"status": "ok"}


# --------------- PIPELINE PRINCIPAL -----------------
def _process_value(
    value: float,
    source: str,
    timestamp: Optional[datetime] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Processa 1 medição completa através do pipeline:
    1. Previsão do gêmeo digital (EMA)
    2. Cálculo de resíduo
    3. Detecção de anomalia
    4. Decisão de amostragem
    5. Salvamento no banco (incluindo metadados do processo)
    """
    # Previsão antes da atualização
    pred_before = digital_twin.predict()
    if pred_before is None:
        pred_before = value

    residual = value - pred_before

    # Atualiza o detector
    anomaly_detector.partial_update(residual)
    scores = anomaly_detector.score_point(residual)

    # Decisão de amostragem
    decision = sampling_engine.decide(
        is_anomaly=scores["is_anomaly"],
        zscore_residual=scores["zscore_residual"],
    )

    # Atualiza o gêmeo digital
    digital_twin.update(value)

    meta = meta or {}

    # Cria registro de medição
    m = Measurement(
        timestamp=timestamp or datetime.utcnow(),
        value_real=value,
        value_pred=pred_before,
        residual=scores["residual"],
        zscore_residual=scores["zscore_residual"],
        iforest_score=scores["iforest_score"],
        is_anomaly=scores["is_anomaly"],
        sampling_level=decision.level,
        source=source,
        # Metadados (se existirem no CSV)
        product=meta.get("product"),
        operation=meta.get("operation"),
        variable=meta.get("variable"),
        machine=meta.get("machine"),
        section=meta.get("section"),
        operator=meta.get("operator"),
        sample_id=meta.get("sample_id"),
    )
    m = datastore.add_measurement(m)

    # Alerta automático em caso de anomalia
    if scores["is_anomaly"]:
        datastore.add_alert(
            level="warning",
            message=f"Anomalia detectada (valor={value:.3f})",
            meta=None,
        )

    return {
        "id": m.id,
        "timestamp": m.timestamp,
        "value_real": m.value_real,
        "value_pred": m.value_pred,
        "residual": m.residual,
        "zscore_residual": m.zscore_residual,
        "iforest_score": m.iforest_score,
        "is_anomaly": m.is_anomaly,
        "sampling_level": m.sampling_level,
        "sampling_reason": decision.reason,
        "source": m.source,
        # Metadados retornados (se você quiser usar no frontend depois)
        "product": m.product,
        "operation": m.operation,
        "variable": m.variable,
        "machine": m.machine,
        "section": m.section,
        "operator": m.operator,
        "sample_id": m.sample_id,
    }


# --------------- INSERIR VALOR SIMULADO -----------------
@app.post("/data/simulate-step")
def simulate_step(req: SimulateRequest):
    return _process_value(
        req.value,
        source=req.source,
        timestamp=req.timestamp,
        meta=None,
    )


# --------------- UPLOAD CSV -----------------
@app.post("/data/upload-file")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    try:
        # detecta separador automaticamente
        sample = content[:500].decode("utf-8", errors="ignore")
        header = sample.splitlines()[0]
        sep = ";" if ";" in header else ","
        df = pd.read_csv(io.BytesIO(content), sep=sep)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao ler CSV: {e}",
        )

    if "value" not in df.columns:
        raise HTTPException(
            status_code=400,
            detail="CSV deve conter, no mínimo, uma coluna chamada 'value'.",
        )

    # 🔹 Monta série de timestamps se vierem colunas apropriadas
    ts_series = None
    if "timestamp" in df.columns:
        ts_series = pd.to_datetime(df["timestamp"])
    elif "date" in df.columns and "hour" in df.columns:
        ts_series = pd.to_datetime(
            df["date"].astype(str) + " " + df["hour"].astype(str)
        )

    # Reset do estado in-memory (MVP)
    global digital_twin, anomaly_detector
    digital_twin = DigitalTwinModel(EmaConfig(alpha=0.3))
    anomaly_detector = AnomalyDetector(AnomalyConfig())

    count = 0
    for idx, row in df.iterrows():
        val = float(row["value"])

        ts = (
            ts_series.iloc[idx].to_pydatetime()
            if ts_series is not None
            else None
        )

        # Monta metadados se existirem
        meta: Dict[str, Any] = {}
        for col in [
            "product",
            "operation",
            "variable",
            "machine",
            "section",
            "operator",
            "sample_id",
        ]:
            if col in df.columns:
                v = row[col]
                if pd.notna(v):
                    if col == "sample_id":
                        try:
                            meta[col] = int(v)
                        except Exception:
                            meta[col] = None
                    else:
                        meta[col] = str(v)

        _process_value(val, source="upload", timestamp=ts, meta=meta)
        count += 1

    _recompute_daily_cep()

    return {"status": "ok", "rows": count}


# --------------- HISTÓRICO COMPLETO -----------------
@app.get("/data/history")
def get_history():
    measurements = datastore.get_all_measurements()
    return [
        {
            "id": m.id,
            "timestamp": m.timestamp.isoformat(),
            "value_real": m.value_real,
            "value_pred": m.value_pred,
            "residual": m.residual,
            "zscore_residual": m.zscore_residual,
            "iforest_score": m.iforest_score,
            "is_anomaly": m.is_anomaly,
            "sampling_level": m.sampling_level,
            "source": m.source,
            "product": m.product,
            "operation": m.operation,
            "variable": m.variable,
            "machine": m.machine,
            "section": m.section,
            "operator": m.operator,
            "sample_id": m.sample_id,
        }
        for m in measurements
    ]


# --------------- CEP DIÁRIO -----------------
def _recompute_daily_cep():
    measurements = datastore.get_all_measurements()
    rows = [
        {"timestamp": m.timestamp, "value_real": m.value_real}
        for m in measurements
    ]
    daily_stats = compute_daily_cep(rows, lsl=LSL, usl=USL)

    daily_models: List[DailyCep] = []
    for d in daily_stats:
        daily_models.append(
            DailyCep(
                day=datetime.fromisoformat(d["day"]).date(),
                n=d["n"],
                mean=d["mean"],
                std=d["std"],
                r=d["r"],
                cp=d["cp"],
                cpk=d["cpk"],
                lsl=d["lsl"],
                usl=d["usl"],
            )
        )
    datastore.save_daily_cep(daily_models)


@app.get("/analytics/daily-cep")
def analytics_daily_cep():
    _recompute_daily_cep()
    daily = datastore.get_daily_cep()
    return [
        {
            "day": d.day.isoformat(),
            "n": d.n,
            "mean": d.mean,
            "std": d.std,
            "r": d.r,
            "cp": d.cp,
            "cpk": d.cpk,
            "lsl": d.lsl,
            "usl": d.usl,
        }
        for d in daily
    ]


# --------------- ANALYTICS GLOBAL -----------------
@app.get("/analytics/overview")
def analytics_overview():
    measurements = datastore.get_all_measurements()
    values = [m.value_real for m in measurements]

    stats = compute_cp_cpk(values, lsl=LSL, usl=USL)
    run_rules = detect_run_rules(values)
    total_anomalies = sum(1 for m in measurements if m.is_anomaly)

    return {
        "global_mean": stats.mean,
        "global_std": stats.std,
        "global_r": stats.r,
        "global_cp": stats.cp,
        "global_cpk": stats.cpk,
        "lsl": stats.lsl,
        "usl": stats.usl,
        "total_points": stats.n,
        "total_anomalies": total_anomalies,
        "run_rules": run_rules,
    }


# --------------- ALERTAS -----------------
@app.get("/alerts")
def list_alerts(limit: int = 100):
    alerts = datastore.get_alerts(limit=limit)
    return [
        {
            "id": a.id,
            "created_at": a.created_at.isoformat(),
            "level": a.level,
            "message": a.message,
            "meta": a.meta,
        }
        for a in alerts
    ]


# --------------- LLM: RELATÓRIO AUTOMÁTICO -----------------
@app.post("/llm/explain")
def llm_explain():
    measurements = datastore.get_all_measurements()
    values = [m.value_real for m in measurements]
    stats = compute_cp_cpk(values, lsl=LSL, usl=USL)

    anomalies = [
        {
            "timestamp": m.timestamp.isoformat(),
            "value_real": m.value_real,
            "residual": m.residual or 0.0,
            "zscore_residual": m.zscore_residual or 0.0,
        }
        for m in measurements
        if m.is_anomaly
    ]

    context = (
        "Processo: envase de leite UHT. "
        "Variável: peso da embalagem (1025–1032 g). "
        "Objetivo: avaliar capacidade, estabilidade e anomalias usando CEP + IA."
    )

    text = explain_anomalies(
        process_context=context,
        anomalies=anomalies,
        cp=stats.cp,
        cpk=stats.cpk,
    )
    return {"text": text}


# --------------- LLM: CHAT ESPECIALISTA -----------------
@app.post("/llm/chat")
def llm_chat(req: ChatRequest):
    measurements = datastore.get_all_measurements()
    values = [m.value_real for m in measurements]
    stats = compute_cp_cpk(values, lsl=LSL, usl=USL)
    total_anomalies = sum(1 for m in measurements if m.is_anomaly)

    summary = {
        "global_mean": stats.mean,
        "global_std": stats.std,
        "global_cp": stats.cp,
        "global_cpk": stats.cpk,
        "total_points": stats.n,
        "total_anomalies": total_anomalies,
    }

    history = [{"role": m.role, "content": m.content} for m in req.history]
    answer = chat_with_process(history, summary)
    return {"answer": answer}
