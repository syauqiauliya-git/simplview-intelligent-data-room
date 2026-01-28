import os
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
from typing import List, Dict, Any # Make sure to import this at top
import re
import json


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

# REPLACE THE ENTIRE plan_execution FUNCTION WITH THIS:

def plan_execution(user_query: str, df: pd.DataFrame, history: List[Dict[str, Any]] = []) -> Dict[str, Any]:
    """
    Agent 1: The Strategist
    """
    schema = get_data_schema(df)

    previous_clarifications = [msg for msg in history if "CLARIFICATION_NEEDED" in str(msg.get("content", ""))]
    clarification_count = len(previous_clarifications)
    
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
    1. Analyze the request. Is the request specific or vague?
    2. **Anti-Nagging:** If clarification_count > 0 ({clarification_count}), output a PLAN.
    3. **Visualization:** explicitly decide if a chart is needed.
    4. **Output:** Return a JSON object ONLY. Do not wrap it in markdown.
    
    --- JSON SCHEMA ---
    
    CASE 1: Vague Request (and count=0)
    {{
        "type": "clarification",
        "message": "The request is vague...",
        "options": ["Option 1", "Option 2", "Option 3"]
    }}
    
    CASE 2: Specific Request (or count>0)
    {{
        "type": "plan",
        "steps": [
            "1. Filter data...",
            "2. Group by...",
            "3. Plot..."
        ],
        "consultant_note": "I chose a horizontal bar chart because...",
        "visualization_needed": true,
        "visualization_type": "bar" 
        // Valid Options: 
        // - 'bar' (standard vertical)
        // - 'horizontal_bar' (good for long labels/many categories)
        // - 'line' (trends over time)
        // - 'multi_line' (comparing trends)
        // - 'scatter' (correlations)
        // - 'pie' (part-to-whole)
        // - 'count' (frequency of occurrences)
        // - 'map' (geospatial data)
        // - 'none'
    }}
    """
    
    # Use the Correct Model
    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )
    
    response = model.generate_content(system_prompt)
    return extract_json_from_response(response.text)
    

def extract_json_from_response(response_text: str) -> dict:
    """Robust JSON extraction from LLM response"""
    import re
    import json
    
    # Try direct parse
    try:
        return json.loads(response_text)
    except:
        pass
    
    # Extract from markdown code block
    pattern = r'```(?:json)?\s*({.*?})\s*```'
    match = re.search(pattern, response_text, re.DOTALL)
    
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    
    # Fallback to prevent crashes
    return {
        "type": "plan",
        "steps": ["1. Analyze the data request"],
        "consultant_note": "Default plan due to parsing issues"
    }