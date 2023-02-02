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


logging.basicConfig(format="%(asctime)s;%(levelname)s;%(message)s")
logger = logging.getLogger("MAIN_CONTROLLER")
logger.setLevel(logging.DEBUG)

entity_state = None
run_search = False
entity_dict = {
    "origin": "Toronto", #default origin to Toronto or current location
    "destination": None,
    "departure_date": None #datetime object
}

async def process(client: SocketModeClient, req: SocketModeRequest):
    global entity_dict, run_search, entity_state
    
    if req.type == "events_api":
        # Acknowledge the request anyway
        response = SocketModeResponse(envelope_id=req.envelope_id)
        # Don't forget having await for method calls
        await client.send_socket_mode_response(response)

        if req.payload["event"]["type"] == "message" and "client_msg_id" in req.payload["event"]:
            try:
                msg_text = slack.Slack.parseMessageText(req.payload["event"])
                logger.debug(f"Msg received '{msg_text}'!")
                
                rasaClient = rasa.Rasa()
                rasaClient.Classify(msg_text)
                print(rasaClient.NLP_dict)
                entity_dict, entity_state, run_search = rasaClient.get_entities(entity_dict, entity_state)
                print("entity dict: ", entity_dict)
                print("run search: ", run_search)
                if run_search:
                    response = searchClient.search_flights(**entity_dict)
                    if response:
                        post_msg = response
                    else:
                        post_msg = "No flight offers found."

                    await client.web_client.chat_postMessage(
                        channel=os.getenv('SLACK_CHANNEL'),
                        text=post_msg
                    )
            except Exception as e:
                logger.exception(str(repr(e)))


# Use async method
async def main():
    load_dotenv()

    slackClient = slack.Slack()
    slackClient.clean_channel()
    await slackClient.post_message("I am listening!")

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

