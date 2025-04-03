import os
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

# Set your API key
os.environ["OPENAI_API_KEY"] = "sk-..."

# Load all .txt files from a directory
def load_all_texts(folder_path):
    docs = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            path = os.path.join(folder_path, filename)
            loader = TextLoader(path)
            docs.extend(loader.load())
    return docs

# Load and process the texts
docs = load_all_texts("./addiction_texts")

# Chunk the docs
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)

# Embed the chunks using OpenAI
embeddings = OpenAIEmbeddings()
db = FAISS.from_documents(chunks, embeddings)

# Set up the GPT model (you can use "gpt-3.5-turbo" or "gpt-4")
llm = ChatOpenAI(model_name="gpt-4")

# Create the QA chain
qa = RetrievalQA.from_chain_type(llm=llm, retriever=db.as_retriever())

# Now you can ask it questions
while True:
    query = input("\nAsk the Addiction Therapist: ")
    if query.lower() in ["exit", "quit"]:
        break
    answer = qa.run(query)
    print("\n🤖", answer)
