from langchain_chroma import Chroma
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from typing import List
from src.lib.data.constants import CHAT_LLM, VECSTORE_PERSIST_DIR, TOP_K, EMBEDDER, BASE_SYS_MSG, ERR_RESPONSE
from src.lib.utils.logger import err_log

class Chatbot:
    """Chatbot assistant that answers end users' questions about products and information through RAG"""
    def __init__(self) -> None:
        self.history = [BASE_SYS_MSG]
        self.llm = CHAT_LLM
        self.template = 'Context: {docs}\n\nUse the above context (if relevant) to answer any question. You must NOT synthesize information; you MUST use the context to answer the question ONLY if it is relevant. Otherwise, answer the question directly. Here is the question: "{question}"'


    def reset_history(self) -> None:
        """Resets the chatbot's conversation memory"""
        self.history = [BASE_SYS_MSG]
    

    def parse_conversation(self, conversation: List) -> None:
        """Loads the given conversation history from strings to chat schemas"""
        try:
            for lst in conversation:
                role, message = lst
                match role:
                    case 'human': self.history.append(HumanMessage(message))
                    case 'ai': self.history.append(AIMessage(message))
                    case 'system': self.history.append(SystemMessage(message))
        except Exception as e:
            err_log('LLM.parse_conversation', e, 'model')
    

    def _retrieve_docs(self, search_input: str, k: int = TOP_K) -> str:
        """Retrieves the top `k` relevant documents with respect to `search_input`"""
        try:
            vectorstore = Chroma(persist_directory=VECSTORE_PERSIST_DIR, embedding_function=EMBEDDER)
            retriever = vectorstore.as_retriever(search_kwargs={'k': k})
            docs = ''
            for doc in retriever.invoke(search_input):
                docs += doc.page_content + '\n'
            return docs
        except Exception as e:
            err_log('LLM._retrieve_docs', e, 'model')


    def chat(self, prompt: str) -> str:
        """Returns an LLM response"""
        try:
            docs = self._retrieve_docs(prompt)
            self.history.append(HumanMessage(self.template.format(docs=docs, question=prompt)))
            response = self.llm.invoke(self.history).content
            self.reset_history()
            return response
        except Exception as e:
            err_log('LLMAgent.chat', e, 'model')
            return ERR_RESPONSE