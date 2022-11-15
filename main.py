import handler.slack as slack
import handler.rasa as rasa
import requests
import json


def main():
    slackClient = slack.Slack()
    msg = slackClient.GetMessages()

    for text in msg:
        # msgText = slackClient.parseLatestMessageText(text)
        msgText = slackClient.parseMessageText(text)
        if not msgText: continue
        
        print("Latest Slack message: " + msgText)
        
        rasaClient = rasa.Rasa()
        print("Travel intent detected: " + str(rasaClient.IsTravelIntent(rasaClient.Classify(msgText))))

if __name__ == '__main__':
    main()
