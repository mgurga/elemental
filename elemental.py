
import socket
import json
import argparse
import os
import datetime
import shutil
from threading import Thread

parser = argparse.ArgumentParser(description='give the elemental server some command line arguments')

parser.add_argument('--port', type=int, help='what port the provider should run on', default=5005)
parser.add_argument('--host', type=str, help='what host ip the provider should run on', default="")
parser.add_argument('--encoding', type=str, help='what encoding algorithm scheme to use, client must be the same', default="ascii")
parser.add_argument('--providername', type=str, help='name of the provider', default="LOCALPROVIDER")
parser.add_argument('--storagepath', type=str, help='name of the provider', default="serverstorage")
parser.add_argument('--jsonfileindent', type=int, help='name of the provider', default=2)
parser.add_argument('--sendotherusersdata', type=bool, help='name of the provider', default=False)
parser.add_argument('--providerNameInConsole', type=str, help='name of the provider', default="[SERVER]")

args = parser.parse_args()

host = args.host
port = args.port
encoding = args.encoding
providername = args.providername
providerwelcome = "welcome to your LOCALPROVIDER, the BEST test provider on localhost"
serverStorage = args.storagepath
providerNameInConsole = args.providerNameInConsole
jsonfileindent = args.jsonfileindent
sendotherusersdata = args.sendotherusersdata

clients = []

if not os.path.exists(serverStorage):
	os.mkdir(serverStorage)
	open(serverStorage + os.sep + "config.json", "w")
	os.mkdir(serverStorage + os.sep + "users")
	os.mkdir(serverStorage + os.sep + "servers")
	print("server storage folder does not exist, creating it")

def new_client(clientsocket,addr):
	client = UserClient(clientsocket, addr)
	clients.append(client)
	print("total clients: " + str(len(clients)))
	while True:
		try:
			clientmsg = clientsocket.recv(4096)
			print("(" + getTime() + ") | " + providerNameInConsole + " <== [" + str(addr[0]) + ":" + str(addr[1]) + "] | " + clientmsg.decode(encoding))
			resp = client.rawcommand(clientmsg.decode(encoding))
			print("(" + getTime() + ") | " + providerNameInConsole + " ==> [" + str(addr[0]) + ":" + str(addr[1]) + "] | " + resp)
			clientsocket.send(resp.encode(encoding))
		except socket.error as e:
			print("(" + getTime() + ") | closing connection because of socket error, details below")
			print(e)
			break
	clients.remove(client)
	client.clientsocket.close()
	print("total clients: " + str(len(clients)))

class UserClient:

	usernm = ""
	passwd = ""
	joinedservers = []
	latestmessagejson = json.loads("{}")
	latestmessageserver = ""
	lastgetmessagerequest = datetime.datetime.now().timestamp()
	lastgetmessagetotalrequest = datetime.datetime.now().timestamp()

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
			self.usernm = usernm
			self.passwd = passwd
			self.joinedservers = userfilejson["joinedservers"]
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

		channelmessagesjson = json.loads('{}')
		channelmessagesjson["messages"] = 0

		self.putjson(channelmessagesjson, serverStorage + os.sep + "servers" + os.sep + servername + os.sep + name + os.sep + "messages")

		return '{"resp": true}'

	def joinserver(self, servername, serverpasswd, usernm):
		if not os.path.exists(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info"):
			return '{"resp": false, "reason":"server does not exist"}'

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
		if not os.path.exists(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info"):
			return '{"resp": false, "reason":"server does not exist"}'

		serverinfo = self.openjson(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info")
		serverusers = serverinfo["users"]

		for i in range(0, len(serverusers)):
			serveruserinfo = self.openjson(serverStorage + os.sep + "users" + os.sep + serverusers[i])
			serveruserinfo["joinedservers"].remove(servername)
			self.putjson(serveruserinfo, serverStorage + os.sep + "users" + os.sep + serverusers[i])

		shutil.rmtree(serverStorage + os.sep + "servers" + os.sep + servername)
		return '{"resp": true}' 

	def leaveserver(self, servername, usernm, passwd):
		if not os.path.exists(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info"):
			return '{"resp": false, "reason":"server does not exist"}'

		userinfo = self.openjson(serverStorage + os.sep + "users" + os.sep + usernm)
		serverinfo = self.openjson(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info")
		userinfo["joinedservers"].remove(servername)
		serverinfo["users"].remove(usernm)

		self.putjson(userinfo, serverStorage + os.sep + "users" + os.sep + usernm)
		self.putjson(serverinfo, serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info")

		return '{"resp": true}'

	def message(self, msg, servername, channel, usernm, passwd):
		if not os.path.exists(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info"):
			return '{"resp": false, "reason":"server does not exist"}'

		serverinfo = self.openjson(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info")
		channelmessages = self.openjson(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + channel + os.sep + "messages")

		if not channel in serverinfo["channels"]:
			return '{"resp": false, "reason":"channel does not exist"}'

		channelmessages["messages"] = channelmessages["messages"] + 1

		self.putjson(channelmessages, serverStorage + os.sep + "servers" + os.sep + servername + os.sep + channel + os.sep + "messages")

		messagejson = json.loads("{}")
		messagejson["message"] = msg
		messagejson["timestamp"] = datetime.datetime.now().timestamp()
		messagejson["author"] = usernm

		self.putjson(messagejson, serverStorage + os.sep + "servers" + os.sep + servername + os.sep + channel + os.sep + str(channelmessages["messages"] - 1))

		messagejson["call"] = "newmessage"
		
		self.latestmessagejson = messagejson
		self.latestmessageserver = servername

		if sendotherusersdata:
			self.sendotherusers(self.latestmessagejson, self.latestmessageserver)

		return '{"resp": true}'

	def getmessages(self, servername, channel, begin, end, usernm):
		if not os.path.exists(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info"):
			return '{"resp": false, "reason":"server does not exist"}'
		if not os.path.exists(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + channel + os.sep + "messages"):
			return '{"resp": false, "reason":"channel does not exist"}'
		if not type(begin) is int:
			return '{"resp": false, "reason":"begin is not an int"}'
		if not type(end) is int:
			return '{"resp": false, "reason":"end is not an int"}'
		if end < begin:
			return '{"resp": false, "reason":"begin is greater than end"}'
		if end < 0 or begin < 0:
			return '{"resp": false, "reason":"end or begin is less than 0"}'

		channelmessages = self.openjson(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + channel + os.sep + "messages")
		serverinfo = self.openjson(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info")

		if end > channelmessages["messages"] or begin > channelmessages["messages"]:
			return '{"resp": false, "reason":"end or begin is less than 0"}'
		if not usernm in serverinfo["users"]:
			return '{"resp": false, "reason":"user not in server"}'

		outjson = json.loads("{}")
		outjson["resp"] = True
		outjson["messages"] = []

		for i in range(0, end - begin):
			messagedata = self.openjson(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + channel + os.sep + str(begin + i))
			outjson["messages"].append(messagedata)

		return json.dumps(outjson)

	def gettotalmessages(self, servername, channel):
		if not os.path.exists(serverStorage + os.sep + "servers" + os.sep + servername):
			return '{"resp": false, "reason":"server does not exist"}'
		if not os.path.exists(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + channel + os.sep + "messages"):
			return '{"resp": false, "reason":"channel does not exist"}'

		channelmessages = self.openjson(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + channel + os.sep + "messages")

		outjson = json.loads("{}")
		outjson["resp"] = True
		outjson["amount"] = channelmessages["messages"]

		return json.dumps(outjson)

	def getjoinedservers(self, usernm, passwd):
		userinfo = self.openjson(serverStorage + os.sep + "users" + os.sep + usernm)

		if not userinfo["passwd"] == passwd:
			return '{"resp": false, "reason":"user password is incorrect"}'

		outjson = json.loads("{}")
		outjson["resp"] = True
		outjson["servers"] = userinfo["joinedservers"]

		return json.dumps(outjson)

	def getserverchannels(self, usernm, servername):
		if not os.path.exists(serverStorage + os.sep + "servers" + os.sep + servername):
			return '{"resp": false, "reason":"server does not exist"}'
		
		serverinfo = self.openjson(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info")

		if not usernm in serverinfo["users"]:
			return '{"resp": false, "reason":"user not in server"}'

		outjson = json.loads("{}")
		outjson["resp"] = True
		outjson["channels"] = serverinfo["channels"]

		return json.dumps(outjson)

	def deletechannel(self, name, servername, usernm):
		if not os.path.exists(serverStorage + os.sep + "servers" + os.sep + servername):
			return '{"resp": false, "reason":"server does not exist"}'
		if not os.path.exists(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + name + os.sep + "messages"):
			return '{"resp": false, "reason":"channel does not exist"}'

		serverinfo = self.openjson(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info")

		if not usernm == serverinfo["owner"]:
			return '{"resp": false, "reason":"user not owner of the server"}'
		
		serverinfo["channels"].remove(name)

		self.putjson(serverinfo, serverStorage + os.sep + "servers" + os.sep + servername + os.sep + "info")

		shutil.rmtree(serverStorage + os.sep + "servers" + os.sep + servername + os.sep + name)

		return '{"resp": true}'

	def getprovidername(self):
		providerinfo = json.loads("{}")
		providerinfo["resp"] = True
		providerinfo["name"] = providername
		providerinfo["welcome"] = providerwelcome

		return json.dumps(providerinfo)

	def rawcommand(self, command):
		if command == "":
			self.clientsocket.close()
			return "CLIENT UNGRACEFULLY CLOSED"
		
		commandjson = json.loads(command)
		call = commandjson["call"]

		# Sanity Checks, makes sure usernm and passwd are in the request
		if not (call == "login" or call == "register"):
			if commandjson.get("usernm") == None:
				return '{"resp": false, "reason":"usernm not in request"}'
			if commandjson.get("passwd") == None:
				return '{"resp": false, "reason":"passwd not in request"}'

			commandjson["usernm"] = ''.join(commandjson["usernm"].split())
			commandjson["passwd"] = ''.join(commandjson["passwd"].split())

			if not os.path.exists(serverStorage + os.sep + "users" + os.sep + commandjson["usernm"]):
				return '{"resp": false, "reason":"user does not exist"}'
			userinfocheck = self.openjson(serverStorage + os.sep + "users" + os.sep + commandjson["usernm"])
			if not userinfocheck["passwd"] == commandjson["passwd"]:
				return '{"resp": false, "reason":"user password is incorrect"}'

		try:
			if call == "login":
				return self.login(commandjson["usernm"], commandjson["passwd"])
			elif call == "register":
				return self.register(commandjson["usernm"], commandjson["passwd"])
			elif call == "createserver":
				return self.createserver(commandjson["servername"], commandjson["serverpasswd"], commandjson["usernm"])
			elif call == "joinserver":
				return self.joinserver(commandjson["servername"], commandjson["serverpasswd"], commandjson["usernm"])
			elif call == "createchannel":
				return self.createchannel(commandjson["name"], commandjson["servername"], commandjson["usernm"])
			elif call == "deleteserver":
				return self.deleteserver(commandjson["servername"], commandjson["serverpasswd"], commandjson["usernm"], commandjson["passwd"])
			elif call == "leaveserver":
				return self.leaveserver(commandjson["servername"], commandjson["usernm"], commandjson["passwd"])
			elif call == "message":
				requesttimediff = datetime.datetime.now().timestamp() - self.lastgetmessagerequest
				#print(requesttimediff)
				self.lastgetmessagerequest = datetime.datetime.now().timestamp()
				if requesttimediff > 0:
					return self.message(commandjson["msg"], commandjson["servername"], commandjson["channel"], commandjson["usernm"], commandjson["passwd"])
				else:
					return '{"resp": false, "reason":"requesting too many times, only request every 0.75 seconds"}'
			elif call == "getjoinedservers":
				return self.getjoinedservers(commandjson["usernm"], commandjson["passwd"])
			elif call == "getmessages":
				return self.getmessages(commandjson["servername"], commandjson["channel"], commandjson["begin"], commandjson["end"], commandjson["usernm"])
			elif call == "gettotalmessages":
				requesttimediff = datetime.datetime.now().timestamp() - self.lastgetmessagetotalrequest
				#print(requesttimediff)
				self.lastgetmessagetotalrequest = datetime.datetime.now().timestamp()
				if requesttimediff > 0.75:
					return self.gettotalmessages(commandjson["servername"], commandjson["channel"])
				else:
					return '{"resp": false, "reason":"requesting too many times, only request every 0.75 seconds"}'
			elif call == "getprovidername":
				return self.getprovidername()
			elif call == "getserverchannels":
				return self.getserverchannels(commandjson["usernm"], commandjson["servername"])
			elif call == "deletechannel":
				return self.deletechannel(commandjson["name"], commandjson["servername"], commandjson["usernm"])
			else:
				out = self.msg(command)
				print("UNKNOWN CALL:")
				print(json.dumps(commandjson))
				return out
		except KeyError:
			return '{"resp": false, "reason":"incorrect request values"}'

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

	def sendotherusers(self, jsondata, servername):
		if len(clients) > 1:
			for i in range(0, len(clients)):
				if not clients[i].usernm == self.usernm:
					if servername in clients[i].joinedservers:
						#print("sending")
						jsontext = json.dumps(jsondata)
						print("(" + getTime() + ") | " + providerNameInConsole + " ==> [" + str(addr[0]) + ":" + str(addr[1]) + "] | " + json.dumps(jsontext))
						clients[i].clientsocket.send(jsontext.encode(encoding))

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