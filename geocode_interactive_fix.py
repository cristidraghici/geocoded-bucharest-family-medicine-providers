#!/usr/bin/env python3
"""
Interactive geocoding utility for updating addresses and coordinates in input.xlsx.

This script has two modes:

1. Interactive Mode (default):
   - Goes through each row in input.xlsx
   - Finds rows where coordinates (latitude/longitude) are missing
   - Shows the current address and prompts for a corrected address
   - Fetches coordinates for the corrected address using Nominatim
   - Updates all rows with the same original address at once

2. Reset Mode (--reset SEARCH_STRING):
   - Searches for rows matching the provided search string
   - Displays all matching rows with their current coordinates
   - Prompts for confirmation to reset coordinates and manual address overrides
   - Clears the manual_address, latitude, and longitude fields for matching rows
   - Removes corresponding entries from addresses_cache.json and coordinates_cache.json
   - Allows re-geocoding of these addresses in interactive mode

Usage:
    python geocode_interactive_fix.py                    # Interactive mode
    python geocode_interactive_fix.py --reset "Strada"   # Reset mode
"""

import pandas as pd
from geopy.geocoders import Nominatim
import utils
import sys
import os
import argparse

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

def reset_matching_rows(search_string):
    """
    Search for rows matching the search string and reset their coordinates and overrides.
    Also cleans the cache entries for the affected addresses.
    
    Args:
        search_string: String to search for in address columns
    """
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
    
    # Search for matching rows in any address column
    search_lower = search_string.lower()
    mask = (
        df[ADDRESS_COLUMN].astype(str).str.lower().str.contains(search_lower, na=False) |
        df[PARSED_ADDRESS_COLUMN].astype(str).str.lower().str.contains(search_lower, na=False) |
        df[MANUAL_ADDRESS_COLUMN].astype(str).str.lower().str.contains(search_lower, na=False)
    )
    
    matching_rows = df[mask]
    
    if matching_rows.empty:
        print(f"No rows found matching '{search_string}'")
        return
    
    print(f"\nFound {len(matching_rows)} row(s) matching '{search_string}':")
    print_separator()
    
    # Collect addresses to remove from cache
    addresses_to_clean = set()
    
    # Display matching rows and collect addresses
    for idx, row in matching_rows.iterrows():
        print(f"Row {idx + 2} (Excel row number):")
        print(f"  Original: {row[ADDRESS_COLUMN]}")
        print(f"  Parsed:   {row[PARSED_ADDRESS_COLUMN]}")
        if pd.notna(row[MANUAL_ADDRESS_COLUMN]):
            print(f"  Manual:   {row[MANUAL_ADDRESS_COLUMN]}")
            addresses_to_clean.add(row[MANUAL_ADDRESS_COLUMN])
        if pd.notna(row[PARSED_ADDRESS_COLUMN]):
            addresses_to_clean.add(row[PARSED_ADDRESS_COLUMN])
        if pd.notna(row[LATITUDE_COLUMN]) and pd.notna(row[LONGITUDE_COLUMN]):
            print(f"  Coords:   {row[LATITUDE_COLUMN]}, {row[LONGITUDE_COLUMN]}")
        print()
    
    print_separator()
    
    # Confirm reset
    confirm = get_user_input(f"Reset coordinates, manual addresses, and cache entries for these {len(matching_rows)} row(s)? (yes/no)", "no").lower()
    
    if confirm not in ['yes', 'y']:
        print("Operation cancelled.")
        return
    
    # Reset the rows
    reset_count = 0
    for idx in matching_rows.index:
        # Reset manual address, latitude, and longitude
        df.at[idx, MANUAL_ADDRESS_COLUMN] = None
        df.at[idx, LATITUDE_COLUMN] = None
        df.at[idx, LONGITUDE_COLUMN] = None
        reset_count += 1
    
    # Save the updated Excel file
    print(f"\nSaving updated data to {INPUT_FILE}...")
    df.to_excel(INPUT_FILE, sheet_name=SHEET_NAME, index=False, engine='openpyxl')
    print(f"✓ Saved! Reset {reset_count} row(s).")
    
    # Clean cache entries
    cache_files = {
        'addresses': '.cache/addresses_cache.json',
        'coordinates': '.cache/coordinates_cache.json'
    }
    
    cache_cleaned = False
    for cache_type, cache_file in cache_files.items():
        if os.path.exists(cache_file):
            cache = utils.load_cache(cache_file)
            original_size = len(cache)
            
            # Remove entries for the affected addresses
            for address in addresses_to_clean:
                if address in cache:
                    del cache[address]
                    cache_cleaned = True
            
            # Save the cleaned cache
            if len(cache) < original_size:
                utils.save_cache(cache_file, cache)
                removed = original_size - len(cache)
                print(f"✓ Cleaned {removed} entry/entries from {cache_type} cache")
    
    if not cache_cleaned:
        print("ℹ No cache entries found for the reset addresses")
    
    print("\nYou can now run the script without parameters to re-geocode these addresses.")


def save_dataframe(df, rows_updated):
    """Save the dataframe to Excel file."""
    print(f"\nSaving updated data to {INPUT_FILE}...")
    df.to_excel(INPUT_FILE, sheet_name=SHEET_NAME, index=False, engine='openpyxl')
    print(f"✓ Saved! Updated {rows_updated} row(s) total.")
    return df

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
        
        # Auto-save after each successful geocoding
        save_dataframe(df, rows_updated)
        
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
    
    # Final save (in case no updates were made in the last iteration)
    if rows_updated > 0:
        print(f"\n✓ All changes have been saved to {INPUT_FILE}")
    
    # Show remaining rows with missing coordinates
    remaining_missing = df[(df[LATITUDE_COLUMN].isna()) | (df[LONGITUDE_COLUMN].isna())]
    if not remaining_missing.empty:
        print(f"\n⚠ {len(remaining_missing)} row(s) still have missing coordinates.")
    else:
        print("\n✓ All rows now have coordinates!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Interactive geocoding utility for updating addresses and coordinates in input.xlsx.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode - fix rows with missing coordinates
  python geocode_interactive_fix.py
  
  # Reset mode - search for and reset coordinates for matching rows
  python geocode_interactive_fix.py --reset "Strada Mihai"
  python geocode_interactive_fix.py --reset "Sector 1"
        """
    )
    
    parser.add_argument(
        '--reset',
        type=str,
        metavar='SEARCH_STRING',
        help='Search for rows matching SEARCH_STRING and reset their coordinates and manual address overrides'
    )
    
    args = parser.parse_args()
    
    try:
        if args.reset:
            # Reset mode - search and reset matching rows
            reset_matching_rows(args.reset)
        else:
            # Interactive mode - fix rows with missing coordinates
            main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        print("Note: All progress has been auto-saved after each geocoded address.")
        sys.exit(0)

