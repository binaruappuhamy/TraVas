from amadeus import Client, ResponseError, Location
import logging
import json
import pandas as pd
import os


class Search:
    def __init__(self):
        self.amadeus = Client(
            client_id=os.getenv("SEARCH_CLIENT_ID"),
            client_secret=os.getenv("SEARCH_CLIENT_SECRET")
        )

        self.df_airports = pd.read_csv('https://ourairports.com/data/airports.csv')
        self.df_airports = self.df_airports[['municipality', 'iata_code']].copy()
        self.df_airports.rename({'municipality': 'city'}, axis=1, inplace=True)
        self.df_airports = self.df_airports[self.df_airports['city'].notna()].reset_index(drop=True)
        self.df_airports = self.df_airports[self.df_airports['iata_code'].notna()].reset_index(drop=True)
        self.df_airports = self.df_airports.sort_values('city')

    # Makes a request to amadeus to get the chapest flights
    # origin: origin city name
    # destination: destination city name
    # departure date: the day you need to book the flight (YYYY/MM/DD)
    # returns jsonified string of amadeus's response or None
    def search_offers(self, origin, destination, departure_date):
        try:
            origin_code_list = self.df_airports.query("city=='{}'".format(origin))
            destination_code_list = self.df_airports.query("city=='{}'".format(destination))

            for origin_row in range(origin_code_list.shape[0]):
                origin_code = origin_code_list.iat[origin_row, 1]

                for dest_row in range(destination_code_list.shape[0]):
                    destination_code = destination_code_list.iat[dest_row, 1]

                    response = self.amadeus.shopping.flight_offers_search.get(
                        originLocationCode=origin_code,
                        destinationLocationCode=destination_code,
                        departureDate=departure_date, 
                        adults=1
                    )

                    if response.data:
                        break

        except Exception as e:
            logging.error(str(repr(e)))
        else:
            if response.data:
                return json.dumps(response.data[0], indent=4)
            else:
                return None