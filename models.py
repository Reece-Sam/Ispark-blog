from database import get_connection

def create_post_table():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
       CREATE TABLE IF NOT EXISTS posts (
           id SERIAL PRIMARY KEY,
           title VARCHAR(255) NOT NULL,
           header_image TEXT,
           author_id INTEGER NOT NULL,
           content TEXT NOT NULL,
           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
           last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
           status VARCHAR(20) DEFAULT 'draft',
           published_at TIMESTAMP,
           destination VARCHAR(50) NOT NULL,

           CONSTRAINT posts_status_check
               CHECK (status IN ('draft', 'published'))

       )
""")

connection.commit()

cursor.close()
connection.close()