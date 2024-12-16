from flask import Flask, render_template, request, redirect, url_for, session, flash,make_response, jsonify
import xml.etree.ElementTree as ET
from werkzeug.security import check_password_hash
import requests

base_url = 'http://localhost:8017'
db_name = 'rush_05_12'
app = Flask(__name__)
app.secret_key = "your_secret_key"


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
        # return response.json()  # Parse and return JSON response
    except requests.exceptions.RequestException as e:
        print(f"Error during authentication: {e}")
        return redirect('login')
    # response = response.json()
    print(response.cookies.get('session_id'))
    session_id = response.cookies.get('session_id')
    if session_id:
        response = make_response(redirect('/'))
        response.set_cookie('session_id', session_id, max_age=3600)  # Set a cookie with a 1-hour expiration

        return response
    else:
        flash('Invalid username or password.', 'danger')
        return  redirect('login',)
    return None


@app.route('/',)
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
    username = request.form.get('username')
    password = request.form.get('password')
    return authenticate_odoo(username,password,base_url,db_name,)




@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/anpr/car/data',   methods=['POST', 'GET'], cors='*', csrf=False)
def anprCameraData(self):
    print("ANPR Data ================>:")
    print("ANPR Data Received:")
    try:
        # Get all files in the request
        uploaded_files = request.httprequest.files
        print("Uploaded files: %s", list(uploaded_files.keys()))

        # Check if 'anpr.xml' is among the uploaded files
        # if 'file' in uploaded_files:
        for file_name, uploaded_file in uploaded_files.items():
            if uploaded_file.filename == 'anpr.xml':
                # Process 'anpr.xml'
                file_content = uploaded_file.read().decode('utf-8')
                print("Content of anpr.xml: %s", file_content)
                root = ET.fromstring(file_content)

                # Extract key-value pairs
                key_value_data = {}
                for element in root.iter():
                    key_value_data[element.tag] = element.text.strip() if element.text else None

                print("Extracted Key-Value Data: %s", key_value_data)
                xml_content = jsonify(key_value_data)
                print(xml_content)

                # Return the extracted data as a JSON response
                return "aaaaaaaa"

    except Exception as e:
        print("Error ================>: %s" ,e)


if __name__ == '__main__':
    app.run(debug=True)
