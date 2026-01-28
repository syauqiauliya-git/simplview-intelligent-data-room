import os
from dotenv import load_dotenv
import pandas as pd
from pandasai import SmartDataframe
from pandasai_litellm.litellm import LiteLLM

load_dotenv()

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
        "save_charts_path": "exports/charts",
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
    2. **CONVERSION:** Use `pd.to_datetime(df['Order Date'], dayfirst=False, errors='coerce')` as a safe default unless the format is clearly DD/MM/YYYY. 
    
    --- 📊 VISUALIZATION RULES (LABELS ARE MANDATORY) ---
    
    1. **LABELS:** All bar charts MUST have labels.
       - Use `mark_text(dy=-10)` for positive values and `mark_text(dy=10)` for negative values to place text OUTSIDE the bar.
       - Ensure you do NOT add the text layer twice for the same data points.
       - Example: `chart = (bars + text).properties(...)`
    
    2. **COMPARISONS (Grouped Bars):** - Use `xOffset` for side-by-side bars.
       - Pattern: `alt.Chart(df).mark_bar().encode(x='Category', y='Value', color='Metric', xOffset='Metric')`.
    
    3. **LAYOUT:** - `.properties(width=600, height=400)` is MANDATORY.
       - Use `labelAngle=-45` for X-axis labels if there are many items.
    
    4. **FILE SAVING:** - Save exactly as PNG: `chart.save('exports/charts/chart_ID.png')`.
    
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