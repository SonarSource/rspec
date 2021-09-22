import os
from slack import WebClient
from slack.errors import SlackApiError

def notify_slack(msg):
  slack_token=os.environ.get('SLACK_API_TOKEN','no slack token in env')
  slack_client=WebClient(slack_token)
  slack_channel=os.environ.get('INPUT_SLACK_CHANNEL')
  if slack_channel is not None:
    try:
      return slack_client.chat_postMessage(
        channel=slack_channel,
        text=msg)
    except SlackApiError as e:
      print(f"Could not notify slack: {e.response['error']}")

print('ERROR: failed to update rule coverage')
print(os.environ.get('GITHUB_RUN_ID'))
print('https://github.com/SonarSource/rspec/actions/runs/' + os.environ.get('GITHUB_RUN_ID'))
# notify_slack('ERROR: failed to update rule coverage.\n' +
#              'See https://github.com/SonarSource/rspec/actions/workflows/update_coverage.yml')
