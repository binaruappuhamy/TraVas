import logging
import json
import time
from slack import WebClient
from slack.errors import SlackApiError
from slack.errors import SlackApiError


logging.basicConfig(level=logging.DEBUG)

# {
#   "client_msg_id": "68ce57ea-db3f-4693-89b5-672059748839",
#   "type": "message",
#   "text": ":wave: Hello, team!",
#   "user": "U047CP2CQVA",
#   "ts": "1666227146.764309",
#   "blocks": [
#     {
#       "type": "rich_text",
#       "block_id": "HWqjJ",
#       "elements": [
#         {
#           "type": "rich_text_section",
#           "elements": [
#             {
#               "type": "emoji",
#               "name": "wave",
#               "unicode": "1f44b"
#             },
#             {
#               "type": "text",
#               "text": " Hello, team!"
#             }
#           ]
#         }
#       ]
#     }
#   ],
#   "team": "T04307JR119"
# }
def get_msgs(from_ts, conv_hist):
    bot_token = "xoxb-4102256851043-4315618939303-Y8BKvWnemlsGRcna7F5NCmrB"
    client = WebClient(token=bot_token)
    channel_id = "C0430AXSH1Q"
    result = client.conversations_history(channel=channel_id, oldest=from_ts)

    for msg in result["messages"]:
        if "client_msg_id" in msg:
            payload_dict = dict()

            ts = msg["ts"]
            if ts > from_ts:
                from_ts = ts
            payload_dict["timestamp"] = ts

            raw_msg_text = None
            processed_text = None
            if "text" in msg:
                raw_msg_text = msg["text"]
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
            
            if raw_msg_text or processed_text:
                if raw_msg_text:
                    payload_dict["text"] = raw_msg_text
                if processed_text:
                    payload_dict["text"] = processed_text

                conv_hist[msg["client_msg_id"]] = payload_dict

    return from_ts, conv_hist

def main():
    latest_ts = "0"
    conv_hist = dict()
    time_interval = 1*60
    cur_time = 61


    try:
        while True:
            if cur_time > time_interval:
                cur_time = 0
                latest_ts, conv_hist = get_msgs(latest_ts, conv_hist)
                print("*"*100)
                logging.info(json.dumps(conv_hist, indent=4))
                print("*"*100)
            else:
                cur_time+=1
                time.sleep(1)
    except Exception as e:
        logging.error(repr(e))


if __name__ == '__main__':
    main()



