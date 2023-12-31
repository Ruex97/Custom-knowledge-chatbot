import streamlit as st #GUI
from dotenv import load_dotenv #Enable use of .env
from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from htmlTemplate import css, bot_template, user_template

def main():
    load_dotenv()

     #session variables initialization
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    #GUI
    st.set_page_config(page_title="Chat with PDFs", page_icon=":books:")

    st.write(css, unsafe_allow_html=True)
    st.header("Chatea with your PDFs :books:")

    user_question = st.text_input("Ask me something about your Pdfs: ")
    if user_question:
        handle_userinput(user_question)
    
    #Creating sidebar
    with st.sidebar:
        st.subheader("Your Files")
        pdf_docs = st.file_uploader(  
            "Drop your files here and click Process",
            accept_multiple_files=True)
        if st.button("Process"):
            with st.spinner("Processing"):
                # Get pdf text
                raw_txt = get_pdf_text(pdf_docs)

                # Get chunks of text
                text_chunks = get_text_chunks(raw_txt)

                # create vector store
                vectorstore = get_vectorstore(text_chunks)

                # Create conversation chain
                st.session_state.conversation = get_conversation_chain(vectorstore)     #Takes history of conversation and returns the next element, that's why we make it persistent


def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()

    return text


def get_text_chunks(raw_txt):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000, 
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(raw_txt)
    
    return chunks

def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)        #Creating the database
    return vectorstore


def get_conversation_chain(vectorstore):
    llm = ChatOpenAI()
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory        
    )
    return conversation_chain

def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
        else: 
            st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
