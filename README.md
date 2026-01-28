# 🤖 Intelligent Data Room

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://simplview-intelligent-data-room-syauqi.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Gemini](https://img.shields.io/badge/AI-Google%20Gemini-orange)

A Multi-Agent AI application that allows users to "talk" to their CSV/Excel data. Instead of a simple chatbot, this system uses a **"Think, then Do"** architecture where a **Planner Agent** strategizes the analysis and an **Executor Agent** writes the Python code to visualize it.

---

## 📸 Demo

<img width="1680" height="965" alt="Screenshot 2026-01-28 at 19 00 05" src="https://github.com/user-attachments/assets/35620283-de53-4544-9a0f-545eb7a190ab" />

---

## ✨ Key Features

- **🧠 Multi-Agent Workflow:**
  - **Agent 1 (The Planner):** Analyzes your data schema and creates a step-by-step "Execution Plan" before any code is written.
  - **Agent 2 (The Executor):** Uses PandasAI and Google Gemini to write Python code, execute it in a sandbox, and generate publication-quality charts.
- **📊 Automatic Visualization:** intelligently decides when to plot data (Bar, Line, Scatter) vs when to show tables.
- **💾 Smart History & Caching:**
  - Sidebar gallery automatically saves every generated chart.
  - Users can download charts directly from the history.
  - Hovering over a sidebar item shows the full prompt that generated it.
- **🛡️ Data Safety:** Built-in validation ensures no code is executed on empty dataframes, and file paths are strictly sanitized.

---

## 🏗️ System Architecture

The application splits the cognitive load to improve accuracy:

1.  **User Input:** *"Compare sales between Q1 and Q2."*
2.  **Planner Agent (Gemini 1.5 Flash):**
    * *Input:* Data Schema + User Query.
    * *Output:* A structured JSON plan (e.g., "Filter by Date > Group by Quarter > Sum Revenue").
3.  **Executor Agent (PandasAI):**
    * *Input:* Execution Plan.
    * *Action:* Generates Python code using `Altair` for visualization.
    * *Output:* Renders the chart and provides a text summary.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or 3.11
- A Google Cloud API Key (for Gemini)

### Installation

1. **Clone the repository**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/intelligent-data-room.git](https://github.com/YOUR_USERNAME/intelligent-data-room.git)
   cd intelligent-data-room
