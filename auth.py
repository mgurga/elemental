import datetime
import random
import os
import json

from dataclasses import dataclass


@dataclass
class UserKey:
    key: str
    creationDate: float
    usernm: str
    passwd: str


validkeychars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,?%&*$#@/;:[]-+!()"
keylifetime = 3600  # in seconds


class UserAuth:
    userkey = None

    def __init__(self, usernm, passwd, ecfg):
        key = ''.join(random.choices(validkeychars, k=25))

        self.ECONFIG = ecfg
        self.userkey = UserKey(key, datetime.datetime.now(), usernm, passwd)

    def refreshkey(self):
        # check if key is older than 1 hour old
        date = datetime.datetime.now() - datetime.datetime.fromtimestamp(self.userkey.creationDate)
        print(date.seconds)
        if date.seconds > keylifetime:
            return (False, "key too old")

        # check if username is still valid
        if not os.path.exists(self.ECONFIG.providerstorage + os.sep + "users" + os.sep + self.userkey.usernm):
            return (False, "username does not exist")

        # check if username-password combination is still valid
        userfile = open(self.ECONFIG.providerstorage + os.sep +
                        "users" + os.sep + self.userkey.usernm, "r")
        userfiletext = userfile.read()
        userfilejson = json.loads(userfiletext)
        # userfilejson["timesloggedin"] = userfilejson["timesloggedin"] + 1
        userfile.close()

        if not userfilejson["passwd"] == self.userkey.passwd:
            return (False, "password is incorrect")

        self.utils.putjson(userfilejson, self.ECONFIG.providerstorage +
                           os.sep + "users" + os.sep + self.userkey.usernm)
        userfile.close()
        self.joinedservers = userfilejson["joinedservers"]
        self.userkey.creationDate = datetime.datetime.now().timestamp
        return (True)

    def putjson(self, jsondata, path):
        pathfile = open(path, "w")
        json.dump(jsondata, pathfile, indent=self.ECONFIG.jsonfileindent)
        pathfile.close()
