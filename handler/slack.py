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
        return result

    @staticmethod
    def parseLatestMessageText(data):
        try:
            # first message is the latest message
            return data["messages"][0]['text']
        except:
            logging.exception("Error: couldn't parse slack message")
