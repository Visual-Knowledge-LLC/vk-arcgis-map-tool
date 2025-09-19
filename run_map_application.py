import bbb
from vk_api_utils import SlackNotifier

slack = SlackNotifier("GIS Mapping Application")

# Run start execution slack message
slack.send_message("Started")

script_name = ''

try:
    # Post ArcGIS data
    script_name = "bbb.py"
    bbb.run_mapping_application()

except Exception as error_message:
    slack.send_error(f"Failed to run {script_name} with error: {str(error_message)}")
    print(f'Error: {script_name}, {error_message}')
    exit(0)

# Run end execution slack message
slack.send_message("Completed")