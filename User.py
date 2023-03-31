import json
from json import JSONEncoder

class MyEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__
    
class User(object):
    def __init__(self, id, username, rol):
        self.id = id
        self.username = username
        self.rol = rol

    def __str__(self):
        return "User(id='%s')" % self.id

    def toJSON(self):
        return json.dumps(self.__dict__)
class FullTemplate(object):
    def __init__(self, template,params):
        self.template = template
        self.params = params
        

    def __str__(self):
        return "User(id='%s')" % self.id

    def toJSON(self):
        return json.dumps(self.__dict__)
        