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

        self.check_date_range = 5

        self.df_airports = pd.read_csv('https://ourairports.com/data/airports.csv')
        self.df_airports = self.df_airports[['municipality', 'iata_code', 'name']].copy()
        self.df_airports.rename({'municipality': 'city'}, axis=1, inplace=True)
        self.df_airports = self.df_airports[self.df_airports['city'].notna()].reset_index(drop=True)
        self.df_airports = self.df_airports[self.df_airports['iata_code'].notna()].reset_index(drop=True)
        self.df_airports = self.df_airports.sort_values('city')

    # input PTXHYMZH flight duration
    # returns formated string of XHrs YMins ZSecs
    # returns jsonified string of amadeus's response or None
    @staticmethod
    def format_duration(dur_str):
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

    # Makes a request to amadeus to get the chapest flights
    # origin: origin city name
    # destination: destination city name
    # departure date: the day you need to book the flight (YYYY-MM-DD)
    # returns jsonified string of amadeus's response or None
    def search_offers(self, origin, destination, departure_date):
        try:
            origin_code_list = self.df_airports.query("city=='{}'".format(origin.title()))
            destination_code_list = self.df_airports.query("city=='{}'".format(destination.title()))

            # #Functionality not available in the free version, would be nice to have
            # date_list = self.amadeus.shopping.flight_dates.get(origin=origin_code, destination=destination_code)

            #Check for flights for dates in range departure_date + check_date_range to give the user some option
            date_list = [datetime.datetime.strftime(departure_date + datetime.timedelta(days=x), "%Y-%m-%d") for x in range(self.check_date_range)]

            for date in date_list:
                for origin_row in range(origin_code_list.shape[0]):
                    origin_code = origin_code_list.iat[origin_row, 1]

                    for dest_row in range(destination_code_list.shape[0]):
                        destination_code = destination_code_list.iat[dest_row, 1]

                        self.logger.debug("searching flight offer from {} to {} on {}".format(origin_code, destination_code, date))

                        try:
                            #10 TPS per user limit for free version...seems like the TPS is even less for me...
                            response = self.amadeus.shopping.flight_offers_search.get(
                                originLocationCode=origin_code,
                                destinationLocationCode=destination_code,
                                departureDate=date, 
                                adults=1,
                                currencyCode="CAD",
                                max=3
                            )
                        except Exception as e:
                            if '429' in e.args[0]:
                                time.sleep(1)
                                continue
                            else:
                                raise(e)

                        if response.data:
                            """
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
                                flight_info["num_stops"] = len(info["itineraries"][0]["segments"])
                                flight_info["num_of_seats"] = info["numberOfBookableSeats"]
                                flight_info["origin"] = self.df_airports.query(f"iata_code=='{origin_code}'").name.values[0]
                                flight_info["dest"] = self.df_airports.query(f"iata_code=='{destination_code}'").name.values[0]
                                flight_info["dept_when"] = info["itineraries"][0]["segments"][0]["departure"]["at"].replace("T", " at ")
                                flight_info["duration"] = self.format_duration(info["itineraries"][0]["duration"])

                                flight_info_report = "\n".join(flight_info_msg).format(**flight_info)
                                flight_report.append(flight_info_report)

                            return "\n\n".join(flight_report)

        except Exception as e:
            self.logger.error(str(repr(e)))
            return None
        else:
            return None

def main():
    load_dotenv()
    searchClient = Search()
    
    flight_info_report = searchClient.search_offers("Toronto", "Sydney", datetime.datetime(2023, 5, 15).date())

    # #not available in the public version, so we can't book flights from the sdk
    # searchClient.amadeus.booking.flight_orders.post(flight_info, traveler)
    print(flight_info_report)

if __name__ == '__main__':
    main()