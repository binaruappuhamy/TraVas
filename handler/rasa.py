import requests
import json
import logging

logger = logging.getLogger('RASA_API')
logger.setLevel(logging.DEBUG)


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

    #return dictionary, of travel entities
    @staticmethod
    def get_entities(data):
        entity_dict = dict()

        try:
            entity_list = data["entities"]

            for entity in entity_list:
                if entity["entity"] == "location" and entity["role"] == "origin":
                    entity_dict["origin"] = entity["value"]
                
                if entity["entity"] == "location" and entity["role"] == "destination":
                    entity_dict["destination"] = entity["value"]

                if entity["entity"] == "DATE":
                    entity_dict["departure_date"] = entity["value"]
        except KeyError as e:
            pass
        except Exception as e:
            logger.error(str(repr(e)))
        else:
            return entity_dict

        return None