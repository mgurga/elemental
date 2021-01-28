import unittest, subprocess, socket, os, random, json, shlex, shutil, time

unittest.TestLoader.sortTestMethodsUsing = None

class ElementalTest(unittest.TestCase):
    randchars = "abcdefghijklmnopqrstuvwxyz0123456789"
    serverprocess = None
    rawsocket = None
    serversocket = None
    randcharnames = 5
    user1 = ["user" + "".join(random.choices(randchars, k=randcharnames)), "pass" + "".join(random.choices(randchars, k=randcharnames)), "key"]
    user2 = ["user" + "".join(random.choices(randchars, k=randcharnames)), "pass" + "".join(random.choices(randchars, k=randcharnames)), "key"]

    def setUp(self):
        self.serverprocess = subprocess.Popen(shlex.split("python3 elemental.py --storagepath 'teststorage'"))
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        time.sleep(1)
        self.serversocket.connect((socket.gethostname(), 5005))

        while self.user1[0] == self.user2[0]:
            self.user2[0] = "user" + "".join(random.choices(self.randchars, k=self.randcharnames))

    def tearDown(self):
        self.serversocket.close()
        self.serverprocess.terminate()
        shutil.rmtree("teststorage")

    def test_user1_register_login(self):
        regjson = '{"call":"register", "usernm": "' + self.user1[0] + '", "passwd": "' + self.user1[1] + '"}'
        self.serversocket.send(regjson.encode("ascii"))

        regresp = self.serversocket.recv(4096)
        regrespjson = json.loads(regresp.decode("ascii"))

        self.assertTrue(regrespjson["resp"])

        time.sleep(1)

        loginjson = '{"call": "login", "usernm": "' + self.user1[0] + '", "passwd": "' + self.user1[1] + '"}'
        self.serversocket.send(loginjson.encode("ascii"))

        loginrawresp = self.serversocket.recv(4096)
        loginrespjson = json.loads(loginrawresp.decode("ascii"))

        if loginrespjson["resp"] == True and loginrespjson["key"] != "" and len(loginrespjson["key"]) > 10:
            self.user1[2] = loginrespjson["key"]
            self.assertTrue(loginrespjson["resp"])
        else:
            print("test_user1_login failed! login response: {}".format(loginrespjson))

    def test_user2_register_login(self):
        regjson = '{"call":"register", "usernm": "' + self.user2[0] + '", "passwd": "' + self.user2[1] + '"}'
        self.serversocket.send(regjson.encode("ascii"))

        regresp = self.serversocket.recv(4096)
        regrespjson = json.loads(regresp.decode("ascii"))

        self.assertTrue(regrespjson["resp"])

        time.sleep(1)

        loginjson = '{"call": "login", "usernm": "' + self.user2[0] + '", "passwd": "' + self.user2[1] + '"}'
        self.serversocket.send(loginjson.encode("ascii"))

        loginrawresp = self.serversocket.recv(4096)
        loginrespjson = json.loads(loginrawresp.decode("ascii"))

        if loginrespjson["resp"] == True and loginrespjson["key"] != "" and len(loginrespjson["key"]) > 10:
            self.user2[2] = loginrespjson["key"]
            self.assertTrue(loginrespjson["resp"])
        else:
            print("test_user2_login failed! login response: {}".format(loginrespjson))

unittest.main()