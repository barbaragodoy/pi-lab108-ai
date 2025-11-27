# 🧪 SmartTwin CEP  
### Gêmeo Digital + CEP + IA para Controle Estatístico de Processo

> MVP desenvolvido como Projeto Integrador aplicando **método científico**, **Controle Estatístico de Processo (CEP)**, **Índices de Capacidade (Cp, Cpk)** e **Inteligência Artificial (Gemini)** sobre um processo real de **envase de leite UHT longa vida**.

---

## 🧠 Visão Geral

O **SmartTwin CEP** é um sistema que combina:

- 📡 **Monitoramento em tempo real** de uma variável crítica de processo (peso da embalagem de leite UHT);
- 📊 **Ferramentas clássicas de CEP** (média, desvio padrão, gráficos X̄ e R, Cp, Cpk, run rules);
- 🧬 **Gêmeo Digital** (modelo que prevê o comportamento esperado do processo);
- 🤖 **Detecção de anomalias com IA** (Isolation Forest e análise de resíduos);
- 🧠 **Explicações com LLM (Gemini)**, para transformar números em insights textuais.

Tudo isso em um MVP com:

- **Backend** em `FastAPI` + `SQLite`  
- **Frontend** em `Streamlit` + `Plotly`  
- Integração com **Gemini** via API (ADK) para geração de insights.

---

## 🎯 Problema de Negócio

Contexto real:

- **Produto:** leite UHT integral longa vida  
- **Operação:** envase  
- **Variável de medição:** peso da embalagem (1025 g – 1032 g)  
- **Máquina:** envasadora  
- **Seção:** processamento  
- **Operador:** Fabricio A. de Oliveira  
- **Período de análise:** 11/04/2021 a 10/05/2021  

O desafio é:

> **Garantir que o processo de envase mantenha o peso dentro dos limites de especificação, com estabilidade e capacidade adequada, identificando desvios e anomalias antes que causem perdas, retrabalho ou não conformidades.**

---

## 🔬 Método Científico Aplicado

### 1. **Observação**
Variação do peso no envase e risco de não conformidade.

### 2. **Problema**
O processo está estável e capaz?

### 3. **Hipóteses**
- H1: Processo é estável mas marginal em capacidade.  
- H2: IA + CEP melhora diagnóstico.  
- H3: LLM consegue traduzir métricas técnicas em insights operacionais.

### 4. **Coleta de Dados**
30 dias, 10 amostras por dia (08:00–17:00).

### 5. **Experimentação**
Modelos implementados:
- EMA (Gêmeo Digital)
- Isolation Forest
- Cp e Cpk
- X̄ e R
- Run Rules

### 6. **Análise**
Combinação CEP + IA → entendimento profundo do processo.

### 7. **Conclusão**
O SmartTwin CEP entrega previsões, diagnósticos, anomalias e recomendações automáticas.

---

## 🏗 Arquitetura da Solução

### Diagrama

```mermaid
flowchart LR
    subgraph Fonte_de_Dados
        CSV[Arquivo CSV<br/>Folha de Verificação]
    end

    subgraph Backend[Backend FastAPI + SQLite]
        API[API REST / FastAPI]
        DB[(SQLite)]
        MODELS[Gêmeo Digital<br/>EMA + CEP]
        ANOM[Detecção de Anomalias<br/>Isolation Forest]
        CEP[Estatísticas CEP<br/>Cp, Cpk, X̄, R]
        LLM[Integração LLM<br/>Gemini]
    end

    subgraph Frontend[Frontend Streamlit]
        UI[Dashboard CEP + IA]
        UPLOAD[Upload CSV]
        GRAFICOS[Gráficos Interativos<br/>Plotly]
        CHAT[Chat com IA]
    end

    CSV -->|Importação /data/upload-file| API
    API --> DB
    API --> MODELS
    MODELS --> ANOM
    MODELS --> CEP
    CEP --> API
    ANOM --> API
    API --> LLM
    API -->|JSON| UI
    UI --> CHAT
    UPLOAD --> UI
    UI -->|Chamada HTTP| API
