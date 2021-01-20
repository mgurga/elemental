import socket, json, argparse, os, datetime, shutil, base64

from auth import UserAuth

class UserClient:
    userkey = None
    joinedservers = []
    latestmessagejson = json.loads("{}")
    latestmessageserver = ""
    lastgetmessagerequest = datetime.datetime.now().timestamp()
    lastgetmessagetotalrequest = datetime.datetime.now().timestamp()

    def __init__(self, clientsocket, addr, ecfg):
        self.clientsocket = clientsocket
        self.addr = addr
        self.ECONFIG = ecfg

    def register(self, usernm, passwd):
        if os.path.exists(self.ECONFIG.providerstorage + os.sep + "users" + os.sep + usernm):
            return '{"resp": false, "reason": "user already exists"}'
        userstartjson = json.loads('{"passwd": "' + passwd + '"}')
        userstartjson["timesloggedin"] = 0
        userstartjson["joinedservers"] = []
        self.putjson(userstartjson, self.ECONFIG.providerstorage + os.sep + "users" + os.sep + usernm)
        return '{"resp": true}'

    def login(self, usernm, passwd):
        if not os.path.exists(self.ECONFIG.providerstorage + os.sep + "users" + os.sep + usernm):
            return '{"resp": false, "reason":"username does not exist"}'
        
        userfile = open(self.ECONFIG.providerstorage + os.sep + "users" + os.sep + usernm, "r")
        userfiletext = userfile.read()
        userfilejson = json.loads(userfiletext)
        userfilejson["timesloggedin"] = userfilejson["timesloggedin"] + 1
        userfile.close()
        if userfilejson["passwd"] == passwd:
            self.putjson(userfilejson, self.ECONFIG.providerstorage + os.sep + "users" + os.sep + usernm)
            userfile.close()
            self.usernm = usernm
            self.passwd = passwd
            self.joinedservers = userfilejson["joinedservers"]
            userkey = UserAuth(usernm, passwd, self.ECONFIG)
            return '{"resp": true, "key": "{}"}'.format(userkey.userkey)
        else:
            return '{"resp": false, "reason":"password is incorrect"}'
    
    def createserver(self, name, spasswd, owner):
        if os.path.exists(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + name):
            return '{"resp": false, "reason":"server already exists by that name"}'
        
        os.mkdir(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + name)
        serverjson = json.loads('{}')
        serverjson["owner"] = owner
        serverjson["passwd"] = spasswd
        serverjson["channels"] = []
        serverjson["users"] = []
        self.putjson(serverjson, self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + name + os.sep + "info")

        self.createchannel("general", name, owner)
        self.joinserver(name, spasswd, owner)

        return '{"resp": true}'

    def createchannel(self, name, servername, key):
        if os.path.exists(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + name):
            return '{"resp": false, "reason":"channel already exists"}'

        os.mkdir(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + name)
        serverinfofile = open(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info", "r")
        serverinfojson = json.load(serverinfofile)
        serverinfojson["channels"].append(name)
        serverinfofile.close()

        if not self.userkey.usernm == serverinfojson["owner"]:
            return '{"resp": false, "reason":"only owner can create channels"}'

        self.putjson(serverinfojson, self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info")

        channelmessagesjson = json.loads('{}')
        channelmessagesjson["messages"] = 0

        self.putjson(channelmessagesjson, self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + name + os.sep + "messages")

        return '{"resp": true}'

    def joinserver(self, servername, serverpasswd, recip):
        if not os.path.exists(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info"):
            return '{"resp": false, "reason":"server does not exist"}'

        serverinfo = self.openjson(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info")
        userfile = self.openjson(self.ECONFIG.providerstorage + os.sep + "users" + os.sep + recip)

        if not serverinfo["passwd"] == serverpasswd:
            return '{"resp": false, "reason":"incorrect server password"}'

        serverinfo["users"].append(recip)
        self.putjson(serverinfo, self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info")

        userfile["joinedservers"].append(servername)
        self.putjson(userfile, self.ECONFIG.providerstorage + os.sep + "users" + os.sep + recip)

        return '{"resp": true}'

    def deleteserver(self, servername, serverpasswd):
        # TODO: only owner can delete server
        if not os.path.exists(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info"):
            return '{"resp": false, "reason":"server does not exist"}'

        serverinfo = self.openjson(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info")
        serverusers = serverinfo["users"]

        for i in range(0, len(serverusers)):
            serveruserinfo = self.openjson(self.ECONFIG.providerstorage + os.sep + "users" + os.sep + serverusers[i])
            serveruserinfo["joinedservers"].remove(servername)
            self.putjson(serveruserinfo, self.ECONFIG.providerstorage + os.sep + "users" + os.sep + serverusers[i])

        shutil.rmtree(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername)
        return '{"resp": true}' 

    def leaveserver(self, servername):
        if not os.path.exists(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info"):
            return '{"resp": false, "reason":"server does not exist"}'

        userinfo = self.openjson(self.ECONFIG.providerstorage + os.sep + "users" + os.sep + self.userkey.usernm)
        serverinfo = self.openjson(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info")
        userinfo["joinedservers"].remove(servername)
        serverinfo["users"].remove(self.userkey.usernm)

        self.putjson(userinfo, self.ECONFIG.providerstorage + os.sep + "users" + os.sep + self.userkey.usernm)
        self.putjson(serverinfo, self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info")

        return '{"resp": true}'

    def message(self, msg, servername, channel):
        if not os.path.exists(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info"):
            return '{"resp": false, "reason":"server does not exist"}'

        serverinfo = self.openjson(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info")
        channelmessages = self.openjson(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + channel + os.sep + "messages")

        if not channel in serverinfo["channels"]:
            return '{"resp": false, "reason":"channel does not exist"}'

        channelmessages["messages"] = channelmessages["messages"] + 1

        self.putjson(channelmessages, self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + channel + os.sep + "messages")

        messagejson = json.loads("{}")
        messagejson["message"] = msg
        messagejson["timestamp"] = datetime.datetime.now().timestamp()
        messagejson["author"] = self.userkey.usernm

        self.putjson(messagejson, self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + channel + os.sep + str(channelmessages["messages"] - 1))

        messagejson["call"] = "newmessage"
        
        self.latestmessagejson = messagejson
        self.latestmessageserver = servername

        if self.ECONFIG.sendotherusersdata:
            self.sendotherusers(self.latestmessagejson, self.latestmessageserver)

        return '{"resp": true}'

    def getmessages(self, servername, channel, begin, end, key):
        if not os.path.exists(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info"):
            return '{"resp": false, "reason":"server does not exist"}'
        if not os.path.exists(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + channel + os.sep + "messages"):
            return '{"resp": false, "reason":"channel does not exist"}'
        if not type(begin) is int:
            return '{"resp": false, "reason":"begin is not an int"}'
        if not type(end) is int:
            return '{"resp": false, "reason":"end is not an int"}'
        if end < begin:
            return '{"resp": false, "reason":"begin is greater than end"}'
        if end < 0 or begin < 0:
            return '{"resp": false, "reason":"end or begin is less than 0"}'

        channelmessages = self.openjson(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + channel + os.sep + "messages")
        serverinfo = self.openjson(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info")

        if end > channelmessages["messages"] or begin > channelmessages["messages"]:
            return '{"resp": false, "reason":"end or begin is less than 0"}'
        if not self.userkey.usernm in serverinfo["users"]:
            return '{"resp": false, "reason":"user not in server"}'

        outjson = json.loads("{}")
        outjson["resp"] = True
        outjson["messages"] = []

        for i in range(0, end - begin):
            messagedata = self.openjson(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + channel + os.sep + str(begin + i))
            outjson["messages"].append(messagedata)

        return json.dumps(outjson)

    def gettotalmessages(self, servername, channel):
        if not os.path.exists(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername):
            return '{"resp": false, "reason":"server does not exist"}'
        if not os.path.exists(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + channel + os.sep + "messages"):
            return '{"resp": false, "reason":"channel does not exist"}'

        channelmessages = self.openjson(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + channel + os.sep + "messages")

        outjson = json.loads("{}")
        outjson["resp"] = True
        outjson["amount"] = channelmessages["messages"]

        return json.dumps(outjson)

    def getjoinedservers(self):
        userinfo = self.openjson(self.ECONFIG.providerstorage + os.sep + "users" + os.sep + self.userkey.usernm)

        outjson = json.loads("{}")
        outjson["resp"] = True
        outjson["servers"] = userinfo["joinedservers"]

        return json.dumps(outjson)

    def getserverchannels(self, key, servername):
        if not os.path.exists(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername):
            return '{"resp": false, "reason":"server does not exist"}'
        
        serverinfo = self.openjson(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info")

        if not self.userkey.usernm in serverinfo["users"]:
            return '{"resp": false, "reason":"user not in server"}'

        outjson = json.loads("{}")
        outjson["resp"] = True
        outjson["channels"] = serverinfo["channels"]

        return json.dumps(outjson)

    def deletechannel(self, name, servername, key):
        if not os.path.exists(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername):
            return '{"resp": false, "reason":"server does not exist"}'
        if not os.path.exists(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + name + os.sep + "messages"):
            return '{"resp": false, "reason":"channel does not exist"}'

        serverinfo = self.openjson(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info")

        if not self.userkey.usernm == serverinfo["owner"]:
            return '{"resp": false, "reason":"user not owner of the server"}'
        
        serverinfo["channels"].remove(name)

        self.putjson(serverinfo, self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + "info")

        shutil.rmtree(self.ECONFIG.providerstorage + os.sep + "servers" + os.sep + servername + os.sep + name)

        return '{"resp": true}'

    def getprovidername(self):
        providerinfo = json.loads("{}")
        providerinfo["resp"] = True
        providerinfo["name"] = self.ECONFIG.providername
        providerinfo["welcome"] = self.ECONFIG.providerwelcome
        if not self.ECONFIG.providericondata == None:
            providerinfo["icon"] = self.ECONFIG.providericondata

        return json.dumps(providerinfo)

    def rawcommand(self, command):
        if command == "":
            self.clientsocket.close()
            return "CLIENT UNGRACEFULLY CLOSED"
        
        commandjson = json.loads(command)
        call = commandjson["call"]

        # Sanity Checks, makes sure usernm and passwd are in the request

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
                return self.deleteserver(commandjson["servername"], commandjson["serverpasswd"])
            elif call == "leaveserver":
                return self.leaveserver(commandjson["servername"])
            elif call == "message":
                requesttimediff = datetime.datetime.now().timestamp() - self.lastgetmessagerequest
                #print(requesttimediff) #prints time difference between message requests
                self.lastgetmessagerequest = datetime.datetime.now().timestamp()
                if requesttimediff > 0:
                    return self.message(commandjson["msg"], commandjson["servername"], commandjson["channel"])
                else:
                    return '{"resp": false, "reason":"requesting too many times, only request every 0.75 seconds"}'
            elif call == "getjoinedservers":
                return self.getjoinedservers()
            elif call == "getmessages":
                return self.getmessages(commandjson["servername"], commandjson["channel"], commandjson["begin"], commandjson["end"], commandjson["usernm"])
            elif call == "gettotalmessages":
                requesttimediff = datetime.datetime.now().timestamp() - self.lastgetmessagetotalrequest
                #print(requesttimediff) #prints time difference between message total requests
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
        json.dump(jsondata, pathfile, indent=self.ECONFIG.jsonfileindent)
        pathfile.close()

    def sendotherusers(self, jsondata, servername):
        from elemental import transmit
        transmit(jsondata, servername, self)