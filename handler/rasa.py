import requests
import json



class Rasa:
    def __init__(self):
        self.url = 'http://localhost:5005/model/parse'

    # Makes a request to local Rasa instance
    # message: string of text
    # returns jsonified string of rasa's response
    def Classify(self, message):
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({'text': message})
        r = requests.post(url=self.url, data=data, headers=headers)
        return json.loads(r.content.decode('utf8'))
    

    # data: what rasa returns
    # returns bool, whether the most likely intent is a travel intent
    @staticmethod
    def IsTravelIntent(data):
        return data["intent"]["name"] == "travel"