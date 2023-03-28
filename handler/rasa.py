import requests
import json
import datetime
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

        # parse entities and intents from response
        return self.process_rasa_response(data)
    
    @staticmethod
    def date_resolve(date_str):
        date_obj = None
        # resolve next, this -> how to do this is next always +1 week
        # resolve summer, winter seasons(will need hemisphere loc data) and other holiday dates
        day_list = ["mon", "tue", "wed", "thur", "fri", "sat", "sun"]
        today = datetime.datetime.today().date()

        if "weekend" in date_str:
            date_obj = today + datetime.timedelta((5 - today.weekday()) % 7)
            return date_obj

        for index, day in enumerate(day_list):
            if day in date_str:
                date_obj = today + \
                    datetime.timedelta((index - today.weekday()) % 7)
                return date_obj

        date_types = [
            "%y %m %d", "%Y %m %d", "%y %m %e", "%Y %m %e",
            "%d %m %y", "%d %m %Y", "%e %m %y", "%e %m %Y",
            "%m %d %y", "%m %d %Y", "%m %e %y", "%m %e %Y",
            "%b %e %Y", "%B %e %Y", "%b %d %Y", "%B %d %Y",
            "%e %b %Y", "%e %B %Y", "%d %b %Y", "%d %B %Y",
            "%Y %b %e", "%Y %B %e", "%Y %b %d", "%Y %B %d",
        ]

        regex = re.compile(f"[{re.escape(string.punctuation)}]")
        date_str = " ".join(regex.sub(" ", date_str).split())

        for date_typ in date_types:
            try:
                date_obj = datetime.datetime.strptime(
                    date_str, date_typ).date()
            except ValueError:
                pass
        return date_obj

    def process_rasa_response(self, data):
        entity_dict = {
            "origin": None,
            "destination": None,
            "departure_date": None,
        }
        intent_dict = {
            "flight": False,
            "hotel": False,
            "restaurant": False,
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
                    entity_dict["origin"] = entity['value'].title()
                elif  entity['role'] == 'destination':
                    entity_dict["destination"] = entity['value'].title()
            elif entity['entity'] == 'DATE':
                entity_dict["departure_date"] = self.date_resolve(entity['value'])
        
        return entity_dict, intent_dict

# test code
def main():
    # Use the following to see what the Rasa response looks like
    rasa = Rasa()
    print(rasa.classify("I want to fly from Toronto to Tokyo on 05/25/2023"))

    # print(rasa.data)

if __name__ == '__main__':
    main()
