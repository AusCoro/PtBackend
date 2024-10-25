from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv() 

MONGO_USER = os.getenv('MONGO_USER')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
MONGO_HOST = os.getenv('MONGO_HOST')
MONGO_DB = os.getenv('MONGO_DB')


uri_db = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}"

db_conection = MongoClient(uri_db)
db_client = db_conection[MONGO_DB]
