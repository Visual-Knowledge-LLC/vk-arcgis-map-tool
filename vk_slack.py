import requests
import json


class SlackNotifier:
    @staticmethod
    def send_post_request(url, data):
        response = requests.post(url, data=json.dumps(data))
        if response.status_code == 200:
            print('Slack message sent successfully')
        else:
            print('Failed to send Slack message. Status code: ' + str(response.status_code) + ' Response: ' + response.text)

    @staticmethod
    def send_message(tool_name, status):
        # Define the webhook URL
        url = 'https://hooks.zapier.com/hooks/catch/10499731/3fnckuh/'
        # Define the data you want to send
        data = {
            'tool_name': str(tool_name),
            'status': str(status)
        }
        # Send the POST request
        SlackNotifier.send_post_request(url, data)

    @staticmethod
    def send_error(tool_name, error_message):
        # Define the webhook URL
        url = 'https://hooks.zapier.com/hooks/catch/10499731/3fnlr38/'
        # Define the data you want to send
        data = {
            'tool_name': str(tool_name),
            'error': str(error_message)
        }
        # Send the POST request
        SlackNotifier.send_post_request(url, data)
