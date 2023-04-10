import logging
import os
from slack_sdk.socket_mode.websocket_client import SocketModeClient
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_cleaner2 import *
from datetime import timedelta, datetime
import asyncio

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
            logging.exception(str(repr(e)))
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
            logging.exception(str(repr(e)))

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
            logging.exception(str(repr(e)))

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
            flight1 = msg_block[4]
            flight2 = msg_block[5]
            flight3 = msg_block[6]

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
                },
                {
                    "type": "section",
                    "text": {
                        "text": "{}. {} - {} {}".format(flight1["index"], flight1["carrier"], flight1["curr"], flight1["price"]),
                        "type": "mrkdwn"
                    },
                    "fields": [
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "{} Stops".format(flight1["num_stops"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "{} Available Seats".format(flight1["num_of_seats"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "From: {}".format(flight1["origin"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "To: {}".format(flight1["dest"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Departing: {}".format(flight1["dept_when"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Flight Time: {}".format(flight1["duration"])
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "text": "{}. {} - {} {}".format(flight2["index"], flight2["carrier"], flight2["curr"], flight2["price"]),
                        "type": "mrkdwn"
                    },
                    "fields": [
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "{} Stops".format(flight2["num_stops"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "{} Available Seats".format(flight2["num_of_seats"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "From: {}".format(flight2["origin"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "To: {}".format(flight2["dest"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Departing: {}".format(flight2["dept_when"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Flight Time: {}".format(flight2["duration"])
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "text": "{}. {} - {} {}".format(flight3["index"], flight3["carrier"], flight3["curr"], flight3["price"]),
                        "type": "mrkdwn"
                    },
                    "fields": [
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "{} Stops".format(flight3["num_stops"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "{} Available Seats".format(flight3["num_of_seats"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "From: {}".format(flight3["origin"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "To: {}".format(flight3["dest"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Departing: {}".format(flight3["dept_when"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Flight Time: {}".format(flight3["duration"])
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
                        "text": "Vote your best flight choice so everyone can see!"
                    },
                    "accessory": {
                        "type": "static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a flight",
                            "emoji": True
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "{}. {} - {} {}".format(flight1["index"], flight1["carrier"], flight1["curr"], flight1["price"]),
                                    "emoji": True
                                },
                                "value": "value-0"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "{}. {} - {} {}".format(flight2["index"], flight2["carrier"], flight2["curr"], flight2["price"]),
                                    "emoji": True
                                },
                                "value": "value-1"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "{}. {} - {} {}".format(flight3["index"], flight3["carrier"], flight3["curr"], flight3["price"]),
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
                        "text": "Filter preferred Flight Dates",
                        "emoji": True
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "datepicker",
                            "initial_date": "{}".format(ts_now.date()),
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select a Departure date",
                                "emoji": True
                            },
                            "action_id": "actionId-0"
                        },
                        {
                            "type": "datepicker",
                            "initial_date": "{}".format(ts_now.date()),
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select a Returning date",
                                "emoji": True
                            },
                            "action_id": "actionId-1"
                        }
                    ]
                },
                {
                    "type": "divider"
                }]

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
            logging.exception(str(repr(e)))


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
            hotel1 = msg_block[0]
            hotel2 = msg_block[1]
            hotel3 = msg_block[2]

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
                        "text": "I suggest these top 3 rated hotels:",
                        "emoji": True
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "text": "{}. {} - {} {}".format(hotel1["index"], hotel1["hotel_name"], hotel1["curr"], hotel1["price"]),
                        "type": "mrkdwn"
                    },
                    "fields": [
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "City: {}".format(hotel1["city"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Guests: {}".format(hotel1["guests"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Check In Date: {}".format(hotel1["check_in_date"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Description: {}".format(hotel1["description"])
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "text": "{}. {} - {} {}".format(hotel2["index"], hotel2["hotel_name"], hotel2["curr"], hotel2["price"]),
                        "type": "mrkdwn"
                    },
                    "fields": [
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "City: {}".format(hotel2["city"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Guests: {}".format(hotel2["guests"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Check In Date: {}".format(hotel2["check_in_date"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Description: {}".format(hotel2["description"])
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "text": "{}. {} - {} {}".format(hotel3["index"], hotel3["hotel_name"], hotel3["curr"], hotel3["price"]),
                        "type": "mrkdwn"
                    },
                    "fields": [
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "City: {}".format(hotel3["city"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Guests: {}".format(hotel3["guests"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Check In Date: {}".format(hotel3["check_in_date"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Description: {}".format(hotel3["description"])
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
                        "text": "Vote your best hotel choice so everyone can see!"
                    },
                    "accessory": {
                        "type": "static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a hotel",
                            "emoji": True
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "{}. {} - {} {}".format(hotel1["index"], hotel1["hotel_name"], hotel1["curr"], hotel1["price"]),
                                    "emoji": True
                                },
                                "value": "value-0"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "{}. {} - {} {}".format(hotel2["index"], hotel2["hotel_name"], hotel2["curr"], hotel2["price"]),
                                    "emoji": True
                                },
                                "value": "value-1"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "{}. {} - {} {}".format(hotel3["index"], hotel3["hotel_name"], hotel3["curr"], hotel3["price"]),
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
                        "text": "Filter preferred Hotel Dates",
                        "emoji": True
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "datepicker",
                            "initial_date": "{}".format(ts_now.date()),
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select a Check-in date",
                                "emoji": True
                            },
                            "action_id": "actionId-0"
                        },
                        {
                            "type": "datepicker",
                            "initial_date": "{}".format(ts_now.date()),
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select a Check-out date",
                                "emoji": True
                            },
                            "action_id": "actionId-1"
                        }
                    ]
                },
                {
                    "type": "divider"
                }]
        
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
            logging.exception(str(repr(e)))


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
            restaurant1 = msg_block[0]
            restaurant2 = msg_block[1]
            restaurant3 = msg_block[2]
            restaurant4 = msg_block[3]
            restaurant5 = msg_block[4]

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
                        "text": "I suggest these top 3 restaurants:",
                        "emoji": True
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "text": "{}. {}".format(restaurant1["index"], restaurant1["restaurant_name"]),
                        "type": "mrkdwn"
                    },
                    "fields": [
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Number of Reviews: {}".format(restaurant1["num_reviews"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Rating: {}".format(restaurant1["rating"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Ranking: {}".format(restaurant1["ranking"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Price Level: {}".format(restaurant1["price_level"])
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "text": "{}. {}".format(restaurant2["index"], restaurant2["restaurant_name"]),
                        "type": "mrkdwn"
                    },
                    "fields": [
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Number of Reviews: {}".format(restaurant2["num_reviews"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Rating: {}".format(restaurant2["rating"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Ranking: {}".format(restaurant2["ranking"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Price Level: {}".format(restaurant2["price_level"])
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "text": "{}. {}".format(restaurant3["index"], restaurant3["restaurant_name"]),
                        "type": "mrkdwn"
                    },
                    "fields": [
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Number of Reviews: {}".format(restaurant3["num_reviews"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Rating: {}".format(restaurant3["rating"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Ranking: {}".format(restaurant3["ranking"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Price Level: {}".format(restaurant3["price_level"])
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "text": "{}. {}".format(restaurant4["index"], restaurant4["restaurant_name"]),
                        "type": "mrkdwn"
                    },
                    "fields": [
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Number of Reviews: {}".format(restaurant4["num_reviews"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Rating: {}".format(restaurant4["rating"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Ranking: {}".format(restaurant4["ranking"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Price Level: {}".format(restaurant4["price_level"])
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "text": "{}. {}".format(restaurant5["index"], restaurant5["restaurant_name"]),
                        "type": "mrkdwn"
                    },
                    "fields": [
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Number of Reviews: {}".format(restaurant5["num_reviews"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Rating: {}".format(restaurant5["rating"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Ranking: {}".format(restaurant5["ranking"])
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Price Level: {}".format(restaurant5["price_level"])
                        }
                    ]
                }]
        
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
            logging.exception(str(repr(e)))

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
            logging.exception(str(repr(e)))

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
