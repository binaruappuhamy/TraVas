import logging
import json
import time
import os
import slack_sdk
from dotenv import load_dotenv


class Slack:
    def __init__(self):
        load_dotenv()
        self.token = os.getenv('SLACK_TOKEN')
        self.channelID = os.getenv('SLACK_CHANNEL')
        self.client = slack_sdk.WebClient(token=self.token)

    def Print(self):
        print(self.token)
        print(self.channelID)

    def GetMessages(self):
        result = self.client.conversations_history(
            channel=self.channelID, oldest="1668389600")

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
                try:
                    # processed_text = msg["blocks"][0]["elements"][0]["elements"][1]["text"]
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
                except KeyError:
                    pass
            
        except:
            logging.exception("Unhandled Error")
        else:
            return processed_text
