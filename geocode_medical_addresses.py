import argparse
import sys
import shutil
import os
import pandas as pd
from geopy.geocoders import Nominatim
from unidecode import unidecode
import json

import utils

# Script parameters
source_file = './20230721_Lista cabinete medicina de familie _20.07.2023.xlsx'
sheet_name = 'Sheet1'
address_column = 'Adresa punct de lucru'
json_title_column = 'Nume medic de familie'
destination_excel_file = 'input.xlsx'
destination_json_file = 'output.json'

# Copy the source folder to the new destination where it will be processed
source_directory = os.path.dirname(source_file)
input_file = os.path.join(source_directory, destination_excel_file)

# Read the arguments from the command line
parser = argparse.ArgumentParser(description='Parse and save with geocoding the list of family medicine offices in Bucharest')
parser.add_argument('--dev', action='store_true', help='in development mode, only the first 5 addresses are looked up in Nominatim')
parser.add_argument('--addresses', action='store_true', help='get the clean address if not set in the custom address column')
parser.add_argument('--geocodes', action='store_true', help='get the latitude and longitude where there are not set in the custom columns')
parser.add_argument('--excel', action='store_true', help='save the data in the excel format')
parser.add_argument('--json', action='store_true', help='save the data in json format')
args = parser.parse_args()

if not any(vars(args).values()):
    parser.print_help()
    sys.exit(0)

# ensure we have a save function
if not args.json and not args.excel:
    print("No save function selected. Exiting...")
    sys.exit(0)

if not os.path.exists(input_file):
    shutil.copy(source_file, input_file)
    print('Input file created')

# Open the excel file
df = pd.read_excel(input_file, sheet_name)

# Add the new columns (parsed_address in case we need to manually change the address, the latitude and longitude)
parsed_address = 'parsed_address' # column containing the result of `extract_street_name_and_number`
manual_address = 'manual_address' # column containing the value of parsed_address by default which can manually be changed (will only be updated manually after being set)
for column in [parsed_address, manual_address, 'latitude', 'longitude']:
    if column not in df.columns:
        df[column] = None

if args.addresses:
    # Parse the address and get an OSM searchable value (street name and street number)
    for index, row in df.iterrows():
        if pd.notna(row[address_column]):
            street_name_and_number = utils.extract_street_name_and_number(row[address_column])
            df.at[index, parsed_address] = street_name_and_number

            if pd.isna(row[manual_address]):
                df.at[index, manual_address] = street_name_and_number

if args.geocodes:
    # Use OSM to get the latitude and longitude of each of the addresses
    geolocator = Nominatim(user_agent='address_validator')
    for index, row in df.iterrows():
        address = row[manual_address]
        if pd.isna(row['latitude']) or pd.isna(row['longitude']):
            latitude, longitude = utils.validate_and_get_coordinates(geolocator, address)

            if latitude is not None and longitude is not None:
                df.at[index, 'latitude'] = latitude
                df.at[index, 'longitude'] = longitude
                print(f"Coordinates retrieved for address at {index}: {address}")

        utils.random_delay(1, 3)

        if args.dev and index == 5:
            break

if args.excel:
    # Save the excel file
    df.to_excel(input_file, sheet_name=sheet_name, index=False, engine='openpyxl')
    print(f"The data has been saved to {input_file} in Excel format.")

if args.json:
    # Filter out rows with null latitude and longitude
    filtered_df = df.dropna(subset=['latitude', 'longitude'])

    # Get the column headers
    column_headers = df.columns.tolist()

    # Initialize a list to hold JSON entities
    json_entities = []

    # Create JSON entities
    for index, row in filtered_df.iterrows():
        entity = {
            "title": unidecode(row[json_title_column]),
            "description": [f"{header}: {unidecode(row[header])}" for header in column_headers[0:] if header not in [json_title_column, parsed_address, manual_address, 'latitude', 'longitude']],
            "latitude": row['latitude'],
            "longitude": row['longitude']
        }
        json_entities.append(entity)

    # Save the data as JSON
    output_file = destination_json_file
    with open(output_file, 'w') as f:
        json.dump(json_entities, f, indent=4)

    print(f"The filtered data has been saved to {output_file} in JSON format.")
