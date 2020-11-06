
import socket
import json
import argparse
import os
import datetime
import shutil
import base64
from threading import Thread
from elementaluser import UserClient

parser = argparse.ArgumentParser(description='give the elemental server some command line arguments')

parser.add_argument('--port', type=int, help='what port the provider should run on', default=5005)
parser.add_argument('--host', type=str, help='what host ip the provider should run on', default="")
parser.add_argument('--encoding', type=str, help='what encoding algorithm scheme to use, client must be the same', default="ascii")
parser.add_argument('--providername', type=str, help='name of the provider', default="LOCALPROVIDER")
parser.add_argument('--storagepath', type=str, help='path of the provider storage', default="providerstorage")
parser.add_argument('--jsonfileindent', type=int, help='how many indents to put in json files', default=2)
parser.add_argument('--sendotherusersdata', type=bool, help='send everyone messages (EXPERIMENTAL)', default=False)
parser.add_argument('--providernameinconsole', type=str, help='name of the provider in the console', default="[SERVER]")

args = parser.parse_args()

clients = []

class ECONFIG:
    host = args.host
    port = args.port
    encoding = args.encoding
    providername = args.providername
    providerwelcome = "welcome to your LOCALPROVIDER, the BEST test provider on localhost"
    providerstorage = args.storagepath
    providernameinconsole = args.providernameinconsole
    providericonfilename = "icon.png" # located in the base of providerstorage, must be 64x64
    jsonfileindent = args.jsonfileindent
    sendotherusersdata = args.sendotherusersdata
    providericondata = None

if not os.path.exists(ECONFIG.providerstorage):
    print("server storage folder does not exist, creating it")
    os.mkdir(ECONFIG.providerstorage)
    open(ECONFIG.providerstorage + os.sep + "config.json", "w")
    os.mkdir(ECONFIG.providerstorage + os.sep + "users")
    os.mkdir(ECONFIG.providerstorage + os.sep + "servers")
else:
    if os.path.isfile(ECONFIG.providerstorage + os.sep + ECONFIG.providericonfilename):
        # print("encoded icon.png as:")
        with open(ECONFIG.providerstorage + os.sep + ECONFIG.providericonfilename, "rb") as fp:
            b64pic = base64.b64encode(fp.read()).decode(encoding="UTF-8")
            # print(b64pic)
            print("encoded " + ECONFIG.providericonfilename + " as base64")
            ECONFIG.providericondata = b64pic

def new_client(clientsocket, addr):
    client = UserClient(clientsocket, addr, ECONFIG)
    clients.append(client)
    print("total clients: " + str(len(clients)))
    while True:
        try:
            clientmsg = clientsocket.recv(4096)
            print("(" + getTime() + ") | " + ECONFIG.providernameinconsole + " <== [" + str(addr[0]) + ":" + str(addr[1]) + "] | " + clientmsg.decode(ECONFIG.encoding))
            resp = client.rawcommand(clientmsg.decode(ECONFIG.encoding))
            print("(" + getTime() + ") | " + ECONFIG.providernameinconsole + " ==> [" + str(addr[0]) + ":" + str(addr[1]) + "] | " + resp)
            clientsocket.send(resp.encode(ECONFIG.encoding))
        except socket.error as e:
            print("(" + getTime() + ") | closing connection because of socket error, details below")
            print(e)
            break
        except:
            print("(" + getTime() + ") | closing connection because of unknown error")
    clients.remove(client)
    client.clientsocket.close()
    print("total clients: " + str(len(clients)))

def transmit(jsondata, servername, user):
    if len(clients) > 1:
            for i in range(0, len(clients)):
                if not clients[i].usernm == user.usernm:
                    if servername in clients[i].joinedservers:
                        #print("sending")
                        jsontext = json.dumps(jsondata)
                        print("(" + getTime() + ") | " + ECONFIG.providernameinconsole + " ==> [" + str(addr[0]) + ":" + str(addr[1]) + "] | " + json.dumps(jsontext))
                        clients[i].clientsocket.send(jsontext.encode(ECONFIG.encoding))

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

serversocket.bind((ECONFIG.host, ECONFIG.port))
serversocket.listen(1) 

print("running elemental server on " + str(ECONFIG.host) + ":" + str(ECONFIG.port) + " encoded with " + ECONFIG.encoding)

def getTime():
    return str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

while True:
    clientsocket, addr = serversocket.accept()
    t = Thread(target=new_client, args=(clientsocket,addr))
    t.daemon = True
    t.start()
    print("(" + getTime() + ") | connection from " + str(addr[0]) + ":" + str(addr[1]))

serversocket.close()