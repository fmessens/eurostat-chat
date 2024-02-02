import os
from typing import List
import re

from langchain import hub
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain.schema.retriever import BaseRetriever
from langchain_core.documents import Document
import pandas as pd
from langchain_core.runnables import RunnablePassthrough
from langchain_mistralai.chat_models import ChatMistralAI
from dotenv import load_dotenv
import psycopg2
load_dotenv()

from chatbot.embedding.embed import Embedder
from settings import (samples_return, 
                      model_ckpt, 
                      postgresshost, 
                      pgport, 
                      pguser, 
                      pgpassword,
                      table)

class CustomPGRetriever(BaseRetriever):
    def __init__(self,
                 postgresshost: str,
                 pgport: int,
                 pguser: str,
                 pgpassword: str,
                 samples_return: int,
                 model_ckpt: str):
        super().__init__()
        self.metadata = {'new_db_conn': psycopg2.connect(
                            host=postgresshost,
                            port=pgport,
                            user=pguser,
                            password=pgpassword,
                            ),
                        'samples_return': samples_return,
                        'embedder': Embedder(model_ckpt)}

    def get_pgdb_docs(self, query: str) -> pd.DataFrame:
        # Use your existing retriever to get the documents
        tablestr = f'{table}'
        emb = self.metadata['embedder'].get_embeddings(query)
        npemb = emb.detach().cpu().numpy()[0]
        emb_q = str(list(npemb))
        nn = pd.read_sql(f"SELECT *,\
                    1/(embeddings <-> '{emb_q}') as score \
                    FROM {tablestr} A ORDER BY \
                    embeddings <-> '{emb_q}' LIMIT {self.metadata['samples_return']};", 
                                        self.metadata['new_db_conn'])
        print(nn)
        return nn
    
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        matches = list(set(re.findall(r'"(.*?)"', query)))
        documents = []
        for m in matches:
            docdf = self.get_pgdb_docs(m)
            for r in docdf.to_dict('records'):
                documents.append(Document(page_content=r['text'], 
                                        metadata={k: v for k, v 
                                                    in r.items()
                                                    if k not in ('text',
                                                                    'embeddings')}))
        print(documents)
        return documents
    


contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""
contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ]
)

mistral_api_key = os.environ.get("MISTRAL_API_KEY")
llm = ChatMistralAI(mistral_api_key=mistral_api_key)
contextualize_q_chain = contextualize_q_prompt | llm | StrOutputParser()


contextualize_q_system_prompt2 = "Given the question, formulate free form search\
 queries that you would use to retrieve relevant eurostat tables. The search engine is\
 specific for finding eurostat columns and related tables.\
 Do NOT answer the question, just formulate the search queries and put them into double quotes.\
 Put nothing else in double quotes."
contextualize_q_prompt2 = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt2),
        ("human", "{question}"),
    ]
)
contextualize_q_chain2 = contextualize_q_prompt2 | llm | StrOutputParser()

def contextualized_questionhist(input: dict):
    if input.get("chat_history"):
        return contextualize_q_chain
    else:
        return contextualize_q_chain2

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

qa_system_prompt = """You are an assistant for creating SQL queries. \
Use the following pieces of retrieved context to construct the query. \
If you don't know the answer, just say that you don't know. \
Use a singe query that is as concise as possible and format as you would in markdown.\

{context}"""

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ]
)

retriever = CustomPGRetriever(postgresshost=postgresshost,
                                pgport=pgport,
                                pguser=pguser,
                                pgpassword=pgpassword,
                                samples_return=samples_return,
                                model_ckpt=model_ckpt)
rag_chain = (
    RunnablePassthrough.assign(
        context=(contextualized_questionhist
                 | retriever 
                 | format_docs)
    )
    | qa_prompt
    | llm
)

