#!/usr/bin/env python3
"""
Interactive geocoding utility for updating addresses and coordinates in input.xlsx.

This script:
1. Goes through each row in input.xlsx
2. Finds rows where coordinates (latitude/longitude) are missing
3. Shows the current address and prompts for a corrected address
4. Fetches coordinates for the corrected address using Nominatim
5. Updates all rows with the same original address at once
"""

import pandas as pd
from geopy.geocoders import Nominatim
import utils
import sys
import os

# Configuration
INPUT_FILE = 'input.xlsx'
SHEET_NAME = 'Sheet1'
ADDRESS_COLUMN = 'Adresa punct de lucru'
PARSED_ADDRESS_COLUMN = 'parsed_address'
MANUAL_ADDRESS_COLUMN = 'manual_address'
LATITUDE_COLUMN = 'latitude'
LONGITUDE_COLUMN = 'longitude'

def print_separator():
    """Print a visual separator."""
    print("\n" + "="*80 + "\n")

def get_user_input(prompt, default=None):
    """Get user input with optional default value."""
    if default:
        user_input = input(f"{prompt} [default: {default}]: ").strip()
        return user_input if user_input else default
    else:
        return input(f"{prompt}: ").strip()

def main():
    """Main interactive geocoding function."""
    
    # Check if input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found!")
        print("Please run geocode_medical_addresses.py first to create the input file.")
        sys.exit(1)
    
    # Load the Excel file
    print(f"Loading {INPUT_FILE}...")
    df = pd.read_excel(INPUT_FILE, SHEET_NAME)
    
    # Ensure required columns exist
    for column in [PARSED_ADDRESS_COLUMN, MANUAL_ADDRESS_COLUMN, LATITUDE_COLUMN, LONGITUDE_COLUMN]:
        if column not in df.columns:
            df[column] = None
    
    # Initialize geocoder
    geolocator = Nominatim(user_agent='bucharest_family_medicine_geocoder_interactive')
    
    # Find rows with missing coordinates
    missing_coords = df[(df[LATITUDE_COLUMN].isna()) | (df[LONGITUDE_COLUMN].isna())]
    
    if missing_coords.empty:
        print("✓ All rows have coordinates! Nothing to update.")
        return
    
    print(f"Found {len(missing_coords)} rows with missing coordinates.")
    
    # Check for existing manual fixes that can be auto-applied
    print("\nChecking for existing manual fixes...")
    
    # Find rows that have coordinates (successfully geocoded)
    rows_with_coords = df[(df[LATITUDE_COLUMN].notna()) & (df[LONGITUDE_COLUMN].notna())]
    
    # Build a mapping of parsed_address -> (manual_address, lat, lon) for rows with coordinates
    existing_fixes = {}
    for _, row in rows_with_coords.iterrows():
        parsed_addr = row[PARSED_ADDRESS_COLUMN]
        manual_addr = row[MANUAL_ADDRESS_COLUMN]
        lat = row[LATITUDE_COLUMN]
        lon = row[LONGITUDE_COLUMN]
        
        # Only store if we have both parsed and manual addresses, and they differ
        # (meaning a manual fix was applied)
        if pd.notna(parsed_addr) and pd.notna(manual_addr) and parsed_addr != manual_addr:
            if parsed_addr not in existing_fixes:
                existing_fixes[parsed_addr] = {
                    'manual_address': manual_addr,
                    'latitude': lat,
                    'longitude': lon
                }
    
    # Auto-apply existing fixes to rows with missing coordinates
    auto_applied = 0
    if existing_fixes:
        print(f"Found {len(existing_fixes)} existing manual fix(es).")
        print("Auto-applying to matching addresses...\n")
        
        for index, row in missing_coords.iterrows():
            parsed_addr = row[PARSED_ADDRESS_COLUMN]
            
            # Check if we have an existing fix for this parsed address
            if pd.notna(parsed_addr) and parsed_addr in existing_fixes:
                fix = existing_fixes[parsed_addr]
                
                # Apply the fix
                df.at[index, MANUAL_ADDRESS_COLUMN] = fix['manual_address']
                df.at[index, LATITUDE_COLUMN] = fix['latitude']
                df.at[index, LONGITUDE_COLUMN] = fix['longitude']
                auto_applied += 1
                
                print(f"✓ Row {index + 2}: Applied existing fix")
                print(f"  {parsed_addr}")
                print(f"  → {fix['manual_address']}")
        
        if auto_applied > 0:
            print(f"\n✓ Auto-applied fixes to {auto_applied} row(s)")
            
            # Save the auto-applied changes
            print(f"Saving auto-applied changes to {INPUT_FILE}...")
            df.to_excel(INPUT_FILE, sheet_name=SHEET_NAME, index=False, engine='openpyxl')
            print("✓ Saved!\n")
            
            # Reload to get updated missing coordinates count
            df = pd.read_excel(INPUT_FILE, SHEET_NAME)
            missing_coords = df[(df[LATITUDE_COLUMN].isna()) | (df[LONGITUDE_COLUMN].isna())]
            
            if missing_coords.empty:
                print("✓ All rows now have coordinates! Nothing more to do.")
                return
            
            print(f"Remaining rows with missing coordinates: {len(missing_coords)}")
    else:
        print("No existing manual fixes found.")
    
    print_separator()
    
    # Track which addresses we've already processed to avoid duplicates
    processed_addresses = {}
    total_rows = len(df)
    rows_updated = 0
    
    # Track remaining rows to fix (will be updated as we process)
    remaining_to_fix = len(missing_coords)
    
    # Iterate through rows with missing coordinates
    for index, row in missing_coords.iterrows():
        original_address = row[ADDRESS_COLUMN]
        parsed_address = row[PARSED_ADDRESS_COLUMN]
        manual_address = row[MANUAL_ADDRESS_COLUMN]
        
        # Use manual_address if available, otherwise parsed_address
        current_address = manual_address if pd.notna(manual_address) else parsed_address
        
        # Skip if we've already processed this address
        if current_address in processed_addresses:
            continue
        
        # Count how many rows have this same address
        same_address_count = len(df[
            ((df[MANUAL_ADDRESS_COLUMN] == current_address) | 
             ((df[MANUAL_ADDRESS_COLUMN].isna()) & (df[PARSED_ADDRESS_COLUMN] == current_address))) &
            ((df[LATITUDE_COLUMN].isna()) | (df[LONGITUDE_COLUMN].isna()))
        ])
        
        # Display current information
        print(f"Row {index + 2} of {total_rows + 1} (Excel row number)")
        print(f"Remaining rows needing fixes: {remaining_to_fix}")
        print(f"Original address: {original_address}")
        print(f"Parsed address:   {parsed_address}")
        if pd.notna(manual_address) and manual_address != parsed_address:
            print(f"Manual address:   {manual_address}")
        print(f"\nCurrent address to geocode: {current_address}")
        
        if same_address_count > 1:
            print(f"⚠ This address appears in {same_address_count} rows with missing coordinates")
        
        print("\nOptions:")
        print("  1. Press ENTER to use the current address")
        print("  2. Type a new address to use instead")
        print("  3. Type 'skip' to skip this address")
        print("  4. Type 'quit' to save and exit")
        
        user_choice = get_user_input("\nYour choice").lower()
        
        if user_choice == 'quit':
            print("\nSaving and exiting...")
            break
        elif user_choice == 'skip':
            print("Skipping this address.")
            processed_addresses[current_address] = None
            # Decrement remaining count by the number of rows with this address
            remaining_to_fix -= same_address_count
            print_separator()
            continue
        elif user_choice == '':
            # Use current address
            address_to_geocode = current_address
        else:
            # User provided a new address
            address_to_geocode = user_choice
        
        # Geocode the address
        print(f"\nGeocoding: {address_to_geocode}")
        latitude, longitude = utils.validate_and_get_coordinates(geolocator, address_to_geocode)
        
        if latitude is None or longitude is None:
            print("✗ Failed to get coordinates for this address.")
            retry = get_user_input("Try a different address? (y/n)", "n").lower()
            if retry == 'y':
                new_address = get_user_input("Enter new address")
                print(f"\nGeocoding: {new_address}")
                latitude, longitude = utils.validate_and_get_coordinates(geolocator, new_address)
                if latitude is not None and longitude is not None:
                    address_to_geocode = new_address
                else:
                    print("✗ Failed again. Skipping this address.")
                    processed_addresses[current_address] = None
                    print_separator()
                    continue
            else:
                processed_addresses[current_address] = None
                print_separator()
                continue
        
        print(f"✓ Coordinates found: {latitude}, {longitude}")
        
        # Update all rows with the same address
        # Find all rows that match this address and have missing coordinates
        mask = (
            ((df[MANUAL_ADDRESS_COLUMN] == current_address) | 
             ((df[MANUAL_ADDRESS_COLUMN].isna()) & (df[PARSED_ADDRESS_COLUMN] == current_address))) &
            ((df[LATITUDE_COLUMN].isna()) | (df[LONGITUDE_COLUMN].isna()))
        )
        
        rows_to_update = df[mask].index
        
        for idx in rows_to_update:
            df.at[idx, MANUAL_ADDRESS_COLUMN] = address_to_geocode
            df.at[idx, LATITUDE_COLUMN] = latitude
            df.at[idx, LONGITUDE_COLUMN] = longitude
            rows_updated += 1
        
        print(f"✓ Updated {len(rows_to_update)} row(s)")
        
        # Decrement remaining count
        remaining_to_fix -= len(rows_to_update)
        
        # Mark this address as processed
        processed_addresses[current_address] = {
            'address': address_to_geocode,
            'latitude': latitude,
            'longitude': longitude
        }
        
        # Add a small delay to be respectful to the geocoding service
        utils.random_delay(1, 2)
        
        print_separator()
    
    # Save the updated Excel file
    print(f"\nSaving updated data to {INPUT_FILE}...")
    df.to_excel(INPUT_FILE, sheet_name=SHEET_NAME, index=False, engine='openpyxl')
    print(f"✓ Saved! Updated {rows_updated} row(s) total.")
    
    # Show remaining rows with missing coordinates
    remaining_missing = df[(df[LATITUDE_COLUMN].isna()) | (df[LONGITUDE_COLUMN].isna())]
    if not remaining_missing.empty:
        print(f"\n⚠ {len(remaining_missing)} row(s) still have missing coordinates.")
    else:
        print("\n✓ All rows now have coordinates!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting without saving.")
        sys.exit(0)
