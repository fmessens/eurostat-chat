#from langchain import OpenAI, ConversationChain
#from langchain.memory import ConversationBufferMemory
#from langchain.llms import OpenAI
import os
import re
from numpy import full

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
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
                      pgpassword)

#adaptr#####
org_name = 'eurostat_test'
table = f'{org_name}.eurostat_metadata'
###########

embedder = Embedder(model_ckpt)

""" chat = OpenAI(temperature=0)

conversation = ConversationChain(
    llm=chat, 
    verbose=True,
    memory=ConversationBufferMemory()
) """
mistral_api_key = os.environ.get("MISTRAL_API_KEY")
chat = ChatMistralAI(mistral_api_key=mistral_api_key)

def first_prompt(query):
    messages = [SystemMessage(content="We will have a conversation about the eurostat database. \
The end result of the conversation should be a simple as possible single SQL query to answer the following question.\
 Whenever you see that the question is out of scope, please say so.")]
    return messages + [HumanMessage(content=f"What free form search queries \
to make to find all data for answerring this question?\
 Please provide a list with queries in double quotes. \
No SQL queries yet please.")]


def get_mistral_answer(full_content, prompt, set_progress):
    messages = [HumanMessage(content=prompt)]
    for chunk in chat.stream(messages):
        full_content += chunk.content
        set_progress(full_content)
    return full_content


def second_prompt(aicontent):
    new_db_conn = psycopg2.connect(
        host=postgresshost,
        port=pgport,
        user=pguser,
        password=pgpassword,
    )
    matches = list(set(re.findall(r'"(.*?)"', aicontent)))

    # query the vector db
    all_meta = []
    for q in matches:
        emb = embedder.get_embeddings(q)
        npemb = emb.detach().cpu().numpy()[0]
        emb_q = str(list(npemb))
        nn = pd.read_sql(f"SELECT *,\
        1/(embeddings <-> '{emb_q}') as score \
        FROM {table} ORDER BY \
        embeddings <-> '{emb_q}' LIMIT {samples_return};", 
                         new_db_conn)
        all_meta.append(nn)

    all_meta_df = pd.concat(all_meta).drop_duplicates()
    full_context = ''
    for _, r in all_meta_df.iterrows():
        full_context += r['text'] + '\n'

    messages = [HumanMessage(content=f"Here are a list of resulting tables based on your search queries:\
'{full_context}'. Give a list of tables in double quotes that you think are relevant to the question.\
 Please nothing else in double quotes.")]
    return messages


def third_prompt(aicontent):
    new_db_conn = psycopg2.connect(
        host=postgresshost,
        port=pgport,
        user=pguser,
        password=pgpassword,
    )
    matches = list(set(re.findall(r'"(.*?)"', aicontent)))
    matchstr = str(tuple([x.replace('\\','').upper() 
                          for x in matches]))
    cols = pd.read_sql(f"SELECT * FROM {org_name}.column_metatdata \
    WHERE table_code IN {matchstr};", new_db_conn)
    markdown_table = cols.to_markdown()
    full_prompt = [HumanMessage(content=f"Given the column and table info in the following table:\n\
{markdown_table}. \n\
List the columns to use for answering the question. Please list items in duoble quotes and nothing else.")]
    return full_prompt


def fourth_prompt():
    return [HumanMessage(content=f"Given the previous info can you construct a SQL query to answer the question?\
 Please provide a single SQL query and format in markdown.")]