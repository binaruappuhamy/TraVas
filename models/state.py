
import logging

logger = logging.getLogger('RASA_API')
logger.setLevel(logging.DEBUG)

class State:
    def __init__(self):
        self.entity_dict = None
        self.intent_dict = None
        self.reset()

    def reset(self):
        self.entity_dict = {
            "origin": None,
            "destination": None,
            "departure_date": None,
        }
        self.intent_dict = {
            "flight": False,
            "hotel": False,
            "restaurant": False,
            "stop": False,
        }
    
    def printState(self):
        print("Entity:")
        for key, value in self.entity_dict.items():
            print(f"{key}: {value}")
        print("\nIntent:")
        for key, value in self.intent_dict.items():
            print(f"{key}: {value}")

    def update(self, new_entity_dict, new_intent_dict):
        # Reset if convo ended
        if new_intent_dict["stop"]:
            self.reset()
            return
    
        # Update only when not None
        for key in new_entity_dict:
            if new_entity_dict[key] is not None:
                self.entity_dict[key] = new_entity_dict[key]

        for key in new_intent_dict:
            if new_intent_dict[key] is not None:
                self.intent_dict[key] = new_intent_dict[key]

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
        return hotel_intent and destination and departure_date

    def should_send_flight_offers(self):
        flight_intent = self.get_intent("flight")
        destination = self.get_entity("destination")
        departure_date = self.get_entity("departure_date")

        # send flights if below are true
        return flight_intent and destination and departure_date
    
    def should_send_restaurant_info(self):
        restaurant_intent = self.get_intent("restaurant")
        destination = self.get_entity("destination")

        # send restaurants if below are true
        return restaurant_intent and destination

