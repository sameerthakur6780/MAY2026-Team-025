"""MongoDB (sync) client & collection accessors."""
import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
_client = MongoClient(mongo_url)
db = _client[os.environ["DB_NAME"]]


def get_client():
    return _client


# Collection accessors
def batches():        return db["batches"]
def students():       return db["students"]
def users():          return db["users"]
def fees():           return db["fees"]
def resources():      return db["resources"]
def homework():       return db["homework"]
def submissions():    return db["submissions"]
def announcements():  return db["announcements"]
def attendance():     return db["attendance"]
def messages():       return db["messages"]