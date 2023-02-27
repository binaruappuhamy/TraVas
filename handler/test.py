import requests
import json


def search_location_id(destination):
        try:
            url = "https://worldwide-restaurants.p.rapidapi.com/typeahead"

            payload = "q=" + destination + "&language=en_US"
            print(payload)
            headers = {
	            "content-type": "application/x-www-form-urlencoded",
	            "X-RapidAPI-Key": "08691c664dmsh172b54fbfcfb87cp1b3742jsn67b6f9936827",
	            "X-RapidAPI-Host": "worldwide-restaurants.p.rapidapi.com"
            }

            response = requests.request("POST", url, data=payload, headers=headers)

            body = json.loads(response.text)

            print(body)
            print(type(body))
            

            location_id = body['results']['data'][0]['result_object']['location_id']
            print(location_id)
            return location_id

        except Exception as e:
            print('Error:', e)
            return None

def search_restaurants(location_id):
    name = list()
    num_reviews = list()
    rating = list()
    ranking = list()
    price_level = list()
    restaurants = dict()

    try:
        url = "https://worldwide-restaurants.p.rapidapi.com/search"

        payload = "language=en_US&limit=5&location_id=187791&currency=CAD"
        payload = "language=en_US&limit=5&location_id=" + location_id + "&currency=CAD"

        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "X-RapidAPI-Key": "08691c664dmsh172b54fbfcfb87cp1b3742jsn67b6f9936827",
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

        return restaurants
        
    except Exception as e:
        #self.logger.error(str(repr(e)))
        return None



def main():

    location_id = search_location_id("Sydney")
    print("Location ID: ", location_id)
    restaurant_info_report = search_restaurants(location_id)


    print(restaurant_info_report)

main()