#from langchain import OpenAI, ConversationChain
#from langchain.memory import ConversationBufferMemory
#from langchain.llms import OpenAI
import os
import re
import json
import time

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from google.cloud import bigquery
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
chat = ChatMistralAI(mistral_api_key=mistral_api_key, timeout=240,
                     temperature=0)

def first_prompt(query):
    return [HumanMessage(content=f"What free form search queries \
to make to find all data for answerring the question:\n\n {query} \n\n\
 The search engine is designed to search for tables in the eurostat database (so searching for eurostat is out of scope).\
 Please provide a list with queries in double quotes.\
 No SQL queries yet please.")]


def get_mistral_answer(full_content, prompt, set_progress):
    messages = [HumanMessage(content=prompt)]
    for chunk in chat.stream(messages):
        full_content += chunk.content
        set_progress(full_content)
    return full_content


def second_prompt(aicontent, query):
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
        full_context += r['text'] + '\n\n\n'

    messages = [HumanMessage(content=f"Here are a list of tables that might be relevant:\n\
'{full_context}'.\n\
 Give a list of table codes in double quotes that you think are relevant to answer the question:\n\n\
 {query} \n\n\
 Please nothing else in double quotes.")]
    return messages


def third_prompt(aicontent, query):
    new_db_conn = psycopg2.connect(
        host=postgresshost,
        port=pgport,
        user=pguser,
        password=pgpassword,
    )
    matches = list(set(re.findall(r'"(.*?)"', aicontent)))
    matchesupper = [x.replace('\\','').upper() for x in matches]
    matchesstr = str(tuple(matchesupper))
    schemaquery = f"SELECT table_name,\
    column_name,\
    data_type,\
    FROM eurostat_all.COLUMNS_INFO\
    WHERE table_name IN {matchesstr}"
    print(schemaquery)
    colssel = pd.read_gbq(schemaquery,
                          project_id='neuraldb-proj')
    print(colssel)
    colcontent = colssel.to_markdown()
    extracts = ''
    for m in matchesupper:
        df = pd.read_gbq(f"SELECT * FROM eurostat_all.{m} LIMIT 3", project_id='neuraldb-proj')
        extracts += m +':\n'+ df.to_markdown() + '\n\n\n'

    full_prompt = [HumanMessage(content=f'Given the column and table info in the following table:\n\
{colcontent}. \n\
And extracts in the following tables:\n\
{extracts}\n\
Can you construct a SQL query to answer the question:\n\n\
 {query}.\n\n\
 The dataset is eurostat_all and the SQL dialect is Bigquery.')]
    return full_prompt, colssel


def fourth_prompt(aicontent, query):
    return [HumanMessage(content=f"Given the following info: \
\n\n{aicontent}\n\n\
 Can you construct a SQL query to answer the question:\n\n\
 {query}.\n\n\
 Please provide a single bigquery SQL and format in markdown.\
 The dataset is called eurostat_all")]