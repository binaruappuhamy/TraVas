import requests
import json
from datetime import datetime
import string
import re
import logging

logger = logging.getLogger('RASA_API')
logger.setLevel(logging.DEBUG)

class Rasa:
    def __init__(self):
        self.url = 'http://localhost:5005/model/parse'
        self.data = None
        
    def classify(self, message):
        '''
        Returned data loaded into NLP dict
        '''
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({'text': message})
        logger.debug("Rasa response: \n" + data)
        r = requests.post(url=self.url, data=data, headers=headers)
        data = json.loads(r.content.decode('utf8'))
        self.data = data

        return self.process_rasa_response(data)
    
    def process_rasa_response(self, data):
        entity_dict = {
            "origin": None,
            "destination": None,
            "departure_date": None,
        }
        intent_dict = {
            "flight": False,
            "hotel": False,
            "stop": False
        }
        
        # Extract top intent
        if data['intent']['name'] in intent_dict and data['intent']['confidence'] > 0.9:
            intent = data['intent']['name']
            intent_dict[intent] = True
        
        # Extract entities
        for entity in data['entities']:
            if "role" in entity:
                if entity['role'] == 'origin':
                    entity_dict["origin"] = entity['value']
                elif  entity['role'] == 'destination':
                    entity_dict["destination"] = entity['value']
            elif entity['entity'] == 'DATE':
                entity_dict["departure_date"] = datetime.strptime(entity['value'], '%m/%d/%Y').date()
        
        return entity_dict, intent_dict


# test code
def main():
    # Use the following to see what the Rasa response looks like
    rasa = Rasa()
    print(rasa.classify(
        "I want to fly from Toronto to Tokyo on 05/25/2023"))

    # print(rasa.data)

if __name__ == '__main__':
    main()