import logging
import os
from slack_sdk.socket_mode.websocket_client import SocketModeClient
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.aiohttp import SocketModeClient
        

class Slack:
    def __init__(self):
        self.token = os.getenv('SLACK_TOKEN')
        self.app_token = os.getenv('SLACK_APP_TOKEN')
        self.channelID = os.getenv('SLACK_CHANNEL')
        self.client = SocketModeClient(
                        app_token=self.app_token, 
                        web_client=AsyncWebClient(token=self.token)
                    )

    def Print(self):
        print(self.token)
        print(self.channelID)

    #function not needed anymore
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

    def post_message(self, msg):
        try:
            self.client.web_client.chat_postMessage(
                channel=os.getenv('SLACK_CHANNEL'),
                text=msg
            )
        except Exception as e:
            logging.exception(str(repr(e)))
