
import socket
import json
import datetime
import getpass
import blessed
import time
from threading import Thread

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

host = socket.gethostname()
port = 5005
encoding = "ascii"

regORlog = ""
usernm = ""
passwd = ""
currentserver = ""
currentchannel = ""
providername = ""
providerwelcome = ""
currentchannelmsgnum = -1
totalmessagesinchannel = -1
messagestoload = 15

terminalguimode = True
awaitingmessage = False

term = blessed.Terminal()

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
		print("invalid option")
		regORlog = ""

getprovidernm = json.loads("{}")
getprovidernm["call"] = "getprovidername"
getprovidernm["usernm"] = usernm
getprovidernm["passwd"] = passwd
getprovidertext = json.dumps(getprovidernm)
serversocket.send(getprovidertext.encode(encoding))

providerrespsock = serversocket.recv(4096)
providerresp = json.loads(providerrespsock.decode(encoding))

if providerresp["resp"] == True:
	providername = providerresp["name"]
	providerwelcome = providerresp["welcome"]

keyboardbuffer = ""
messagebuffer = [providerwelcome]

def drawterminal():
	print(term.home + term.clear)

	while len(messagebuffer) > term.height - 5:
		del messagebuffer[0]

	if currentserver == "" and currentchannel == "":
		connectedtodisplay = "not connected"
	else:
		connectedtodisplay = currentserver + "/" + currentchannel
		
	print(term.move_xy(0, 0) + providername + ", " + connectedtodisplay + ", loaded messages up to: " + str(currentchannelmsgnum) + "(" + str(totalmessagesinchannel) + " latest)")
	print(term.move_xy(0, 1) + ("-" * term.width))

	for i in range(0, len(messagebuffer)):
		print(term.move_xy(0, i + 2) + messagebuffer[i])
	
	print(term.move_xy(0, term.height - 3) + ("-" * term.width))
	print(term.move_xy(0, term.height - 2) + usernm + ": " + keyboardbuffer)

drawterminal()

def updateMessages():
	while True:
		if not (currentserver == "" or currentchannel == ""):
			messagetotal = json.loads("{}")
			messagetotal["call"] = "gettotalmessages"
			messagetotal["servername"] = currentserver
			messagetotal["channel"] = currentchannel
			messagetotal["usernm"] = usernm
			messagetotal["passwd"] = passwd

			serversocket.send((json.dumps(messagetotal)).encode(encoding))
			servresponse = serversocket.recv(4096)
			servresponsejson = json.loads(servresponse.decode(encoding))

			if servresponsejson["resp"] == True:
				begin = 0
				end = 0
				global currentchannelmsgnum
				global totalmessagesinchannel

				totalmessagesinchannel = servresponsejson["amount"] 
				if currentchannelmsgnum == -1:
					if servresponsejson["amount"] < messagestoload:
						begin = 0
					else:
						begin = servresponsejson["amount"] - messagestoload
					end = servresponsejson["amount"]
				elif currentchannelmsgnum < servresponsejson["amount"]:
					begin = currentchannelmsgnum
					end = servresponsejson["amount"]

				if not (begin == 0 or end == 0):
					messagetotal = json.loads("{}")
					messagetotal["call"] = "getmessages"
					messagetotal["servername"] = currentserver
					messagetotal["channel"] = currentchannel
					messagetotal["begin"] = begin
					messagetotal["end"] = end
					messagetotal["usernm"] = usernm
					messagetotal["passwd"] = passwd

					serversocket.send((json.dumps(messagetotal)).encode(encoding))
					servresponse = serversocket.recv(4096)
					servresponsejson = json.loads(servresponse.decode(encoding))

					if servresponsejson["resp"] == True:
						messages = servresponsejson["messages"]

						for i in range(0, len(messages)):
							messagebuffer.append(messages[i]["author"] + ": " + messages[i]["message"])

						#log("messages up to date")
						currentchannelmsgnum = end

						drawterminal()
					else:
						err("unable to get messages, " + servresponsejson["reason"])

			else:
				err("unable to get total messages, " + servresponsejson["reason"])
		time.sleep(0.75)
		
def log(msg):
	if terminalguimode == True:
		messagebuffer.append(msg)
		drawterminal()
	else:
		print(msg)

def err(err):
	if terminalguimode == True:
		messagebuffer[len(messagebuffer) - 1] = messagebuffer[len(messagebuffer) - 1] + "  !!!" + err + "!!!"
		drawterminal()
	else:
		print(err)

messageupdater = Thread(target=updateMessages)
messageupdater.daemon = True
messageupdater.start()

while True:
	#usermsg = input(currentserver + "/" + currentchannel + ": ")
	usermsg = ""

	with term.cbreak():
		inputkey = term.inkey()
		if inputkey.code == 343:
			messagebuffer.append(usernm + ": " + keyboardbuffer)
			usermsg = keyboardbuffer
			keyboardbuffer = ""
			
		elif inputkey.code == 263:
			keyboardbuffer = keyboardbuffer[0:(len(keyboardbuffer) - 1)]
		else:
			keyboardbuffer += inputkey

	drawterminal()

	try:
		if usermsg == "/createserver":
			newservername = input("new server name: ")
			newserverpass = input("new server password: ")

			newserverjson = json.loads("{}")
			newserverjson["call"] = "createserver"
			newserverjson["name"] = newservername
			newserverjson["serverpasswd"] = newserverpass
			#newserverjson["owner"] = usernm
			newserverjson["usernm"] = usernm
			newserverjson["passwd"] = passwd
			serversocket.send((json.dumps(newserverjson)).encode(encoding))

			servresponse = serversocket.recv(4096)
			servresponsejson = json.loads(servresponse.decode(encoding))

			if servresponsejson.get("call") == None:
				if servresponsejson["resp"] == True:
					log("server created")
					currentserver = newservername
					currentchannel = "general"
				else:
					log("server not created, " + servresponsejson["reason"])
		
		elif usermsg == "/deleteserver":
			delservername = input("server name: ")
			delserverpasswd = input("server passwd: ")

			delserverjson = json.loads("{}")
			delserverjson["call"] = "deleteserver"
			delserverjson["servername"] = delservername
			delserverjson["serverpasswd"] = delserverpasswd
			delserverjson["usernm"] = usernm
			delserverjson["passwd"] = passwd

			serversocket.send((json.dumps(delserverjson)).encode(encoding))

			servresponse = serversocket.recv(4096)
			servresponsejson = json.loads(servresponse.decode(encoding))

			if servresponsejson.get("call") == None:
				if servresponsejson["resp"] == True:
					log("server successfully deleted")
					if currentserver == delservername:
						currentserver = ""
					currentchannel = ""
				else:
					log("server not deleted, " + servresponsejson["reason"])

		elif usermsg == "/listservers":
			log("listing servers...")

			listrequest = json.loads("{}")
			listrequest["call"] = "getjoinedservers"
			listrequest["usernm"] = usernm
			listrequest["passwd"] = passwd

			serversocket.send((json.dumps(listrequest)).encode(encoding))

			servresponse = serversocket.recv(4096)
			servresponsejson = json.loads(servresponse.decode(encoding))

			if servresponsejson.get("call") == None:
				if servresponsejson["resp"] == True:
					servers = servresponsejson["servers"]
					log(" ".join(servers))
				else:
					err("couldn't list servers, " + servresponsejson["reason"])

		elif usermsg == "/listchannels":
			log("listing channels...")
			
			if not currentserver == "":
				listrequest = json.loads("{}")
				listrequest["call"] = "getserverchannels"
				listrequest["servername"] = currentserver
				listrequest["usernm"] = usernm
				listrequest["passwd"] = passwd

				serversocket.send((json.dumps(listrequest)).encode(encoding))

				servresponse = serversocket.recv(4096)
				servresponsejson = json.loads(servresponse.decode(encoding))

				if servresponsejson.get("call") == None:
					if servresponsejson["resp"] == True:
						servers = servresponsejson["channels"]
						log(" ".join(servers))
					else:
						err("couldn't list channels, " + servresponsejson["reason"])
			else:
				err("not connected to server")

		elif usermsg == "/joinserver":
			servername = input("input server name: ")
			serverpasswd = input("input server password: ")

			joinrequest = json.loads("{}")
			joinrequest["call"] = "joinserver"
			joinrequest["servername"] = servername
			joinrequest["serverpasswd"] = serverpasswd
			joinrequest["usernm"] = usernm
			joinrequest["passwd"] = passwd

			serversocket.send((json.dumps(joinrequest)).encode(encoding))

			servresponse = serversocket.recv(4096)
			servresponsejson = json.loads(servresponse.decode(encoding))

			if servresponsejson.get("call") == None:
				if servresponsejson["resp"] == True:
					log("successfully joined server")
				else:
					err("unable to join server, " + servresponsejson["reason"])

		elif usermsg == "/gotoserver":
			gotoserver = input("target server: ")

			listrequest = json.loads("{}")
			listrequest["call"] = "getjoinedservers"
			listrequest["usernm"] = usernm
			listrequest["passwd"] = passwd

			serversocket.send((json.dumps(listrequest)).encode(encoding))

			servresponse = serversocket.recv(4096)
			servresponsejson = json.loads(servresponse.decode(encoding))

			if servresponsejson.get("call") == None:
				if servresponsejson["resp"] == True:
					if gotoserver in servresponsejson["servers"]:
						log("entered server and joined #general")
						currentserver = gotoserver
						currentchannel = "general"
						currentchannelmsgnum = -1
						messagebuffer = []
					else:
						err("not apart of target server")
				else:
					err("couldn't get list of servers, " + servresponsejson["reason"])

		elif usermsg == "/gotochannel":
			gotochannel = input("target channel: ")

			listrequest = json.loads("{}")
			listrequest["call"] = "getserverchannels"
			listrequest["servername"] = currentserver
			listrequest["usernm"] = usernm
			listrequest["passwd"] = passwd

			serversocket.send((json.dumps(listrequest)).encode(encoding))

			servresponse = serversocket.recv(4096)
			servresponsejson = json.loads(servresponse.decode(encoding))

			if servresponsejson.get("call") == None:
				if servresponsejson["resp"] == True:
					if gotochannel in servresponsejson["channels"]:
						log("connected to #" + gotochannel)
						currentchannel = gotochannel
						currentchannelmsgnum = -1
						messagebuffer = []
						drawterminal()
					else:
						err("not apart of target server")
				else:
					err("couldn't get list of servers, " + servresponsejson["reason"])

		elif usermsg == "/createchannel":
			newchannelname = input("new channel name: ")

			newchannelrequest = json.loads("{}")
			newchannelrequest["call"] = "createchannel"
			newchannelrequest["name"] = newchannelname
			newchannelrequest["servername"] = currentserver
			newchannelrequest["usernm"] = usernm
			newchannelrequest["passwd"] = passwd

			serversocket.send((json.dumps(newchannelrequest)).encode(encoding))

			servresponse = serversocket.recv(4096)
			servresponsejson = json.loads(servresponse.decode(encoding))

			if servresponsejson["resp"] == True:
				log("channel has been created")
			else:
				err("couldn't create channel, " + servresponsejson["reason"])

		elif usermsg == "/deletechannel":
			todeletechannel = input("what channel do you want to delete: ")

			delchannelrequest = json.loads("{}")
			delchannelrequest["call"] = "deletechannel"
			delchannelrequest["name"] = todeletechannel
			delchannelrequest["servername"] = currentserver
			delchannelrequest["usernm"] = usernm
			delchannelrequest["passwd"] = passwd

			serversocket.send((json.dumps(delchannelrequest)).encode(encoding))

			servresponse = serversocket.recv(4096)
			servresponsejson = json.loads(servresponse.decode(encoding))

			if servresponsejson["resp"] == True:
				log("channel has been deleted")
				if currentchannel == todeletechannel:
					currentchannel = ""
			else:
				err("couldn't create channel, " + servresponsejson["reason"])

		elif len(usermsg) > 0 and usermsg[0] == "/":
			log("command not recognized")

		elif usermsg != "":
			usermsgjson = json.loads("{}")
			usermsgjson["call"] = "message"
			usermsgjson["msg"] = usermsg
			usermsgjson["servername"] = currentserver
			usermsgjson["channel"] = currentchannel
			usermsgjson["usernm"] = usernm
			usermsgjson["passwd"] = passwd

			serversocket.send((json.dumps(usermsgjson)).encode(encoding))

			servresponse = serversocket.recv(4096)
			servresponsejson = json.loads(servresponse.decode(encoding))

			if servresponsejson.get("call") == None:
				if not servresponsejson["resp"] == True:
					err(servresponsejson["reason"])
				else:
					currentchannelmsgnum = currentchannelmsgnum + 1
					totalmessagesinchannel = totalmessagesinchannel + 1
					drawterminal()
	
	except KeyError as e:
		print("error")
		print(e.with_traceback())


serversocket.close()