import handler.slack as slack
import handler.rasa as rasa
import handler.search as search
import logging
from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest
import asyncio
import os
from dotenv import load_dotenv
import json


async def process(client: SocketModeClient, req: SocketModeRequest):
    if req.type == "events_api":
        # Acknowledge the request anyway
        response = SocketModeResponse(envelope_id=req.envelope_id)
        # Don't forget having await for method calls
        await client.send_socket_mode_response(response)

        if req.payload["event"]["type"] == "message" and "client_msg_id" in req.payload["event"]:
            try:
                msg_text = slack.Slack.parseMessageText(req.payload["event"])
                rasaClient = rasa.Rasa()

                NLP_info_dict = rasaClient.Classify(msg_text)
                if rasaClient.IsTravelIntent(NLP_info_dict):
                    post_msg = "Travel Intent Detected!"
                    await client.web_client.chat_postMessage(
                        channel=os.getenv('SLACK_CHANNEL'),
                        text=post_msg
                    )

                    entity_dict = rasaClient.get_entities(NLP_info_dict)

                    if entity_dict:
                        response = searchClient.search_offers(**entity_dict)
                        if response:
                            post_msg = response
                        else:
                            post_msg = "No flight offers found."

                        await client.web_client.chat_postMessage(
                            channel=os.getenv('SLACK_CHANNEL'),
                            text=post_msg
                        )
                    else:
                        await client.web_client.chat_postMessage(
                            channel=os.getenv('SLACK_CHANNEL'),
                            text=f"Entities missing\n{json.dumps(NLP_info_dict, indent=4)}"
                        )
            except Exception as e:
                logging.exception(str(repr(e)))


# Use async method
async def main():
    load_dotenv()

    slackClient = slack.Slack()

    global searchClient
    searchClient = search.Search()

    # Add a new listener to receive messages from Slack
    # You can add more listeners like this
    slackClient.client.socket_mode_request_listeners.append(process)
    
    # Establish a WebSocket connection to the Socket Mode servers
    await slackClient.client.connect()

    # Just not to stop this process
    await asyncio.sleep(float("inf"))

# You can go with other way to run it. This is just for easiness to try it out.
asyncio.run(main())

