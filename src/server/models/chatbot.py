from langchain_chroma import Chroma
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from typing import List, Dict, TypeAlias
import random, textwrap
from src.lib.data.constants import CHAT_LLM, CONDITIONAL_LLM, VECSTORE_PERSIST_DIR, TOP_K, EMBEDDER, BASE_SYS_MSG, ERR_RESPONSE
from src.lib.utils.logger import err_log
from src.lib.utils.db import search_products, get_all_products, search_users, get_all_users, get_user_info

## Private utils
_Conversation: TypeAlias = List[Dict[str, str]]

def _prompt(string: str) -> str:
    """Formats prompts for LLMs"""
    res = textwrap.dedent(string)
    if res[0] == '\n': res = res[1:]
    if res[-1] == '\n': res = res[:-2]
    return res

def _condition(question: str) -> bool:
    """Returns true or false intelligently to a given query"""
    prompt = _prompt(f'''
        You are an intelligent yes-no answerer of general-knowledge questions; you ONLY answer with "yes" or "no".
        Message: {question}
    ''')
    response = CONDITIONAL_LLM.invoke(prompt)
    return 'yes' in response.lower()


## Main class
class Chatbot:
    """Chatbot assistant that answers end users' questions about products and information through RAG"""
    def __init__(self) -> None:
        self._reset_history()
        self._add_sys_msg = lambda msg: self.history.append(SystemMessage(_prompt(msg)))
        self.llm = CHAT_LLM
        self.template = _prompt('''
            Context: """{docs}"""\n\n
            You are a friendly EcomGo customer support employee!
            Use the above context (if relevant) to answer any question concisely.
            You must NOT synthesize information; ONLY if the context is relevant, you MUST use the context or previous messages to answer the question.
            Otherwise, answer the question directly. Here is the question/message: "{question}"'
        ''')

    def __call__(self, prompt: str, sender: str = '', conv: _Conversation = []) -> str:
        self._parse_conversation(conv)
        return self.chat(prompt, sender)


    def chat(self, prompt: str, sender: str = '') -> str:
        """Returns the LLM's response to the given prompt"""
        try:
            # Using tools
            self._search_products(prompt)
            self._search_users(prompt)
            self._get_sender_info(sender)

            # Prompting the LLM
            self.history.append(HumanMessage(self.template.format(docs=self._retrieve_docs(prompt), question=prompt)))
            response = self.llm.invoke(self.history).content
            self._reset_history()
            return response
        except Exception as e:
            err_log('Chatbot.chat', e, 'model')
            return ERR_RESPONSE


    def _reset_history(self) -> None:
        """Resets the chatbot's conversation memory"""
        self.history = [BASE_SYS_MSG]


    def _parse_conversation(self, conv: _Conversation) -> None:
        """Loads the given conversation history from strings to chat schemas"""
        try:
            for msg in conv:
                sender, content = msg['sender'], msg['content']
                match sender:
                    case 'chatbot': self.history.append(AIMessage(content))
                    case 'system': self.history.append(SystemMessage(content))
                    case _: self.history.append(HumanMessage(content))
        except Exception as e:
            err_log('Chatbot._parse_conversation', e, 'model')


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
            err_log('Chatbot._retrieve_docs', e, 'model')


    def _search_products(self, prompt: str) -> None:
        """Retrieves product(s) info & adds it to the chatbot's memory"""
        products = []
        if _condition(f'Does the message "{prompt}" explicitly/implicitly care about a specific product(s)?'):
            products = search_products(prompt)
        else:
            products = random.sample(get_all_products(), 4)

        for p in products:
            self._add_sys_msg(f'''
                PRODUCT NAME: {p.name}
                - MANUFACTURER: {p.owner}
                - PRICE: {p.price}
                - DISCOUNT: {p.discount}
                - DISCOUNTED PRICE: {p.price - (p.discount * p.price):.2f}\n\n
            ''')


    def _search_users(self, prompt: str) -> None:
        """Retrieves user(s) info & adds it to the chatbot's memory"""
        users = []
        if _condition(f'Does the message "{prompt}" explicitly/implicitly care about a specific user(s)?'):
            users = search_users(prompt)
        else:
            users = random.sample(get_all_users(), 4)

        for u in users:
            info = get_user_info(u.username)
            owned_product_names = ', '.join([p.name for p in info['owned_products']])
            self._add_sys_msg(f"""
                USER/MANUFACTURER NAME: {info['username']}
                - BIO: {info['bio']}
                - OWNED PRODUCTS: {owned_product_names}\n\n
            """)


    def _get_sender_info(self, sender: str) -> None:
        """Retrieves more info about the customer & adds it to the chatbot's memory"""
        if len(sender) == 0: return ''
        info = get_user_info(sender)
        self._add_sys_msg(f"""
            INFO OF THE CUSTOMER YOU'RE ANSWERING:
            - USERNAME: {info['username']}
            - BIO: {info['bio']}
        """)