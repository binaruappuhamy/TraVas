import unittest
import search
import rasa
from models.state import State
import time
import datetime
from dotenv import load_dotenv


class TestSearch(unittest.TestCase):

    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        load_dotenv()
        self.rasa = rasa.Rasa()
        self.target_time = datetime.timedelta(seconds=10)

        self.test_cases = [
            {
                "message": "I want to travel from Toronto to Tokyo on 05/25/2023",
                "date": "05/25/2023",
                "origin": "Toronto",
                "destination": "Tokyo",
                "travel_intent": True
            },
            {
                "message": "I'm planning a trip from Toronto to Paris on 07/15/2023",
                "date": "07/15/2023",
                "origin": "Toronto",
                "destination": "Paris",
                "travel_intent": True
            },
            {
                "message": "I want to fly from Los Angeles to Sydney on 10/10/2023",
                "date": "10/10/2023",
                "origin": "Los Angeles",
                "destination": "Sydney",
                "travel_intent": True
            },
            {
                "message": "I'm dreaming of going from Dubai to Barcelona on 12/31/2023",
                "date": "12/31/2023",
                "origin": "Dubai",
                "destination": "Barcelona",
                "travel_intent": True
            },
            {
                "message": "I'm looking to travel from London to Toronto on 03/01/2023",
                "date": "03/01/2023",
                "origin": "London",
                "destination": "Toronto",
                "travel_intent": True
            },
            {
                "message": "I want to take a trip from Munich to Cape Town on 06/05/2023",
                "date": "06/05/2023",
                "origin": "Munich",
                "destination": "Cape Town",
                "travel_intent": True
            },
            {
                "message": "I'm planning a journey from Amsterdam to New York City on 09/12/2023",
                "date": "09/12/2023",
                "origin": "Amsterdam",
                "destination": "New York City",
                "travel_intent": True
            },
            {
                "message": "I want to fly from Sydney to Cape Town on 01/05/2023",
                "date": "01/05/2023",
                "origin": "Sydney",
                "destination": "Cape Town",
                "travel_intent": True
            },
            {
                "message": "I'm dreaming of going from Tokyo to Barcelona on 04/22/2023",
                "date": "04/22/2023",
                "origin": "Tokyo",
                "destination": "Barcelona",
                "travel_intent": True
            },
            {
                "message": "I'm looking to travel from Rio de Janeiro to Amsterdam on 08/08/2023",
                "date": "08/08/2023",
                "origin": "Rio de Janeiro",
                "destination": "Amsterdam",
                "travel_intent": True
            },
            {
                "message": "I want to take a trip from Dubai to Paris on 11/17/2023",
                "date": "11/17/2023",
                "origin": "Dubai",
                "destination": "Paris",
                "travel_intent": True
            },
            {
                "message": "I'm planning a vacation from New York to Madrid on 12/20/2023",
                "date": "12/20/2023",
                "origin": "New York",
                "destination": "Madrid",
                "travel_intent": True
            },
            {
                "message": "I want to fly from Los Angeles to Tokyo on 02/14/2024",
                "date": "02/14/2024",
                "origin": "Los Angeles",
                "destination": "Tokyo",
                "travel_intent": True
            },
            {
                "message": "I'm thinking of traveling from Sydney to Bangkok on 09/01/2024",
                "date": "09/01/2024",
                "origin": "Sydney",
                "destination": "Bangkok",
                "travel_intent": True
            },
            {
                "message": "I'm planning to travel from Bangkok to Shanghai on 05/25/2023",
                "date": "05/25/2023",
                "origin": "Bangkok",
                "destination": "Shanghai",
                "travel_intent": True
            },
            {
                "message": "Have you seen the latest movie that just came out?",
                "travel_intent": False
            },
            {
                "message": "I love spending my Sundays at the park",
                "travel_intent": False
            },
            {
                "message": "I've been really enjoying cooking lately",
                "travel_intent": False
            },
            {
                "message": "Do you have any plans for the weekend?",
                "travel_intent": False
            },
            {
                "message": "I just finished reading a great book",
                "travel_intent": False
            },
            {
                "message": "I'm thinking about redecorating my living room",
                "travel_intent": False
            },
            {
                "message": "I need to buy some new clothes for the summer",
                "travel_intent": False
            },
            {
                "message": "Today was really hot",
                "travel_intent": False
            },
            {
                "message": "I got 40% and failed my final exam",
                "travel_intent": False
            },
            {
                "message": "I'm thinking about getting a new pet",
                "travel_intent": False
            },
            {
                "message": "why do all tech people like hiking",
                "travel_intent": False
            },
            {
                "message": "I need to stop writing test cases",
                "travel_intent": False
            },
            {
                "message": "my boss fired me",
                "travel_intent": False
            },
            {
                "message": "I just started a new job last week",
                "travel_intent": False
            },
            {
                "message": "I'm thinking about starting a garden in my backyard",
                "travel_intent": False
            },
        ]

    def test_intent(self):
        num_correct = 0
        for test_case in self.test_cases:
            _, intent_dict = self.rasa.classify(test_case["message"])
            # print("Message: ", test_case["message"])
            # print(intent_dict)
            if (intent_dict["flight"] or intent_dict["hotel"]) and test_case["travel_intent"]:
                num_correct += 1
            elif not (intent_dict["flight"] or intent_dict["hotel"]) and not test_case["travel_intent"]:
                num_correct += 1

        avg = num_correct/len(self.test_cases)
        print("Results: ", num_correct, "out of ", len(self.test_cases),  "were correct" )
        self.assertGreaterEqual(avg, 0.9)
    
    def test_entity(self):
        num_correct = 0
        num_total = 0
        for test_case in self.test_cases:
            if not test_case["travel_intent"]:
                continue

            num_total += 1
            entity_dict, _ = self.rasa.classify(test_case["message"])
            if entity_dict["destination"] == test_case["destination"] and\
                entity_dict["origin"] == test_case["origin"]:
                num_correct += 1
            else:
                # print(entity_dict)
                # print(test_case)
                pass

        avg = num_correct/num_total
        print("Results: ", num_correct, "out of ",
              num_total,  "were correct")
        self.assertGreaterEqual(avg, 0.9)
    
    def test_time(self):
        num_correct = 0
        start_time = datetime.datetime.now()
        for test_case in self.test_cases:
            _, intent_dict = self.rasa.classify(test_case["message"])
            # print("Message: ", test_case["message"])
            # print(intent_dict)
            if (intent_dict["flight"] or intent_dict["hotel"]) and test_case["travel_intent"]:
                num_correct += 1
            elif not (intent_dict["flight"] or intent_dict["hotel"]) and not test_case["travel_intent"]:
                num_correct += 1

        total_time = datetime.datetime.now() - start_time
        avg_time = total_time/len(self.test_cases)
        print("Average Classification Time: ", avg_time)

        self.assertLess(avg_time, self.target_time, f"Average time {avg_time} exceeded 10 seconds")

if __name__ == '__main__':
    unittest.main()
