from flask import Blueprint, jsonify
from db_config import get_db_connection
film_bp = Blueprint('film_bp', __name__)

@film_bp.route('/api/film-details/<int:id>', methods=['GET'])
def get_film_details(id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    query = """
            SELECT f.film_id, f.title, f.description, f.release_year, c.name AS category_name,
                   GROUP_CONCAT(CONCAT(a.first_name, ' ', a.last_name) SEPARATOR ', ') AS actors
            FROM film f
            JOIN film_category fc ON f.film_id = fc.film_id
            JOIN category c ON fc.category_id = c.category_id
            JOIN film_actor fa ON f.film_id = fa.film_id
            JOIN actor a ON fa.actor_id = a.actor_id
            WHERE f.film_id = %s
            GROUP BY f.film_id;
        """

    cursor.execute(query, (id,))
    results = cursor.fetchone()
    cursor.close()
    db.close()

    return jsonify(results)

@film_bp.route('/api/actor-details/<int:id>', methods=['GET'])
def get_actor_details(id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    query = """
            SELECT a.actor_id, CONCAT(a.first_name, ' ', a.last_name) AS actor_name,
                     GROUP_CONCAT(f.title SEPARATOR ', ') AS films
            FROM actor a
            JOIN film_actor fa ON a.actor_id = fa.actor_id
            JOIN film f ON fa.film_id = f.film_id
            WHERE a.actor_id = %s;
            """

    cursor.execute(query, (id,))
    results = cursor.fetchone()
    cursor.close()
    db.close()

    return jsonify(results)