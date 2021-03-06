from flask import Flask, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
from classifier import NNClassifier

app = Flask(__name__)
socketio = SocketIO(app)
kcls = NNClassifier()

device_list = [2, 3]
device_history = {}
device_last_pose = {}
app_list = []

@app.route('/')
def index():
	return jsonify(devices=device_list)


@socketio.on('login')
def on_login(app_id):
	join_room(app_id)
	app_list.append(app_id)
	print("%s logged in." % app_id)
	emit("login", {'devices': device_list})


@socketio.on('logout')
def on_logout(app_id):
	leave_room(app_id)
	app_list.remove(app_id)
	print("%s logged out." % app_id)


@socketio.on('subscribe')
def on_subscribe(device_id):
	join_room(device_id)


@socketio.on('unsubscribe')
def on_unsubscribe(device_id):
	leave_room(device_id)


@socketio.on('register')
def on_register(device_id):
	device_list.append(device_id)
	# deque(iterable, maxlen)
	device_history[device_id] = deque([3] * 25, 25)
	device_last_pose[device_id] = 3
	print(device_list)


@socketio.on('deregister')
def on_deregister(device_id):
	device_list.remove(device_id)
	device_history.pop(device_id, None)
	print(device_list)


@socketio.on('emg')
def on_emg(data):
	device_id = data.get('device_id')
	emg_data = data.get('emg')
	device_history.get(device_id).append(kcls.classify(emg_data))
	# most_common(k) return k most common elements in list
	# return (elements, count)
	r, n = Counter(device_history.get(device_id)).most_common(1)[0]
	if n > 12 and r != device_last_pose.get(device_id):
		send_alert({'status': r==1, 'device_id':device_id})
	device_last_pose[device_id] = r
	print("receive %s from device %s" % (emg_data, device_id))
	emit("emg", emg_data, room=device_id)


@socketio.on('message')
def handle_message(message):
    print('received message: %s' % message)

@socketio.on('alert')
def send_alert(alert_info):
    print('-----------device: %d alerted--------------' % (alert_info.get('status')))
    print(app_list)
    for app_id in app_list:
        emit("alert", alert_info, room=app_id)

if __name__ == '__main__':
    socketio.run(app)
