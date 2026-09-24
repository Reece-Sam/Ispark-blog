import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection(row_factory=None):
    return psycopg.connect(
        DATABASE_URL,
        row_factory=row_factory
    )