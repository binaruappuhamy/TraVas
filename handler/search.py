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

        self.date_range = 5
        self.load_airports()

    def load_airports(self):
        '''Load airport data from csv'''
        self.df_airports = pd.read_csv('https://ourairports.com/data/airports.csv')
        self.df_airports = self.df_airports[['municipality', 'iata_code', 'name']].copy()
        self.df_airports.rename({'municipality': 'city'}, axis=1, inplace=True)
        self.df_airports = self.df_airports[self.df_airports['city'].notna()].reset_index(drop=True)
        self.df_airports = self.df_airports[self.df_airports['iata_code'].notna()].reset_index(drop=True)
        self.df_airports = self.df_airports.sort_values('city')

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

    def search_flights(self, origin, destination, departure_date):
        '''
        Makes a request to amadeus to get the chapest flights
            origin: origin city name
            destination: destination city name
            departure date: the day you need to book the flight (YYYY-MM-DD)
            returns jsonified string of amadeus's response or None
        '''
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
                        formatted_message = self.format_flight_offers(response, origin, destination, departure_date, origin_code, destination_code)
                        return formatted_message

        except Exception as e:
            self.logger.error(str(repr(e)))
            return None
        else:
            return None


    # Hotel Methods
    def format_hotel_offers(self, hotel_offers_list):
        if not hotel_offers_list:
            return "Bro there ain't hotels for this location"

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

        return "\n\n".join(hotel_message)

    def search_hotels(self, location, dates):
        try:
            '''
            Get list of hotel offers by city code
            '''
            response = self.amadeus.reference_data.locations.hotels.by_city.get(cityCode=location, ratings='5')
            hotel_ids = [hotel['hotelId'] for hotel in response.data]
            hotel_offers = self.amadeus.shopping.hotel_offers_search.get(hotelIds=hotel_ids, adults='2')
            # print(hotel_offers.data)

            return self.format_hotel_offers(hotel_offers.data)

        except ResponseError as error:
            raise error

def main():
    load_dotenv()
    searchClient = Search()

    # flight_info_report = searchClient.search_flights("Toronto", "Sydney", datetime.datetime(2023, 2, 20).date())
    # print(flight_info_report)

    # Booking not available in the public version, so we can't book flights from the sdk
    # searchClient.amadeus.booking.flight_orders.post(flight_info, traveler)

    # Hotel search test
    print(searchClient.search_hotels("SEA", ""))


if __name__ == '__main__':
    main()
