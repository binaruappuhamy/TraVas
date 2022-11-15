import handler.slack as slack
import handler.rasa as rasa
import requests
import json


def main():
    slackClient = slack.Slack()
    msg = slackClient.GetMessages()
    msgText = slackClient.parseLatestMessageText(msg)
    print("Latest Slack message: " + msgText)
    
    rasaClient = rasa.Rasa()
    print("Travel intent detected: " + str(rasaClient.IsTravelIntent(rasaClient.Classify(msgText))))

if __name__ == '__main__':
    main()
