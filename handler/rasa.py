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
        self.vague_dates = None
        self.init_vague_dates()
        
    def classify(self, message, StateContext):
        '''
        Returned data loaded into NLP dict
        '''
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({'text': message})
        logger.debug("Rasa response: \n" + data)
        r = requests.post(url=self.url, data=data, headers=headers)
        data = json.loads(r.content.decode('utf8'))
        self.data = data
        print(data)
        # parse entities and intents from response
        return self.process_rasa_response(data, StateContext)
    
    @staticmethod
    def print_rasa_rep(entity_dict, intent_dict):
        print("\nEntity received from Rasa:")
        for key, value in entity_dict.items():
            print(f"{key}: {value}")
        print("\nIntent received from Rasa:")
        for key, value in intent_dict.items():
            print(f"{key}: {value}")

    def init_vague_dates(self):
        # Get the current year
        now = datetime.datetime.now()
        year = now.year

        # Define a dictionary that maps phrases to start dates for each season
        vague_dates = {
            "jan": datetime.date(year, 1, 1),
            "feb": datetime.date(year, 2, 1),
            "mar": datetime.date(year, 3, 1),
            "apr": datetime.date(year, 4, 1),
            "may": datetime.date(year, 5, 1),
            "june": datetime.date(year, 6, 1),
            "july": datetime.date(year, 7, 1),
            "aug": datetime.date(year, 8, 1),
            "sep": datetime.date(year, 9, 1),
            "oct": datetime.date(year, 10, 1),
            "nov": datetime.date(year, 11, 1),
            "dec": datetime.date(year, 12, 1),
            "next year": datetime.date(year+1, 1, 1),
            "the following year": datetime.date(year+1, 1, 1),
            "the upcoming year": datetime.date(year+1, 1, 1),
            "next summer": datetime.date(year + 1, 6, 1),
            "the following summer": datetime.date(year, 6, 1),
            "the upcoming summer": datetime.date(year, 6, 1),
            "next fall": datetime.date(year + 1, 9, 1),
            "the following fall": datetime.date(year, 9, 1),
            "the upcoming fall": datetime.date(year, 9, 1),
            "next autumn": datetime.date(year + 1, 9, 1),
            "the following autumn": datetime.date(year, 9, 1),
            "the upcoming autumn": datetime.date(year, 9, 1),
            "next spring": datetime.date(year + 1, 3, 1),
            "the following spring": datetime.date(year, 3, 1),
            "the upcoming spring": datetime.date(year, 3, 1),
            "next winter": datetime.date(year + 1, 12, 1),
            "the following winter": datetime.date(year, 12, 1),
            "the upcoming winter": datetime.date(year, 12, 1)
        }

        # Adjust dates that are in the past to be in the future
        for phrase, date in vague_dates.items():
            if date < datetime.date(now.year, now.month, now.day):
                vague_dates[phrase] = date.replace(year=year+1)
        self.vague_dates = vague_dates


    def date_resolve(self, date_str):
        date_obj = None
        # resolve next, this -> how to do this is next always +1 week
        # resolve summer, winter seasons(will need hemisphere loc data) and other holiday dates
        day_list = ["mon", "tue", "wed", "thur", "fri", "sat", "sun"]
        today = datetime.datetime.today().date()
        year = today.year

        if "weekend" in date_str:
            date_obj = today + datetime.timedelta((5 - today.weekday()) % 7)
            return date_obj


        for index, day in enumerate(day_list):
            if day in date_str:
                date_obj = today + \
                    datetime.timedelta((index - today.weekday()) % 7)
                return date_obj
            
        for vague_date in self.vague_dates.keys():
            if date_str.lower() in vague_date:
                return self.vague_dates[vague_date]
            else:
                date_list = date_str.lower().split(" ")
                for str in date_list:
                    if str in vague_date:
                      return self.vague_dates[vague_date]  
        
        # if date_str.lower() in self.vague_dates:
        #     return self.vague_dates[date_str.lower()]
        

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

    def process_rasa_response(self, data, StateContext):
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
            if data['intent']['name'] != "stop" or (data['intent']['name'] == "stop" and 'Travas' in data['text']):
                intent = data['intent']['name']
                intent_dict[intent] = True

        # Extract entities
        for entity in data['entities']:
            if "role" in entity:
                if entity['role'] == 'origin':
                    entity_dict["origin"] = entity['value'].title()
                    StateContext.prev_entity_convo = "origin"
                elif  entity['role'] == 'destination':
                    entity_dict["destination"] = entity['value'].title()
                    StateContext.prev_entity_convo = "destination"
                elif entity['role'] == 'correction':
                    if StateContext.prev_entity_convo in ["origin", "destination"]: #don't need for date as you can learn latest date w/o context
                        entity_dict[StateContext.prev_entity_convo]=entity['value'].title()
            elif entity['entity'] == 'DATE':
                entity_dict["departure_date"] = self.date_resolve(entity['value'])
                StateContext.prev_entity_convo = "departure_date"

        self.print_rasa_rep(entity_dict, intent_dict)

        return entity_dict, intent_dict




# test code
class State:
    def __init__(self):
        self.entity_dict = None
        self.intent_dict = None
        self.prev_entity_convo = None
        self.served = None


def main():
    # Use the following to see what the Rasa response looks like
    rasa = Rasa()
    StateContext = State()
    print(rasa.classify("I want to fly from Toronto to Tokyo next winter", StateContext))
    # print(rasa.classify("What about sydney", StateContext))


    # print(rasa.data)

if __name__ == '__main__':
    main()
