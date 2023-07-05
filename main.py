from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

rooms = {}

def genrate_code(length):
    code = ''.join(random.choice(ascii_uppercase) for i in range(length))
    if code in rooms:
        genrate_code(length)
    else:
        return code


@app.route('/', methods=['GET', 'POST'])
def home():

    session.clear()
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        join = request.form.get('join', False)
        create = request.form.get('create', False)

        if not name: 
            name = "anonymous"
        
        if join != False and not code:
            return render_template('index.html', error="Please enter a code to join a room.", code=code, name=name)
        
        room = code
        if create != False:
            room = genrate_code(4)
            rooms[room] = {"members": 0, "messages":[]}

        elif room not in rooms:
            return render_template('index.html', error="Invalid code.", code=code, name=name)

        session['name'] = name
        session['room'] = room
        return redirect(url_for('room'))

    return render_template('index.html')



@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])


@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)

    rooms[room]["messages"].append(content)

    print(f"{session.get('name')} said: {data['data']}")


@socketio.on('connect')
def on_connect():
    room = session.get('room')
    name = session.get('name')

    if not room or not name:
        return
    
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    rooms[room]["members"] += 1
    send({"name":name, "message":' has entered the room.'}, to=room)
    print(f"{name} has entered the room {room}.")
    


@socketio.on('disconnect')
def on_disconnect():
    room = session.get('room')
    name = session.get('name')
    if room in rooms:
        if rooms[room]["members"] == 0:
            del rooms[room]

    rooms[room]["members"] -= 1
    send({"name":name, "message":' has left the room.'}, to=room)
    print(f"{name} has left the room {room}.")
    leave_room(room)






if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
    print("SERVER STARTED ON PORT 5000")
