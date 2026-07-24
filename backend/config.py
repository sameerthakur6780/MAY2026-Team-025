import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


DEFAULT_DB_PATH = os.path.join(BASE_DIR, "instance", "smartbatch.db")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///" + DEFAULT_DB_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False
