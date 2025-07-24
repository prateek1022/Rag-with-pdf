# Chat with Multiple PDFs - A RAG-based Streamlit Application

This project is a multi-user Streamlit application that allows users to upload and chat with their PDF documents. It leverages a Retrieval-Augmented Generation (RAG) architecture with Google's Generative AI models to provide answers based on the content of the uploaded files.

**Live App:** <a href="https://ragaspdf.streamlit.app/" target="_blank">https://ragaspdf.streamlit.app/</a>

## ✨ Features

-   **Multi-User Authentication:** Secure login and registration system. Each user has their own private document space.
-   **Persistent Conversations:** Chat history is saved and restored across sessions.
-   **Dynamic Knowledge Base:** Upload new PDFs at any time to update the context for the chat.
-   **User-Specific Vector Stores:** Each user's documents are stored in a separate, isolated FAISS vector store.
-   **Dark/Light Theme Toggle:** Choose your preferred UI theme.
-   **Download Chat History:** Export your conversation as a CSV file.

## 🚀 Tech Stack

-   **Frontend:** <a href="https://streamlit.io/" target="_blank">Streamlit</a>
-   **Backend & Orchestration:** <a href="https://www.langchain.com/" target="_blank">LangChain</a>
-   **Language Model:** Google Generative AI (Gemini)
-   **Embeddings:** Google Generative AI (`embedding-001`)
-   **Vector Store:** <a href="https://github.com/facebookresearch/faiss" target="_blank">FAISS</a> (Facebook AI Similarity Search)
-   **Database:** SQLite for user and PDF metadata

## 📸 Screenshots
### Login Page
[Login img1](./screenshots/screenshot-1.png) &nbsp; &nbsp; &nbsp; [Login img2](./screenshots/screenshot-6.png)



### Main Chat Interface
[Chat img1](./screenshots/screenshot-3.png) &nbsp; &nbsp; &nbsp; [Chat img2](./screenshots/screenshot-2.png)

### PDF Management in Sidebar
[Sidebar img1](./screenshots/screenshot-4.png) &nbsp; &nbsp; &nbsp; [Sidebar img2](./screenshots/screenshot-5.png)

## 🛠️ How It Works

1.  **User Authentication:** A user logs in or registers with a username and a Google API Key.
2.  **PDF Upload & Processing:**
    *   The user uploads one or more PDF files.
    *   The text is extracted from the PDFs.
    *   The text is split into smaller, manageable chunks.
    *   Each chunk is converted into a numerical representation (embedding) using Google's AI.
    *   These embeddings are stored in a user-specific FAISS vector store.
3.  **Question Answering (RAG):**
    *   When the user asks a question, the question is also converted into an embedding.
    *   The system searches the user's vector store to find the most relevant text chunks from the PDFs.
    *   These relevant chunks (the "context") and the user's question are sent to the Gemini model.
    *   The model generates an answer based *only* on the provided context.

## ⚙️ Local Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/prateek1022/Rag-with-pdf.git
    cd Rag-with-pdf
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Get your Google API Key:**
    *   Visit <a href="https://ai.google.dev/" target="_blank">Google AI for Developers</a> to create your API key.

5.  **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```

## 🔗 Connect with Me

-   **LinkedIn:** <a href="https://www.linkedin.com/in/prateek1022/" target="_blank">Prateek Sharma</a>
-   **GitHub:** <a href="https://github.com/prateek1022" target="_blank">@prateek1022</a>
