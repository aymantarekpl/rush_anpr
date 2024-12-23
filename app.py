from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, jsonify
import xml.etree.ElementTree as ET
from werkzeug.security import check_password_hash
import requests
from flask_cors import CORS
import re
from flask_socketio import SocketIO, emit

base_url = 'https://rush-pre.odoo.com'
db_name = 'rush_05_12'
app = Flask(__name__)
app.secret_key = "your_secret_key"
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable CORS for all origins


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    socketio.emit('message', {'data': 'Connected'})

@socketio.on('client_message')
def handle_message(data):
    print(f'Received message: {data}')
    socketio.emit('server_message', {'data': data})

def authenticate_odoo(username, password, base_url, db_name, ):
    # return redirect(url_for('home'))
    url = f"{base_url}/web/session/authenticate"
    headers = {
        'Content-Type': 'application/json',
    }
    payload = {
        'jsonrpc': '2.0',
        'method': 'call',
        'params': {
            'db': db_name,
            'login': username,
            'password': password,
        },
        # 'id': 1,
    }
    # response = requests.post(url, json=payload, headers=headers)
    # result = response.json()
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        # Parse and return JSON response
    except requests.exceptions.RequestException as e:
        print(f"Error during authentication: {e}")
        return jsonify({'error': 'No Odoo session ID found in cookies'}), 403
    # response = response.json()
    print(response.cookies.get('session_id'))
    session_id = response.cookies.get('session_id')
    if session_id:
        res = response.json()
        res.update({'session_id': session_id})
        response = make_response(res)
        response.set_cookie('session_id', session_id, max_age=3600)  # Set a cookie with a 1-hour expiration

        return response
    else:
        return jsonify({'error': 'No Odoo session ID found in cookies'}), 403
    return None


@app.route('/', )
def home():
    if not request.cookies.get('session_id'):
        return redirect(url_for('login'))
    return "<p>Hello, World from \
                    redirected page.!</p>"


@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')


@app.route('/authenticate', methods=['GET', 'POST'])
def authenticate():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    return authenticate_odoo(username, password, base_url, db_name, )


@app.route('/get/car/packages', methods=['POST','GET'])
def get_packages():
    # Retrieve session from Flask's cookies
    request_data = request.get_json()
    odoo_session_id = request_data.get('session_id')  # Ensure the session ID is already saved in Flask session
    #
    if not odoo_session_id:
        return jsonify({'error': 'No Odoo session ID found in cookies'}), 403

    # Odoo URL and endpoint
    odoo_url = f"{base_url}/web/dataset/call_kw"

    # Example data to send (if any required for get_car_packages)


    car_number = request_data.get('car_number')
    data = {
        "jsonrpc": "2.0",
        "method": "call",
        "db": db_name,
        "kwargs": [],
        "params": {
            "service": "object",
            "db": db_name,
            "model": "sale.order",  # Odoo model name
            "method": "get_car_packages",  # Function to call
            "args": [car_number],  # Arguments for the function, if needed
            "kwargs": {},  # Arguments for the function, if needed
        },
        "id": 1
    }

    # Headers including the session cookie
    headers = {
        "Content-Type": "application/json",
        'Cookie': f'session_id={odoo_session_id};'
    }

    try:
        # Send POST request to Odoo
        response = requests.post(odoo_url, json=data, headers=headers, )

        # Check the response from Odoo
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to call Odoo function', 'details': response.text}), response.status_code

    except Exception as e:
        return jsonify({'error': 'Request failed', 'details': str(e)}), 500


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/anpr/car/data', methods=['POST', 'GET'], )
def anprCameraData():
    print("================>ANPR Data Received<========")
    try:
        if not request.files:
            return jsonify({"error": "No file part in the request"}), 400

        uploaded_files = request.files

        # Check if 'anpr.xml' is among the uploaded files
        # if 'file' in uploaded_files:
        for file_name, uploaded_file in uploaded_files.items():
            if file_name == 'anpr.xml':
                # Process 'anpr.xml'
                file_content = uploaded_file.read().decode('utf-8')
                root = ET.fromstring(file_content)

                # Extract key-value pairs
                key_value_data = {}
                for element in root.iter():
                    clean_tag = re.sub(r'\{.*\}', '', element.tag)
                    key_value_data[clean_tag] = element.text.strip() if element.text else None
                if 'licensePlate' in key_value_data:
                    licensePlate = key_value_data['licensePlate']
                    print('licensePlate==========>', licensePlate)
                    handle_message(licensePlate)
                    return {"licensePlate": licensePlate}

                # Return the extracted data as a JSON response
                return {"error": "licensePlate not arrive"}

    except Exception as e:
        return jsonify({'error': 'Request failed', 'details': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
