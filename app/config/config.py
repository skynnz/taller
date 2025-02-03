from flask import current_app, g
import psycopg2
from psycopg2.extras import DictCursor

def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(
            dbname=current_app.config.get('DB_DATABASE','systemlb'),
            user=current_app.config.get('DB_USER', 'postgres'),
            password=current_app.config.get('DB_PASSWORD', 'admin'),
            host=current_app.config.get('DB_HOST', 'localhost'),
            cursor_factory= DictCursor
        )
        g.db.autocommit = False
    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()
