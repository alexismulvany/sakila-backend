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

@customer_bp.route('/api/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    data = request.get_json()
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Update customer table with new first name, last name, and email
        update_cust_sql = """
            UPDATE customer 
            SET first_name = %s, last_name = %s, email = %s 
            WHERE customer_id = %s
        """
        cursor.execute(update_cust_sql, (data['first_name'], data['last_name'], data['email'], id))

        # Find customer's address_id to update the address table
        cursor.execute("SELECT address_id FROM customer WHERE customer_id = %s", (id,))
        address_id = cursor.fetchone()['address_id']

        # Updated the address and phone number in the address table
        update_addr_sql = """
            UPDATE address 
            SET address = %s, phone = %s 
            WHERE address_id = %s
        """
        cursor.execute(update_addr_sql, (data['address'], data['phone'], address_id))

        db.commit()
        return jsonify({"message": "Customer updated successfully!"})

    #undo in case something goes wrong with the update
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()


@customer_bp.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.get_json()
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Inserts new address with default values for district and city
        insert_addr_sql = """
                          INSERT INTO address (address, phone, district, city_id, location)
                          VALUES (%s, %s, 'N/A', 1, ST_GeomFromText('POINT(0 0)')) \
                          """
        cursor.execute(insert_addr_sql, (data['address'], data['phone']))

        # Grab the ID of new address
        new_address_id = cursor.lastrowid

        # Inserts new customer with new address_id and default store_id and active status
        insert_cust_sql = """
                          INSERT INTO customer (store_id, first_name, last_name, email, address_id, active)
                          VALUES (1, %s, %s, %s, %s, 1) \
                          """
        cursor.execute(insert_cust_sql, (data['first_name'], data['last_name'], data['email'], new_address_id))

        db.commit()
        return jsonify({"message": "New customer added successfully!"}), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()


@customer_bp.route('/api/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Check for unreturned rentals before allowing deletion
        check_sql = "SELECT COUNT(*) as unreturned FROM rental WHERE customer_id = %s AND return_date IS NULL"
        cursor.execute(check_sql, (id,))
        result = cursor.fetchone()

        if result['unreturned'] > 0:
            return jsonify({"error": "Customer must return all films before they can be deleted!"}), 400

        # We need to delete the payments and rentals first because of the foreign key constraints
        cursor.execute("DELETE FROM payment WHERE customer_id = %s", (id,))
        cursor.execute("DELETE FROM rental WHERE customer_id = %s", (id,))

        # Delete customer
        cursor.execute("DELETE FROM customer WHERE customer_id = %s", (id,))

        db.commit()
        return jsonify({"message": "Customer deleted successfully!"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()