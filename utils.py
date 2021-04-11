import json


class Utils:
    def __init__(self, ecfg):
        self.ECONFIG = ecfg

    def openjson(self, path):
        pathfile = open(path, "r")
        filejson = json.load(pathfile)
        pathfile.close()
        return filejson

    def putjson(self, jsondata, path):
        pathfile = open(path, "w")
        json.dump(jsondata, pathfile, indent=self.ECONFIG.jsonfileindent)
        pathfile.close()
