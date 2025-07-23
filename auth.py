import streamlit as st
import sqlite3
import os # Needed for directory check
from datetime import datetime
from config import DB_NAME, API_KEY_URL, VECTOR_DB_PATH # Import constants

# --- Database Functions ---

def init_db():
    """Initialize the SQLite database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            api_key TEXT
        )
    ''')
    # User PDFs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_pdfs (
            pdf_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            filename TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            extracted_text TEXT,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    # Index to potentially speed up lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_pdfs_username ON user_pdfs (username)
    ''')
    conn.commit()
    conn.close()
    # Ensure base vector store directory exists
    if not os.path.exists(VECTOR_DB_PATH):
        os.makedirs(VECTOR_DB_PATH)


def get_user(username):
    """Retrieve user's API key from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT api_key FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def add_user(username):
    """Add a new user to the database with a null API key."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, api_key) VALUES (?, NULL)", (username,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_api_key(username, api_key):
    """Update the API key for a given user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET api_key = ? WHERE username = ?", (api_key, username))
    conn.commit()
    conn.close()

# --- PDF Data Functions ---

def add_pdf_record(username, filename, extracted_text):
    """Adds a record for an uploaded PDF, avoiding duplicates by filename for the user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Check if this filename already exists for this user
    cursor.execute("SELECT 1 FROM user_pdfs WHERE username = ? AND filename = ?", (username, filename))
    exists = cursor.fetchone()
    if not exists:
        try:
            cursor.execute(
                "INSERT INTO user_pdfs (username, filename, extracted_text, uploaded_at) VALUES (?, ?, ?, ?)",
                (username, filename, extracted_text, datetime.now())
            )
            conn.commit()
            st.sidebar.info(f"'{filename}' added to your records.") # Feedback
        except Exception as e:
            st.sidebar.error(f"Error adding PDF record for {filename}: {e}")
    else:
        st.sidebar.warning(f"'{filename}' already exists in your records. Skipping.")
    conn.close()


def get_user_pdf_texts(username):
    """Retrieves a list of all extracted texts for a given user's PDFs."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT extracted_text FROM user_pdfs WHERE username = ?", (username,))
    results = cursor.fetchall()
    conn.close()
    # Return a list of non-empty text strings
    return [row[0] for row in results if row[0]]

def get_user_pdf_filenames(username):
    """Retrieves a list of filenames for a given user's PDFs."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM user_pdfs WHERE username = ? ORDER BY uploaded_at DESC", (username,))
    results = cursor.fetchall()
    conn.close()
    return [row[0] for row in results]

def get_user_pdf_data(username):
    """Retrieves a list of (filename, extracted_text) tuples for a given user's PDFs."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, extracted_text FROM user_pdfs WHERE username = ?", (username,))
    results = cursor.fetchall()
    conn.close()
    # Return list of tuples, ensuring text is not None (though DB likely handles this)
    return [(row[0], row[1]) for row in results if row[1]]


# --- Login Page Rendering ---

def render_login_page():
    """Displays the login/registration form."""
    st.image("logo.png", width=200) # Add the logo here
    st.markdown("<h2>Welcome! Please Login or Register</h2>", unsafe_allow_html=True)

    # Use columns to control the width of the username input
    col1, col2 = st.columns([0.4, 0.6]) # First column for input, second for spacing
    with col1:
        username = st.text_input("Username", key="login_username", placeholder="Enter your username")
    api_key_input = None

    # Check if user exists when username is entered
    user_exists = False
    existing_api_key = None
    if username:
        existing_api_key = get_user(username)
        # Check if user exists in the database (even if API key is NULL)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        user_record_exists = cursor.fetchone()
        conn.close()

        if user_record_exists:
             user_exists = True
             if existing_api_key: # User exists and has API key
                 if not st.session_state.show_api_key_input:
                     st.success(f"Welcome back, {username}! Click Login.")
             else: # User exists but API key is NULL
                 st.info(f"Welcome back, {username}. Please provide your API key below and click 'Register / Update Key'.")
                 st.session_state.show_api_key_input = True # Force API key input
        else: # User does not exist
             user_exists = False
             st.info(f"New user '{username}'. Please provide an API key below and click Register.")
             st.session_state.show_api_key_input = True # Show API key input for new user

    # Show API key input if needed
    if st.session_state.show_api_key_input:
        api_key_input = st.text_input("Google API Key", type="password", key="login_api_key", placeholder="Enter your Google API Key")
        st.markdown(f"[Get an API key here]({API_KEY_URL})", unsafe_allow_html=True)

    # Determine button label
    button_label = "Login" if user_exists and not st.session_state.show_api_key_input else "Register / Update Key"

    # Login/Register Button
    if st.button(button_label, key="login_button"):
        st.session_state.login_error = None # Reset error on attempt
        if not username:
            st.session_state.login_error = "Please enter a username."
        else:
            # Logic for existing user login (who already has a key)
            if user_exists and not st.session_state.show_api_key_input:
                 if existing_api_key:
                     st.session_state.logged_in = True
                     st.session_state.username = username
                     st.session_state.api_key = existing_api_key
                     st.session_state.show_api_key_input = False
                     # Load user's existing PDF filenames into session state upon login
                     st.session_state.processed_filenames = get_user_pdf_filenames(username)
                     st.rerun()
                 else:
                     # This case means user exists but key is missing, force input
                     st.session_state.login_error = "API Key missing. Please provide it."
                     st.session_state.show_api_key_input = True
                     st.rerun()

            # Logic for new user registration or existing user providing/updating key
            elif not user_exists or st.session_state.show_api_key_input:
                 if not api_key_input:
                     st.session_state.login_error = "Please enter your Google API Key."
                 else:
                     if not user_exists:
                         add_user(username) # Add the new user record
                     update_api_key(username, api_key_input) # Save/update the key
                     st.session_state.logged_in = True
                     st.session_state.username = username
                     st.session_state.api_key = api_key_input
                     st.session_state.show_api_key_input = False # Reset
                     # New user starts with no processed files
                     st.session_state.processed_filenames = []
                     st.rerun()

    # Display login errors
    if st.session_state.login_error:
        st.error(st.session_state.login_error)

    st.markdown('</div>', unsafe_allow_html=True)
