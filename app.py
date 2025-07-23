import streamlit as st
import nest_asyncio # Import nest_asyncio
nest_asyncio.apply() # Apply the patch

# Import configurations and constants
from config import APP_TITLE, APP_ICON

# Import authentication and database functions
from auth import init_db, render_login_page

# Import UI rendering functions
from ui import load_css, render_main_app

# Import utility and processing functions
from utils import process_user_question, process_uploaded_pdfs

# --- Session State Initialization ---
def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    defaults = {
        'conversation_history': [],
        'vector_store_created': False, # Tracks if VS is loaded/created *in this session*
        # 'processed_files': set(), # No longer needed, using DB
        # 'current_pdfs': None, # No longer needed, using DB filenames
        'username': None,
        'api_key': None,
        'logged_in': False,
        'login_error': None,
        'show_api_key_input': False,
        'processed_filenames': [], # Stores filenames loaded from DB for the user
        'debug_logs': [] # Initialize list for debug/vector/LLM logs
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- Callback Functions ---
# These functions connect the UI actions (like button clicks) to the backend logic in utils.py

def handle_pdf_processing(pdf_docs):
    """Callback function to handle PDF processing for the logged-in user."""
    username = st.session_state.get('username')
    api_key = st.session_state.get('api_key')

    if not username or not api_key:
        st.error("User session invalid. Please log in again.")
        return

    # Call the actual processing function from utils, passing username and api_key
    success = process_uploaded_pdfs(pdf_docs, username, api_key)
    if success:
        # Optionally trigger a rerun if UI needs immediate update based on new files
        st.rerun()


def handle_question_processing(prompt):
    """Callback function to handle user question processing for the logged-in user."""
    username = st.session_state.get('username')
    api_key = st.session_state.get('api_key')

    if not username or not api_key:
        st.error("User session invalid. Please log in again.")
        return

    # Call the actual processing function from utils
    # pdf_docs are no longer needed here, context comes from user's vector store
    process_user_question(prompt, username, api_key)

    # Rerun to display the new message pair added to history by process_user_question
    st.rerun()


# --- Main Execution ---
def main():
    """Main application function."""
    # Configure the page
    st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")
    # Load custom CSS
    st.markdown(load_css(), unsafe_allow_html=True)

    # Initialize database and session state
    init_db()
    initialize_session_state()

    # Check login status and render appropriate page
    if not st.session_state.logged_in:
        render_login_page()
    else:
        # Pass the callback functions to the main app renderer
        render_main_app(
            process_pdf_callback=handle_pdf_processing,
            process_question_callback=handle_question_processing
        )

if __name__ == "__main__":
    main()
