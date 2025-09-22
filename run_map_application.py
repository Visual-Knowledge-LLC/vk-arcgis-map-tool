import os
import sys
import argparse
import bbb

# Parse command line arguments
parser = argparse.ArgumentParser(description='VK BBB Partner API Tool')
parser.add_argument('--no-slack', action='store_true', help='Disable Slack notifications')
parser.add_argument('--skip-processed', action='store_true', help='Skip BBBs that already have output files')
parser.add_argument('--bbb-ids', nargs='+', help='Process only specific BBB IDs (e.g., --bbb-ids 1126 0995)')
args = parser.parse_args()

# Set environment variable for Slack notifications
if args.no_slack:
    os.environ['DISABLE_SLACK'] = '1'
    print("Slack notifications disabled")
    slack = None
else:
    from vk_api_utils import SlackNotifier
    slack = SlackNotifier("GIS Mapping Application")
    # Start execution with threaded messaging
    try:
        slack.notify_start()
    except Exception as e:
        print(f"Warning: Failed to start Slack thread: {e}")
        print("Continuing without Slack notifications...")
        slack = None

script_name = ''

try:
    # Post ArcGIS data
    script_name = "bbb.py"
    if slack:
        try:
            slack.notify_progress("Running BBB data collection and mapping")
        except:
            pass

    # Pass arguments to the main function
    bbb.run_mapping_application(
        skip_processed=args.skip_processed,
        specific_bbb_ids=args.bbb_ids
    )

    # Success notification in thread
    if slack:
        try:
            slack.notify_success("Completed successfully")
        except:
            pass

except Exception as error_message:
    # Error notification in thread
    if slack:
        try:
            slack.notify_error(f"Failed to run {script_name}: {str(error_message)}")
        except:
            pass
    print(f'Error: {script_name}, {error_message}')
    exit(1)