"""Quickly create a vectorstore"""
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.lib.data.constants import CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDER, VECSTORE_PERSIST_DIR

if __name__ == '__main__':
    with open('../data/company_docs.txt') as file:
        splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        splitted = splitter.split_text(text=file.read())

    docs = [Document(page_content=text, metadata={'source': 'src/db/data/company_docs.txt'}) for text in splitted]
    Chroma.from_documents(docs, embedding=EMBEDDER, persist_directory=VECSTORE_PERSIST_DIR)