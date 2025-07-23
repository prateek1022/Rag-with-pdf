import streamlit as st
from PyPDF2 import PdfReader
import os
from datetime import datetime
import traceback

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document # Import Document

# Import constants from config
from config import (
    EMBEDDING_MODEL, LLM_MODEL, TEMPERATURE,
    CHUNK_SIZE, CHUNK_OVERLAP, VECTOR_DB_PATH
)
# Import PDF DB functions from auth
# Assuming a function get_user_pdf_data exists or can be added to return [(filename, text), ...]
from auth import add_pdf_record, get_user_pdf_data, get_user_pdf_filenames

# --- PDF Text Extraction ---
def extract_text_from_uploads(pdf_docs):
    """Extracts text from a list of uploaded PDF file objects. Returns a dict {filename: text}."""
    extracted_data = {}
    if not pdf_docs: return extracted_data
    for pdf in pdf_docs:
        filename = pdf.name
        text = ""
        try:
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text: text += page_text + "\n"
            if text.strip():
                extracted_data[filename] = text
            else:
                 st.warning(f"No text could be extracted from '{filename}'.")
        except Exception as e:
            st.error(f"Error processing {filename}: {str(e)}")
            if 'debug_logs' not in st.session_state:
                st.session_state.debug_logs = []
            st.session_state.debug_logs.append(f"TRACEBACK: {traceback.format_exc()}")
    return extracted_data

# --- Text Chunking ---
# --- Text Chunking (Now done within vector store creation) ---
# def get_text_chunks(text): # No longer needed here
#     """Split a single block of text into manageable chunks."""
#     if not text: return []
#     try:
#         text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
#         return text_splitter.split_text(text)
#     except Exception as e: st.error(f"Error splitting text: {str(e)}"); return []

# --- Vector Store Management ---
def get_user_vector_store_path(username):
    """Returns the path for the user-specific vector store."""
    return os.path.join(VECTOR_DB_PATH, username)

def create_and_save_vector_store(username, pdf_data, api_key):
    """Creates/updates and saves a FAISS vector store using Document objects with metadata.
       Expects pdf_data as a list of tuples: [(filename1, text1), (filename2, text2), ...].
       Returns (vector_store, logs) or (None, logs).
    """
    vector_logs = [] # Initialize logs list
    if not pdf_data or not api_key:
        vector_logs.append("Skipping vector store creation: Missing PDF data or API key.")
        return None, vector_logs

    try:
        vector_logs.append("Preparing documents for vector store...")
        all_docs = []
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

        for filename, text in pdf_data:
            if not text or not text.strip():
                vector_logs.append(f"Skipping '{filename}': No text content.")
                continue
            vector_logs.append(f"Splitting text from '{filename}'...")
            chunks = text_splitter.split_text(text)
            vector_logs.append(f" -> Created {len(chunks)} chunks.")
            for i, chunk in enumerate(chunks):
                # Create LangChain Document object with metadata
                doc = Document(
                    page_content=chunk,
                    metadata={"source": filename, "chunk_index": i} # Add source filename and chunk index
                )
                all_docs.append(doc)

        if not all_docs:
            st.warning("No processable text content found in any PDF for vector store creation.")
            vector_logs.append("WARNING: No processable documents generated.")
            return None, vector_logs

        vector_logs.append(f"Embedding {len(all_docs)} total document chunks...")
        if 'debug_logs' not in st.session_state: st.session_state.debug_logs = []
        st.session_state.debug_logs.append(f"DEBUG: Before GoogleGenerativeAIEmbeddings initialization: {datetime.now()}")
        embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=api_key)
        st.session_state.debug_logs.append(f"DEBUG: After GoogleGenerativeAIEmbeddings initialization: {datetime.now()}")

        # Create vector store from Document objects
        st.session_state.debug_logs.append(f"DEBUG: Before FAISS.from_documents: {datetime.now()}")
        vector_store = FAISS.from_documents(all_docs, embedding=embeddings)
        st.session_state.debug_logs.append(f"DEBUG: After FAISS.from_documents: {datetime.now()}")
        vector_logs.append("Embedding complete.")

        user_store_path = get_user_vector_store_path(username)
        if not os.path.exists(user_store_path):
            os.makedirs(user_store_path)

        vector_logs.append(f"Saving vector store to: {user_store_path}")
        vector_store.save_local(user_store_path)
        vector_logs.append("Vector store saved successfully.")
        return vector_store, vector_logs # Return the created store and logs
    except Exception as e:
        error_msg = f"Error creating/saving vector store: {str(e)}"
        st.error(error_msg)
        vector_logs.append(f"ERROR: {error_msg}")
        vector_logs.append(f"TRACEBACK: {traceback.format_exc()}")
        return None, vector_logs

def load_vector_store(username, api_key):
    """Loads the FAISS vector store for the user."""
    user_store_path = get_user_vector_store_path(username)
    index_path = os.path.join(user_store_path, "index.faiss")
    pkl_path = os.path.join(user_store_path, "index.pkl")

    if not os.path.exists(index_path) or not os.path.exists(pkl_path):
        # st.info("Vector store not found for this user. Please process PDFs.")
        return None # Indicate store doesn't exist

    if not api_key:
        st.error("API Key needed to load vector store embeddings.")
        return None

    try:
        embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=api_key)
        vector_store = FAISS.load_local(user_store_path, embeddings, allow_dangerous_deserialization=True)
        return vector_store
    except Exception as e:
        st.error(f"Error loading vector store: {str(e)}")
        if 'debug_logs' not in st.session_state:
            st.session_state.debug_logs = []
        st.session_state.debug_logs.append(f"TRACEBACK: {traceback.format_exc()}")
        # Attempt to delete corrupted index? Or just inform user?
        # For now, just inform. Consider deleting corrupted files if this becomes common.
        st.warning("The existing vector store might be corrupted. Try reprocessing PDFs.")
        return None


# --- QA Chain Function ---
def display_vector_store_contents(username, api_key):
    """Loads the vector store and displays its contents."""
    vector_store = load_vector_store(username, api_key)
    if not vector_store:
        st.warning("Vector store not found or failed to load.")
        return

    try:
        # Extract texts from the vector store
        texts = vector_store.index_to_docstore_id.values()
        all_texts = [vector_store.docstore.search(text) for text in texts]

        # Display the texts
        return "\n\n".join(all_texts)

    except Exception as e:
        st.error(f"Error displaying vector store contents: {str(e)}")
        if 'debug_logs' not in st.session_state:
            st.session_state.debug_logs = []
        st.session_state.debug_logs.append(f"TRACEBACK: {traceback.format_exc()}")
        return None

def get_conversational_chain(api_key):
    """Create a conversational chain."""
    if not api_key: return None
    try:
        model = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=TEMPERATURE, google_api_key=api_key)
        prompt = PromptTemplate(
            template="""You are an AI assistant tasked with answering questions using only the information provided in the context (extracted from user's PDFs).

            Instructions:
            - Analyze the Context to extract all relevant information.
            - Use the context to answer the Question as thoroughly and accurately as possible.
            - Do not use any external knowledge or assumptions.
            - If the answer is not present in the context, respond with: "Answer is not available in the provided documents."

            Formatting Guidelines:
            1. Use clear and concise language.
            2. Organize the answer into paragraphs for readability.
            3. Use bullet points or numbered lists when explaining complex information.
            4. Add headings or subheadings if needed for structure.
            5. Ensure proper grammar, punctuation, and spelling.
            6. Do not include greetings, explanations, or meta-commentary—just the answer.

            Context:\n {context}?\n
            Question: \n{question}\n

            Answer:""",
            input_variables=["context", "question"]
        )
        return load_qa_chain(model, chain_type="stuff", prompt=prompt)
    except Exception as e:
        st.error(f"Error creating conversational chain: {str(e)}")
        if 'debug_logs' not in st.session_state:
            st.session_state.debug_logs = []
        st.session_state.debug_logs.append(f"TRACEBACK: {traceback.format_exc()}")
        return None

# --- Core Question Processing Logic ---
def process_user_question(user_question, username, api_key):
    """Loads vector store, performs search, generates response, and updates history."""
    if not api_key:
        st.warning("API key is missing.")
        return
    if not username:
        st.error("Username missing. Cannot process question.")
        return

    vector_store = load_vector_store(username, api_key)
    if not vector_store:
         # Attempt to rebuild if text exists? Or just rely on user reprocessing?
         # For now, require reprocessing via button.
         st.warning("Vector store not found or failed to load. Please process/reprocess your PDFs.")
         return

    try:
        # Perform search using MMR
        # k = number of final docs, fetch_k = number of docs to fetch initially for MMR calculation
        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 5, 'fetch_k': 20}
        )
        docs = retriever.invoke(user_question) # Use invoke for LCEL compatibility

        # --- Log the fetched documents ---
        log_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        vs_log_entry = f"[{log_timestamp}] VectorDB Search Results:\nUser Question: {user_question}\n\n--- Retrieved Docs from VectorDB ---\n"
        for i, doc in enumerate(docs):
            # Log the full page content and metadata
            full_content = doc.page_content
            metadata_str = ", ".join([f"{k}: {v}" for k, v in doc.metadata.items()])
            vs_log_entry += f"\n--- Document {i+1} (Metadata: {metadata_str}) ---\n{full_content}\n--- End Document {i+1} ---\n"
        vs_log_entry += "\n--- End VectorDB Results ---"
        if 'debug_logs' not in st.session_state:
            st.session_state.debug_logs = []
        st.session_state.debug_logs.append(vs_log_entry)
        # --- End Logging ---

        # Get QA chain and generate response
        chain = get_conversational_chain(api_key)
        if not chain: return # Error handled in get_conversational_chain

        with st.spinner("Generating answer..."):
            response = chain.invoke({"input_documents": docs, "question": user_question})
            answer = response['output_text']

        # --- Logging ---
        # Log the prompt and retrieved docs before sending to LLM
        log_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        llm_log_entry = f"[{log_timestamp}] LLM Query:\nUser Question: {user_question}\n\n--- Retrieved Docs Context ---\n"
        for i, doc in enumerate(docs):
            # Log the full page content and metadata for LLM context
            full_content = doc.page_content
            metadata_str = ", ".join([f"{k}: {v}" for k, v in doc.metadata.items()])
            llm_log_entry += f"\n--- Document {i+1} (Metadata: {metadata_str}) ---\n{full_content}\n--- End Document {i+1} ---\n"
        llm_log_entry += "\n--- End Context ---"  # Mark the end of the context block
        if 'debug_logs' not in st.session_state:
            st.session_state.debug_logs = []
        st.session_state.debug_logs.append(llm_log_entry)
        # --- End Logging ---

        # Get QA chain and generate response
        chain = get_conversational_chain(api_key)
        if not chain: return # Error handled in get_conversational_chain

        with st.spinner("Generating answer..."):
            
            response = chain.invoke({"input_documents": docs, "question": user_question})
            answer = response['output_text']
            # Update history (in session state)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Get current list of processed filenames for context
            processed_filenames = st.session_state.get('processed_filenames', [])
            st.session_state.conversation_history.append(
                (user_question, answer, "Google AI", timestamp, ", ".join(processed_filenames))
            )

    except Exception as e:
        st.error(f"Error processing question: {str(e)}")
        # Log the error
        log_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_log = f"[{log_timestamp}] ERROR processing question: {str(e)}\nTRACEBACK: {traceback.format_exc()}"
        if 'debug_logs' not in st.session_state: st.session_state.debug_logs = []
        st.session_state.debug_logs.append(error_log)

# --- PDF Processing Callback Logic ---
def process_uploaded_pdfs(pdf_docs, username, api_key):
    """Handles PDF extraction, DB saving, and vector store creation/update."""
    if not pdf_docs:
        st.error("Please upload PDF files first.")
        return False
    if not api_key:
        st.error("API Key is missing. Cannot process PDFs.")
        return False
    if not username:
        st.error("Username missing. Cannot process PDFs.")
        return False

    success = True
    new_files_processed = False
    with st.spinner("Processing uploaded PDFs..."):
        # 1. Extract text from newly uploaded files
        extracted_data = extract_text_from_uploads(pdf_docs)

        # 2. Add new records to the database
        for filename, text in extracted_data.items():
            add_pdf_record(username, filename, text)
            new_files_processed = True # Mark that at least one new file was processed

        # 3. Retrieve ALL texts WITH filenames for the user from the database
        # Assuming get_user_pdf_data returns [(filename, text), ...]
        pdf_data_for_user = get_user_pdf_data(username)

        # 4. Rebuild the vector store with all documents and metadata
        vector_logs = [] # Initialize logs list here
        if not pdf_data_for_user:
            st.warning("No text content found for this user in the database.")
            vector_logs.append("WARNING: No text content found for user in DB.")
            success = False
        else:
            # Capture logs from vector store creation (now expects pdf_data)
            vector_store, vector_logs = create_and_save_vector_store(username, pdf_data_for_user, api_key)
            if vector_store:
                st.session_state.vector_store_created = True
                # Update the list of processed filenames in session state
                st.session_state.processed_filenames = get_user_pdf_filenames(username)
                st.success("✅ PDFs processed and vector store updated!")
            else:
                st.error("Failed to create or save the vector store.")
                st.session_state.vector_store_created = False
                success = False

        # Append vector logs to session state
        if 'debug_logs' not in st.session_state: st.session_state.debug_logs = []
        st.session_state.debug_logs.extend(vector_logs)

    return success
