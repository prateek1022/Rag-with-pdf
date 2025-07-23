# Configuration constants for the Streamlit PDF Chat App

APP_TITLE = "Chat with multiple PDFs (v1)"
APP_ICON = ":books:"

# Model and Embedding Configuration
EMBEDDING_MODEL = "models/embedding-001"
LLM_MODEL = "gemini-2.0-flash" # Or your preferred model
TEMPERATURE = 0.3

# Text Splitting Configuration
CHUNK_SIZE = 5000 # Smaller chunk size for more focused context
CHUNK_OVERLAP = 500 # Smaller overlap

# Vector Store Configuration
VECTOR_DB_PATH = "faiss_index"

# Database Configuration
DB_NAME = "user_data.db"

# Avatar URLs
USER_AVATAR = "https://i.ibb.co/CKpTnWr/user-icon-2048x2048-ihoxz4vq.png"
BOT_AVATAR = "https://i.ibb.co/wNmYHsx/langchain-logo.webp"

# Social Links
LINKEDIN_URL = "https://www.linkedin.com/in/prateek1022/"
GITHUB_URL = "https://github.com/prateek1022"
API_KEY_URL = "https://ai.google.dev/" # URL for getting API key
