
import socket
import json
import argparse
import os
import datetime
from threading import Thread

parser = argparse.ArgumentParser(description='give the elemental server some command line arguments')

parser.add_argument('--port', type=int, help='what port the server should run on', default=5005)
parser.add_argument('--host', type=str, help='what host ip the server should run on', default="")
parser.add_argument('--encoding', type=str, help='what encoding algorithm scheme to use, client must be the same', default="ascii")

args = parser.parse_args()

host = args.host
port = args.port
encoding = args.encoding
serverStorage = "serverstorage"
serverName = "[SERVER]"

if not os.path.exists(serverStorage):
	os.mkdir(serverStorage)
	open(serverStorage + os.sep + "config.json")
	os.mkdir(serverStorage + os.sep + "users")
	os.mkdir(serverStorage + os.sep + "servers")
	os.mkdir(serverStorage + os.sep + "channels")

def new_client(clientsocket,addr):
	client = UserClient(clientsocket, addr)
	while True:
		try:
			clientmsg = clientsocket.recv(4096)
			print("(" + getTime() + ") | " + serverName + " <== [" + str(addr[0]) + ":" + str(addr[1]) + "] | " + clientmsg.decode(encoding))
			resp = client.rawcommand(clientmsg.decode(encoding))
			print("(" + getTime() + ") | " + serverName + " ==> [" + str(addr[0]) + ":" + str(addr[1]) + "] | " + resp)
			clientsocket.send(resp.encode(encoding))
		except socket.error:
			print("(" + getTime() + ") | closing connection because of error")
			break
	client.clientsocket.close()

class UserClient:
	def __init__(self, clientsocket, addr):
		self.clientsocket = clientsocket
		self.addr = addr

	def register(self, usernm, passwd):
		if os.path.exists(serverStorage + os.sep + "users" + os.sep + usernm):
			return '{"resp": false, "reason": "user is already defined"}'
		userfile = open(serverStorage + os.sep + "users" + os.sep + usernm, "w")
		userstartjson = json.loads('{"passwd": "' + passwd + '"}')
		userstartjson["timesloggedin"] = 0
		userstartjson["joinedservers"] = []
		json.dump(userstartjson, userfile, indent=2)
		userfile.close()
		return '{"resp": true}'

	def login(self, usernm, passwd):
		if not os.path.exists(serverStorage + os.sep + "users" + os.sep + usernm):
			return '{"resp": false, "reason":"username does not exist"}'
		else:
			userfile = open(serverStorage + os.sep + "users" + os.sep + usernm, "r")
			userfiletext = userfile.read()
			userfilejson = json.loads(userfiletext)
			userfilejson["timesloggedin"] = userfilejson["timesloggedin"] + 1
			userfile.close()
			if userfilejson["passwd"] == passwd:
				userfile = open(serverStorage + os.sep + "users" + os.sep + usernm, "w")
				json.dump(userfilejson, userfile, indent=2)
				userfile.close()
				return '{"resp": true}'
			else:
				return '{"resp": false, "reason":"password is incorrect"}'
	
	def rawcommand(self, command):
		if command == "":
			self.clientsocket.close()
			return "CLIENT UNGRACEFULLY CLOSED"
		commandjson = json.loads(command)
		call = commandjson["call"]
		if call == "login":
			return self.login(commandjson["usernm"], commandjson["passwd"])
		elif call == "register":
			return self.register(commandjson["usernm"], commandjson["passwd"])
		else:
			out = self.msg(command)
			#print(out)
			return out

	def msg(self, msg):
		return str(msg)

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

serversocket.bind((host, port))
serversocket.listen(1) 

print("running elemental server on " + str(host) + ":" + str(port) + " encoded with " + encoding)

def getTime():
	return str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

while True:
	clientsocket, addr = serversocket.accept()
	t = Thread(target=new_client, args=(clientsocket,addr))
	t.daemon = True
	t.start()
	print("(" + getTime() + ") | connection from " + str(addr[0]) + ":" + str(addr[1]))

serversocket.close()