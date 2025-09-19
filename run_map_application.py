import bbb
from vk_api_utils import SlackNotifier

slack = SlackNotifier("GIS Mapping Application")

# Start execution with threaded messaging
slack.notify_start()

script_name = ''

try:
    # Post ArcGIS data
    script_name = "bbb.py"
    slack.notify_progress("Running BBB data collection and mapping")
    bbb.run_mapping_application()

    # Success notification in thread
    slack.notify_success("Completed successfully")

except Exception as error_message:
    # Error notification in thread
    slack.notify_error(f"Failed to run {script_name}: {str(error_message)}")
    print(f'Error: {script_name}, {error_message}')
    exit(1)