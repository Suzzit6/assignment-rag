import streamlit as st
import os
import time
# from langchain.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from huggingface_hub import login
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
from PyDictionary import PyDictionary
# from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import Docx2txtLoader  # Add this import for DOCX support
import re
from sympy import symbols, sympify, factorial, sqrt, log, exp, sin, cos, tan, pi


st.set_page_config(
    page_title="Document Assistant",
    page_icon="📚",
    layout="wide"
)


st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .source-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #4285f4;
        color: #333333; /* Dark text color for better visibility */
    }
    .source-box p {
        color: #333333;
        font-size: 14px;
    }
    .source-box b {
        color: #1a73e8;
        font-weight: 600;
    }
    .source-box i {
        color: #5bc0de;
        font-style: italic;
    }
    .log-container {
        max-height: 300px;
        overflow-y: auto;
        background-color: #f9f9f9;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ddd;
    }
    .answer-container {
        background-color: #eef7f2;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #5cb85c;
        margin: 20px 0;
        color: #2e4e2e; /* Dark green text for better visibility */
        font-size: 16px;
        line-height: 1.5;
    }
    .answer-container b {
        color: #3c763d; /* Darker green for bold text */
        font-weight: 600;
    }
    .answer-container i {
        color: #5bc0de; /* Light blue for italic text */
        font-style: italic;
    }
    .stButton>button {
        background-color: #4285f4;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #3b77db;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .log-entry {
        margin-bottom: 5px;
        font-family: monospace;
        color: #333333;
    }
    .header-container {
        background-color: #f9f9f9;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem; /* Reduced from 2rem to 1rem */
        border-bottom: 3px solid #4285f4;
    }
    .tab-subheader {
        color: #4285f4;
        margin-bottom: 0.5rem; /* Reduced from 1rem to 0.5rem */
    }
    .stRadio > div {
        margin-bottom: 1rem; /* Reduced from 1.5rem to 1rem */
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #e6f2ff;
        border-left: 5px solid #4285f4;
        color: #333; /* Ensure text color is visible */
    }
    .chat-message.assistant {
        background-color: #f0f0f0;
        border-left: 5px solid #424242;
        color: #333; /* Ensure text color is visible */
    }
    .chat-message .message-content {
        margin-top: 0.5rem;
        color: #333; /* Ensure text color is visible */
    }
    .chat-container {
        height: 60vh;
        overflow-y: auto;
        padding: 1rem;
        background-color: #f9f9f9;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        margin-top: 0.5rem; /* Added to reduce space after the header */
    }
    /* Remove space between elements */
    .tab-content {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    .message-input {
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin-top: 0; /* Remove any extra margin */
    }
    .agent-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .agent-badge.calculator {
        background-color: #ffe0b2;
        color: #e65100;
    }
    .agent-badge.dictionary {
        background-color: #e1bee7;
        color: #6a1b9a;
    }
    .agent-badge.rag {
        background-color: #bbdefb;
        color: #0d47a1;
    }
    /* Fix the welcome message display */
    .welcome-message {
        text-align: center;
        padding: 2rem;
        color: #333; /* Darker text color for better visibility */
        background-color: #f9f9f9;
        border-radius: 10px;
    }
    /* Remove extra padding in tabs */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 0.5rem !important;
    }
    /* Ensure text is visible in all areas */
    p, div, span {
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None
if 'qa_chain' not in st.session_state:
    st.session_state.qa_chain = None
if 'documents_processed' not in st.session_state:
    st.session_state.documents_processed = False
if 'answer' not in st.session_state:
    st.session_state.answer = None
if 'sources' not in st.session_state:
    st.session_state.sources = []
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = None
if 'agent_used' not in st.session_state:
    st.session_state.agent_used = None
if 'agent_details' not in st.session_state:
    st.session_state.agent_details = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'vectorstore_loaded' not in st.session_state:
    st.session_state.vectorstore_loaded = False

def add_log(message):
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {message}")


def load_documents(uploaded_files):
    docs = []
    processed_files = []
    
    for uploaded_file in uploaded_files:
        temp_dir = "temp_uploaded_files"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, uploaded_file.name)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        add_log(f"Processing file: {uploaded_file.name}")
        print(f"Processing file: {uploaded_file.name}")
        
        if uploaded_file.name.endswith('.txt'):
            loader = TextLoader(file_path)
            processed_files.append({"name": uploaded_file.name, "type": "Text"})
        # elif uploaded_file.name.endswith('.pdf'):
        #     loader = PyPDFLoader(file_path)
            processed_files.append({"name": uploaded_file.name, "type": "PDF"})
        elif uploaded_file.name.endswith(('.docx', '.doc')):  # Add DOCX support
            loader = Docx2txtLoader(file_path)
            processed_files.append({"name": uploaded_file.name, "type": "DOCX"})
        else:
            add_log(f"Unsupported file format: {uploaded_file.name}")
            print(f"Unsupported file format: {uploaded_file.name}")
            continue
            
        docs.extend(loader.load())
    
    add_log(f"Loaded {len(docs)} documents successfully")
    print(f"Loaded {len(docs)} documents successfully")
    st.session_state.processed_files = processed_files
    return docs

def load_documents_from_folder(folder_path):
    docs = []
    processed_files = []
    
    if not os.path.exists(folder_path):
        add_log(f"ERROR: Folder {folder_path} does not exist!")
        print(f"ERROR: Folder {folder_path} does not exist!")
        return []
        
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if not os.path.isfile(file_path):
            continue
            
        add_log(f"Processing file: {filename}")
        print(f"Processing file: {filename}")
        
        if filename.endswith('.txt'):
            loader = TextLoader(file_path)
            processed_files.append({"name": filename, "type": "Text"})
        # elif filename.endswith('.pdf'):
        #     loader = PyPDFLoader(file_path)
            processed_files.append({"name": filename, "type": "PDF"})
        elif filename.endswith(('.docx', '.doc')):  # Add DOCX support
            loader = Docx2txtLoader(file_path)
            processed_files.append({"name": filename, "type": "DOCX"})
        else:
            add_log(f"Skipping unsupported file: {filename}")
            print(f"Skipping unsupported file: {filename}")
            continue
            
        docs.extend(loader.load())
    
    add_log(f"Loaded {len(docs)} documents from folder")
    print(f"Loaded {len(docs)} documents from folder")
    st.session_state.processed_files = processed_files
    return docs
# Chunk documents function
def chunk_documents(documents, chunk_size=500, chunk_overlap=100):
    if not documents:
        add_log("No documents to chunk!")
        print("No documents to chunk!")
        return []
        
    add_log(f"Chunking documents with size={chunk_size}, overlap={chunk_overlap}")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(documents)
    
    add_log(f"Created {len(chunks)} chunks from {len(documents)} documents")
    print(f"Created {len(chunks)} chunks from {len(documents)} documents")
    return chunks

# Embed and store function
def embed_and_store(chunks):
    if not chunks:
        add_log("No chunks to embed!")
        print("No chunks to embed!")
        return None
        
    add_log("Initializing embedding model...")
    print("Initializing embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    add_log("Creating vector database...")
    print("Creating vector database...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    vectorstore_dir = "rag_vectorstore"
    os.makedirs(vectorstore_dir, exist_ok=True)
    vectorstore.save_local(vectorstore_dir)
    
    add_log(f"Vector database created and saved to {vectorstore_dir}")
    print(f"Vector database created and saved to {vectorstore_dir}")
    return vectorstore

def calculator_agent(question):
    add_log(f"Calculator processing: '{question}'")
    print(f"Calculator processing: '{question}'")

    math_expression = None
    
    expression_patterns = [
        r'calculate\s+(.*)',
        r'compute\s+(.*)',
        r'solve\s+(.*)',
        r'evaluate\s+(.*)',
        r'(.*[\d\+\-\*\/\^\!\(\)\s]+.*)'
    ]
    
    for pattern in expression_patterns:
        match = re.search(pattern, question.lower())
        if match:
            potential_expression = match.group(1).strip()

            potential_expression = re.sub(r'[a-zA-Z]', '', potential_expression)
            potential_expression = potential_expression.replace('^', '**')
            
            if '!' in potential_expression:

                factorial_match = re.search(r'(\d+)!', potential_expression)
                if factorial_match:
                    num = int(factorial_match.group(1))
                    potential_expression = potential_expression.replace(f"{num}!", f"factorial({num})")
            
            #square roots
            if 'sqrt' in question.lower() or '√' in question:
                sqrt_match = re.search(r'sqrt\s*\(?(\d+)\)?', question.lower())
                if not sqrt_match:
                    sqrt_match = re.search(r'√\s*\(?(\d+)\)?', question)
                if sqrt_match:
                    num = int(sqrt_match.group(1))
                    potential_expression = f"sqrt({num})"
            
            #log
            if 'log' in question.lower():
                log_match = re.search(r'log\s*\(?(\d+)\)?', question.lower())
                if log_match:
                    num = int(log_match.group(1))
                    potential_expression = f"log({num})"
            
            #trigonometric
            if any(trig in question.lower() for trig in ['sin', 'cos', 'tan']):
                trig_match = re.search(r'(sin|cos|tan)\s*\(?(\d+)\)?', question.lower())
                if trig_match:
                    func = trig_match.group(1)
                    angle = int(trig_match.group(2))
                    potential_expression = f"{func}({angle}*pi/180)"  # Convert to radians
            
            if potential_expression and any(c in potential_expression for c in '0123456789+-*/()!^'):
                math_expression = potential_expression
                break
    
    if not math_expression:
        numbers = re.findall(r'\d+', question)
        if "add" in question.lower() or "sum" in question.lower() or "plus" in question.lower() or "+" in question.lower():
            if len(numbers) >= 2:
                math_expression = f"{numbers[0]} + {numbers[1]}"
        elif "subtract" in question.lower() or "minus" in question.lower() or "difference" in question.lower() or "-" in question.lower():
            if len(numbers) >= 2:
                math_expression = f"{numbers[0]} - {numbers[1]}"
        elif "multiply" in question.lower() or "product" in question.lower() or "*" in question.lower():
            if len(numbers) >= 2:
                math_expression = f"{numbers[0]} * {numbers[1]}"
        elif "divide" in question.lower() or "/" in question.lower():
            if len(numbers) >= 2:
                math_expression = f"{numbers[0]} / {numbers[1]}"
        elif "factorial" in question.lower() or "!" in question:
            if len(numbers) >= 1:
                math_expression = f"factorial({numbers[0]})"
        elif "power" in question.lower() or "exponent" in question.lower() or "^" in question or "to the power" in question.lower():
            if len(numbers) >= 2:
                math_expression = f"{numbers[0]} ** {numbers[1]}"
        elif "square root" in question.lower() or "sqrt" in question.lower() or "√" in question:
            if len(numbers) >= 1:
                math_expression = f"sqrt({numbers[0]})"
        elif "log" in question.lower() or "logarithm" in question.lower():
            if len(numbers) >= 1:
                math_expression = f"log({numbers[0]})"
    
    if math_expression:
        try:
            x = symbols('x')
            namespace = {"factorial": factorial, "sqrt": sqrt, "log": log, 
                        "exp": exp, "sin": sin, "cos": cos, "tan": tan, "pi": pi}
            
            result = sympify(math_expression, locals=namespace)
            
            if result.is_real:
                if result.is_integer:
                    result_str = str(int(result))
                else:
                    result_str = f"{float(result):.6f}".rstrip('0').rstrip('.')
            else:
                result_str = str(result)
            
            return {
                "result": f"Calculator result: {result_str}",
                "tool_used": "Calculator",
                "math_expression": math_expression
            }
        except Exception as e:
            return {
                "result": f"Sorry, I couldn't calculate that. Error: {str(e)}",
                "tool_used": "Calculator",
                "error": str(e)
            }
    else:
        return {
            "result": "I detected a calculation request but couldn't parse the mathematical expression.",
            "tool_used": "Calculator",
            "error": "Failed to parse expression"
        }
        
def dictionary_agent(question):
    add_log(f"Dictionary processing: '{question}'")
    print(f"Dictionary processing: '{question}'")
    
    import re
    
    term = None
    patterns = [
        r'define\s+(?:the\s+)?(?:term\s+)?["\']?([^"\'?]+)["\']?',
        r'what\s+(?:does|is|are)\s+(?:the\s+)?(?:definition\s+of\s+)?["\']?([^"\'?]+)["\']?',
        r'meaning\s+of\s+["\']?([^"\'?]+)["\']?'
    ]
    
    for pattern in patterns:
        matches = re.search(pattern, question.lower())
        if matches:
            term = matches.group(1).strip()
            break
    
    if not term:
        words = question.lower().split()
        for word in words:
            if word not in ["what", "is", "the", "definition", "of", "meaning", "define"]:
                term = word
                break
    
    if term:
        try:
            add_log(f"Trying PyDictionary for term: '{term}'")
            print(f"Trying PyDictionary for term: '{term}'")
            try:
                dictionary = PyDictionary()
                definition = dictionary.meaning(term)
                
                if definition:
                    result = f"Definition of '{term}':\n\n"
                    for part_of_speech, meanings in definition.items():
                        result += f"**{part_of_speech}**:\n"
                        for i, meaning in enumerate(meanings, 1):
                            result += f"{i}. {meaning}\n"
                    
                    return {
                        "result": result,
                        "tool_used": "Dictionary (PyDictionary)",
                        "term": term
                    }
            except Exception as e:
                add_log(f"PyDictionary failed: {str(e)}")
                print(f"PyDictionary failed: {str(e)}")
                
            add_log(f"Trying Free Dictionary API for term: '{term}'")
            print(f"Trying Free Dictionary API for term: '{term}'")
            try:
                import requests
                url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{term}"
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and isinstance(data, list) and len(data) > 0:
                        result = f"Definition of '{term}':\n\n"
                        entry = data[0]
                        
                        if "meanings" in entry:
                            for meaning in entry["meanings"]:
                                part_of_speech = meaning.get("partOfSpeech", "")
                                result += f"**{part_of_speech.capitalize()}**:\n"
                                
                                for i, definition in enumerate(meaning.get("definitions", []), 1):
                                    result += f"{i}. {definition.get('definition', '')}\n"
                                    
                                    if "example" in definition and definition["example"]:
                                        result += f"   _Example: {definition['example']}_\n"
                                
                                result += "\n"
                        
                        return {
                            "result": result,
                            "tool_used": "Dictionary (Free Dictionary API)",
                            "term": term
                        }
            except Exception as e:
                add_log(f"Free Dictionary API failed: {str(e)}")
                print(f"Free Dictionary API failed: {str(e)}")
            
            add_log(f"Falling back to LLM for definition of: '{term}'")
            print(f"Falling back to LLM for definition of: '{term}'")
            return query_system_with_info(f"Define the term '{term}'", tool="Dictionary (LLM Fallback)")
                
        except Exception as e:
            add_log(f"All dictionary methods failed: {str(e)}")
            print(f"All dictionary methods failed: {str(e)}")
            return {
                "result": f"Sorry, I couldn't find a definition for '{term}'. Error: {str(e)}",
                "tool_used": "Dictionary",
                "error": str(e)
            }
    else:
        return {
            "result": "I detected a definition request but couldn't identify the term to define.",
            "tool_used": "Dictionary",
            "error": "Failed to extract term"
        }
        
        
def query_system(question):
    if st.session_state.qa_chain is None and question.lower().startswith(("calculate", "define")):
        pass
    elif st.session_state.qa_chain is None:
        add_log("Error: QA chain not initialized!")
        print("Error: QA chain not initialized!")
        return
    
    add_log(f"Processing query: '{question}'")
    print(f"Processing query: '{question}'")
    
    agent_type = route_query(question)
    
    try:
        if agent_type == "calculator":
            result = calculator_agent(question)
            answer = result["result"]
            agent_used = "Calculator"
            agent_details = {
                "expression": result.get("math_expression", "Unknown")
            }
            sources = []
            
        elif agent_type == "dictionary":
            print("Using dictionary")
            result = dictionary_agent(question)
            answer = result["result"]
            agent_used = "Dictionary"
            agent_details = {
                "term": result.get("term", "Unknown")
            }
            sources = []
            
        else:  # RAG
            result = st.session_state.qa_chain(question)
            answer = result["result"]
            sources = result["source_documents"]
            agent_used = "RAG"
            agent_details = {
                "sources_used": len(result["source_documents"])
            }
        
        add_log(f"Query processed successfully using {agent_used} agent")
        print(f"Query processed successfully using {agent_used} agent")
        
        # Add to chat history
        st.session_state.chat_history.append({
            "role": "user",
            "content": question
        })
        
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": answer,
            "agent_used": agent_used,
            "agent_details": agent_details,
            "sources": sources
        })
        
    except Exception as e:
        add_log(f"Error during query processing: {str(e)}")
        print(f"Error during query processing: {str(e)}")
        
        error_message = f"Error processing your question: {str(e)}"
        
        st.session_state.chat_history.append({
            "role": "user",
            "content": question
        })
        
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": error_message,
            "agent_used": "Error",
            "agent_details": {"error": str(e)},
            "sources": []
        })


def query_system_with_info(question, tool="Dictionary"):
    """Fallback query function that uses the QA chain when dictionary fails"""
    try:
        if st.session_state.qa_chain:
            result = st.session_state.qa_chain(question)
            return {
                "result": result["result"],
                "tool_used": tool,
                "sources": result.get("source_documents", [])
            }
        else:
            return {
                "result": f"I couldn't find information for '{question}'.",
                "tool_used": tool,
                "error": "QA chain not available"
            }
    except Exception as e:
        return {
            "result": f"Error processing '{question}': {str(e)}",
            "tool_used": tool,
            "error": str(e)
        }

def route_query(question):
    question_lower = question.lower()
    print(f"Routing query: '{question}'")
    if any(keyword in question_lower for keyword in ["calculate", "compute", "math", "sum", "difference", "multiply", "divide","plus","minus","add","+","-","*","/","factorial","!","power","exponent","^","square root","sqrt","√","log","logarithm","trigonometric","sin","cos","tan","pi","trig","trigonometry","trigonometrical","trigonometric functions","trigonometric ratios","trigonometric identities"]):
        add_log("Routing to Calculator agent")
        print("Routing to Calculator agent")
        return "calculator"
    elif any(keyword in question_lower for keyword in ["define", "definition", "meaning","means", "what are"]):
        add_log("Routing to Dictionary agent")
        print("Routing to Dictionary agent")
        return "dictionary"
    else:
        add_log("Routing to RAG agent")
        print("Routing to RAG agent")
        return "rag"

def load_vectorstore():
    """Load the preexisting vector store"""
    vectorstore_dir = "rag_vectorstore"
    
    if not os.path.exists(vectorstore_dir):
        add_log(f"ERROR: Vector store directory '{vectorstore_dir}' not found!")
        print(f"ERROR: Vector store directory '{vectorstore_dir}' not found!")
        return None
    
    try:
        add_log("Loading embedding model...")
        print("Loading embedding model...")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        add_log("Loading vector database from disk...")
        print("Loading vector database from disk...")
        vectorstore = FAISS.load_local(vectorstore_dir, embeddings, allow_dangerous_deserialization=True)
        
        add_log("Vector database loaded successfully!")
        print("Vector database loaded successfully!")
        return vectorstore
    except Exception as e:
        add_log(f"Error loading vector database: {str(e)}")
        print(f"Error loading vector database: {str(e)}")
        return None

def create_qa_chain(vectorstore):
    if vectorstore is None:
        add_log("Error: No vector store available to create QA chain!")
        print("Error: No vector store available to create QA chain!")
        return None
        
    add_log("Setting up retriever...")
    print("Setting up retriever...")
    retriever = vectorstore.as_retriever(
        search_type="similarity_score_threshold", 
        search_kwargs={"k": 3, "score_threshold": 0.1}  
    )
    
    # Try to get API key from environment first, then from session state
    # api_key = "AIzaSyCiY8WwfFnZXuUEzWvBzmHl0OqpHLiUHJQ"
    api_key = os.environ.get("GOOGLE_API_KEY", st.session_state.api_key)
    
    if not api_key:
        add_log("No Google API key found. Please set it in the settings.")
        print("No Google API key found. Please set it in the settings.")
        return None
    
    # Set the API key in the environment
    os.environ["GOOGLE_API_KEY"] = api_key
    
    add_log("Initializing LLM...")
    print("Initializing LLM...")
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", convert_system_message_to_human=True)
        
        add_log("Creating QA chain...")
        print("Creating QA chain...")
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        add_log("QA system ready!")
        print("QA system ready!")
        return qa_chain
    except Exception as e:
        add_log(f"Error initializing LLM: {str(e)}")
        print(f"Error initializing LLM: {str(e)}")
        return None

def route_query(question):
    question_lower = question.lower()
    
    if any(keyword in question_lower for keyword in ["calculate", "compute", "math", "sum", "difference", "multiply", "divide","plus","minus","add","+","-","*","/"]):
        add_log("Routing to Calculator agent")
        print("Routing to Calculator agent")
        return "calculator"
    elif any(keyword in question_lower for keyword in ["define", "definition", "meaning"]):
        add_log("Routing to Dictionary agent")
        print("Routing to Dictionary agent")
        return "dictionary"
    else:
        add_log("Routing to RAG agent")
        print("Routing to RAG agent")
        return "rag"

with st.container():
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.title("Document Assistant")
    st.markdown("#### Ask questions about your documents and get intelligent answers")
    st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state.vectorstore_loaded:
    with st.spinner("Loading vector store from disk..."):
        st.session_state.vector_store = load_vectorstore()
        if st.session_state.vector_store is not None:
            st.session_state.qa_chain = create_qa_chain(st.session_state.vector_store)
            if st.session_state.qa_chain is not None:
                st.session_state.documents_processed = True
                st.session_state.vectorstore_loaded = True
                add_log("Vector store and QA chain successfully initialized")
            else:
                st.error("Failed to create QA chain. Please check your API key in the settings.")
        else:
            st.error("Failed to load vector store. Please make sure the 'rag_vectorstore' folder exists and contains index files.")

tab1, tab2 = st.tabs(["Chatbot", "Settings"])

with tab1:
    st.markdown('<h2 class="tab-subheader">Document Assistant Chatbot</h2>', unsafe_allow_html=True)
    
    if not st.session_state.documents_processed:
        st.warning("System is initializing. Please wait or check Settings tab if this persists.")
    else: 
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
                
        if not st.session_state.chat_history:
            st.markdown("""
            <div class="welcome-message">
                <p>👋 Hello! I'm your document assistant.</p>
                <p>Ask me questions about your documents, calculations, or definitions!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message user">
                        <b>You:</b>
                        <div class="message-content">{message["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:  # assistant
                    agent_class = ""
                    agent_badge = ""
                    
                    if "agent_used" in message:
                        if message["agent_used"] == "Calculator":
                            agent_class = "calculator"
                        elif message["agent_used"] == "Dictionary":
                            agent_class = "dictionary"
                        elif message["agent_used"] == "RAG":
                            agent_class = "rag"
                            
                        agent_badge = f'<span class="agent-badge {agent_class}">{message["agent_used"]}</span>'
                    
                    st.markdown(f"""
                    <div class="chat-message assistant">
                        <b>Assistant:</b> {agent_badge}
                        <div class="message-content" >{message["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if "sources" in message and message.get("agent_used") == "RAG" and message["sources"]:
                        with st.expander("View Source Documents"):
                            for i, source in enumerate(message["sources"]):
                                st.markdown(f"""
                                <div class="source-box">
                                    <b>Source {i+1}:</b><br>
                                    <p>{source.page_content}</p>
                                    <i>From: {source.metadata.get('source', 'Unknown')}</i>
                                </div>
                                """, unsafe_allow_html=True)
                    
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.container():
            user_question = st.text_input(
                "",
                key="chat_input",
                placeholder="Ask me anything about Nvidia",
                label_visibility="collapsed"
            )
            
            col1, col2 = st.columns([5, 1])
            
            with col1:
                submit_placeholder = st.empty()
            
            with col2:
                if st.button("Clear Chat", use_container_width=True):
                    st.session_state.chat_history = []
                    st.rerun()
            
            if user_question:
                if submit_placeholder.button("Send", use_container_width=True):
                    with st.spinner("Thinking..."):
                        query_system(user_question)
                    st.rerun()  # Rerun to update the UI

with tab2:
    st.markdown('<h2 class="tab-subheader">Settings</h2>', unsafe_allow_html=True)
    
    api_key = st.text_input(
        "Google API Key (required for Google Gemini)", 
        type="password",
        help="Enter your Google API Key to use the Gemini model",
        value=st.session_state.api_key if st.session_state.api_key else ""
    )
    
    if st.button("Save API Key"):
        if api_key:
            st.session_state.api_key = api_key
            add_log("API key saved")
            os.environ["GOOGLE_API_KEY"] = api_key
            
            if st.session_state.vector_store is not None and st.session_state.qa_chain is None:
                with st.spinner("Initializing chatbot with new API key..."):
                    st.session_state.qa_chain = create_qa_chain(st.session_state.vector_store)
                    if st.session_state.qa_chain is not None:
                        st.session_state.documents_processed = True
                        st.success("Chatbot initialized successfully with new API key!")
            
            st.success("API key saved successfully!")
        else:
            st.warning("Please enter an API key")
    
    with st.expander("System Status"):
        st.markdown(f"**Vector Store Loaded:** {st.session_state.vector_store is not None}")
        st.markdown(f"**QA Chain Initialized:** {st.session_state.qa_chain is not None}")
        st.markdown(f"**Documents Processed:** {st.session_state.documents_processed}")
        
        if st.button("Reload Vector Store"):
            with st.spinner("Reloading vector store..."):
                st.session_state.vector_store = load_vectorstore()
                if st.session_state.vector_store is not None:
                    st.session_state.qa_chain = create_qa_chain(st.session_state.vector_store)
                    if st.session_state.qa_chain is not None:
                        st.session_state.documents_processed = True
                        st.success("Vector store and QA chain successfully reloaded!")
                    else:
                        st.error("Failed to create QA chain. Please check your API key.")
                else:
                    st.error("Failed to load vector store.")
    
    with st.expander("System Logs"):
        if st.button("Clear Logs"):
            st.session_state.logs = []
            st.success("Logs cleared!")
        
        st.markdown('<div class="log-container">', unsafe_allow_html=True)
        if not st.session_state.logs:
            st.info("No logs recorded yet.")
        else:
            for log in st.session_state.logs:
                st.markdown(f'<div class="log-entry">{log}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### About")
    st.markdown("""
    This application uses:
    - Google Gemini model for answering questions
    - Hugging Face embeddings for document indexing
    - FAISS for efficient vector similarity search
    
    The system can:
    - Answer questions about your documents using RAG technology
    - Perform calculations using the Calculator module
    - Provide definitions using the Dictionary module
    """)