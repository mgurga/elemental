
import socket
import json
import argparse
import os
import datetime
import shutil
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
jsonfileindent = 2

if not os.path.exists(serverStorage):
	os.mkdir(serverStorage)
	open(serverStorage + os.sep + "config.json", "w")
	os.mkdir(serverStorage + os.sep + "users")
	os.mkdir(serverStorage + os.sep + "servers")
	print("server storage folder does not exist, creating it")

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
		userstartjson = json.loads('{"passwd": "' + passwd + '"}')
		userstartjson["timesloggedin"] = 0
		userstartjson["joinedservers"] = []
		self.putjson(userstartjson, serverStorage + os.sep + "users" + os.sep + usernm)
		return '{"resp": true}'

	def login(self, usernm, passwd):
		if not os.path.exists(serverStorage + os.sep + "users" + os.sep + usernm):
			return '{"resp": false, "reason":"username does not exist"}'
		
		userfile = open(serverStorage + os.sep + "users" + os.sep + usernm, "r")
		userfiletext = userfile.read()
		userfilejson = json.loads(userfiletext)
		userfilejson["timesloggedin"] = userfilejson["timesloggedin"] + 1
		userfile.close()
		if userfilejson["passwd"] == passwd:
			self.putjson(userfilejson, serverStorage + os.sep + "users" + os.sep + usernm)
			userfile.close()
			return '{"resp": true}'
		else:
			return '{"resp": false, "reason":"password is incorrect"}'
	
	def createserver(self, name, passwd, owner):
		if os.path.exists(serverStorage + os.sep + "servers" + os.sep + name):
			return '{"resp": false, "reason":"server already exists by that name"}'
		
		os.mkdir(serverStorage + os.sep + "servers" + os.sep + name)
		serverjson = json.loads('{}')
		serverjson["owner"] = owner
		serverjson["passwd"] = passwd
		serverjson["channels"] = []
		serverjson["users"] = []
		self.putjson(serverjson, serverStorage + os.sep + "servers" + os.sep + name + os.sep + "info")

		self.createchannel("general", name, owner)
		self.joinserver(name, passwd, owner)

		return '{"resp": true}'

	def createchannel(self, name, servername, usernm):
		if os.path.exists(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + name):
			return '{"resp": false, "reason":"channel already exists"}'

		os.mkdir(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + name)
		serverinfofile = open(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info", "r")
		serverinfojson = json.load(serverinfofile)
		serverinfojson["channels"].append(name)
		serverinfofile.close()

		if not usernm == serverinfojson["owner"]:
			return '{"resp": false, "reason":"only owner can create channels"}'

		self.putjson(serverinfojson, serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info")

		return '{"resp": true}'

	def joinserver(self, servername, serverpasswd, usernm):
		if not os.path.exists(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info"):
			return '{"resp": false, "reason":"server does not exist"}'

		if not os.path.exists(serverStorage + os.sep + "users" + os.sep + usernm):
			return '{"resp": false, "reason":"user does not exist"}'

		serverinfo = self.openjson(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info")
		userfile = self.openjson(serverStorage + os.sep + "users" + os.sep + usernm)

		if not serverinfo["passwd"] == serverpasswd:
			return '{"resp": false, "reason":"incorrect server password"}'

		serverinfo["users"].append(usernm)
		self.putjson(serverinfo, serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info")

		userfile["joinedservers"].append(servername)
		self.putjson(userfile, serverStorage + os.sep + "users" + os.sep + usernm)

		return '{"resp": true}'

	def deleteserver(self, servername, serverpasswd, usernm, passwd):
		if not os.path.exists(serverStorage + os.sep + "servers" + os.sep + servername):
			return '{"resp": false, "reason":"server does not exist"}'

		if not os.path.exists(serverStorage + os.sep + "users" + os.sep + usernm):
			return '{"resp": false, "reason":"user does not exist"}'

		serverinfo = self.openjson(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info")
		userinfo = self.openjson(serverStorage + os.sep + "users" + os.sep + usernm)

		if not userinfo["passwd"] == passwd:
			return '{"resp": false, "reason":"user password is incorrect"}'

		serverusers = serverinfo["users"]

		for i in range(0, len(serverusers)):
			serveruserinfo = self.openjson(serverStorage + os.sep + "users" + os.sep + serverusers[i])
			serveruserinfo["joinedservers"].remove(servername)
			self.putjson(serveruserinfo, serverStorage + os.sep + "users" + os.sep + serverusers[i])

		shutil.rmtree(serverStorage + os.sep + "servers" + os.sep + servername)
		return '{"resp": true}' 

	def leaveserver(self, servername, usernm, passwd):
		if not os.path.exists(serverStorage + os.sep + "users" + os.sep + usernm):
			return '{"resp": false, "reason":"user does not exist"}'
		
		if not os.path.exists(serverStorage + os.sep + "servers" + os.sep + servername):
			return '{"resp": false, "reason":"server does not exist"}'

		userinfo = self.openjson(serverStorage + os.sep + "users" + os.sep + usernm)
		serverinfo = self.openjson(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info")

		if not userinfo["passwd"] == passwd:
			return '{"resp": false, "reason":"user password is incorrect"}'

		userinfo["joinedservers"].remove(servername)
		serverinfo["users"].remove(usernm)

		self.putjson(userinfo, serverStorage + os.sep + "users" + os.sep + usernm)
		self.putjson(serverinfo, serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info")

		return '{"resp": true}'

	def message(self, msg, servername, channel, usernm, passwd):
		return '{"resp": true}'

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
		elif call == "createserver":
			return self.createserver(commandjson["name"], commandjson["passwd"], commandjson["owner"])
		elif call == "joinserver":
			return self.joinserver(commandjson["servername"], commandjson["serverpasswd"], commandjson["usernm"])
		elif call == "createchannel":
			return self.createchannel(commandjson["name"], commandjson["servername"], commandjson["usernm"])
		elif call == "deleteserver":
			return self.deleteserver(commandjson["servername"], commandjson["serverpasswd"], commandjson["usernm"], commandjson["passwd"])
		elif call == "leaveserver":
			return self.leaveserver(commandjson["servername"], commandjson["usernm"], commandjson["passwd"])
		elif call == "message":
			return self.message(commandjson["msg"], commandjson["servername"], commandjson["channel"], commandjson["usernm"], commandjson["passwd"])
		else:
			out = self.msg(command)
			#print(out)
			return out

	def msg(self, msg):
		return str(msg)

	def openjson(self, path):
		pathfile = open(path, "r")
		filejson = json.load(pathfile)
		pathfile.close()
		return filejson

	def putjson(self, jsondata, path):
		pathfile = open(path, "w")
		json.dump(jsondata, pathfile, indent=jsonfileindent)
		pathfile.close()

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