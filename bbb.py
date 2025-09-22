import os
import csv
import math
import json
import random
import requests
from arcgis.gis import GIS
from progress.bar import Bar
from arcgis.features import FeatureLayerCollection
from api import make_api_request_with_retry

def fetch_bbb_ids(skip=False):
    """Fetch BBB IDs and names from CSV file
    
    Args:
        skip (bool): Whether to skip this step
        
    Returns:
        tuple: (bbb_ids, bbb_names) lists
    """
    if skip:
        print("SKIPPING: Fetch BBB IDs")
        return [], []
        
    print("STARTING: Fetch BBB IDs from CSV")
    bbb_ids = []
    bbb_names = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bbb_id_path = os.path.join(script_dir, 'bbb_ids', 'bbb_ids.csv')
    
    with open(bbb_id_path, "r") as bbb_id_csv_file:
        bbb_id_csv_reader = csv.reader(bbb_id_csv_file)
        for line in bbb_id_csv_reader:
            csv_bbb_id = line[0]
            csv_bbb_name = line[2]
            if "\ufeff" in csv_bbb_id:
                csv_bbb_id = csv_bbb_id[1:]
            if "\ufeff" in csv_bbb_name:
                csv_bbb_name = csv_bbb_name[1:]

            csv_bbb_id = str(csv_bbb_id).zfill(4)
            bbb_ids.append(csv_bbb_id)
            bbb_names.append(csv_bbb_name)
    
    print(f"COMPLETED: Fetched {len(bbb_ids)} BBB IDs")
    return bbb_ids, bbb_names

def fetch_zip_codes(bbb_id, skip=False):
    """Fetch zip codes for a specific BBB ID
    
    Args:
        bbb_id (str): BBB ID to fetch zip codes for
        skip (bool): Whether to skip this step
        
    Returns:
        list: List of zip codes
    """
    if skip:
        print(f"SKIPPING: Fetch zip codes for {bbb_id}")
        return []
        
    print(f"STARTING: Fetch zip codes for {bbb_id}")
    zip_codes = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    zips_dir = os.path.join(script_dir, "zips")
    
    with open(os.path.join(zips_dir, bbb_id + "_zips.csv"), "r") as zip_csv_file:
        zip_csv_reader = csv.reader(zip_csv_file)
        for line in zip_csv_reader:
            zip_code = line[0]

            if len(line) == 2:
                zip_code = line[1]
            
            zip_codes.append(zip_code)
    
    print(f"COMPLETED: Fetched {len(zip_codes)} zip codes for {bbb_id}")
    return zip_codes

def determine_is_blue(bbb_id, skip=False):
    """Determine if BBB is 'Blue' or 'Hurdman'
    
    Args:
        bbb_id (str): BBB ID to check
        skip (bool): Whether to skip this step
        
    Returns:
        bool: True if Blue, False if Hurdman
    """
    if skip:
        print(f"SKIPPING: Determine if {bbb_id} is Blue")
        return True  # Default to Blue if skipped
        
    print(f"STARTING: Determine if {bbb_id} is Blue")
    is_blue = True
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bbb_id_path = os.path.join(script_dir, 'bbb_ids', 'bbb_ids.csv')
    
    with open(bbb_id_path, "r") as bbb_id_csv_file:
        bbb_id_csv_reader = csv.reader(bbb_id_csv_file)
        for line in bbb_id_csv_reader:
            csv_bbb_id = line[0]
            blue_or_hurdman = line[1].strip()

            csv_bbb_id = str(csv_bbb_id).zfill(4)

            # gets rid of all whitespace
            new_bbb_id = ""
            for c in csv_bbb_id:
                if c.isdigit():
                    new_bbb_id += c
            csv_bbb_id = new_bbb_id

            if bbb_id == csv_bbb_id:
                if blue_or_hurdman == "Blue":
                    is_blue = True
                else:
                    is_blue = False
                break
    
    print(f"COMPLETED: {bbb_id} is {'Blue' if is_blue else 'Hurdman'}")
    return is_blue

def fetch_api_data(bbb_id, bbb_name, zip_codes, skip=False):
    """Fetch data from the BBB API
    
    Args:
        bbb_id (str): BBB ID to fetch data for
        bbb_name (str): BBB name for display purposes
        zip_codes (list): List of zip codes to filter results by
        skip (bool): Whether to skip this step
        
    Returns:
        str: Path to results CSV file, or None if skipped
    """
    if skip:
        print(f"SKIPPING: API data fetch for {bbb_id}")
        return None
        
    print(f"STARTING: API data fetch for {bbb_id} ({bbb_name})")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "results")
    results_path = os.path.join(results_dir, bbb_id + ".csv")
    
    token = "Bearer 901-oMnw8jzZg0WVOvf8wjWngb8/ms7i1lLilyG4U+x7kLc="
    pageSize = "250"
    zip_filtered_count = 0
    
    # Create initial CSV file
    with open(results_path, "w", newline='', encoding='utf-8') as bbb_file:
        bbb_csv_writer = csv.writer(bbb_file)

        # header row
        bbb_csv_writer.writerow(["Business Name","BBB Rating","Accredited","Category","BBB Profile URL","Owner Name","Owner Email","Phone Number","Address","City","State","Zip Code","BBB ID","Business ID","Business Start Date","Accreditation Date","Accreditation Status Last Changed","Website","Latitude","Longitude","License Agency Name","License Agency URL","License Number","License Issue Date", "License Expiration Date", "License Suspension Date", "License Revocation Date", "License Status ID", "License Status"])

        # Updated API URL structure for V2
        url = f"https://api.bbb.org/v2/orgs/search?PageSize=1&PageNumber=1&BbbId={bbb_id}"
        
        # Initial API call to get pagination info
        headers = {"Authorization": token, "accept": "application/json"}
        response = make_api_request_with_retry(url=url, headers=headers, max_retries=3, base_timeout=30)
        
        try:
            responseJSON = response.json()
        except Exception as e:
            print(f"Error parsing JSON response for {bbb_id}: {str(e)}")
            print(response.text)
            return None
            
        # Get pagination details from API
        totalRecords = responseJSON["totalResults"]
        pageTurns = math.ceil(responseJSON["totalResults"] / int(pageSize))
        
        print(f"Found {totalRecords} records across {pageTurns} pages")

        # Setup progress bar
        bar = Bar("Processing", max=pageTurns, suffix="%(index)d / %(max)d - %(percent).1f%% - %(eta_td)s remaining")

        # Fetch and process all pages
        for pageNumber in range(0, pageTurns):
            try:
                # Construct URL for this page
                url = f"https://api.bbb.org/v2/orgs/search?PageSize={pageSize}&PageNumber={pageNumber+1}&BbbId={bbb_id}"

                # Make API request with retry logic
                response = make_api_request_with_retry(url=url, headers=headers, max_retries=3, base_timeout=30)
                
                if response.status_code != 200:
                    print(f"Error: Status code {response.status_code}")
                    print(response.text)
                    bar.next()
                    continue
                    
                try:
                    responseJSON = response.json()
                except Exception as e:
                    print(f"Error parsing JSON response for {bbb_id}, page {pageNumber+1}: {str(e)}")
                    print(response.text)
                    bar.next()
                    continue
                
                # Get businesses from API response
                results = responseJSON["searchResults"]

                for result in results:
                    # Process each business record
                    name = result["organizationName"]
                    if name:
                        name = name.replace(',','')

                    rating = result["bbbRating"]
                    accredited = result["isBBBAccredited"]
                    category = result["primaryCategory"] 
                    profileURL = result["profileUrl"] 

                    license_details = ""
                    license_number = ""
                    license_issue_date = ""
                    license_expiration_date = ""
                    license_suspension_date = ""
                    license_revocation_date = ""
                    license_agency_name = ""
                    license_agency_url = ""
                    license_status_id = ""
                    license_status_string = ""

                    try:
                        # V2 API returns an array of licenseDetails
                        if "licenseDetails" in result and result["licenseDetails"] and len(result["licenseDetails"]) > 0:
                            license_details = result["licenseDetails"][0]
                            license_number = license_details["licenseNumber"]
                            license_issue_date = license_details["issueDate"]
                            license_expiration_date = license_details["expirationDate"]
                            license_suspension_date = license_details["suspensionDate"]
                            license_revocation_date = license_details["revocationDate"]
                            license_agency_name = license_details["licenseAgencyName"]
                            license_agency_url = license_details["detailsUrl"]
                            license_status_id = str(license_details["licenseStatusId"])

                            if license_status_id == "3902":
                                license_status_string = "Active"
                            elif license_status_id == "3903":
                                license_status_string = "Expired"
                            elif license_status_id == "3904":
                                license_status_string = "Suspended"
                            elif license_status_id == "3905":
                                license_status_string = "Revoked"
                            elif license_status_id == "3906":
                                license_status_string = "Inactive"
                            else:
                                license_status_string = "Unknown"
                    except Exception as e:
                        # Reset license details on error
                        license_details = ""
                        license_number = ""
                        license_issue_date = ""
                        license_expiration_date = ""
                        license_suspension_date = ""
                        license_revocation_date = ""
                        license_agency_name = ""
                        license_agency_url = ""
                        license_status_id = ""
                        license_status_string = ""

                    latitude = ""
                    longitude = ""
                    try:
                        lat_long = result["latLng"]
                        lat_long_array = lat_long.split(',')
                        latitude = lat_long_array[0]
                        longitude = lat_long_array[1]
                    except:
                        latitude = ""
                        longitude = ""

                    # handling empty ratings
                    if rating == "" or rating == "NA":
                        rating = "NR"

                    # these try except blocks prevents any errors from crashing our program
                    ownerName = ""
                    try:
                        ownerName = result["contactFirstName"] + " " + result["contactLastName"]
                    except:
                        ownerName = ""

                    ownerEmail = ""
                    try:
                        ownerEmail = result["contactEmailAddress"][0] if result["contactEmailAddress"] else ""
                    except:
                        ownerEmail = ""

                    phoneNumber = ""
                    try:
                        phoneNumber = result["phones"][0] if result["phones"] else ""
                    except:
                        phoneNumber = ""

                    address = result["address"]
                    city = result["city"]
                    state = result["stateProvince"]

                    zipCode = ""
                    try:
                        zipCode = result["postalCode"][:5]
                    except:
                        zipCode = ""

                    bbbID = ""
                    try:
                        bbbID = result["bbbId"]
                    except:
                        bbbID = ""

                    businessID = ""
                    try:
                        businessID = result["businessId"]
                    except:
                        businessID = ""

                    businessStartDate = ""
                    try:
                        businessStartDate = result["dateBusinessStarted"]
                    except:
                        businessStartDate = ""

                    accreditationDate = ""
                    try:
                        accreditationDate = result["accreditationDate"]
                    except:
                        accreditationDate = ""

                    accreditationChangeDate = ""
                    try:
                        accreditationChangeDate = result["accreditationStatusLastChanged"]
                    except:
                        accreditationChangeDate = ""

                    if accredited == True:
                        accredited = "Accredited"
                    if accredited == False:
                        accredited = "Not Accredited"

                    website = ""
                    try:
                        website = result["businessURLs"][0] if result["businessURLs"] else ""
                    except:
                        website = ""

                    # only add the business if it's in our zip codes list
                    if zipCode in zip_codes:
                        try:
                            row = [str(item).replace('\0', '') if item is not None else "" for item in [name,rating,accredited,category,profileURL,ownerName,ownerEmail,phoneNumber,address,city,state,zipCode,bbbID,businessID,businessStartDate,accreditationDate,accreditationChangeDate,website,latitude,longitude,license_agency_name,license_agency_url,license_number,license_issue_date,license_expiration_date,license_suspension_date,license_revocation_date,license_status_id,license_status_string]]
                            bbb_csv_writer.writerow(row)
                            zip_filtered_count += 1
                        except Exception as e:
                            print(f"Error writing row: {str(e)}")
                            continue

            except Exception as e:
                print(f"Error processing page {pageNumber+1}: {str(e)}")
                bar.next()
                continue

            bar.next()
        bar.finish()
    
    print(f"COMPLETED: API data fetch with {zip_filtered_count} filtered records")
    return results_path

def process_and_write_results(bbb_id, results_path, is_blue, skip=False):
    """Process results and write to various CSV files
    
    Args:
        bbb_id (str): BBB ID being processed
        results_path (str): Path to results CSV file
        is_blue (bool): Whether this BBB is Blue or Hurdman
        skip (bool): Whether to skip this step
        
    Returns:
        bool: Success status
    """
    if skip:
        print(f"SKIPPING: Process and write results for {bbb_id}")
        return True
        
    if results_path is None:
        print(f"ERROR: Cannot process results for {bbb_id}, no results file")
        return False
        
    print(f"STARTING: Process and write results for {bbb_id}")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    uploads_dir = os.path.join(script_dir, "uploads")
    
    with open(os.path.join(uploads_dir, bbb_id + "_accredited.csv"), "w+", newline='', encoding='utf-8') as accredited_file, \
        open(os.path.join(uploads_dir, bbb_id + "_accredited_but_not_rated.csv"), "w+", newline='', encoding='utf-8') as accredited_but_not_rated_file, \
        open(os.path.join(uploads_dir, bbb_id + "_rated_but_not_accredited.csv"), "w+", newline='', encoding='utf-8') as rated_but_not_accredited_file, \
        open(os.path.join(uploads_dir, bbb_id + "_not_rated_and_not_accredited.csv"), "w+", newline='', encoding='utf-8') as not_rated_and_not_accredited_file, \
        open(os.path.join(uploads_dir, bbb_id + "_contractors_rated_but_not_accredited.csv"), "w+", newline='', encoding='utf-8') as contractors_rated_but_not_accredited_file, \
        open(os.path.join(uploads_dir, bbb_id + "_contractors_not_rated.csv"), "w+", newline='', encoding='utf-8') as contractors_not_rated_file, \
        open(os.path.join(uploads_dir, bbb_id + "_licensed_records.csv"), "w+", newline='', encoding='utf-8') as licensed_records_file, \
        open(os.path.join(uploads_dir, bbb_id + "_licensed_inactive_records.csv"), "w+", newline='', encoding='utf-8') as licensed_inactive_records_file, \
        open(os.path.join(uploads_dir, bbb_id + "_licensed_accredited_records.csv"), "w+", newline='', encoding='utf-8') as licensed_accredited_records_file:
        
        accredited_writer = csv.writer(accredited_file)
        accredited_but_not_rated_writer = csv.writer(accredited_but_not_rated_file)
        rated_but_not_accredited_writer = csv.writer(rated_but_not_accredited_file)
        not_rated_and_not_accredited_writer = csv.writer(not_rated_and_not_accredited_file)
        contractors_rated_but_not_accredited_writer = csv.writer(contractors_rated_but_not_accredited_file)
        contractors_not_rated = csv.writer(contractors_not_rated_file)
        licensed_records_writer = csv.writer(licensed_records_file)
        licensed_inactive_records_writer = csv.writer(licensed_inactive_records_file)
        licensed_accredited_records_writer = csv.writer(licensed_accredited_records_file)

        i = 0
        with open(results_path, "r", encoding='utf-8') as geocoded_file:
            bbb_geocoded_reader = csv.reader(geocoded_file)
            for line in bbb_geocoded_reader:
                # Skip empty lines
                if not line:
                    continue
                    
                # remove address
                del line[8:12]

                if i == 0:
                    if is_blue:
                        line.insert(4, "Blue Profile URL")
                    else:
                        line.insert(4, "Hurdman Profile URL")
                    accredited_writer.writerow(line)
                    accredited_but_not_rated_writer.writerow(line)
                    rated_but_not_accredited_writer.writerow(line)
                    not_rated_and_not_accredited_writer.writerow(line)
                    contractors_rated_but_not_accredited_writer.writerow(line)
                    contractors_not_rated.writerow(line)
                    licensed_records_writer.writerow(line)
                    licensed_inactive_records_writer.writerow(line)
                    licensed_accredited_records_writer.writerow(line)
                    i += 1
                    continue

                # adding profile url
                blue_url = ""
                hurdman_url = ""
                try:
                    business_id = line[9]
                except IndexError:
                    print(f"Warning: Line doesn't have enough elements: {line}")
                    continue

                if is_blue:
                    blue_base_url = "https://bluebbb.org/core/manage/?firm="
                    blue_url = blue_base_url + business_id
                else:
                    hurdman_base_url = "https://lubbockweb.ebindr.com/ebindr/#"
                    hurdman_url = hurdman_base_url + business_id

                if is_blue:
                    line.insert(4, blue_url)
                else:
                    line.insert(4, hurdman_url)

                try:
                    rating = line[1]
                    accredited = line[2]
                    category = line[3]
                    license_id = line[19]
                    license_status_string = line[25]
                except IndexError:
                    print(f"Warning: Line doesn't have enough elements after insert: {line}")
                    continue

                is_rated = False
                is_accredited = False
                is_contractor = False
                is_licensed = False

                if rating != "NR":
                    is_rated = True

                if accredited == "Accredited":
                    is_accredited = True

                if "contractor" in category.lower():
                    is_contractor = True

                if license_id != "":
                    is_licensed = True

                if is_accredited:
                    accredited_writer.writerow(line)

                if is_accredited and not is_rated:
                    accredited_but_not_rated_writer.writerow(line)

                if is_rated and not is_accredited:
                    rated_but_not_accredited_writer.writerow(line)

                if not is_accredited and not is_rated:
                    not_rated_and_not_accredited_writer.writerow(line)

                if is_contractor and is_rated and not is_accredited:
                    contractors_rated_but_not_accredited_writer.writerow(line)

                if is_contractor and not is_rated:
                    contractors_not_rated.writerow(line)

                if is_licensed and is_accredited and license_status_string == "Active":
                    licensed_accredited_records_writer.writerow(line)
                elif is_licensed and license_status_string == "Active":
                    licensed_records_writer.writerow(line)
                elif is_licensed and license_status_string != "Active":
                    licensed_inactive_records_writer.writerow(line)
    
    print(f"COMPLETED: Process and write results for {bbb_id}")
    return True

def upload_to_arcgis(bbb_id, skip=False):
    """Upload CSV files to ArcGIS
    
    Args:
        bbb_id (str): BBB ID to upload data for
        skip (bool): Whether to skip this step
        
    Returns:
        bool: Success status
    """
    if skip:
        print(f"SKIPPING: ArcGIS upload for {bbb_id}")
        return True
        
    print(f"STARTING: ArcGIS upload for {bbb_id}")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    uploads_dir = os.path.join(script_dir, "uploads")
    
    url = "https://visual-knowledge.maps.arcgis.com/"
    username = "visualknowledge"
    password = "McKenzie123!!"

    try:
        gis = GIS(url, username, password)
    except Exception as e:
        print(f"Error connecting to ArcGIS: {str(e)}")
        return False

    titles = [
        bbb_id+"_accredited", 
        bbb_id+"_accredited_but_not_rated", 
        bbb_id+"_rated_but_not_accredited", 
        bbb_id+"_not_rated_and_not_accredited", 
        bbb_id+"_contractors_rated_but_not_accredited", 
        bbb_id+"_contractors_not_rated", 
        bbb_id+"_licensed_records", 
        bbb_id+"_licensed_inactive_records", 
        bbb_id+"_licensed_accredited_records"
    ]

    try:
        search_results = gis.content.search(query=bbb_id,
                                        item_type="Service",
                                        max_items=50)
    except Exception as e:
        print(f"Error searching ArcGIS content: {str(e)}")
        return False

    success_count = 0
    for title in titles:
        csv_title = title + ".csv"
        csv_path = os.path.join(uploads_dir, csv_title)
        
        # Skip if file doesn't exist or is empty
        if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
            print(f"Skipping {csv_title} - file doesn't exist or is empty")
            continue
            
        csv_properties = {
            'title': title,
            'description':'Data created for BBB ID: ' + bbb_id,
            'tags':'arcgis, bbb'
        }

        # publishing the csv and the feature layer for the first time
        try:
            csv_item = gis.content.add(item_properties=csv_properties, data=csv_path)
            feature_layer = csv_item.publish()
            print(f"{csv_title} published for the first time!")
            success_count += 1
        except Exception as e:
            print(f"Error publishing {csv_title}: {str(e)}")
            print("Searching for existing feature layer to update...")
            
            try:
                # Try to update existing layer
                found_existing = False
                for search_result in search_results:
                    search_result_title = search_result.title
                    search_result_id = search_result.id
                    # TODO: Validate the search result type
                    search_result_type = search_result.type

                    if search_result_title == title and search_result_type == "Feature Service":
                        print(f"Updating {csv_title}")
                        found_existing = True

                        try:
                            feature_layer_item = gis.content.get(search_result.id)
                            feature_layer = FeatureLayerCollection.fromitem(feature_layer_item)
                            result = feature_layer.manager.overwrite(csv_path)
                            print(f"Update result: {result}")
                            success_count += 1
                        except Exception as update_error:
                            print(f"Update failed: {str(update_error)}")
                        break
                
                if not found_existing:
                    print(f"No existing feature layer found for {title}")
            except Exception as search_error:
                print(f"Error searching for existing layer: {str(search_error)}")
    
    print(f"COMPLETED: ArcGIS upload for {bbb_id} - {success_count}/{len(titles)} successful")
    return success_count > 0

def run_mapping_application(skip_processed=False, specific_bbb_ids=None):
    """Main function to run the mapping application with options to skip steps"""
    print()
    print("===================================")
    print()
    print("Welcome to the Visual Knowledge BBB Partner API Tool!\n")
    print("________  ________  ________")
    print("|\   __  \|\   __  \|\   __  \\")
    print("\ \  \|\ /\ \  \|\ /\ \  \|\ /_")
    print(" \ \   __  \ \   __  \ \   __  \\")
    print("  \ \  \|\  \ \  \|\  \ \  \|\  \\")
    print("   \ \_______\ \_______\ \_______\\")
    print("    \|_______|\|_______|\|_______|")
    print("")
    print("===================================")
    print()
    
    # Configuration for which steps to run
    # Set any of these to True to skip that step
    skip_fetch_bbb_ids = False
    skip_fetch_zip_codes = False
    skip_determine_is_blue = False
    skip_fetch_api_data = False
    skip_process_results = False
    skip_upload_to_arcgis = False
    
    # Additional configuration to process only specific BBB IDs
    # Leave empty to process all, or add IDs to process only those
    if specific_bbb_ids is None:
        specific_bbb_ids = []
    ignore_bbb_ids = [] # specify which BBBs to ignore from the list

    # Execute the workflow
    bbb_ids, bbb_names = fetch_bbb_ids(skip=skip_fetch_bbb_ids)

    # Filter to specific BBB IDs if requested
    if specific_bbb_ids:
        filtered_ids = []
        filtered_names = []
        for i, bbb_id in enumerate(bbb_ids):
            if bbb_id in specific_bbb_ids:
                filtered_ids.append(bbb_id)
                filtered_names.append(bbb_names[i])
        bbb_ids = filtered_ids
        bbb_names = filtered_names
        print(f"Filtered to {len(bbb_ids)} specific BBB IDs: {', '.join(bbb_ids)}")
    else:
        # Remove ignored BBB IDs
        filtered_ids = []
        filtered_names = []
        for i, bbb_id in enumerate(bbb_ids):
            if bbb_id not in ignore_bbb_ids:
                filtered_ids.append(bbb_id)
                filtered_names.append(bbb_names[i])
        bbb_ids = filtered_ids
        bbb_names = filtered_names
        print(f"Ignoring {len(ignore_bbb_ids)} BBB IDs: {', '.join(ignore_bbb_ids)}")
        print(f"Processing the remaining {len(bbb_ids)} BBB IDs")

    for index, bbb_id in enumerate(bbb_ids):
        bbb_name = bbb_names[index] if index < len(bbb_names) else "Unknown"

        print(f"\nProcessing BBB ID: {bbb_id} ({bbb_name})\n" + "="*50)

        # Check if we should skip this BBB
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Check if zip file exists
        zip_file_path = os.path.join(script_dir, "zips", f"{bbb_id}_zips.csv")
        if not os.path.exists(zip_file_path):
            print(f"WARNING: No zip file found for {bbb_id} at {zip_file_path}")
            print(f"Skipping {bbb_id} ({bbb_name})")
            continue

        # Check if already processed (if skip_processed flag is set)
        if skip_processed:
            results_path = os.path.join(script_dir, "results", f"{bbb_id}.csv")
            if os.path.exists(results_path):
                print(f"Already processed {bbb_id} ({bbb_name}), skipping due to --skip-processed flag")
                continue

        # Step 1: Fetch zip codes
        zip_codes = fetch_zip_codes(bbb_id, skip=skip_fetch_zip_codes)
        
        # Step 2: Determine if Blue or Hurdman
        is_blue = determine_is_blue(bbb_id, skip=skip_determine_is_blue)
        
        # Step 3: Fetch API data
        results_path = fetch_api_data(bbb_id, bbb_name, zip_codes, skip=skip_fetch_api_data)
        
        # If we're not skipping fetch_api_data but it failed, stop processing this BBB ID
        if not skip_fetch_api_data and results_path is None:
            print(f"ERROR: API data fetch failed for {bbb_id}, skipping further processing")
            continue
            
        # If we skipped fetch_api_data, try to find the results file
        if skip_fetch_api_data:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            results_dir = os.path.join(script_dir, "results")
            potential_results_path = os.path.join(results_dir, bbb_id + ".csv")
            
            if os.path.exists(potential_results_path):
                results_path = potential_results_path
                print(f"Found existing results file: {results_path}")
            else:
                print(f"WARNING: Skipped API fetch but no results file found for {bbb_id}")
        
        # Step 4: Process and write results
        process_success = process_and_write_results(bbb_id, results_path, is_blue, skip=skip_process_results)
        
        # Step 5: Upload to ArcGIS
        if process_success or skip_process_results:
            upload_success = upload_to_arcgis(bbb_id, skip=skip_upload_to_arcgis)
        else:
            print(f"ERROR: Processing failed for {bbb_id}, skipping ArcGIS upload")
        
        print(f"\nCompleted processing for {bbb_id} ({bbb_name})")

def main():
    """Main entry point for the script"""
    import argparse

    parser = argparse.ArgumentParser(description='VK BBB Partner API Tool - Direct Execution')
    parser.add_argument('--no-slack', action='store_true', help='Disable Slack notifications')
    parser.add_argument('--skip-processed', action='store_true', help='Skip BBBs that already have output files')
    parser.add_argument('--bbb-ids', nargs='+', help='Process only specific BBB IDs (e.g., --bbb-ids 1126 0995)')
    args = parser.parse_args()

    # Set environment variable for Slack notifications if disabled
    if args.no_slack:
        os.environ['DISABLE_SLACK'] = '1'
        print("Slack notifications disabled")

    # Run the application with the provided arguments
    run_mapping_application(
        skip_processed=args.skip_processed,
        specific_bbb_ids=args.bbb_ids
    )

if __name__ == "__main__":
    main()