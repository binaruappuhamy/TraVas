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
    def CheckTravelIntent(self):
        return self.NLP_dict["intent"]["name"] == "travel"

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
            if len(entity_dict) == 3:
                return entity_dict

        return None