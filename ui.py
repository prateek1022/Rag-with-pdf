import streamlit as st
import pandas as pd
import base64
from config import ( # Import constants from config.py
    APP_TITLE, APP_ICON, USER_AVATAR, BOT_AVATAR,
    LINKEDIN_URL,  GITHUB_URL
)
# Import the new function from utils
from utils import display_vector_store_contents

# --- CSS Styling ---
def load_css():
    """Loads the appropriate CSS file based on the current theme."""
    theme = st.session_state.get('theme', 'dark')
    css_file = 'dark_theme.css' if theme == 'dark' else 'light_theme.css'
    with open(css_file, 'r') as f:
        css = f.read()
    return f'<style>{css}</style>'

# --- Chat Display Function ---
def display_chat_message(is_user, content):
    """Display a chat message using Streamlit's chat elements."""
    avatar = USER_AVATAR if is_user else BOT_AVATAR
    role = "user" if is_user else "assistant"
    with st.chat_message(name=role, avatar=avatar):
        st.markdown(content)

# --- Helper Functions (Download Button, Social Links) ---
def display_download_button():
    """Display a button to download conversation history."""
    if st.session_state.get('conversation_history'): # Check if history exists
        df = pd.DataFrame(
            st.session_state.conversation_history,
            columns=["Question", "Answer", "Model", "Timestamp", "PDF Name"]
        )
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
           label="📥 Download Chat History",
           data=csv,
           file_name="conversation_history.csv",
           mime="text/csv",
           key='download-csv',
           use_container_width=True
        )

def display_social_links():
    """Display social media links."""
    st.markdown("##### Connect with the Developer")
    st.markdown(
        f"""
        <a href="{LINKEDIN_URL}" target="_blank"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"></a>
        <a href="{GITHUB_URL}" target="_blank"><img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"></a>
        """,
        unsafe_allow_html=True # Kaggle link already removed, ensuring state
    )

# --- Main Application UI Rendering ---
def render_main_app(process_pdf_callback, process_question_callback):
    """Renders the main application interface after login."""

    # --- Sidebar ---
    with st.sidebar:
        # Replace Settings title with personalized greeting
        st.title(f"👋 Welcome, {st.session_state.username}!")
        # Removed redundant markdown welcome message
        st.markdown("---")

        # --- PDF Management Section ---
        st.subheader("📄 PDF Management")

        # Display list of already processed files
        processed_files = st.session_state.get('processed_filenames', [])
        if processed_files:
            st.markdown("**Processed Files:**")
            # Use markdown for a scrollable list
            list_markdown = "<ul>" + "".join([f"<li>{f}</li>" for f in processed_files]) + "</ul>"
            st.markdown(f'<div class="processed-files-list">{list_markdown}</div>', unsafe_allow_html=True)
        else:
            st.markdown("_No PDFs processed yet for this session._")

        # PDF Uploader
        pdf_docs = st.file_uploader(
            "Upload New PDF Files", accept_multiple_files=True, type=['pdf'], key='pdf_uploader'
        )
        if pdf_docs:
            file_names = [pdf.name for pdf in pdf_docs]
            # Display only newly uploaded names, not confirming processing yet
            # st.success(f"Ready to process: {', '.join(file_names)}")

        # Process button - Calls the callback from app.py
        if st.button("🚀 Process Uploaded PDFs", key="process_pdfs_button", use_container_width=True):
            if not pdf_docs:
                st.warning("Please upload new PDF files to process.")
            else:
                process_pdf_callback(pdf_docs) # Pass newly uploaded pdf_docs

        st.markdown("---")

        # --- Actions Section (using expander) ---
        with st.expander("🛠️ Actions & Info"):
            # Logout Button
            if st.button("🚪 Logout", key="logout_button", use_container_width=True):
                # Clear session state related to login and app data
                keys_to_clear = [
                    'logged_in', 'username', 'api_key', 'conversation_history',
                    'vector_store_created', 'processed_files', 'current_pdfs',
                    'login_error', 'show_api_key_input', 'processed_filenames' # Clear filenames too
                ]
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun() # Go back to login page

            # Clear Chat Button
            if st.button("🧹 Clear Chat", key="clear_chat_button", use_container_width=True):
                st.session_state.conversation_history = []
                st.success("Chat history cleared!")
                st.rerun()

            # Theme toggle button
            if 'theme' not in st.session_state:
                st.session_state.theme = 'dark'

            if st.button("Toggle Theme", key="toggle_theme_button", use_container_width=True):
                st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
                st.rerun() # Rerun to apply CSS changes

            # Display download button
            display_download_button()

            # Display social links
            st.markdown("<br>", unsafe_allow_html=True)
            display_social_links()

            st.markdown("---")

            # Button to display vector store contents
            if st.button("View Vector Store Contents", key="view_vector_store", use_container_width=True):
                username = st.session_state.get('username')
                api_key = st.session_state.get('api_key')
                if not username or not api_key:
                    st.error("User session invalid. Please log in again.")
                else:
                    vs_contents = display_vector_store_contents(username, api_key)
                    if vs_contents:
                        st.text_area("Vector Store Contents:", value=vs_contents, height=400)
                    else:
                        st.info("No data to display in vector store.")

        st.markdown("---") # Add a divider

        # --- Debug Log Section (New) ---
        with st.expander("⚙️ Debug Logs", expanded=False):
            debug_logs = st.session_state.get('debug_logs', [])
            if debug_logs:
                if st.button("Clear Logs", key="clear_debug_logs", use_container_width=True):
                    st.session_state.debug_logs = []
                    st.rerun()

                # Display logs in reverse order (newest first)
                st.markdown("---") # Divider before logs
                log_container = st.container(height=300) # Scrollable container
                with log_container:
                    for log_entry in reversed(debug_logs):
                        st.code(log_entry, language=None) # Use st.code for better formatting
            else:
                st.info("No debug logs recorded yet.")


    # --- Main content area - Chat Interface ---
    st.header(f"{APP_ICON} {APP_TITLE}")
    st.markdown(f"Chatting as **{st.session_state.username}**. Interact with your uploaded PDFs below.")
    st.markdown("---")


    # Display existing chat messages from history
    for question, answer, model_name, timestamp, pdf_name in st.session_state.conversation_history:
        display_chat_message(True, question)
        display_chat_message(False, answer)

    # Chat input
    prompt = st.chat_input(
        placeholder="Ask a question about the processed PDFs...",
        key="user_question_input",
        # Enable chat input if the vector store is ready (or assumed ready based on processed files)
        disabled=not st.session_state.get('vector_store_created', False) and not processed_files
    )

    # Handle new user input - Calls the callback from app.py
    if prompt:
        # Pass only the prompt; pdf_docs are not needed here as context comes from user's store
        process_question_callback(prompt)
        # Rerun handled in app.py after callback finishes

    # Initial state messages in the main area (after login)
    elif not processed_files and not pdf_docs: # If no files processed and none uploaded
        st.info("👈 Please upload one or more PDF files in the sidebar and click 'Process'.")
    elif not st.session_state.get('vector_store_created', False) and not processed_files:
         # This state might occur if processing failed or hasn't happened yet
         st.warning("👈 Please click 'Process Uploaded PDFs' in the sidebar after uploading files.")
    elif not st.session_state.conversation_history and (st.session_state.get('vector_store_created', False) or processed_files):
        st.info("Your PDFs are processed. Ask your first question below!")
