# frontend/app.py
import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

API_BASE = "http://localhost:8000"


def fetch_json(path: str, method: str = "GET", json=None, files=None):
    url = f"{API_BASE}{path}"
    if method == "GET":
        r = requests.get(url)
    elif method == "POST":
        if files is not None:
            r = requests.post(url, files=files)
        else:
            r = requests.post(url, json=json)
    else:
        raise ValueError("Método HTTP não suportado")
    r.raise_for_status()
    return r.json()


# ----------------- CONFIG GERAL -----------------
st.set_page_config(
    page_title="SmartTwin CEP",
    page_icon="🧪",
    layout="wide",
)

# CSS customizado
st.markdown(
    """
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
    }
    .main {
        background: radial-gradient(circle at top left, #1a1f3b 0, #050814 40%, #000000 100%);
        color: #f5f5f5;
    }
    .stMetric {
        background: rgba(15, 23, 42, 0.9);
        border-radius: 16px;
        padding: 12px !important;
        box-shadow: 0 0 18px rgba(15, 23, 42, 0.6);
    }
    .stTabs [role="tablist"] {
        border-bottom: 1px solid rgba(148, 163, 184, 0.4);
    }
    .stTabs [role="tab"] {
        padding: 0.5rem 1rem;
        border-radius: 999px;
        margin-right: 0.5rem;
        background: rgba(15, 23, 42, 0.6);
        color: #e5e7eb;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #22c55e, #0ea5e9);
        color: white !important;
    }
    .sidebar-title {
        font-size: 1.3rem;
        font-weight: 700;
        padding-bottom: 0.5rem;
    }
    .sidebar-subtitle {
        font-size: 0.85rem;
        color: #9ca3af;
        margin-bottom: 1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">🧪 SmartTwin CEP</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-subtitle">Gêmeo Digital + CEP + IA para envase de leite UHT</div>',
        unsafe_allow_html=True,
    )

    menu_labels = [
        "📡 Monitoramento em tempo real",
        "📊 Análise CEP + IA",
        "🧠 Insights com IA (Gemini)",
    ]
    page = st.radio("Navegação", menu_labels, label_visibility="collapsed")

    st.markdown("---")
    st.caption("Desenvolvido por Bárbara • Projeto SmartTwin CEP")


# ----------------- PÁGINA: MONITORAMENTO -----------------
if page == "📡 Monitoramento em tempo real":
    st.title("📡 Monitoramento em tempo real")

    col_header_left, col_header_right = st.columns([3, 2])
    with col_header_left:
        st.markdown(
            "### 🎛 Painel de controle\n"
            "Acompanhe em tempo real o **peso da embalagem** e a resposta do **Gêmeo Digital**."
        )
    with col_header_right:
        st.markdown("##### Estado da API")
        try:
            _ = fetch_json("/health")
            st.success("Backend online ✅")
        except Exception:
            st.error("Backend offline ❌")

    # Upload e simulação lado a lado
    col_left, col_right = st.columns([2.2, 1.8])

    with col_left:
        st.subheader("📂 Importar CSV de histórico")
        st.caption(
            "Estrutura recomendada: `product, operation, variable, machine, section, operator, "
            "date, hour, sample_id, value` (PT-BR será tratado na tela)."
        )
        file = st.file_uploader(
            "Selecione um arquivo CSV para análise:",
            type=["csv"],
        )
        if file is not None and st.button("🚀 Enviar arquivo para análise"):
            try:
                data = fetch_json(
                    "/data/upload-file",
                    method="POST",
                    files={"file": (file.name, file.getvalue())},
                )
                st.success(f"Arquivo importado com sucesso! Linhas processadas: {data['rows']}")
            except Exception as e:
                st.error(f"Erro ao importar: {e}")

    with col_right:
        st.subheader("🎯 Simular novo ponto")
        val = st.number_input("Novo valor de peso (g)", value=1028.0, step=0.01)
        if st.button("➕ Gerar ponto (simulação)"):
            try:
                res = fetch_json(
                    "/data/simulate-step",
                    method="POST",
                    json={"value": val, "source": "simulator"},
                )
                st.success("Ponto gerado e processado.")
                st.json(res)
            except Exception as e:
                st.error(f"Erro ao simular: {e}")

    st.markdown("---")
    st.subheader("📡 Visão geral do comportamento")

    try:
        hist = fetch_json("/data/history")
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
        hist = []

    if hist:
        # DataFrame bruto com nomes do backend
        df = pd.DataFrame(hist)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        # ---- Metadados principais (produto, operação etc.) ----
        meta_cols = ["product", "operation", "variable", "machine", "section", "operator"]
        meta_info = {}
        if len(df) > 0:
            first_row = df.iloc[0]
            for c in meta_cols:
                if c in df.columns and pd.notna(first_row.get(c)):
                    meta_info[c] = first_row.get(c)

        if meta_info:
            with st.expander("ℹ️ Contexto do processo"):
                if meta_info.get("product"):
                    st.write(f"**Produto:** {meta_info['product']}")
                if meta_info.get("operation"):
                    st.write(f"**Operação:** {meta_info['operation']}")
                if meta_info.get("variable"):
                    st.write(f"**Variável:** {meta_info['variable']}")
                if meta_info.get("machine"):
                    st.write(f"**Máquina:** {meta_info['machine']}")
                if meta_info.get("section"):
                    st.write(f"**Seção:** {meta_info['section']}")
                if meta_info.get("operator"):
                    st.write(f"**Operador:** {meta_info['operator']}")

        # KPIs com último ponto
        last_row = df.iloc[-1]
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Último peso real (g)", f"{last_row['value_real']:.3f}")
        with k2:
            st.metric("Previsão do Gêmeo (g)", f"{last_row['value_pred']:.3f}")
        with k3:
            st.metric("Resíduo (g)", f"{(last_row['residual'] or 0):.3f}")
        with k4:
            z_val = last_row["zscore_residual"] if last_row["zscore_residual"] is not None else 0.0
            st.metric("Z-score do resíduo", f"{z_val:.2f}")

        # Prepara colunas auxiliares
        df["residual"] = df["residual"].fillna(0.0)
        df["zscore_residual"] = df["zscore_residual"].fillna(0.0)
        df["is_anomaly_flag"] = df["is_anomaly"].fillna(False).astype(bool)

        # DataFrame para exibição com nomes em PT-BR
        df_viz = df.copy()
        rename_map = {
            "timestamp": "Data/Hora",
            "value_real": "Peso (g)",
            "value_pred": "Previsto (Gêmeo)",
            "residual": "Resíduo (g)",
            "zscore_residual": "Z-score Resíduo",
            "iforest_score": "Score IsolationForest",
            "is_anomaly": "Anomalia",
            "sampling_level": "Nível de Amostragem",
            "source": "Origem",
            "product": "Produto",
            "operation": "Operação",
            "variable": "Variável",
            "machine": "Máquina",
            "section": "Seção",
            "operator": "Operador",
            "sample_id": "Nº da Amostra",
        }
        df_viz = df_viz.rename(columns=rename_map)

        # Abas de visualização
        tab1, tab2, tab3 = st.tabs(
            ["📈 Série temporal", "🧬 Resíduo & Anomalias", "📋 Tabela detalhada"]
        )

        with tab1:
            st.markdown("#### Peso real vs Gêmeo Digital (EMA)")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df["timestamp"],
                    y=df["value_real"],
                    mode="lines+markers",
                    name="Peso real (g)",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df["timestamp"],
                    y=df["value_pred"],
                    mode="lines",
                    name="Previsto (Gêmeo Digital)",
                    line=dict(dash="dash"),
                )
            )
            fig.add_hrect(
                y0=1025,
                y1=1032,
                fillcolor="rgba(56, 189, 248, 0.08)",
                line_width=0,
                annotation_text="Faixa de especificação (LSL/USL)",
            )
            fig.update_layout(
                margin=dict(l=10, r=10, t=40, b=30),
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.markdown("#### Resíduos e anomalias")
            fig_res = go.Figure()
            fig_res.add_trace(
                go.Scatter(
                    x=df["timestamp"],
                    y=df["residual"],
                    mode="lines+markers",
                    name="Resíduo (g)",
                )
            )
            anomalies = df[df["is_anomaly_flag"]]
            if not anomalies.empty:
                fig_res.add_trace(
                    go.Scatter(
                        x=anomalies["timestamp"],
                        y=anomalies["residual"],
                        mode="markers",
                        name="Anomalias",
                        marker=dict(color="red", size=10, symbol="x"),
                    )
                )
            fig_res.update_layout(
                margin=dict(l=10, r=10, t=40, b=30),
                height=350,
            )
            st.plotly_chart(fig_res, use_container_width=True)

        with tab3:
            st.markdown("#### Últimas medições (com metadados)")
            st.dataframe(df_viz.tail(150), use_container_width=True)

    else:
        st.info("Nenhuma medição registrada ainda. Importe um CSV ou simule dados.")


# ----------------- PÁGINA: CEP + IA -----------------
elif page == "📊 Análise CEP + IA":
    st.title("📊 Análise CEP + IA")

    try:
        overview = fetch_json("/analytics/overview")
        daily = fetch_json("/analytics/daily-cep")
        alerts = fetch_json("/alerts")
    except Exception as e:
        st.error(f"Erro ao carregar análises: {e}")
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Média global (g)", f"{overview['global_mean']:.3f}")
    with c2:
        st.metric("Desvio padrão global (g)", f"{overview['global_std']:.3f}")
    with c3:
        cp = overview["global_cp"]
        st.metric("Cp", f"{cp:.3f}" if cp is not None else "N/A")
    with c4:
        cpk = overview["global_cpk"]
        st.metric("Cpk", f"{cpk:.3f}" if cpk is not None else "N/A")

    st.caption(
        f"Total de pontos: {overview['total_points']} • Anomalias detectadas: {overview['total_anomalies']}"
    )

    tab1, tab2, tab3 = st.tabs(
        ["📆 CEP diário", "📉 Regras de execução (Run Rules)", "🚨 Alertas"]
    )

    with tab1:
        st.markdown("#### Estatísticas diárias (X̄, R, Cp, Cpk)")

        if daily:
            df_daily = pd.DataFrame(daily)
            df_daily["day"] = pd.to_datetime(df_daily["day"])

            col_cep1, col_cep2 = st.columns(2)
            with col_cep1:
                fig_mean = go.Figure()
                fig_mean.add_trace(
                    go.Scatter(
                        x=df_daily["day"],
                        y=df_daily["mean"],
                        mode="lines+markers",
                        name="Média diária (X̄)",
                    )
                )
                fig_mean.add_hrect(
                    y0=overview["lsl"],
                    y1=overview["usl"],
                    fillcolor="rgba(52, 211, 153, 0.08)",
                    line_width=0,
                    annotation_text="Limites de especificação",
                )
                fig_mean.update_layout(
                    margin=dict(l=10, r=10, t=40, b=30),
                    height=350,
                )
                st.plotly_chart(fig_mean, use_container_width=True)

            with col_cep2:
                fig_r = go.Figure()
                fig_r.add_trace(
                    go.Bar(
                        x=df_daily["day"],
                        y=df_daily["r"],
                        name="Amplitude (R)",
                    )
                )
                fig_r.update_layout(
                    margin=dict(l=10, r=10, t=40, b=30),
                    height=350,
                )
                st.plotly_chart(fig_r, use_container_width=True)

            st.markdown("#### Cp e Cpk por dia")
            fig_cp = go.Figure()
            fig_cp.add_trace(
                go.Scatter(
                    x=df_daily["day"],
                    y=df_daily["cp"],
                    mode="lines+markers",
                    name="Cp",
                )
            )
            fig_cp.add_trace(
                go.Scatter(
                    x=df_daily["day"],
                    y=df_daily["cpk"],
                    mode="lines+markers",
                    name="Cpk",
                )
            )
            fig_cp.add_hline(
                y=1.33,
                line=dict(color="green", dash="dash"),
                annotation_text="Alvo típico (1.33)",
            )
            fig_cp.update_layout(
                margin=dict(l=10, r=10, t=40, b=30),
                height=350,
            )
            st.plotly_chart(fig_cp, use_container_width=True)

            st.markdown("#### Tabela CEP diária")
            df_daily_viz = df_daily.rename(
                columns={
                    "day": "Dia",
                    "n": "Nº de pontos",
                    "mean": "Média (g)",
                    "std": "Desvio padrão (g)",
                    "r": "Amplitude (R)",
                    "cp": "Cp",
                    "cpk": "Cpk",
                    "lsl": "LSL",
                    "usl": "USL",
                }
            )
            st.dataframe(df_daily_viz, use_container_width=True)
        else:
            st.info("Ainda não há dados suficientes para CEP diário.")

    with tab2:
        st.markdown("#### Regras de Shewhart (Run Rules)")
        rr = overview["run_rules"]
        col_rr1, col_rr2 = st.columns(2)
        with col_rr1:
            st.write(f"🔹 Regra 1 – 1 ponto fora de 3σ: **{len(rr['rule1'])}** ocorrências")
        with col_rr2:
            st.write(
                f"🔹 Regra 4 – 8 pontos consecutivos do mesmo lado da média: **{len(rr['rule4'])}** ocorrências"
            )
        st.caption(
            "Essas regras ajudam a identificar padrões de instabilidade que podem não aparecer "
            "apenas com base nos limites de especificação."
        )

    with tab3:
        st.markdown("#### Alertas recentes")
        if alerts:
            df_alerts = pd.DataFrame(alerts)
            df_alerts["created_at"] = pd.to_datetime(df_alerts["created_at"])
            df_alerts = df_alerts.rename(
                columns={
                    "created_at": "Data/Hora",
                    "level": "Nível",
                    "message": "Mensagem",
                    "meta": "Meta",
                    "id": "ID",
                }
            )
            st.dataframe(df_alerts, use_container_width=True)
        else:
            st.info("Nenhum alerta registrado ainda.")


# ----------------- PÁGINA: INSIGHTS COM IA -----------------
elif page == "🧠 Insights com IA (Gemini)":
    st.title("🧠 Insights com IA (Gemini)")
    st.markdown(
        "Use a camada de IA para interpretar **CP, CPK, anomalias e tendências** do processo."
    )

    col_left, col_right = st.columns([1.2, 1.8])

    with col_left:
        st.subheader("📄 Relatório automático")
        st.caption(
            "Gera uma análise textual sobre capacidade do processo e anomalias identificadas."
        )
        if st.button("✨ Gerar explicação com IA"):
            try:
                res = fetch_json("/llm/explain", method="POST")
                st.markdown("##### Resultado")
                st.markdown(res["text"])
            except Exception as e:
                st.error(f"Erro ao chamar IA: {e}")

    with col_right:
        st.subheader("💬 Chat especialista em CEP + IA")
        st.caption("Converse com a IA sobre o comportamento do processo.")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # render histórico
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_input = st.chat_input(
            "Faça uma pergunta sobre o processo, CP, CPK, anomalias, estabilidade, etc."
        )
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            try:
                res = fetch_json(
                    "/llm/chat",
                    method="POST",
                    json={"history": st.session_state.chat_history},
                )
                answer = res["answer"]
            except Exception as e:
                answer = f"Erro ao falar com Gemini: {e}"

            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.experimental_rerun()
