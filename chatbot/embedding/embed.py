from io import BytesIO

from transformers import AutoTokenizer, AutoModel
import torch
import pandas as pd
import numpy as np
from psycopg2.extras import execute_values


def create_flecontext(file_path):
    flecontxt = (file_path.replace('C:/', '')
                 .replace('/', ' ').replace('\\', ' '))
    return flecontxt

def md_lines_text(mdbytes, file_path, window, step):
    """convert md text to dataframe with text chunks
    for embedding

    Args:
        mdbytes (str): binary md file
        window (int): window size of text chunks
        step (int): step size of text chunks

    Returns:
        pd.DataFrame: dataframe with text chunks, 
            start and end line, page and token index
    """
    fullseq = []
    linetotal = 0
    with BytesIO(mdbytes) as file:
        md_reader = file.readlines()
        for line in md_reader:
            lineseq = line.decode('utf-8').split('\n')
            lineseq2 = [x+'§§' for x in lineseq]
            tokenseq = [(linetotal+i,
                         y.replace('§§', '\n'))
                        for i, x in
                        enumerate(lineseq2)
                        for y in
                        x.split()]
            tokendf = pd.DataFrame(tokenseq,
                                   columns=['line',
                                            'token'])
            linetotal = tokendf.line.max()+1
            fullseq.append(tokendf)
    fulldf = pd.concat(fullseq).reset_index(drop=True)
    tokenseq = fulldf.token.tolist()
    lineseq = fulldf.line.tolist()
    idx = fulldf.index.tolist()
    flecontxt = create_flecontext(file_path)
    window = window-len(flecontxt.split())
    seqlen = len(tokenseq)
    mdchunks = [' '.join(tokenseq[i:i+window])
                for i in range(0, seqlen, step)]
    mdchunks2 = [flecontxt + ':\n ' + x
                 for x in mdchunks]
    startlines = [lineseq[i] for i in
                  range(0, seqlen, step)]
    starrtidx = [idx[i] for i in
                 range(0, seqlen, step)]
    endlines = [lineseq[-1] if i+window >= len(lineseq)
                else lineseq[i+window] 
                for i in range(0, seqlen, step)]
    endidx = [idx[-1] if i+window >= len(idx) 
              else idx[i+window] 
              for i in range(0, seqlen, step)]
    startpages = [np.nan for _ in range(len(endidx))]
    endpages = [np.nan for _ in range(len(endidx))]
    mdchunksdf = pd.DataFrame({'text': mdchunks2,
                                 'startlines': startlines,
                                 'startpages': startpages,
                                    'startidx': starrtidx,
                                    'endpages': endpages, # 'endpages': endpages,
                                    'endlines': endlines,
                                    'endidx': endidx})
    return mdchunksdf


def pg_insert(df, table, conn):
    exampledf = pd.read_sql('SELECT * FROM {table} LIMIT 0'.format(table=table),
                            conn) # type: ignore
    print(exampledf)
    df.columns = [x.lower() for x in df.columns]
    df = df[exampledf.columns]
    insert_statement = "INSERT INTO {table} VALUES %s".format(table=table)
    values = [tuple(row) for row in df.itertuples(index=False, name=None)]
    cursor = conn.cursor()
    execute_values(cursor, insert_statement, values)
    conn.commit()


class Embedder():
    def __init__(self, model_ckpt):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.tokenizer = AutoTokenizer.from_pretrained(model_ckpt)
        self.model = AutoModel.from_pretrained(model_ckpt).to(self.device)

    def cls_pooling(self, model_output):
        return model_output.last_hidden_state[:, 0]

    def get_embeddings(self, text_list):
        encoded_input = self.tokenizer(
            text_list, padding=True, truncation=True, return_tensors="pt"
        )
        encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}
        model_output = self.model(**encoded_input)
        return self.cls_pooling(model_output)
    

class QueryIndexPG:
    def __init__(self, model_ckpt, vector_conn,
                 samples_return=5):
        self.embedder = Embedder(model_ckpt)
        self.samples_return = samples_return
        self.vector_conn = vector_conn
    
    def query(self, query, table):
        query_embedding = (self.embedder
                           .get_embeddings([query])
                           .detach()
                           .cpu()
                           .numpy())
        emb_q = str(list(query_embedding))
        nn = pd.read_sql("SELECT id,\
                            text,\
                            cid,\
                            startlines,\
                            startpages,\
                            startidx,\
                            endlines,\
                            endpages,\
                            endidx,\
                            file,\
                         1/(embedding <-> '{}') as score \
                         FROM {} ORDER BY \
                         embedding <-> '{}' LIMIT {};".format(table,
                                                                emb_q, 
                                                              self.samples_return), 
                         conn=self.vector_conn) # type: ignore
        return nn