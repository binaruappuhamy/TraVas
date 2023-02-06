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
        '''
        Makes a request to local Rasa instance
        message: string of text
        initialises jsonified string of rasa's response in NLP_dict attrib
        example below:
        {
            "text": "hey",
            "intent": {
                "name": "travel_stop",
                "confidence": 0.9885662198066711
            },
            "entities": [],
            "text_tokens": [
                [
                    0,
                    3
                ]
            ],
            "intent_ranking": [
                {
                    "name": "travel_stop",
                    "confidence": 0.9885662198066711
                },
                {
                    "name": "travel",
                    "confidence": 0.011433818377554417
                }
            ]
        }
        '''
        self.url = 'http://localhost:5005/model/parse'
        self.NLP_dict = None
        
    def Classify(self, message):
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({'text': message})
        r = requests.post(url=self.url, data=data, headers=headers)
        self.NLP_dict = json.loads(r.content.decode('utf8'))
        return None

    # data: what rasa returns
    # returns bool, whether the most likely intent is a travel intent
    def CheckTravelIntent(self):
        return self.NLP_dict["intent"]["name"] == "travel"
    
    def CheckHotelIntent(self):
        return self.NLP_dict["intent"]["name"] == "hotel"

    # data: what rasa returns
    # returns bool, whether the reset flag is raised
    def CheckResetFlag(self):
        if self.NLP_dict["intent"]["name"] == "travel_stop":
            for entity in self.NLP_dict["entities"]:
                if entity["value"].title() == "Travas":
                    return True
        return False

    def loc_resolve(self, entity, entity_state):
        loc_type_dict = {
            "origin": ["from"],
            "destination": ["to", "in"]
        }

        if entity["entity"] == "GPE":
            pre_entity_pos = max(self.NLP_dict["text_tokens"].index([entity["start"], entity["end"]]) - 1, 0)

            #if no state initialised default to destination
            if not entity_state:
                entity_state = "destination"

            if pre_entity_pos:
                identifier = self.NLP_dict["text"].split()[pre_entity_pos]

                for key, val in loc_type_dict.items():
                    if identifier in val:
                        entity_state = key

            return entity["value"].title(), entity_state

        return None, entity_state

    @staticmethod
    def date_resolve(date_str):
        date_obj = None
        #resolve next, this -> how to do this is next always +1 week
        #resolve summer, winter seasons(will need hemisphere loc data) and other holiday dates
        day_list = ["mon", "tue", "wed", "thur", "fri", "sat", "sun"]
        today = datetime.datetime.today().date()

        if "weekend" in date_str:
            date_obj = today + datetime.timedelta((5 - today.weekday()) % 7)
            return date_obj

        for index, day in enumerate(day_list):
            if day in date_str:
                date_obj = today + datetime.timedelta((index - today.weekday()) % 7)
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
                date_obj = datetime.datetime.strptime(date_str, date_typ).date()
            except ValueError:
                pass
        return date_obj

    #return dictionary, of travel entities
    def get_entities(self, entity_dict, entity_state):
        run_search = False
        dict_cache = entity_dict.copy()

        try:
            if self.CheckResetFlag():
                entity_dict = {
                    "origin": "Toronto",
                    "destination": None,
                    "departure_date": None
                }
                entity_state = None
            else:
                for entity in self.NLP_dict["entities"]:
                    # the location grouping is still too inaccurate eg: Tokyo tends to be origin by default
                    # needs more data and training
                    # if entity["entity"] == "location" and entity["role"] == "origin":
                    #     entity_dict["origin"] = entity["value"]
                    #     entity_state = "origin"
                    
                    # if entity["entity"] == "location" and entity["role"] == "destination":
                    #     entity_dict["destination"] = entity["value"]
                    #     entity_state = "destination"

                    if entity["entity"] in ["DATE", "date_time"]:
                        entity_dict["departure_date"] = self.date_resolve(entity["value"])
                        entity_state = "departure_date"

                    loc_val, entity_state = self.loc_resolve(entity, entity_state)

                    if loc_val:
                        entity_dict[entity_state] = loc_val

                if None not in entity_dict.values() and dict_cache != entity_dict:
                    run_search = True

        except Exception as e:
            logger.error(str(repr(e)))

        return entity_dict, entity_state, run_search


def main():
    rasa = Rasa()
    entity_state = None
    entity_dict = {
        "origin": "Toronto",
        "destination": None,
        "departure_date": None
    }

    while True:
        msg = input(">")
        rasa.Classify(msg)
        print(json.dumps(rasa.NLP_dict, indent=4))

        entity_dict, entity_state, run_search = rasa.get_entities(entity_dict, entity_state)
        print(entity_dict, entity_state, run_search)

if __name__ == '__main__':
    main()