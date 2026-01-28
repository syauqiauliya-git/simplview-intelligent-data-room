# 🤖 Intelligent Data Room

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://simplview-intelligent-data-room-syauqi.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Gemini](https://img.shields.io/badge/AI-Google%20Gemini-orange)

A Multi-Agent AI application that allows users to "talk" to their CSV/Excel data. Instead of a simple chatbot, this system uses a **Planner-Executor Architecture** to ensure accurate data analysis and visualization.

<img width="958" height="898" alt="Screenshot 2026-01-28 at 19 07 54" src="https://github.com/user-attachments/assets/8b067cc5-270b-4aec-b54e-5f2977e3677b" />


## ✨ Key Features

- **🧠 Multi-Agent Workflow:**
  - **Agent 1 (The Planner):** Analyzes your request and data schema to build a step-by-step "Execution Plan." It decides *if* a chart is needed and *what* kind (Bar, Line, Scatter, etc.).
  - **Agent 2 (The Executor):** A code-generating agent (powered by PandasAI) that writes Python code to execute the plan and generate the visualization.
- **📊 Auto-Visualization:** Automatically detects trends and renders publication-quality charts using `Altair` or `Matplotlib`.
- **📂 Sidebar Gallery:** A "History" sidebar that caches every generated chart, allowing you to review and download previous insights easily.
- **🛡️ Data Safety:** Built-in validation prevents execution on empty dataframes and secures file uploads (Max 10MB).
- **📝 Explainable AI:** Users can expand the "Execution Plan" dropdown to see exactly how the agent intends to solve the problem before the code runs.

## 🏗️ System Architecture

The application splits the cognitive load into two distinct phases:

1.  **Phase 1: Strategy (Planner Agent)**
    * **Input:** User Question + Data Schema (Column Types, Missing Values).
    * **Output:** A structured JSON Plan + Consultant Note.
2.  **Phase 2: Execution (Executor Agent)**
    * **Input:** The Plan from Agent 1.
    * **Action:** Generates Python code in a sandbox.
    * **Output:** A Visual Chart or Data Table.

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or 3.11
- A Google Cloud API Key (Gemini)

### Installation

1. **Clone the repository**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/intelligent-data-room.git](https://github.com/YOUR_USERNAME/intelligent-data-room.git)
   cd intelligent-data-room

```

2. **Install Dependencies**
```bash
pip install -r requirements.txt

```

3. **Set up Environment**
Create a `.env` file in the root directory:
```bash
GOOGLE_API_KEY="AIzaSyYourKeyHere..."

```

4. **Run the App**
```bash
streamlit run app.py

```

## 📂 Project Structure

```text
├── app.py                 # Main Streamlit UI & Orchestrator
├── agent_planner.py       # Agent 1: Logic, Schema Analysis, JSON Planning
├── agent_executor.py      # Agent 2: PandasAI Configuration, Code Execution
├── requirements.txt       # Dependencies
├── runtime.txt            # Streamlit Cloud Config (Python 3.11)
└── .env                   # API Keys (Not committed)

```

## 📸 Screenshots

### 1. The Execution Plan

*Agent 1 breaks down the problem before solving it.*
<img width="1032" height="335" alt="Screenshot 2026-01-28 at 19 08 33" src="https://github.com/user-attachments/assets/b7b13c0e-b13f-4653-99cc-b32d9a13a3e6" />


### 2. Analysis History

*The sidebar keeps track of your charts.*
<img width="382" height="868" alt="Screenshot 2026-01-28 at 19 09 43" src="https://github.com/user-attachments/assets/dd697a57-49da-4231-9d93-45a6c32e1386" />

## 🛠️ Tech Stack

* **Frontend:** Streamlit
* **LLM Orchestration:** Google Gemini (2.5 Flash)
* **Data Engine:** PandasAI + Pandas
* **Visualization:** Altair

## 📄 License

This project is open-source and available under the MIT License.

```
