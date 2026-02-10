from flask import Blueprint, jsonify
from db_config import get_db_connection;
customer_bp = Blueprint('customer_bp', __name__)

