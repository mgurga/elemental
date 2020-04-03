import socket
import json
import datetime
import getpass

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

host = socket.gethostname()
port = 5005
encoding = "ascii"

regORlog = ""
usernm = ""
passwd = ""
currentserver = ""
currentchannel = ""

serversocket.connect((host, port))

while True:
	if regORlog == "":
		regORlog = input("(r)egister or (l)ogin: ")

		usernm = input("username: ")
		passwd = getpass.getpass("password: ")
	elif regORlog == "l":
		loginjson = '{"call": "login", "usernm": "' + usernm + '", "passwd": "' + passwd + '"}'
		serversocket.send(loginjson.encode(encoding))

		loginresp = serversocket.recv(4096)
		loginrespjson = json.loads(loginresp.decode(encoding))
		if loginrespjson["resp"] == True:
			print("login completed, logged in as " + usernm)
			break
		else:
			print("login failed, " + loginrespjson["reason"])
			regORlog = ""
	elif regORlog == "r":
		regjson = '{"call":"register", "usernm": "' + usernm + '", "passwd": "' + passwd + '"}'
		serversocket.send(regjson.encode(encoding))

		regresp = serversocket.recv(4096)
		regrespjson = json.loads(regresp.decode(encoding))
		if regrespjson["resp"] == True:
			print("registration completed, now login")
			regORlog = ""
		else:
			print("registration failed, " + regrespjson["reason"])
			regORlog = ""
	else:
		regORlog = ""

while True:
	usermsg = input()
	if usermsg == "/createserver":
		newservername = input("new server name: ")
		newserverpass = input("new server password: ")
		
	else:
		usermsgjson = '{"call": "message", "msg": "' + usermsg + '"}'
		serversocket.send(usermsgjson.encode(encoding))

		servresponse = serversocket.recv(4096)
		print("server responded with: " + servresponse.decode(encoding))

serversocket.close()