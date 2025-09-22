#!/usr/bin/env python3
"""Check the status of BBB processing"""

import os
import csv

def check_bbb_status():
    """Check which BBBs are ready to process and which have been processed"""

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Read BBB IDs from CSV
    bbb_ids = []
    bbb_names = []
    bbb_id_path = os.path.join(script_dir, 'bbb_ids', 'bbb_ids.csv')

    with open(bbb_id_path, "r") as f:
        reader = csv.reader(f)
        for line in reader:
            if len(line) >= 3:
                bbb_id = line[0].strip()
                bbb_name = line[2].strip()
                if bbb_id:
                    bbb_ids.append(bbb_id.zfill(4))
                    bbb_names.append(bbb_name)

    print("="*60)
    print("BBB Processing Status Check")
    print("="*60)
    print()

    ready_to_process = []
    missing_zips = []
    already_processed = []

    for i, bbb_id in enumerate(bbb_ids):
        bbb_name = bbb_names[i]

        # Check zip file
        zip_file = os.path.join(script_dir, "zips", f"{bbb_id}_zips.csv")
        has_zip = os.path.exists(zip_file)

        # Check if processed
        results_file = os.path.join(script_dir, "results", f"{bbb_id}.csv")
        is_processed = os.path.exists(results_file)

        status = []
        if has_zip:
            status.append("✓ Has Zip")
        else:
            status.append("✗ No Zip")
            missing_zips.append(f"{bbb_id} ({bbb_name})")

        if is_processed:
            status.append("✓ Processed")
            already_processed.append(f"{bbb_id} ({bbb_name})")
        else:
            status.append("○ Not Processed")

        if has_zip and not is_processed:
            ready_to_process.append(f"{bbb_id} ({bbb_name})")

        print(f"{bbb_id} ({bbb_name:20s}): {' | '.join(status)}")

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    print(f"\nTotal BBBs: {len(bbb_ids)}")
    print(f"Ready to Process: {len(ready_to_process)}")
    print(f"Already Processed: {len(already_processed)}")
    print(f"Missing Zip Files: {len(missing_zips)}")

    if ready_to_process:
        print("\n📋 Ready to Process:")
        for bbb in ready_to_process:
            print(f"  - {bbb}")

    if missing_zips:
        print("\n⚠️  Missing Zip Files:")
        for bbb in missing_zips:
            print(f"  - {bbb}")

    if already_processed:
        print("\n✅ Already Processed:")
        for bbb in already_processed:
            print(f"  - {bbb}")

    # Suggest commands
    if ready_to_process:
        print("\n" + "="*60)
        print("SUGGESTED COMMANDS")
        print("="*60)

        ready_ids = [bbb.split()[0] for bbb in ready_to_process]

        print("\nProcess all ready BBBs (without Slack):")
        print(f"  python3 run_map_application.py --no-slack --bbb-ids {' '.join(ready_ids)}")

        print("\nProcess all ready BBBs (with Slack):")
        print(f"  python3 run_map_application.py --bbb-ids {' '.join(ready_ids)}")

        if len(ready_ids) > 0:
            print(f"\nProcess just the first ready BBB:")
            print(f"  python3 run_map_application.py --no-slack --bbb-ids {ready_ids[0]}")

if __name__ == "__main__":
    check_bbb_status()