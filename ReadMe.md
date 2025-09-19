# BBB Partner API Retrieval Tool

## How to run the code:

1. Download the source code from the repository or clone it to your local machine.
2. Open the folder locally through terminal or command prompt
3. Try running the file by typing “python bbb.py”.
4. Download any necessary libraries by typing “pip install library_name”
Open the file to make modifications or to see

## How the code works:

Step 1: Get all of the records for a specific BBB region (BBB ID) using the BBB Partner API
[BBB Partner API Documentation](https://developer.bbb.org/). The bbb_ids folder contains a CSV file which has a list of the BBB regions that are going to be downloaded from the partner API. Add or remove new regions here. Whenever a new BBB region is added, a list of zip codes must be added in the zips folder, following the naming convention and format of the other files.

Step 2: Upload the resulting file to ArcGIS Online to be mapped. The results are split into separate files and prepared to upload to ArcGIS. We upload a CSV and then specify to use that CSV within a hosted feature layer.

Step 3: Once the layers are on ArcGIS, further implementation will be done on ArcGIS Online.

## Notes
- Blue uploads their data once per night to the IABBB. The IABBB is in charge of the Partner API.
- All of the fields can be shown by adding the following print statement to the returned JSON:
```
print(json.dumps(results, indent=2))
```
