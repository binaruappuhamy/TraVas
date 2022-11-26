from amadeus import Client, ResponseError, Location
import logging
import json
import pandas as pd
import os
from dotenv import load_dotenv
import logging
import datetime

logger = logging.getLogger('SEARCH_API')
logger.setLevel(logging.DEBUG)

class Search:
    def __init__(self):
        self.amadeus = Client(
            client_id=os.getenv("SEARCH_CLIENT_ID"),
            client_secret=os.getenv("SEARCH_CLIENT_SECRET"),
            logger=logger,
            log_level='debug'
        )

        self.check_date_range = 5

        self.df_airports = pd.read_csv('https://ourairports.com/data/airports.csv')
        self.df_airports = self.df_airports[['municipality', 'iata_code', 'name']].copy()
        self.df_airports.rename({'municipality': 'city'}, axis=1, inplace=True)
        self.df_airports = self.df_airports[self.df_airports['city'].notna()].reset_index(drop=True)
        self.df_airports = self.df_airports[self.df_airports['iata_code'].notna()].reset_index(drop=True)
        self.df_airports = self.df_airports.sort_values('city')

    # Makes a request to amadeus to get the chapest flights
    # origin: origin city name
    # destination: destination city name
    # departure date: the day you need to book the flight (YYYY-MM-DD)
    # returns jsonified string of amadeus's response or None
    def search_offers(self, origin, destination, departure_date):
        try:
            origin_code_list = self.df_airports.query("city=='{}'".format(origin))
            destination_code_list = self.df_airports.query("city=='{}'".format(destination))

            # #Functionality not available in the free version, would be nice to have
            # date_list = self.amadeus.shopping.flight_dates.get(origin=origin_code, destination=destination_code)

            #Check for flights for dates in range departure_date + check_date_range to give the user some option
            base = datetime.datetime.strptime(departure_date, "%Y-%m-%d").date()
            date_list = [datetime.datetime.strftime(base + datetime.timedelta(days=x), "%Y-%m-%d") for x in range(self.check_date_range)]

            for origin_row in range(origin_code_list.shape[0]):
                origin_code = origin_code_list.iat[origin_row, 1]

                for dest_row in range(destination_code_list.shape[0]):
                    destination_code = destination_code_list.iat[dest_row, 1]

                    for date in date_list:
                        response = self.amadeus.shopping.flight_offers_search.get(
                            originLocationCode=origin_code,
                            destinationLocationCode=destination_code,
                            departureDate=date, 
                            adults=1
                        )

                        if response.data:
                            cheapest_flight_info = response.data[0]          
                            origin_airport = self.df_airports.query(f"iata_code=='{origin_code}'").name.values[0]
                            dest_airport = self.df_airports.query(f"iata_code=='{destination_code}'").name.values[0]
                            flight_info_report = "Found a flight offer from {} to {} for a price of {price[currency]} {price[grandTotal]} available until {lastTicketingDate} with {numberOfBookableSeats} available seats."
                            return flight_info_report.format(origin_airport, dest_airport, **cheapest_flight_info)

        except Exception as e:
            logger.error(str(repr(e)))
            return None
        else:
            return None

def main():
    load_dotenv()
    searchClient = Search()
    flight_info_report = searchClient.search_offers("Toronto", "Sydney", "2023-10-12")

    # #not available in the public version, so we can't book flights from the sdk
    # searchClient.amadeus.booking.flight_orders.post(flight_info, traveler)
    print(flight_info_report)

main()