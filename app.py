from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():  # put application's code here
    return jsonify({"status": "Success", "message": "The bridge is working!"})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
