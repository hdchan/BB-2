from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask_bootstrap import Bootstrap
import requests
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
bootstrap = Bootstrap(app)

socketio = SocketIO(app, ping_interval=60, ping_timeout=120)

# Dictionary to store users and their assigned rooms
satellites = {}
base_sid = []

SATELLITES_ROOM_KEY = "satellites"
BASE_ROOM_KEY = "base"
@app.route('/')
def index():
    return render_template('child.html')

@app.route('/search')
def get_external_data():
    try:        
        return render_template('child.html')
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# Handle new user joining
@socketio.on('join')
def handle_join():
    username = f'satellite-{request.sid}'
    satellites[request.sid] = f'satellite-{request.sid}'  # Store username by session ID
    join_room(SATELLITES_ROOM_KEY)
    # join_room(request.sid)
    emit("join-satellite", request.sid, room=BASE_ROOM_KEY)
    # emit("message", f"{username} joined the chat", broadcast=True)

@socketio.on('join-base')
def handle_join():
    username = f'base-{request.sid}'
    satellites[request.sid] = f'base-{request.sid}' # Store username by session ID
    base_sid.append(request.sid)
    join_room(BASE_ROOM_KEY)
    emit("message", f"{username} joined the chat", broadcast=True)

@socketio.on('send-satellite')
def handle_send_state(data):
    # print(data)
    emit("message", data.get('data'), broadcast=data.get('satellite'))

# Handle user messages
@socketio.on('search')
def handle_message(data):
    api_url = f"https://api.swu-db.com/cards/search?q=name:{data}"  # Example API

    # Make a GET request to the external API
    response = requests.get(api_url)

    # Raise an exception for bad status codes (4xx or 5xx)
    response.raise_for_status()

    # Parse the JSON response
    data = response.json()['data']

    emit("search-result", data, room=request.sid)

# Handle user messages
@socketio.on('add-card')
def handle_message(data):
    print(data)

# Handle user messages
@socketio.on('message')
def handle_message(data):
    username = satellites.get(request.sid, "Anonymous")  # Get the user's name
    if request.sid in base_sid:
        emit("message", f"{username}: {data}", room=SATELLITES_ROOM_KEY)  # Send to everyone
    else:
        emit("message", f"{username}: {data}", room=BASE_ROOM_KEY)

# Handle disconnects
@socketio.on('disconnect')
def handle_disconnect():
    username = satellites.pop(request.sid, "Anonymous")
    # if request.sid in base_sid:
    #     base_sid.remove(request.sid)
    # emit("message", f"{username} left the chat", broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True)