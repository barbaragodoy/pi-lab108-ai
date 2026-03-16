# 🧪 SmartTwin CEP  
### Gêmeo Digital + CEP + IA para Controle Estatístico de Processo

> MVP desenvolvido como Projeto Integrador aplicando **método científico**, **Controle Estatístico de Processo (CEP)**, **Índices de Capacidade (Cp, Cpk)** e **Inteligência Artificial (Gemini)** sobre um processo real de **envase de leite UHT longa vida**.

---

## 🚀 Como rodar o projeto (passo a passo)

Siga os passos abaixo para deixar o **SmartTwin CEP** rodando no seu ambiente.

### 1. Pré-requisitos

- **Python 3.10+** instalado ([python.org](https://www.python.org/downloads/)).
- (Opcional) **Git**, se for clonar o repositório.

### 2. Clonar e entrar na pasta do projeto

```bash
git clone <url-do-repositorio>
cd pi-lab108-ai
```

*(Se você já tiver o código, apenas abra o terminal na pasta do projeto.)*

### 3. Criar e ativar um ambiente virtual (recomendado)

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalar as dependências

Na raiz do projeto (com o venv ativado):

```bash
pip install -r requirements.txt
```

### 5. Configurar variáveis de ambiente (opcional para IA)

Para usar **insights e chat com o Gemini**, crie um arquivo `.env` na raiz do projeto:

```env
GEMINI_API_KEY=sua_chave_aqui
```

*(Ou use `GOOGLE_API_KEY` com a mesma chave.)*  
Sem essa chave, o sistema roda normalmente; apenas as funções de explicação por LLM ficarão desabilitadas.

### 6. Subir o backend (API FastAPI)

No terminal, **na raiz do projeto**:

```bash
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

- A API ficará em: **http://localhost:8000**
- Documentação interativa: **http://localhost:8000/docs**
- O banco SQLite (`smarttwin.db`) é criado automaticamente na raiz ao subir a API.

### 7. Subir o frontend (Streamlit)

Em **outro terminal**, na raiz do projeto (com o mesmo venv ativado):

```bash
streamlit run frontend/app.py
```

- O dashboard abrirá em: **http://localhost:8501**

### 8. Usar o sistema

1. Acesse **http://localhost:8501** no navegador.
2. Use o dashboard para enviar dados (upload de CSV ou simulador), ver gráficos CEP, Cp/Cpk e chat com a IA (se tiver configurado `GEMINI_API_KEY`).

---

| Serviço   | URL                  | Descrição        |
|----------|----------------------|------------------|
| Frontend | http://localhost:8501 | Dashboard Streamlit |
| Backend  | http://localhost:8000 | API FastAPI      |
| Docs API | http://localhost:8000/docs | Swagger UI   |

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
