# DalalStreet AI — Indian Stock Market Advisor & Portfolio Analyst

![DalalStreet AI Demo](demo.gif)

**DalalStreet AI** is an autonomous financial assistant and portfolio advisor for the Indian stock market (NSE/BSE), built with the **Google Agent Development Kit (ADK)** and powered by **Gemini 2.5 Flash**.

---

## 🚀 Wired Features & GCP Integrations

This project implements the following capabilities and Google Cloud services:

* **🧠 Vertex AI Memory Bank**: Retains user preferences, investment guidelines, and context across sessions using `VertexAiMemoryBankService`.
* **🔥 Google Cloud Firestore**: Stores and queries stock records (tickers, P/E ratios, market cap, analyst recommendations) in the `indian_stocks` database collection.
* **📦 Google Cloud Storage**: Hosts generated stock market media assets in a dedicated public bucket.
* **🎨 Vertex AI Image Generation**: Generates infographic banners for stock analysis using `gemini-3.1-flash-lite-image`.
* **🎬 Google Omni Video Generation**: Produces animated stock market videos using `gemini-omni-flash-preview` in the `global` location.
* **🛡️ Agent Engine Sandbox**: Executes Python code safely for discounted cash flow (DCF) valuations and financial modeling.
* **🗺️ Google Maps Services**: Geocodes address locations and finds nearby bank/financial branches.
* **📈 Real-Time Market Data**: Fetches live exchange rates (USD/INR) and real-time Indian stock market quotes.
* **💎 Agent-to-User Interface (A2UI v0.8)**: Renders structured, rich cards and UI components seamlessly within the conversation flow.
* **⚡ FastAPI Proxy & Custom Frontend**: Serves a responsive web interface tailored for financial analysis.

---

## 🛠️ Project Structure

```
dalalstreet-ai/
├── app/                        # Core agent logic and ADK tool definitions
│   ├── agent.py                # System prompt, Memory Bank, Firestore & AI tools
│   ├── fast_api_app.py         # FastAPI backend server
│   └── a2ui_utils.py           # A2UI callback wrappers
├── frontend/                   # Web frontend proxy & user interface
│   ├── main.py                 # FastAPI proxy server for A2A / Reasoning Engine
│   ├── static/index.html       # Branded chat UI with prompt chips & A2UI renderer
│   └── Dockerfile              # Cloud Run container configuration
├── demo.gif                    # Animated demonstration preview
├── pyproject.toml              # Project dependencies & tool configurations
└── agents-cli-manifest.yaml    # Agents CLI deployment manifest
```

---

## 💻 Local Setup & Execution Instructions

### Prerequisites
* Python 3.11+
* `uv` package manager (`pip install uv`)
* `google-agents-cli` (`uv tool install google-agents-cli`)
* Google Cloud SDK (`gcloud`) with authenticated project credentials

### 1. Install Dependencies
```bash
agents-cli install
```

### 2. Run Agent Playground Locally
To launch the interactive ADK agent playground locally:
```bash
agents-cli playground
```

### 3. Run Web Frontend Locally
Navigate to the `frontend` folder and start the FastAPI proxy server:
```bash
cd frontend
pip install -r requirements.txt
export AGENT_ENGINE_RESOURCE_NAME="<YOUR_AGENT_ENGINE_RESOURCE_NAME>"
export AGENT_DIRECTORY="app"
python main.py
```
*(Once started, open your web browser to the server port shown in terminal output, typically port 8080).*

---

## ☁️ Deployment

Deploy the agent logic to Google Cloud Agent Runtime:
```bash
agents-cli deploy --project <YOUR_GCP_PROJECT_ID> --service-name simple-agent
```

Deploy the frontend container to Cloud Run:
```bash
gcloud run deploy dalalstreet-ai-frontend \
  --source ./frontend \
  --region us-east1 \
  --project <YOUR_GCP_PROJECT_ID> \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="<YOUR_AGENT_ENGINE_RESOURCE_NAME>",AGENT_DIRECTORY="app"
```
