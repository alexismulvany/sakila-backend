from flask import Blueprint, jsonify, request
from db_config import get_db_connection;
customer_bp = Blueprint('customer_bp', __name__)

@customer_bp.route('/api/customers', methods=['GET'])
def get_customers():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    search_query = request.args.get('search')

    # Searches firstname OR lastname OR customerid
    if search_query and search_query.isdigit():
        # search by exact customer_id
        sql = """
                SELECT c.customer_id, c.first_name, c.last_name, c.email, a.address, a.phone, ci.city
                FROM customer c
                JOIN address a ON c.address_id = a.address_id
                JOIN city ci ON a.city_id = ci.city_id
                WHERE c.customer_id = %s
            """
        cursor.execute(sql, (search_query,))
    else:
        sql = """
                SELECT DISTINCT c.customer_id, c.first_name, c.last_name, c.email, a.address, a.phone, ci.city
                FROM customer c
                JOIN address a ON c.address_id = a.address_id
                JOIN city ci ON a.city_id = ci.city_id
                WHERE c.first_name LIKE %s
                   OR c.last_name LIKE %s
                   OR c.customer_id LIKE %s
            """
        wildcard = f"%{search_query}%"
        cursor.execute(sql, (wildcard, wildcard, wildcard))

    results = cursor.fetchall()
    cursor.close()
    db.close()

    return jsonify(results)

@customer_bp.route('/api/customer-details/<int:id>', methods=['GET'])
def get_customer_details(id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Customer's profile info
    profile_sql = """
        SELECT c.customer_id, c.first_name, c.last_name, c.email, c.create_date,
               a.address, a.phone, ci.city, a.postal_code
        FROM customer c
        JOIN address a ON c.address_id = a.address_id
        JOIN city ci ON a.city_id = ci.city_id
        WHERE c.customer_id = %s
    """
    cursor.execute(profile_sql, (id,))
    customer_profile = cursor.fetchone()

    # Customer rental history (limit 20)
    history_sql = """
        SELECT f.title, r.rental_date, r.return_date
        FROM rental r
        JOIN inventory i ON r.inventory_id = i.inventory_id
        JOIN film f ON i.film_id = f.film_id
        WHERE r.customer_id = %s
        ORDER BY r.rental_date DESC
        LIMIT 20
    """
    cursor.execute(history_sql, (id,))
    rental_history = cursor.fetchall()

    cursor.close()
    db.close()

    # Combine both queries
    return jsonify({
        "profile": customer_profile,
        "rentals": rental_history
    })