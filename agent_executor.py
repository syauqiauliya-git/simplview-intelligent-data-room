import os
from dotenv import load_dotenv
import pandas as pd
from pandasai import SmartDataframe
from pandasai_litellm.litellm import LiteLLM
import tempfile # <--- NEW
import pathlib  # <--- NEW
from typing import Union, List, Dict, Any

load_dotenv()

# Create a temp dir that works on any OS (Windows/Mac/Linux)
CHART_DIR = pathlib.Path(tempfile.mkdtemp()) / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

def clean_and_validate_result(result):
    """
    The 'Python Validator' Layer.
    """
    # 1. Handle Empty Data Error specifically
    if isinstance(result, str) and "No data found" in result:
        return result 

    # 2. Convert lists/dicts to Markdown
    if isinstance(result, (list, dict)):
        import pandas as pd
        try:
            df = pd.DataFrame(result)
            return df.to_markdown()
        except:
            return str(result)
            
    # 3. Format numbers
    if isinstance(result, (int, float)):
        return f"{result:,.2f}"
        
    # 4. Check for broken image paths
    if isinstance(result, str) and result.endswith(".png"):
        if not os.path.exists(result):
            return "Error: Chart was generated but file is missing."
            
    return result

def execute_analysis(df: pd.DataFrame, planner_output: str, user_query: str) -> str:
    """
    Agent 2: The Executor (Powered by LiteLLM)
    """
    
    # 1. Initialize LiteLLM with STABLE model
    llm = LiteLLM(
        model="gemini/gemini-2.5-flash", 
        api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # 2. Configure SmartDataframe
    sdf = SmartDataframe(df, config={
        "llm": llm, 
        "enable_cache": False,
        "save_charts": True,
        "save_charts_path": str(CHART_DIR), # <--- USE THE TEMP PATH
        "verbose": True
    })
    
    # 3. Construct the prompt with FIXED SYNTAX RULES
    execution_prompt = f"""
    You are a Senior Python Data Analyst & Visualization Expert. 
    Your goal is to produce publication-quality charts using the 'altair' library.
    
    PLAN:
    {planner_output}
    
    CONTEXT (User Question):
    {user_query}
    
    --- 🛡️ DATA SAFETY RULES (MUST RUN FIRST) ---
    1. **CHECK EMPTINESS:** Before any plotting, you MUST check if your filtered DataFrame is empty.
       - USE THIS EXACT PATTERN: 
         `if df.empty: result = "⚠️ No data found for this request. Please check your filters."`
       - **DO NOT use 'return'.** Use 'result = ...' instead.
    
    --- 📅 DATE HANDLING RULES ---
    1. **INSPECTION:** Do NOT assume a format. Check the string format first.
    2. **CONVERSION:** Use `pd.to_datetime(df['Order Date'], dayfirst=False, errors='coerce')` as a safe default.
    
    --- 🔧 CODE CONSTRAINTS (CRITICAL) ---
    1. **SQL DIALECT:** Use `STRPTIME` (DuckDB), NOT `TO_DATE`.
    
    2. **FILE SAVING (THE "BASENAME" RULE):**
       - The variable `CHART_DIR` is set to: {str(CHART_DIR)}
       - You MUST use `os.path.basename()` to strip any accidental folders from the filename.
       - **REQUIRED PATTERN:**
         ```python
         # 1. Define base filename (even if you add paths, basename fixes it)
         raw_filename = "exports/charts/my_chart.png"
         clean_filename = os.path.basename(raw_filename) 
         
         # 2. Save using the clean path
         final_path = f"{{CHART_DIR}}/{{clean_filename}}"
         chart.save(final_path)
         
         # 3. Return the result
         result = {{'type': 'plot', 'value': final_path}}
         ```

    --- 📊 VISUALIZATION RULES (LABELS ARE MANDATORY) ---
    
    1. **LABELS:** All bar charts MUST have labels.
       - Use `mark_text(dy=-10)` for positive values and `mark_text(dy=10)` for negative values to place text OUTSIDE the bar.
       - Ensure you do NOT add the text layer twice for the same data points.
       - Example: `chart = (bars + text).properties(...)`
    
    2. **COMPARISONS (Grouped Bars):** - Use `xOffset` for side-by-side bars.
       - Pattern: `alt.Chart(df).mark_bar().encode(x='Category', y='Value', color='Metric', xOffset='Metric')`.
    
    3. **LAYOUT:** - `.properties(width=600, height=400)` is MANDATORY.
       - Use `labelAngle=-45` for X-axis labels if there are many items.
    
    4. **FILE SAVING:** - The variable `CHART_DIR` is set to: {str(CHART_DIR)}
       - Save exactly as: `chart.save(f"{{CHART_DIR}}/chart_ID.png")`
       - **CRITICAL:** DO NOT use `chart.show()`, `chart.display()`, or `plt.show()`. This crashes the server. ONLY save.

    5. **SCATTER PLOTS (Smart Handling):** - IF rows > 1000: AGGREGATE (e.g., `groupby().mean()`) and plot trend line.
       - IF rows < 1000: Plot raw scatter points.

    --- DATA OUTPUT RULES ---
    - **Verification:** After generating the chart, return a string summary of the Top 3 Insights.
    - **Tables:** Return a Pandas DataFrame.
    """
    
    # 4. Run!
    result = sdf.chat(execution_prompt)
    
    # 5. Run the Validator
    return clean_and_validate_result(result)