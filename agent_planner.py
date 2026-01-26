import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY not found. Check your .env file!")

genai.configure(api_key=api_key)

def get_data_schema(df):
    schema = []
    for col, dtype in df.dtypes.items():
        sample_val = df[col].iloc[0] if not df.empty else "N/A"
        schema.append(f"{col} (Type: {dtype}, Sample: {sample_val})")
    return "\n".join(schema)

def plan_execution(user_query, df, history=[]):
    """
    Agent 1: The Strategist
    """
    schema = get_data_schema(df)

    # 1. Check History for previous clarifications to prevent loops
    previous_clarifications = [msg for msg in history if "CLARIFICATION_NEEDED" in str(msg.get("content", ""))]
    clarification_count = len(previous_clarifications)
    
    # Format history for the prompt
    history_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-5:]])

    system_prompt = f"""
    You are a Senior Data Strategist.
    
    DATASET SCHEMA:
    {schema}
    
    USER CONTEXT:
    {history_context}
    
    CURRENT QUESTION:
    {user_query}
    
    INSTRUCTIONS:
    1. **Analyze the Request:** Is it specific (e.g., "Sales by Region") or vague (e.g., "How is the business doing?")?
    2. **Anti-Nagging Protocol (CRITICAL):** - You have asked for clarification **{clarification_count}** times already.
       - If {clarification_count} > 0, do NOT ask again. Make an executive decision (e.g., "Assuming user wants Total Sales...") and generate a plan immediately.
    3. **Protocol for Vague Requests [FIRST-TIME ONLY]:** - Do NOT guess. Do NOT generate a complex execution plan.
       - Instead, output a response starting with **"CLARIFICATION_NEEDED:"**.
       - List 3 distinct options/metrics the user might want (e.g., "1. Sales Trend, 2. Profitability Analysis, 3. Regional Breakdown").
    4. **Protocol for Specific Requests:**
       - Generate a standard numbered execution plan.
       - Focus on the SINGLE most impactful chart/metric. Do NOT try to calculate 10 different things at once.
    
    OUTPUT FORMAT (Choose One):
    
    [Option A - If Vague]
    CLARIFICATION_NEEDED:
    The request is broad. Would you like to focus on:
    1. [Option 1]
    2. [Option 2]
    3. [Option 3]
    
    [Option B - If Specific Enough OR History > 0]
    1. [Step 1]
    2. [Step 2]
    ...
    **Consultant's Note:** [Explain or justify your executive decision making]
    """
    
    # Use Flash for speed
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(system_prompt)
    
    return response.text