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
source_file = './20250416_LISTA_FURNIZORI_DE_SERVICII_MEDICALE_MEDICINA_DE_FAMILIE_16.04.2025.xlsx'
sheet_name = 'Sheet1'
address_column = 'Adresa punct de lucru'
json_title_column = 'Nume medic de familie'
destination_excel_file = 'input.xlsx'
destination_json_file = 'output.json'
coordinates_cache_json_file = '.cache/coordinates_cache.json'
addresses_cache_json_file = '.cache/addresses_cache.json'

# Initialize the cache dictionaries
coordinates_cache = utils.load_cache(coordinates_cache_json_file)
addresses_cache = utils.load_cache(addresses_cache_json_file)

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
parser.add_argument('--cache', action='store_true', help='cache addresses and coordinates for use with the new versions of the list of family medicine offices')
args = parser.parse_args()

# Check for dependencies
if args.geocodes:
    args.addresses = True

if not any(vars(args).values()):
    parser.print_help()
    sys.exit(0)

# ensure we have a save function
if not args.json and not args.excel and not args.cache:
    print("No save function selected. Cache not being used, either. Exiting...")
    sys.exit(0)

if not os.path.exists(input_file):
    # if os.path.exists(input_file):
    #     os.remove(input_file)
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
                if args.cache and addresses_cache.get(street_name_and_number) is not None:
                    df.at[index, manual_address] = addresses_cache[street_name_and_number]
                else:
                    df.at[index, manual_address] = street_name_and_number
        if args.dev and index == 4:
            break

if args.geocodes:
    # Use OSM to get the latitude and longitude of each of the addresses
    geolocator = Nominatim(user_agent='bucharest_family_medicine_geocoder')
    for index, row in df.iterrows():
        address = row[manual_address]
        if pd.isna(row['latitude']) or pd.isna(row['longitude']):
            
            if args.cache and coordinates_cache.get(address) is not None:
                current_coordinates = coordinates_cache[address]
                df.at[index, 'latitude'] = current_coordinates['latitude']
                df.at[index, 'longitude'] = current_coordinates['longitude']
                print(f"Coordinates retrieved from cache for address at {index}: {address}")
            else:
                latitude, longitude = utils.validate_and_get_coordinates(geolocator, address)
                utils.random_delay(1, 3)

                if latitude is not None and longitude is not None:
                    df.at[index, 'latitude'] = latitude
                    df.at[index, 'longitude'] = longitude
                    print(f"Coordinates retrieved for address at {index}: {address}")

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
            "title": unidecode(str(row[json_title_column])),
            "description": [
                f"{header}: {unidecode(str(row[header])) if isinstance(row[header], str) else row[header]}"
                for header in column_headers[0:]
                if header not in [json_title_column, parsed_address, manual_address, 'latitude', 'longitude']
            ],
            "latitude": row['latitude'],
            "longitude": row['longitude']
        }
        json_entities.append(entity)

        
        if args.dev and index == 5:
            break

    # Save the data as JSON
    output_file = destination_json_file
    with open(output_file, 'w') as f:
        json.dump(json_entities, f, indent=4)

    print(f"The filtered data has been saved to {output_file} in JSON format.")

if args.cache:
    for index, row in df.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']):
            address = row[manual_address]
            coordinates_cache[address] = {
                'latitude': row['latitude'],
                'longitude': row['longitude']
            }
        if pd.notna(row[parsed_address]) and pd.notna(row[manual_address]):
            addresses_cache[row[parsed_address]] = row[manual_address]

        if args.dev and index == 5:
            break
    utils.save_cache(coordinates_cache_json_file, coordinates_cache)
    utils.save_cache(addresses_cache_json_file, addresses_cache)

    print(f"The cache has been saved in JSON format.")