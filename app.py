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
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = None
if "trigger_retry" not in st.session_state:
    st.session_state.trigger_retry = False
if "redo_in_progress" not in st.session_state:
    st.session_state.redo_in_progress = False

# --- SIDEBAR ---
with st.sidebar:
    st.header("1. Upload Data")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    
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
                for img_idx, img_path in enumerate(msg["images"]):
                    if os.path.exists(img_path):
                        prompt_text = msg.get("trigger_prompt", "Unknown")
                        # Unique key for every single image
                        unique_key = f"{len(visuals)-i}_{img_idx}"
                        
                        with st.expander(f"Visual {unique_key}: {prompt_text[:20]}...", expanded=False):
                            st.image(img_path, use_container_width=True)
                            with open(img_path, "rb") as file:
                                st.download_button("Download", file, os.path.basename(img_path), "image/png", key=f"dl_sidebar_{unique_key}")
        else:
            st.info("No visuals generated yet.")

# --- PROCESSING FUNCTION ---
def process_prompt(prompt_text, df, is_redo=False):
    with st.chat_message("assistant"):
        status_container = st.empty()
        
        try:
            # 1. PLANNER PHASE
            status_container.markdown("🧠 **Agent 1 (Planner):** Thinking...")
            
            # Logic to handle Redo
            effective_prompt = prompt_text
            if is_redo:
                effective_prompt += " (NOTE: The user was unsatisfied. Try a DIFFERENT approach.)"
                
            plan = plan_execution(effective_prompt, df, st.session_state.messages)
            
            # --- NEW: CLARIFICATION CHECK ---
            if "CLARIFICATION_NEEDED" in plan:
                status_container.empty()
                
                # Clean up the tag
                clarification_text = plan.replace("CLARIFICATION_NEEDED:", "").strip()
                
                # Show the question to user
                st.markdown(f"**🤖 I need a bit more detail:**\n\n{clarification_text}")
                
                # Save to history so the next turn remembers this context
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": clarification_text,
                    "images": [] # No images for clarification
                })
                return  # <--- STOP HERE. Don't run the executor.

            # If we are here, the plan is solid. Proceed.
            with st.expander("See Execution Plan", expanded=False):
                st.markdown(plan)
            
            # 2. EXECUTOR PHASE
            status_container.markdown("⚙️ **Agent 2 (Executor):** Generating Visuals...")
            result = execute_analysis(df, plan, prompt_text)
            
            status_container.empty()
            
            # 3. RESULT PROCESSING (REGEX FIX)
            final_response = {
                "role": "assistant", 
                "content": str(result), 
                "images": [],
                "trigger_prompt": prompt_text
            }
            
            # Use Regex to find ALL png paths in the output text
            # This fixes the "Invisible Chart" bug
            image_paths = re.findall(r'(exports/charts/[\w\-]+\.png)', str(result))
            valid_images = [img for img in image_paths if os.path.exists(img)]
            
            final_response["images"] = valid_images

            # --- THE CLEANUP FIX ---
            # Remove the ugly file paths from the text, since we show the image separately
            clean_content = str(result)
            for img in valid_images:
                clean_content = clean_content.replace(img, "")
            
            # If the agent only returned a path (now empty), add a default message
            if not clean_content.strip():
                clean_content = "I have generated the visualization based on your request."
                
            final_response["content"] = clean_content.strip()
            
            # Render Text
            st.markdown(final_response["content"])
            
            # Render Images
            for img in valid_images:
                st.image(img, caption=f"Generated for: '{prompt_text}'")
            
            st.session_state.messages.append(final_response)
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.session_state.trigger_retry = True

# --- MAIN LOGIC ---
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if not st.session_state.messages:
        st.sidebar.success("Data Loaded!")

    # 1. Display History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # Render any images attached to this message
            if "images" in msg:
                for img in msg["images"]:
                    if os.path.exists(img):
                        st.image(img)

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
    st.info("Please upload a CSV file to begin.")