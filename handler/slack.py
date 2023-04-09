import logging
import os
from slack_sdk.socket_mode.websocket_client import SocketModeClient
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_cleaner2 import *
from datetime import timedelta, datetime
import asyncio


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

    async def update_pin_message_block(self, msg_block):
        try:
            ts_now = datetime.now()
            if not self.msg['ts'] or (ts_now - self.msg['ts']) > self.msg['timeout']:
                self.msg['str'] = [msg_block]
                self.msg['ts'] = ts_now
            else:
                self.msg['str'].insert(0, msg_block)

            await self.client.web_client.chat_update(
                channel=self.channelID,
                ts=self.msg['id'],
                text="Block message failed",
                blocks=self.msg['str']
            )

        except Exception as e:
            logging.exception(str(repr(e)))

    async def reset_pin_message(self):
        try:
            post_msg = "I am listening!"
            self.msg['ts'] = None

            await self.client.web_client.chat_update(
                channel=self.channelID,
                ts=self.msg['id'],
                text=post_msg
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
