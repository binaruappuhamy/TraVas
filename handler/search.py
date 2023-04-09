from amadeus import Client, ResponseError, Location
import logging
import json
import pandas as pd
import os
from dotenv import load_dotenv
import logging
import datetime
import time
import re
import models.state as State
import requests


class Search:
    def __init__(self):
        logging.basicConfig(format="%(asctime)s;%(levelname)s;%(message)s")
        logger = logging.getLogger("SEARCH_API")
        logger.setLevel(logging.DEBUG)
        self.logger = logger

        self.amadeus = Client(
            client_id=os.getenv("SEARCH_CLIENT_ID"),
            client_secret=os.getenv("SEARCH_CLIENT_SECRET"),
            logger=self.logger,
            log_level="info"
        )
        self.rapidapi_key = os.getenv("X-RapidAPI-Key")

        self.date_range = 5
        self.load_airports()
        self.load_cities()

    def load_airports(self):
        '''Load airport data from csv'''
        self.df_airports = pd.read_csv('https://ourairports.com/data/airports.csv')
        self.df_airports = self.df_airports[['municipality', 'iata_code', 'name']].copy()
        self.df_airports.rename({'municipality': 'city'}, axis=1, inplace=True)
        self.df_airports = self.df_airports[self.df_airports['city'].notna()].reset_index(drop=True)
        self.df_airports = self.df_airports[self.df_airports['iata_code'].notna()].reset_index(drop=True)
        self.df_airports = self.df_airports.sort_values('city')

    def load_cities(self):
        csv_path = os.path.join(os.path.dirname(__file__), '../data/city_codes.csv')
        self.city_codes = pd.read_csv(csv_path)

    @staticmethod
    def format_duration(dur_str):
        '''
        input PTXHYMZH flight duration
        returns formated string of XHrs YMins ZSecs
        returns jsonified string of amadeus's response or None
        '''
        dur_list = re.findall(r"(\d+(?:\.\d)?)([SMH])", dur_str)
        time_str = ""
        subst_dict = {
            "H": "Hrs",
            "M": "Mins",
            "S": "Secs"
        }

        for val, key in dur_list:
            time_str += f"{val}{subst_dict[key]} "

        return time_str

    def get_city_airports(self, city):
        '''
        Each city may have multiple airports
        @param city: city to find the airports of
        @return: a list of airports in the city
        '''
        return self.df_airports.query("city=='{}'".format(city.title()))

    def get_city_code(self, city):
        city_code = self.city_codes.loc[self.city_codes['Location'] == city, 'CityCode'].iloc[0]
        return city_code

    def get_airport_combinations(self, origin, destination):
        '''Get all combinations of airports of (origin, destination)'''
        origin_code_list = self.get_city_airports(origin)["iata_code"].tolist()
        dest_code_list = self.get_city_airports(destination)["iata_code"].tolist()

        return [(x, y) for x in origin_code_list for y in dest_code_list]

    @staticmethod
    def get_date_list(date, date_range):
        '''Create a list of dates in a range (departure_date + check_date_range) to give the user some option'''
        # Functionality not available in the free version, would be nice to have
        # date_list = self.amadeus.shopping.flight_dates.get(origin=origin_code, destination=destination_code)
        date_list = [datetime.datetime.strftime(date + datetime.timedelta(days=x), "%Y-%m-%d") for x in range(date_range)]
        return date_list

    def request_amadeus_flight_offers(self, origin_code, destination_code, date):
        try:
            # 10 TPS per user limit for free version...seems like the TPS is even less for me...
            response = self.amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin_code,
                destinationLocationCode=destination_code,
                departureDate=date,
                adults=1,
                currencyCode="CAD",
                max=3
            )
            return response
        except Exception as e:
            if '429' in e.args[0]:
                time.sleep(1)
            else:
                raise (e)

    def get_cheapest_flight_dates(self, origin_code, dest_code):
        # not working some how - shouldn't be an API issue because it's under the quotas on Amadeus
        try:
            response = self.amadeus.shopping.flight_dates.get(
                origin='MAD', destination='MUC')
            print(response.data)
        except ResponseError as error:
            raise error

    def format_flight_offers(self, response, origin, destination, departure_date, origin_code, destination_code):
        """
        Using the following Format:
        ----------------------------------
        Carrier - Flight Price (Flight stops, Available Seats)
            From: Origin
            Deprating: Depart Time
            To: Depart
            Arriving: Arrive Time
        """

        flight_report = [
            f"I believe that you are looking for flights from {origin} to {destination} on {str(departure_date)}!",
            f"I suggest these top {len(response.data)} cheapest flights:"
        ]

        flight_info_msg = [
            "{index}. {carrier} - {curr} {price} ({num_stops} Stops, {num_of_seats} Available Seats)",
            "\tFrom:\t{origin}",
            "\tTo:\t{dest}",
            "\tDeprating:\t{dept_when}",
            "\tFlight Time:\t{duration}"
        ]

        cheapest_flight_info_list = response.data
        cheapest_flight_dict = response.result['dictionaries']

        for index, info in enumerate(cheapest_flight_info_list):
            flight_info = dict()
            flight_info["index"] = index+1
            flight_info["carrier"] = cheapest_flight_dict["carriers"][info["validatingAirlineCodes"][0]]
            flight_info["curr"] = info["price"]["currency"]
            flight_info["price"] = info["price"]["grandTotal"]
            flight_info["num_stops"] = len(
                info["itineraries"][0]["segments"])
            flight_info["num_of_seats"] = info["numberOfBookableSeats"]
            flight_info["origin"] = self.df_airports.query(
                f"iata_code=='{origin_code}'").name.values[0]
            flight_info["dest"] = self.df_airports.query(
                f"iata_code=='{destination_code}'").name.values[0]
            flight_info["dept_when"] = info["itineraries"][0]["segments"][0]["departure"]["at"].replace(
                "T", " at ")
            flight_info["duration"] = self.format_duration(
                info["itineraries"][0]["duration"])

            flight_info_report = "\n".join(
                flight_info_msg).format(**flight_info)
            flight_report.append(flight_info_report)

        return "\n\n".join(flight_report)
    
    def format_flight_offers_block(self, response, origin, destination, departure_date, origin_code, destination_code):
        """
        Using the following Format:
        ----------------------------------
        Carrier - Flight Price (Flight stops, Available Seats)
            From: Origin
            Deprating: Depart Time
            To: Depart
            Arriving: Arrive Time
        """

        flight_report_block = [origin, destination, str(departure_date), len(response.data)]

        cheapest_flight_info_list = response.data
        cheapest_flight_dict = response.result['dictionaries']

        for index, info in enumerate(cheapest_flight_info_list):
            flight_info = dict()
            flight_info["index"] = index+1
            flight_info["carrier"] = cheapest_flight_dict["carriers"][info["validatingAirlineCodes"][0]]
            flight_info["curr"] = info["price"]["currency"]
            flight_info["price"] = info["price"]["grandTotal"]
            flight_info["num_stops"] = len(
                info["itineraries"][0]["segments"])
            flight_info["num_of_seats"] = info["numberOfBookableSeats"]
            flight_info["origin"] = self.df_airports.query(
                f"iata_code=='{origin_code}'").name.values[0]
            flight_info["dest"] = self.df_airports.query(
                f"iata_code=='{destination_code}'").name.values[0]
            flight_info["dept_when"] = info["itineraries"][0]["segments"][0]["departure"]["at"].replace(
                "T", " at ")
            flight_info["duration"] = self.format_duration(
                info["itineraries"][0]["duration"])

            flight_report_block.append(flight_info)

        return flight_report_block

    def search_flights(self, state:State):
        '''
        Makes a request to amadeus to get the chapest flights
            origin: origin city name
            destination: destination city name
            departure date: the day you need to book the flight (YYYY-MM-DD)
            returns jsonified string of amadeus's response or None
        '''
        origin = state.get_entity("origin")
        destination = state.get_entity("destination")
        departure_date = state.get_entity("departure_date")

        try:
            # Get the airport combinations in the departure & arrival cities (there can be multiple in each city)
            airport_pairs = self.get_airport_combinations(origin, destination)
            # Get a range of departure dates
            date_list = self.get_date_list(departure_date, self.date_range)

            for date in date_list:
                for (origin_code, destination_code) in airport_pairs:
                    self.logger.debug("searching flight offer from {} to {} on {}".format(origin_code, destination_code, date))
                    
                    # Request flight offers from Amadeus
                    response = self.request_amadeus_flight_offers(origin_code, destination_code, date)
                    if response.data:
                        formatted_message = self.format_flight_offers_block(response, origin, destination, departure_date, origin_code, destination_code)

                        return formatted_message

        except Exception as e:
            self.logger.error(str(repr(e)))
            return None
        else:
            return None


    # Hotel Methods
    def format_hotel_offers(self, hotel_offers_list):
        if not hotel_offers_list:
            return None

        hotel_message = ["My friend, I feel like these hotels would be nice on your trip, don't you think? \n"]

        hotel_offer_formatter = [
            "{index}. {hotel_name} - {curr} {price}",
            "\tCity:\t{city}",
            "\tGuests:\t{guests}",
            "\tCheck In Date:\t{check_in_date}",
            "\tDescription:\t{description}"
        ]

        for index, info in enumerate(hotel_offers_list):
            hotel_info = dict()
            hotel_info["index"] = index+1
            hotel_info["hotel_name"] = info["hotel"]["name"]
            hotel_info["city"] = info["hotel"]["cityCode"]

            # Gets the first offer - too lazy to code the other ones
            first_offer = info["offers"][0]

            hotel_info["curr"] = first_offer["price"]["currency"]
            hotel_info["price"] = first_offer["price"]["total"]
            
            hotel_info["guests"] = first_offer["guests"]["adults"]
            hotel_info["check_in_date"] = first_offer["checkInDate"]
            if first_offer["room"]["description"]:
                # remove escaped characters
                hotel_info["description"] = first_offer["room"]["description"]["text"].replace("\n", ", ").strip()
            else:
                hotel_info["description"] = "No Description"

            hotel_info_report = "\n".join(
                hotel_offer_formatter).format(**hotel_info)
            hotel_message.append(hotel_info_report)
        print(hotel_message)
        return "\n\n".join(hotel_message)

    def search_hotels(self, state: State):
        try:
            '''
            Get list of hotel offers by city code
            '''
            city = state.get_entity("destination")
            city_code = self.get_city_code(city)
            date = state.get_entity("departure_date")

            if not city_code:
                return None
            response = self.amadeus.reference_data.locations.hotels.by_city.get(cityCode=city_code, ratings='5')
            hotel_ids = [hotel['hotelId'] for hotel in response.data]
            hotel_offers = self.amadeus.shopping.hotel_offers_search.get(hotelIds=hotel_ids, adults='2', radius='100', checkInDate=date)
            return self.format_hotel_offers(hotel_offers.data)

        except ResponseError as error:
            raise error

    def search_location_id(self, destination):
        try:
            url = "https://worldwide-restaurants.p.rapidapi.com/typeahead"

            payload = "q=" + destination + "&language=en_US"
            print(payload)
            headers = {
                "content-type": "application/x-www-form-urlencoded",
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "worldwide-restaurants.p.rapidapi.com"
            }

            response = requests.request("POST", url, data=payload, headers=headers)

            body = json.loads(response.text)

            #print(body)
            #print(type(body))
            

            location_id = body['results']['data'][0]['result_object']['location_id']
            print(location_id)
            return location_id

        except Exception as e:
            print('Error:', e)
            return None
        
    def format_restaurant_info(self, restaurants):
        if not restaurants:
            return None
        
        message = ["These are some great options if you're looking for restaurants: \n"]

        retaurant_list_formatter = [
            "{index}. {restaurant_name}",
            "\tNumber of Reviews:\t{num_reviews}",
            "\tRating:\t{rating}",
            "\tRanking:\t{ranking}",
            "\tPrice Level:\t{price_level}"
        ]

        for i in range(len(restaurants["name"])):
            restaurant_info = dict()
            restaurant_info["index"] = i+1
            restaurant_info["restaurant_name"] = restaurants["name"][i]
            restaurant_info["num_reviews"] = restaurants["num_reviews"][i]
            restaurant_info["rating"] = restaurants["rating"][i]
            restaurant_info["ranking"] = restaurants["ranking"][i]
            restaurant_info["price_level"] = restaurants["price_level"][i]

            report = "\n".join(retaurant_list_formatter).format(**restaurant_info)
            message.append(report)

        return "\n\n".join(message)

    def search_restaurants(self, state:State):
        name = list()
        num_reviews = list()
        rating = list()
        ranking = list()
        price_level = list()
        restaurants = dict()

        try:
            destination = state.get_entity("destination")
            location_id = self.search_location_id(destination)

            url = "https://worldwide-restaurants.p.rapidapi.com/search"

            payload = "language=en_US&limit=5&location_id=187791&currency=CAD"
            payload = "language=en_US&limit=5&location_id=" + location_id + "&currency=CAD"

            headers = {
                "content-type": "application/x-www-form-urlencoded",
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "worldwide-restaurants.p.rapidapi.com"
            }

            response = requests.request("POST", url, data=payload, headers=headers)   

            body = json.loads(response.text)     
            
            for i in range(5):
                name.append(body['results']['data'][i]['name'])
                num_reviews.append(body['results']['data'][i]['num_reviews'])
                rating.append(body['results']['data'][i]['rating'])
                ranking.append(body['results']['data'][i]['ranking'])
                price_level.append(body['results']['data'][i]['price_level'])

            restaurants["name"] = name
            restaurants["num_reviews"] = num_reviews
            restaurants["rating"] = rating
            restaurants["ranking"] = ranking
            restaurants["price_level"] = price_level

            message = self.format_restaurant_info(restaurants)

            return message
            
        except Exception as e:
            #self.logger.error(str(repr(e)))
            return None

def main():
    load_dotenv()
    searchClient = Search()
    state = State.State()
    state.entity_dict = {
        "origin": "Toronto",
        "destination": "Tokyo",
        "departure_date": "2023-03-24",
    }    
    print(searchClient.search_restaurants(state))
    # print(searchClient.get_city_code("Tokyo"))
    # print(searchClient.get_city_airports("Sydney"))

    # flight_info_report = searchClient.search_flights("Toronto", "Sydney", datetime.datetime(2023, 2, 20).date())
    # print(flight_info_report)

    # Booking not available in the public version, so we can't book flights from the sdk
    # searchClient.amadeus.booking.flight_orders.post(flight_info, traveler)

    # Hotel search test
    # print(searchClient.search_hotels("Paris", "2023-02-20"))


if __name__ == '__main__':
    main()
