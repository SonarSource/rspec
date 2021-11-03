import os
from slack import WebClient
from slack.errors import SlackApiError

def notify_slack(msg, slack_channel):
  slack_token=os.environ.get('SLACK_API_TOKEN','no slack token in env')
  slack_client=WebClient(slack_token)
  if slack_channel is not None:
    try:
      return slack_client.chat_postMessage(
        channel=slack_channel,
        text=msg)
    except SlackApiError as e:
      print(f"Could not notify slack: {e.response['error']}")
