import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='size624RACY!',
        database='sakila'
    )
    return connection