import os

samples_return = 5

postgresshost = 'localhost'
pguser = 'postgres'
pgpassword = os.environ['POSTGRESS_PASSWORD']
pgport = 5432

model_ckpt = "sentence-transformers/multi-qa-mpnet-base-dot-v1"

schema_name = 'eurostat_test'
table = f'{schema_name}.eurostat_metadata2'