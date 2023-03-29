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
        self.target_time = datetime.timedelta(seconds=10)
        self.search = search.Search()
        self.rasa = rasa.Rasa()
        self.states = [State() for _ in range(10)]
        # destinations = ["London", "Paris", "Tokyo", "Beijing", "Moscow",
        #                 "Istanbul", "Sydney", "Dubai", "Los Angeles", "Chicago"]
        destinations = ["Vancouver", "Calgary", "Edmonton", "Paris", "London",
                        "Tokyo", "Osaka", "Kyoto", "Sydney", "Chicago"]
        
        for i, destination in enumerate(destinations):
            self.states[i].entity_dict = {
                "origin": "Toronto",
                "destination": destination,
                "departure_date": self.rasa.date_resolve("05/01/2023"),
            }
        

    def test_flight_time(self):
        print("\n Test:", self._testMethodName)
        total_time = datetime.timedelta(seconds=0)
        

        for _, state in enumerate(self.states):
            start_time = datetime.datetime.now()
            try:
                self.search.search_flights(state)
            except Exception as e:
                continue
            total_time += datetime.datetime.now() - start_time
            time.sleep(1)

        avg_time = total_time / len(self.states)
        print("Average Flight Query Time: ", avg_time)

        self.assertLess(avg_time, self.target_time, f"Average time {avg_time} exceeded 10 seconds")
    
    def test_restaurant_time(self):
        print("\n Test:", self._testMethodName)
        total_time = datetime.timedelta(seconds=0)

        for _, state in enumerate(self.states):
            start_time = datetime.datetime.now()
            try:
                self.search.search_restaurants(state)
            except Exception as e:
                continue

            total_time += datetime.datetime.now() - start_time
            time.sleep(1)

        avg_time = total_time / len(self.states)
        print("Average Restaurant Query Time: ", avg_time)

        self.assertLess(avg_time, self.target_time,
                        f"Average time {avg_time} exceeded 10 seconds")

    def test_hotel_time(self):
        print("\n Test:", self._testMethodName)
        total_time = datetime.timedelta(seconds=0)

        for _, state in enumerate(self.states):
            start_time = datetime.datetime.now()
            try:
                self.search.search_hotels(state)
            except Exception as e:
                continue
            total_time += datetime.datetime.now() - start_time
            time.sleep(1)

        avg_time = total_time / len(self.states)
        print("Average Hotel Query Time: ", avg_time)

        self.assertLess(avg_time, self.target_time, f"Average time {avg_time} exceeded 10 seconds")
    

if __name__ == '__main__':
    unittest.main()