import unittest, subprocess, socket, os, random, json, shlex, shutil, time

events = []

class ElementalTest(unittest.TestCase):
    randchars = "abcdefghijklmnopqrstuvwxyz0123456789"
    usernm = "user" + "".join(random.choices(randchars, k=5))
    passwd = "pass" + "".join(random.choices(randchars, k=5))
    serverprocess = None
    rawsocket = None
    serversocket = None

    def setUp(self):
        self.serverprocess = subprocess.Popen(shlex.split("python3 elemental.py --storagepath 'teststorage'"))
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        time.sleep(1)
        self.serversocket.connect((socket.gethostname(), 5005))

    def tearDown(self):
        self.serverprocess.kill()
        self.serversocket.close()
        shutil.rmtree("teststorage")

    def test_user_register(self):
        regjson = '{"call":"register", "usernm": "' + self.usernm + '", "passwd": "' + self.passwd + '"}'
        self.serversocket.send(regjson.encode("ascii"))

        regresp = self.serversocket.recv(4096)
        regrespjson = json.loads(regresp.decode("ascii"))

        self.assertTrue(regrespjson["resp"])

unittest.main()