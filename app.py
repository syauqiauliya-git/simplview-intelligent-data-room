import streamlit as st
import pandas as pd
import os
import re  # <--- NEW IMPORT
from dotenv import load_dotenv

# Import our two agents
from agent_planner import plan_execution
from agent_executor import execute_analysis

# Load env vars safely
load_dotenv()
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except Exception:
    pass

st.set_page_config(page_title="Intelligent Data Room", layout="wide")

st.title("🤖 Intelligent Data Room")
st.markdown("### Talk to your data with Multi-Agent AI")

# --- INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chart_cache" not in st.session_state: # <--- NEW
    st.session_state.chart_cache = {}     # Stores { "filename.png": bytes }
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = None
if "trigger_retry" not in st.session_state:
    st.session_state.trigger_retry = False
if "redo_in_progress" not in st.session_state:
    st.session_state.redo_in_progress = False

# --- SIDEBAR ---
with st.sidebar:
    st.header("1. Upload Data")
    uploaded_file = st.file_uploader("Upload Data", type=["csv", "xlsx"])
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.last_prompt = None
        st.session_state.redo_in_progress = False
        st.rerun()
        
    st.divider()
    
    # --- GALLERY SECTION ---
    st.header("2. Analysis History")
    if "messages" in st.session_state:
        # Find all messages with images
        visuals = [m for m in st.session_state.messages if m.get("images")]
        if visuals:
            for i, msg in enumerate(reversed(visuals)):
                # Handle potentially multiple images per message
                for img_idx, fname in enumerate(msg["images"]):
                    # LOOK IN CACHE, NOT DISK
                    if fname in st.session_state.chart_cache:
                        prompt_text = msg.get("trigger_prompt", "Unknown")
                        unique_key = f"{len(visuals)-i}_{img_idx}"
                        
                        # Get bytes
                        img_bytes = st.session_state.chart_cache[fname]
                        
                        with st.expander(f"Visual {unique_key}: {prompt_text[:20]}...", expanded=False):
                            st.image(img_bytes)
                            st.download_button(
                                label="Download", 
                                data=img_bytes,
                                file_name=fname,
                                mime="image/png", 
                                key=f"dl_sidebar_{unique_key}"
                            )
        else:
            st.info("No visuals generated yet.")
            
def validate_uploaded_file(uploaded_file) -> bool:
    """Validate uploaded file for security and format"""
    ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}
    MAX_SIZE_MB = 10
    
    # Check extension
    file_ext = '.' + uploaded_file.name.split('.')[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        st.error(f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
        return False
    
    # Check size (10MB limit)
    if uploaded_file.size > MAX_SIZE_MB * 1024 * 1024:
        st.error(f"File too large. Max size: {MAX_SIZE_MB}MB")
        return False
    
    return True

# --- PROCESSING FUNCTION ---
def process_prompt(prompt_text, df, is_redo=False):
    with st.chat_message("assistant"):
        status_container = st.empty()
        
        try:
            # 1. PLANNER PHASE
            status_container.markdown("🧠 **Agent 1 (Planner):** Thinking...")
            
            effective_prompt = prompt_text
            if is_redo:
                effective_prompt += " (NOTE: User unsatisfied. Try different approach.)"
            
            # Now gets a DICT
            plan_data = plan_execution(effective_prompt, df, st.session_state.messages)
            
            # --- LOGIC BRANCHING ---
            
            # CASE A: CLARIFICATION
            if plan_data.get("type") == "clarification":
                status_container.empty()
                options_text = "\n".join([f"- {opt}" for opt in plan_data.get("options", [])])
                message = f"**🤖 {plan_data['message']}**\n\n{options_text}"
                st.markdown(message)
                st.session_state.messages.append({"role": "assistant", "content": message, "images": []})
                return 
            
            # CASE B: EXECUTION PLAN
            steps = plan_data.get("steps", [])
            note = plan_data.get("consultant_note", "")
            formatted_plan = "\n".join(steps)
            if note:
                formatted_plan += f"\n\n**Consultant's Note:** {note}"
                
            with st.expander("See Execution Plan", expanded=False):
                st.markdown(formatted_plan)
            
            # 2. EXECUTOR PHASE
            status_container.markdown("⚙️ **Agent 2 (Executor):** Generating Visuals...")
            result = execute_analysis(df, formatted_plan, prompt_text)
            status_container.empty()
            
            # --- NEW: CACHE IMAGES ---
            # Regex Explanation:
            # [\w\-\./\\:]+  -> Matches letters, numbers, dashes, dots, slashes, backslashes, colons
            # \.png          -> Matches the .png extension
            image_paths = re.findall(r'([\w\-\./\\:]+\.png)', str(result))
            
            # Deduplicate and Filter
            unique_paths = list(dict.fromkeys(image_paths))
            
            valid_images = []
            for img_path in unique_paths:
                if os.path.exists(img_path):
                    # Read bytes into memory
                    with open(img_path, "rb") as f:
                        img_bytes = f.read()
                    
                    # Store in session cache
                    fname = os.path.basename(img_path)
                    st.session_state.chart_cache[fname] = img_bytes
                    valid_images.append(fname) # Store only filename in history
            
            # 3. RESULT PROCESSING

            final_response = {
                "role": "assistant", 
                "content": str(result), 
                "images": valid_images, # Store filenames, not full paths
                "plan": formatted_plan, 
                "trigger_prompt": prompt_text
            }            
            
            # Clean text
            clean_content = str(result)
            for img_path in unique_paths:
                clean_content = clean_content.replace(img_path, "")
            final_response["content"] = clean_content.strip() or "I have generated the visualization."       

            # Render
            st.markdown(final_response["content"])
            for fname in valid_images:
                if fname in st.session_state.chart_cache:
                    st.image(st.session_state.chart_cache[fname], caption=f"Generated for: '{prompt_text}'")
            
            st.session_state.messages.append(final_response)
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.session_state.trigger_retry = True

# --- MAIN LOGIC ---
if uploaded_file:
    if not validate_uploaded_file(uploaded_file):
        st.stop()  # Stop execution if validation fails
        
    # Check file extension to use correct loader
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
        
    if not st.session_state.messages:
        st.sidebar.success("Data Loaded!")

    # 1. Display History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            # A. Re-render the Plan (If it exists)
            if "plan" in msg and msg["plan"]:
                with st.expander("See Execution Plan", expanded=False):
                    st.markdown(msg["plan"])

            # B. Render the Answer Text
            st.markdown(msg["content"])
            
            # C. Render Images
            if "images" in msg:
                for fname in msg["images"]:
                    # Check if bytes exist in cache
                    if fname in st.session_state.chart_cache:
                        st.image(
                            st.session_state.chart_cache[fname], 
                            caption=f"Generated for: '{msg.get('trigger_prompt', 'User Request')}'"
                        )

    # 2. Check Auto-Redo
    if st.session_state.redo_in_progress:
        st.session_state.redo_in_progress = False 
        if st.session_state.last_prompt:
            process_prompt(st.session_state.last_prompt, df, is_redo=True)
            st.rerun()

    # 3. Buttons
    if st.session_state.trigger_retry:
        if st.button("🔄 An error occurred. Try again?"):
            st.session_state.trigger_retry = False
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
                st.session_state.messages.pop()
            process_prompt(st.session_state.last_prompt, df, is_redo=False)
            st.rerun()

    if not st.session_state.redo_in_progress and st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        # Only show Redo if it wasn't a clarification question
        last_msg = st.session_state.messages[-1]
        if "CLARIFICATION_NEEDED" not in str(last_msg["content"]): 
            col1, col2 = st.columns([0.8, 0.2])
            with col2:
                if st.button("Not satisfied? Redo 🔀"):
                    st.session_state.messages.pop()
                    st.session_state.redo_in_progress = True
                    st.rerun()

    # 4. Input
    if prompt := st.chat_input("Ask a question..."):
        st.session_state.trigger_retry = False
        st.session_state.redo_in_progress = False
        st.session_state.last_prompt = prompt
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        process_prompt(prompt, df, is_redo=False)
        st.rerun()

else:
    st.info("Please upload a CSV or XLSX file to begin.")