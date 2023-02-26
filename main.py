import handler.slack as slack
import handler.rasa as rasa
import handler.search as search
import models.state as state
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


async def process(client: SocketModeClient, req: SocketModeRequest):
    global entity_dict, run_search, entity_state
    
    if req.type == "events_api":
        # Acknowledge the request anyway
        response = SocketModeResponse(envelope_id=req.envelope_id)
        # Don't forget having await for method calls
        await client.send_socket_mode_response(response)

        if req.payload["event"]["type"] == "message" and "client_msg_id" in req.payload["event"]:
            try:
                # Receive message
                msg_text = slack.Slack.parseMessageText(req.payload["event"])
                logger.debug(f"Msg received '{msg_text}'!")

                # Get intent and entities
                RasaClient.get_entities


            except Exception as e:
                pass




# Use async method
async def main():
    load_dotenv()

    # Initialize globals
    global SearchClient, RasaClient, StateContext, SlackClient
    RasaClient = rasa.Rasa()
    SlackClient = slack.Slack()
    StateContext = state.State()
    SearchClient = search.Search()


    SlackClient.clean_channel()
    await SlackClient.post_message("I am listening!")

    # Add a new listener to receive messages from Slack
    # You can add more listeners like this
    SlackClient.client.socket_mode_request_listeners.append(process)
    
    # Establish a WebSocket connection to the Socket Mode servers
    await SlackClient.client.connect()

    # Just not to stop this process
    await asyncio.sleep(float("inf"))

asyncio.run(main())