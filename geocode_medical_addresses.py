import shutil
import os
import pandas as pd
from geopy.geocoders import Nominatim

import utils

# Script parameters
source_file = './20230721_Lista cabinete medicina de familie _20.07.2023.xlsx'
sheet_name = 'Sheet1'
address_column = 'Adresa punct de lucru'
destination_file = 'input.xlsx'

# Copy the source folder to the new destination where it will be processed
source_directory = os.path.dirname(source_file)
input_file = os.path.join(source_directory, destination_file)

if not os.path.exists(input_file):
    shutil.copy(source_file, input_file)
    print('Input file created')

# Open the excel file
df = pd.read_excel(input_file, sheet_name)

# Add the new columns (parsed_address in case we need to manually change the address, the latitude and longitude)
for column in ['parsed_address', 'latitude', 'longitude']:
    if column not in df.columns:
        df[column] = None

# Parse the address and get an OSM searchable value (street name and street number)
for index, row in df.iterrows():
    if pd.notna(row[address_column]):
        df.at[index, 'parsed_address'] = utils.extract_street_name_and_number(row[address_column])

# Use OSM to get the latitude and longitude of each of the addresses
geolocator = Nominatim(user_agent='address_validator')
for index, row in df.iterrows():
    address = row['parsed_address']
    if pd.isna(row['latitude']) or pd.isna(row['longitude']):
        latitude, longitude = utils.validate_and_get_coordinates(geolocator, address)

        if latitude is not None and longitude is not None:
            df.at[index, 'latitude'] = latitude
            df.at[index, 'longitude'] = longitude
            print(f"Coordinates retrieved for address at {index}: {address}")

    utils.random_delay(1, 3)
    # use this to develop and just do a limited number of queries to OSM
    # if index == 3:
    #     break

# Save the excel file
df.to_excel(input_file, sheet_name=sheet_name, index=False, engine='openpyxl')