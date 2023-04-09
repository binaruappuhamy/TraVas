import logging

logger = logging.getLogger('RASA_API')
logger.setLevel(logging.DEBUG)

class State:
    def __init__(self):
        self.entity_dict = None
        self.intent_dict = None
        self.prev_entity_convo = None
        self.served = None

        self.reset()

    def reset(self):
        self.entity_dict = {
            "origin": "Toronto", #assume initial origin to Toronto (GPS data)
            "destination": None,
            "departure_date": None,
        }
        self.intent_dict = {
            "flight": False,
            "hotel": False,
            "restaurant": False,
            "stop": False,
        }
        self.prev_entity_convo = None
        self.served = {
            "flight": None,
            "hotel": None,
            "restaurant": None,
        }

    
    def printState(self):
        print("\nEntity:")
        for key, value in self.entity_dict.items():
            print(f"{key}: {value}")
        print("\nIntent:")
        for key, value in self.intent_dict.items():
            print(f"{key}: {value}")

    def update(self, new_entity_dict, new_intent_dict):
        # Reset if convo ended
        if new_intent_dict["stop"]:
            print("Reseting intent dict on condition stop flag")
            self.reset()
            return False

        # Update only when not None
        for key in new_entity_dict:
            if new_entity_dict[key]:
                self.entity_dict[key] = new_entity_dict[key]

        #same origin/dest entity correction -  basically keep the latest - if latest has both then assign it to dest, origin back to Toronto (default)
        future_origin = self.entity_dict["origin"]
        future_dest = self.entity_dict["destination"]
        if future_origin and future_dest and future_origin == future_dest:
            if new_entity_dict["origin"] and new_entity_dict["destination"]:
                self.entity_dict["origin"] = "Toronto"
            else:
                if new_entity_dict["origin"]:
                    self.entity_dict["destination"] = None
                else:
                    self.entity_dict["origin"] = "Toronto"

        for key in new_intent_dict:
            if new_intent_dict[key]:
                self.intent_dict[key] = new_intent_dict[key]
        return True

    def set_entity(self, key, value):
        self.entity_dict[key] = value

    def set_intent(self, key, value):
        self.intent_dict[key] = value

    def get_entity(self, key):
        return self.entity_dict[key]

    def get_intent(self, key):
        return self.intent_dict[key]
    
    def should_send_hotel_offers(self):
        hotel_intent = self.get_intent("hotel")
        destination = self.get_entity("destination")
        departure_date = self.get_entity("departure_date")

        # send hotels if below are true
        return hotel_intent and self.entity_dict != self.served["hotel"]  and destination and departure_date

    def should_send_flight_offers(self):
        flight_intent = self.get_intent("flight")
        destination = self.get_entity("destination")
        departure_date = self.get_entity("departure_date")

        # send flights if below are true
        return flight_intent and self.entity_dict != self.served["flight"] and destination and departure_date
    
    def should_send_restaurant_info(self):
        restaurant_intent = self.get_intent("restaurant")
        destination = self.get_entity("destination")

        # send restaurants if below are true
        return restaurant_intent and self.entity_dict != self.served["restaurant"]  and destination

