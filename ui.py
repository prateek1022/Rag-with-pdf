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
    theme = st.session_state.get('theme', 'dark') # Get current theme, default to dark

    if theme == 'dark':
            bg_color = "#121212"       # Rich dark background
            text_color = "#E0E0E0"     # Light grey text for less strain
            sidebar_bg = "#1E1E1E"     # Slightly lighter sidebar
            input_bg = "#2C2C2C"       # Medium dark input background
            msg_user_bg = "#2A2D34"    # Slight bluish tint for user messages
            msg_bot_bg = "#31363F"     # Slightly lighter bluish tint for bot messages
            border_color = "#3C3C3C"   # Subtle border color
    else:  # Light theme
            bg_color = "#FAFAFA"       # Soft off-white background
            text_color = "#202124"     # Dark gray text for comfort
            sidebar_bg = "#F5F5F5"     # Very light gray sidebar
            input_bg = "#EEEEEE"       # Soft gray input field
            msg_user_bg = "#E6F0FF"    # Very light blue for user messages
            msg_bot_bg = "#F1F3F4"     # Google-style light grey for bot messages
            border_color = "#DADCE0"   # Light grey border


    return f"""
    <style>
        /* Base Colors */
        :root {{
            --bg-color: {bg_color};
            --text-color: {text_color};
            --sidebar-bg: {sidebar_bg};
            --accent-red: #FF4136;
            --accent-blue: #0074D9;
            --border-color: {border_color};
            --input-bg: {input_bg};
            --msg-user-bg: {msg_user_bg};
            --msg-bot-bg: {msg_bot_bg};
        }}

        /* General body styling */
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: var(--text-color);
            background-color: var(--bg-color);
        }}
        /* Ensure Streamlit's main container also gets the background */
         div[data-testid="stAppViewContainer"] > section {{
            background-color: var(--bg-color);
        }}


        /* Main container adjustments */
        .main .block-container {{
            padding-top: 2rem; padding-bottom: 2rem;
            padding-left: 3rem; padding-right: 3rem;
        }}

        /* Sidebar styling */
        [data-testid="stSidebar"] {{
            background-color: var(--sidebar-bg);
            padding: 1rem;
            line-height: 1.4;
            border-right: 1px solid var(--border-color);
        }}
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h5,
        [data-testid="stSidebar"] label, /* Input labels */
        [data-testid="stSidebar"] .stMarkdown /* General markdown text */
         {{
            color: var(--text-color); /* White text */
        }}
        [data-testid="stSidebar"] h1 {{ margin-top: 0; margin-bottom: 0.5rem; font-weight: 600; }}
        [data-testid="stSidebar"] h3 {{ margin-top: 1rem; margin-bottom: 0.3rem; font-weight: 600; }}
        [data-testid="stSidebar"] h5 {{ margin-top: 0.6rem; margin-bottom: 0.3rem; font-weight: 600; }}

        /* Reduce spacing around widgets */
        [data-testid="stSidebar"] [data-testid="stTextInput"],
        [data-testid="stSidebar"] [data-testid="stFileUploader"],
        [data-testid="stSidebar"] [data-testid="stButton"],
        [data-testid="stSidebar"] [data-testid="stDownloadButton"] {{
            margin-bottom: 0.6rem;
        }}

        /* Sidebar Buttons - Default (Clear Chat, Reset) */
        [data-testid="stSidebar"] .stButton>button:not(:contains("Process")):not(:contains("Logout")):not(:contains("Download")) {{
             border-radius: 5px; border: 1px solid var(--accent-red);
             color: var(--accent-red); background-color: transparent;
             transition: all 0.2s ease-in-out; width: 100%; margin-bottom: 0.4rem; padding: 8px 0;
        }}
        [data-testid="stSidebar"] .stButton>button:not(:contains("Process")):not(:contains("Logout")):not(:contains("Download")):hover {{
             border-color: var(--accent-red); color: var(--text-color);
             background-color: var(--accent-red);
        }}

        /* Special styling for Process/Logout buttons (Blue) */
        [data-testid="stSidebar"] .stButton button:contains("Process"),
        [data-testid="stSidebar"] .stButton button:contains("Logout") {{
            background-color: var(--accent-blue); color: white; border: none; border-radius: 5px;
            width: 100%; margin-bottom: 0.4rem; transition: background-color 0.2s ease-in-out; padding: 8px 0;
        }}
         [data-testid="stSidebar"] .stButton button:contains("Process"):hover,
         [data-testid="stSidebar"] .stButton button:contains("Logout"):hover {{
            background-color: #0056b3; /* Darker Blue */
        }}

        /* Download button styling (Red) */
        [data-testid="stSidebar"] [data-testid="stDownloadButton"] button {{
             background-color: var(--accent-red); color: white; border: none; border-radius: 5px;
             font-weight: 500; transition: background-color 0.2s ease-in-out;
             width: 100%; margin-bottom: 0.4rem; padding: 8px 0;
        }}
        [data-testid="stSidebar"] [data-testid="stDownloadButton"] button:hover {{
             background-color: #cc342b; /* Darker Red */ color: white;
        }}

        /* Chat message styling */
        .chat-message {{
            padding: 1rem 1.25rem; border-radius: 6px; margin-bottom: 1rem;
            display: flex; align-items: flex-start;
            box-shadow: 0 1px 3px rgba(255,255,255,0.05); transition: background-color 0.3s ease;
            border-left: 4px solid transparent;
        }}
        .chat-message.user {{ background-color: var(--msg-user-bg); border-left-color: var(--accent-blue); }}
        .chat-message.bot {{ background-color: var(--msg-bot-bg); border-left-color: var(--accent-red); }}
        .chat-message .avatar {{
            width: 38px; height: 38px; margin-right: 0.75rem; flex-shrink: 0;
            border-radius: 50%; overflow: hidden; border: 1px solid var(--border-color);
        }}
        .chat-message .avatar img {{ width: 100%; height: 100%; object-fit: cover; }}
        .chat-message .message {{
            width: 100%; padding: 0; color: var(--text-color); font-size: 0.95rem; line-height: 1.6;
        }}
        /* Ensure markdown within messages is white */
        .chat-message .message p, .chat-message .message li, .chat-message .message h1, .chat-message .message h2, .chat-message .message h3, .chat-message .message h4, .chat-message .message h5, .chat-message .message h6 {{
             color: var(--text-color) !important;
        }}
        .chat-message .message pre {{
            background-color: #1a1a1a; padding: 0.8rem; border-radius: 4px;
            overflow-x: auto; border: 1px solid var(--border-color);
        }}
        .chat-message .message code {{ /* Code within pre */
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 0.9rem;
            color: #f0f0f0; background-color: transparent; padding: 0.1em 0.3em;
        }}
        .chat-message .message p code {{ /* Inline code */
             background-color: #444;
             border-radius: 3px; padding: 0.2em 0.4em; color: #f0f0f0; border: 1px solid #555;
        }}

        /* Input fields styling */
        .stTextInput input, .stTextArea textarea, .stChatInput input {{
            border-radius: 4px; border: 1px solid var(--border-color); padding: 10px;
            background-color: var(--input-bg);
            color: var(--text-color); /* White text in input */
        }}
        /* Placeholder text color */
        .stTextInput input::placeholder, .stTextArea textarea::placeholder, .stChatInput input::placeholder {{
            color: #aaaaaa;
        }}
        .stTextInput input:focus, .stTextArea textarea:focus, .stChatInput input:focus {{
            border-color: var(--accent-blue); /* Blue focus */
            box-shadow: 0 0 0 2px rgba(0, 116, 217, 0.25);
            background-color: #444; /* Slightly lighter focus bg */
        }}

        /* Expander styling */
        [data-testid="stSidebar"] .stExpander {{
            border: 1px solid var(--border-color); border-radius: 5px; margin-top: 0.75rem;
            margin-bottom: 0.5rem; background-color: var(--input-bg); /* Darker background */
        }}
        [data-testid="stSidebar"] .stExpander header {{
            background-color: #444; padding: 0.5rem 1rem; border-radius: 5px 5px 0 0;
            border-bottom: 1px solid var(--border-color); font-weight: 500; color: var(--text-color); /* White text */
        }}
        .stExpander header:hover {{ background-color: #555; }}
        .stExpander div[data-testid="stExpanderDetails"] {{ padding: 1rem; background-color: var(--input-bg); }}

        /* Divider styling */
        [data-testid="stSidebar"] hr {{
            margin-top: 0.75rem; margin-bottom: 0.75rem; border-top: 1px solid var(--border-color);
        }}
        /* Status messages */
        [data-testid="stSidebar"] [data-testid="stInfo"],
        [data-testid="stSidebar"] [data-testid="stWarning"],
        [data-testid="stSidebar"] [data-testid="stSuccess"],
        [data-testid="stSidebar"] [data-testid="stError"] {{
            margin-bottom: 0.5rem; border-radius: 4px; color: var(--text-color); /* White text */
        }}
         [data-testid="stSidebar"] [data-testid="stInfo"] {{ background-color: rgba(0, 116, 217, 0.3); border: 1px solid var(--accent-blue); }}
         [data-testid="stSidebar"] [data-testid="stWarning"] {{ background-color: rgba(255, 133, 27, 0.3); border: 1px solid #FF851B; }} /* Orange warning */
         [data-testid="stSidebar"] [data-testid="stSuccess"] {{ background-color: rgba(46, 204, 64, 0.3); border: 1px solid #2ECC40; }} /* Green success */
         [data-testid="stSidebar"] [data-testid="stError"] {{ background-color: rgba(255, 65, 54, 0.3); border: 1px solid var(--accent-red); }}


        /* Login Page Specific Styling */
        .login-container {{
            max-width: 450px; margin: 5rem auto; padding: 2.5rem;
            background-color: var(--sidebar-bg); border-radius: 6px;
            box-shadow: 0 4px 10px rgba(255,255,255,0.07); border: 1px solid var(--border-color);
        }}
        .login-container h2 {{
            color: var(--text-color); text-align: center; margin-bottom: 2rem; font-weight: 600;
        }}
        .login-container label {{ color: var(--text-color); }} /* White labels */
        .login-container .stButton>button {{
             background-color: var(--accent-blue); color: white; border: none;
             border-radius: 4px; width: 100%; margin-top: 1.5rem; padding: 10px 0;
             font-weight: 500; transition: background-color 0.2s ease-in-out;
        }}
        .login-container .stButton>button:hover {{
             background-color: var(--accent-red); /* Red hover */
        }}
        /* Style for processed files list */
        .processed-files-list {{
            font-size: 0.9em; margin-top: 0.5rem; max-height: 150px;
            overflow-y: auto; background-color: var(--input-bg);
            padding: 0.5rem 0.75rem; border-radius: 4px; border: 1px solid var(--border-color);
        }}
        .processed-files-list ul {{ list-style-type: none; padding-left: 0; margin-bottom: 0; }}
         .processed-files-list li {{
            margin-bottom: 0.3rem; word-break: break-all; color: #cccccc; /* Lighter gray text */
        }}

    </style>
    """

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
