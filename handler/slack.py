import logging
import os
from slack_sdk.socket_mode.websocket_client import SocketModeClient
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_cleaner2 import *
from datetime import timedelta, datetime
import asyncio
import sys

block_dict = dict.fromkeys(["flight_block", "hotel_block", "restaurant_block"])

class Slack:
    def __init__(self):
        self.token = os.getenv('SLACK_TOKEN')
        self.admin_token = os.getenv('SLACK_ADMIN_TOKEN')
        self.app_token = os.getenv('SLACK_APP_TOKEN')
        self.channelID = os.getenv('SLACK_CHANNEL')
        self.channelName = "capstone-project"
        self.client = SocketModeClient(
                        app_token=self.app_token, 
                        web_client=AsyncWebClient(token=self.token)
                    )
        self.cleaner = SlackCleaner(self.admin_token)
        self.msg = {
            "id": None,
            "str": list(),
            "ts": None,
            "timeout": timedelta(minutes=5),
        }
    
    def clean_channel(self):
        for msg in self.cleaner.c[self.channelName].msgs(with_replies=True):
            msg.delete()

    def Print(self):
        print(self.token)
        print(self.channelID)

    #function not needed anymore
    async def GetMessages(self):
        result = await self.client.web_client.conversations_history(channel=self.channelID, oldest="0")

        return result.data.get("messages", None)

    @staticmethod
    def parseLatestMessageText(data):
        try:
            # first message is the latest message
            return data['text']
        except:
            logging.exception("Error: couldn't parse slack message")
    
    #Input a message payload in slack["messages"]
    #parse only processed msg texts to avoid passing emojis to the model
    @staticmethod
    def parseMessageText(msg):
        try:
            processed_text = None
            if "text" in msg:
                block_list = msg["blocks"]
                for block in block_list:
                    if block["type"] == "rich_text":
                        element_list = block["elements"]
                        for element in element_list:
                            if element["type"] == "rich_text_section":
                                text_element_list = element["elements"]
                                for text_el in text_element_list:
                                    if text_el["type"] == "text":
                                        processed_text = text_el["text"]   
        except Exception as e:
            logging.exception(str(repr(e)), exc_info=sys.exc_info())
        else:
            return processed_text

    async def post_message(self, msg):
        try:
            res = await self.client.web_client.chat_postMessage(
                channel=self.channelID,
                text=msg
            )
            print(res)
            self.msg['id'] = res['ts']
            await self.client.web_client.pins_add(
                channel=self.channelID,
                timestamp=self.msg['id']
            )

        except Exception as e:
            logging.exception(str(repr(e)), exc_info=sys.exc_info())

    async def update_pin_message(self, msg):
        try:
            ts_now = datetime.now()
            if not self.msg['ts'] or (ts_now - self.msg['ts']) > self.msg['timeout']:
                self.msg['str'] = [msg]
                self.msg['ts'] = ts_now
            else:
                self.msg['str'].insert(0, msg)

            await self.client.web_client.chat_update(
                channel=self.channelID,
                ts=self.msg['id'],
                text=("\n").join(self.msg['str'])
            )
            # self.msg['str'] = post_msg

        except Exception as e:
            logging.exception(str(repr(e)), exc_info=sys.exc_info())

    async def update_pin_message_block_flights(self, msg_block):
        ts_now = datetime.now()

        if(msg_block == "No flight offers found."):
            flight_block=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "No flight offers found.",
                        "emoji": True
                    }
                },
                {
                    "type": "divider"
                }]
        else:
            origin = msg_block[0]
            destination = msg_block[1]
            departure_date = msg_block[2]
            response_length = msg_block[3]

            flight_block=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Here are some Flight Offers",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "I believe that you are looking for flights from {} to {} on {}!".format(origin, destination, departure_date),
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "I suggest these top {} cheapest flights:".format(response_length),
                        "emoji": True
                    }
                },
                {
                    "type": "divider"
                }]

            flights=[]
            flight_options=[]

            # If 3 or more results, show only Top 3
            if response_length > 2:
                stop = 3
            else: # If less than 3 results
                stop = response_length

            for index in range(stop):
                flights.append(msg_block[index+4])

            for flight in flights:                
                flight_block.append(
                    {
                        "type": "section",
                        "text": {
                            "text": "{}. {} - {} {}".format(flight["index"], flight["carrier"], flight["curr"], flight["price"]),
                            "type": "mrkdwn"
                        },
                        "fields": [
                            {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "{} Stops".format(flight["num_stops"])
                            },
                            {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "{} Available Seats".format(flight["num_of_seats"])
                            },
                            {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "From: {}".format(flight["origin"])
                            },
                            {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "To: {}".format(flight["dest"])
                            },
                            {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "Departing: {}".format(flight["dept_when"])
                            },
                            {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "Flight Time: {}".format(flight["duration"])
                            }
                        ]
                    })
                
                flight_block.append(
                    {
                        "type": "divider"
                    })

                flight_options.append(
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "{}. {} - {} {}".format(flight["index"], flight["carrier"], flight["curr"], flight["price"]),
                            "emoji": True
                        },
                        "value": "value-{}".format(flight["index"]-1)
                    })
                
            flight_block.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Vote your best flight choice so everyone can see!"
                    },
                    "accessory": {
                        "type": "static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a flight",
                            "emoji": True
                        },
                        "options": flight_options,
                        "action_id": "static_select-action"
                    }
                })
            
            flight_block.append(
                {
                    "type": "divider"
                })

        block_dict["flight_block"] = flight_block

        final_block = []

        if(block_dict["flight_block"] != None):
            for i in range(len(block_dict["flight_block"])):
                final_block.append(block_dict["flight_block"][i])
        if(block_dict["hotel_block"] != None):
            for i in range(len(block_dict["hotel_block"])):
                final_block.append(block_dict["hotel_block"][i])
        if(block_dict["restaurant_block"] != None):
            for i in range(len(block_dict["restaurant_block"])):
                final_block.append(block_dict["restaurant_block"][i])

        try:
            if not self.msg['ts'] or (ts_now - self.msg['ts']) > self.msg['timeout']:
                self.msg['str'] = [msg_block]
                self.msg['ts'] = ts_now
            else:
                self.msg['str'].insert(0, msg_block)

            await self.client.web_client.chat_update(
                channel=self.channelID,
                ts=self.msg['id'],
                text="Block message pinned",
                blocks=final_block
            )

        except Exception as e:
            logging.exception(str(repr(e)), exc_info=sys.exc_info())


    async def update_pin_message_block_hotels(self, msg_block):
        ts_now = datetime.now()

        if(msg_block == "No hotel offers found."):
            hotel_block=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "No hotel offers found.",
                        "emoji": True
                    }
                },
                {
                    "type": "divider"
                }]
        else:
            hotel_block=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Here are some Hotel Offers",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "My friend, I feel like these hotels would be nice on your trip, don't you think?",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "I suggest these top {} rated hotels:".format(len(msg_block)),
                        "emoji": True
                    }
                },
                {
                    "type": "divider"
                }]
            
            hotels=[]
            hotel_options=[]

            # If 3 or more results, show only Top 3
            if len(msg_block) > 2:
                stop = 3
            else: # If less than 3 results
                stop = len(msg_block)

            for index in range(stop):
                hotels.append(msg_block[index])

            for hotel in hotels:                
                hotel_block.append(
                    {
                        "type": "section",
                        "text": {
                            "text": "{}. {} - {} {}".format(hotel["index"], hotel["hotel_name"], hotel["curr"], hotel["price"]),
                            "type": "mrkdwn"
                        },
                        "fields": [
                            {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "City: {}".format(hotel["city"])
                            },
                            {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "Guests: {}".format(hotel["guests"])
                            },
                            {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "Check In Date: {}".format(hotel["check_in_date"])
                            },
                            {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "Description: {}".format(hotel["description"])
                            }
                        ]
                    })
                
                hotel_block.append(
                    {
                        "type": "divider"
                    })

                hotel_options.append(
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "{}. {} - {} {}".format(hotel["index"], hotel["hotel_name"], hotel["curr"], hotel["price"]),
                            "emoji": True
                        },
                        "value": "value-{}".format(hotel["index"]-1)
                    })
                
            hotel_block.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Vote your best hotel choice so everyone can see!"
                    },
                    "accessory": {
                        "type": "static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a hotel",
                            "emoji": True
                        },
                        "options": hotel_options,
                        "action_id": "static_select-action"
                    }
                })
            
            hotel_block.append(
                {
                    "type": "divider"
                })
        
        block_dict["hotel_block"] = hotel_block

        final_block = []

        if(block_dict["flight_block"] != None):
            for i in range(len(block_dict["flight_block"])):
                final_block.append(block_dict["flight_block"][i])
        if(block_dict["hotel_block"] != None):
            for i in range(len(block_dict["hotel_block"])):
                final_block.append(block_dict["hotel_block"][i])
        if(block_dict["restaurant_block"] != None):
            for i in range(len(block_dict["restaurant_block"])):
                final_block.append(block_dict["restaurant_block"][i])

        try:
            if not self.msg['ts'] or (ts_now - self.msg['ts']) > self.msg['timeout']:
                self.msg['str'] = [msg_block]
                self.msg['ts'] = ts_now
            else:
                self.msg['str'].insert(0, msg_block)

            await self.client.web_client.chat_update(
                channel=self.channelID,
                ts=self.msg['id'],
                text="Block message pinned",
                blocks=final_block
            )

        except Exception as e:
            logging.exception(str(repr(e)), exc_info=sys.exc_info())


    async def update_pin_message_block_restaurants(self, msg_block):
        ts_now = datetime.now()

        if(msg_block == "No restaurant offers found."):
            restaurant_block=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "No restaurant offers found.",
                        "emoji": True
                    }
                }]
        else:
            restaurant_block=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Here are some Restaurant Offers",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "These are some great options if you're looking for restaurants:",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "I suggest these top {} restaurants:".format(len(msg_block)),
                        "emoji": True
                    }
                },
                {
                    "type": "divider"
                }]

            restaurants=[]

            # If 5 or more results, show only Top 5
            if len(msg_block) > 4:
                stop = 5
            else: # If less than 3 results
                stop = len(msg_block)

            for index in range(stop):
                restaurants.append(msg_block[index])

            for restaurant in restaurants:                
                restaurant_block.append(
                    {
                        "type": "section",
                        "text": {
                            "text": "{}. {}".format(restaurant["index"], restaurant["restaurant_name"]),
                            "type": "mrkdwn"
                        },
                        "fields": [
                            {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "Number of Reviews: {}".format(restaurant["num_reviews"])
                            },
                            {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "Rating: {}".format(restaurant["rating"])
                            },
                            {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "Ranking: {}".format(restaurant["ranking"])
                            },
                            {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "Price Level: {}".format(restaurant["price_level"])
                            }
                        ]
                    })
                
                restaurant_block.append(
                    {
                        "type": "divider"
                    })
        
        block_dict["restaurant_block"] = restaurant_block

        final_block = []

        if(block_dict["flight_block"] != None):
            for i in range(len(block_dict["flight_block"])):
                final_block.append(block_dict["flight_block"][i])
        if(block_dict["hotel_block"] != None):
            for i in range(len(block_dict["hotel_block"])):
                final_block.append(block_dict["hotel_block"][i])
        if(block_dict["restaurant_block"] != None):
            for i in range(len(block_dict["restaurant_block"])):
                final_block.append(block_dict["restaurant_block"][i])

        try:
            if not self.msg['ts'] or (ts_now - self.msg['ts']) > self.msg['timeout']:
                self.msg['str'] = [msg_block]
                self.msg['ts'] = ts_now
            else:
                self.msg['str'].insert(0, msg_block)

            await self.client.web_client.chat_update(
                channel=self.channelID,
                ts=self.msg['id'],
                text="Block message pinned",
                blocks=final_block
            )

        except Exception as e:
            logging.exception(str(repr(e)), exc_info=sys.exc_info())

    async def reset_pin_message(self):
        block_dict["flight_block"] = None
        block_dict["hotel_block"] = None
        block_dict["restaurant_block"] = None

        try:
            post_msg = "I am listening!"
            self.msg['ts'] = None

            await self.client.web_client.chat_update(
                channel=self.channelID,
                ts=self.msg['id'],
                text=post_msg,
                blocks=[{
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": post_msg,
                        "emoji": True
                    }
                }]
            )
            self.msg['str'] = list()

        except Exception as e:
            logging.exception(str(repr(e)), exc_info=sys.exc_info())

async def main():
    from dotenv import load_dotenv


    load_dotenv()

    # Initialize globals
    SlackClient = Slack()


    # SlackClient.clean_channel()
    res = await SlackClient.client.web_client.chat_postMessage(
        channel=SlackClient.channelID,
        text="dummy text",
        blocks=[
        {
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": "This is a header block",
				"emoji": True
			}
		},
		{
			"type": "section",
			"text": {
				"type": "plain_text",
				"text": "This is a plain text section block.",
				"emoji": True
			}
		},
		{
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"text": "A message *with some bold text* and _some italicized text_.",
				"type": "mrkdwn"
			},
			"fields": [
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				},
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				},
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				},
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				},
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				},
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				}
			]
		},
		{
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"text": "A message *with some bold text* and _some italicized text_.",
				"type": "mrkdwn"
			},
			"fields": [
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				},
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				},
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				},
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				},
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				},
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				}
			]
		},
		{
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"text": "A message *with some bold text* and _some italicized text_.",
				"type": "mrkdwn"
			},
			"fields": [
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				},
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				},
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				},
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				},
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				},
				{
					"type": "plain_text",
					"emoji": True,
					"text": "String"
				}
			]
		},
		{
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "Pick an item from the dropdown list"
			},
			"accessory": {
				"type": "static_select",
				"placeholder": {
					"type": "plain_text",
					"text": "Select an item",
					"emoji": True
				},
				"options": [
					{
						"text": {
							"type": "plain_text",
							"text": "*this is plain_text text*",
							"emoji": True
						},
						"value": "value-0"
					},
					{
						"text": {
							"type": "plain_text",
							"text": "*this is plain_text text*",
							"emoji": True
						},
						"value": "value-1"
					},
					{
						"text": {
							"type": "plain_text",
							"text": "*this is plain_text text*",
							"emoji": True
						},
						"value": "value-2"
					}
				],
				"action_id": "static_select-action"
			}
		},
		{
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": "This is a header block",
				"emoji": True
			}
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "datepicker",
					"initial_date": "1990-04-28",
					"placeholder": {
						"type": "plain_text",
						"text": "Select a date",
						"emoji": True
					},
					"action_id": "actionId-0"
				},
				{
					"type": "datepicker",
					"initial_date": "1990-04-28",
					"placeholder": {
						"type": "plain_text",
						"text": "Select a date",
						"emoji": True
					},
					"action_id": "actionId-1"
				}
			]
		}
        ]
    )
    print(res)

# asyncio.run(main())
if __name__ == '__main__':
    asyncio.run(main())
