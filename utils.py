from unidecode import unidecode
import re

from random import randint
from time import sleep

import json
import os

# Pre-compiled regex patterns for better performance
_CLEANUP_PATTERNS = [
    # fix for number not separated - must be preceded by a letter to avoid matching standalone "nr"
    (re.compile(r'([a-zA-Z])nr\b', re.I), r'\1, nr'),
    
    # text cleanup (ensure there is a space at the end of the replace string)
    # Note: patterns consume trailing partial words to avoid duplication (e.g., "Bdul" -> "Bulevardul", not "Bulevardul ul")
    (re.compile(r'\b(?:Numarul\.|Numarul|Nr\.|Nr)(?:ul)?\s*', re.I), 'Numarul '),
    (re.compile(r'\b(?:Calea|Cal\.)(?:ea)?\s*', re.I), 'Calea '),
    (re.compile(r'\b(?:Piata|Pta\.?)(?:ta)?\s*', re.I), 'Piata '),
    (re.compile(r'\b(?:Drumul)(?:ul)?\s*', re.I), 'Drumul '),
    (re.compile(r'\b(?:Strada|Str\.?|Stra\.)(?:ada)?\s*', re.I), 'Strada '),
    (re.compile(r'\b(?:Bulevardul|Bulevard|Bd\.?|Bld\.?|Bdul\.?|B-dul)(?:ul)?\s*', re.I), 'Bulevardul '),
    (re.compile(r'\b(?:Soseaua|Sos\.?)(?:aua)?\s*', re.I), 'Soseaua '),
    (re.compile(r'\b(?:Splaiul|Spl\.?)(?:ul)?\s*', re.I), 'Splaiul '),
    (re.compile(r'\b(?:Aleea|Al\.)(?:ea)?\s*', re.I), 'Aleea '),
    (re.compile(r'\b(?:Intrarea|Intarea|Intr\.|Int\.)(?:area)?\s*', re.I), 'Intrarea '),
    (re.compile(r'\b(?:Sector|Sect\.?)(?:or)?\s*', re.I), 'Sector ')
]

# Pre-compiled patterns for whitespace and comma cleanup
_MULTIPLE_COMMAS = re.compile(r',{2,}')
_MULTIPLE_SPACES = re.compile(r'\s{2,}')
_SPACE_BEFORE_COMMA = re.compile(r'\s+,')
_COMMA_SPACE = re.compile(r',\s+')

# Pre-compiled patterns for street, number, and sector extraction
_STREET_PATTERN = re.compile(r'(Calea|Piata|Drumul|Strada|Bulevardul|Soseaua|Splaiul|Aleea|Intrarea)\s+(.*?)(?:,|(?=\s*Numarul)|$)', re.I)
_NUMBER_PATTERN = re.compile(r'Numarul\s+(.*?)(?:,|$)', re.I)
_SECTOR_PATTERN = re.compile(r'Sector\s+(\d+)', re.I)

# A file based cache to store the coordinates
def load_cache(cache_file):
    """Load cache from JSON file if it exists, otherwise return empty dict."""
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as file:
            return json.load(file)
    else:
        return {}

def save_cache(cache_file, cache):
    """Save cache dictionary to JSON file."""
    print(f"Saving cache to {cache_file} {len(cache)} entries...")
    with open(cache_file, 'w') as file:
        json.dump(cache, file)

def extract_street_name_and_number(address):
    """
    Extract and normalize street name, number, and sector from a Romanian address.
    
    Args:
        address: Raw address string
        
    Returns:
        Normalized address string in format "Street Type Street Name, Number, Sector X, Bucuresti"
    """
    # Convert to ASCII characters
    address = unidecode(address)

    # Apply all cleanup patterns
    for pattern, replacement in _CLEANUP_PATTERNS:
        address = pattern.sub(replacement, address)

    # Clean up multiple spaces and commas
    address = _MULTIPLE_COMMAS.sub(',', address)
    address = _MULTIPLE_SPACES.sub(' ', address)
    address = _SPACE_BEFORE_COMMA.sub(',', address)
    address = _COMMA_SPACE.sub(',', address)
    
    # Extract street, number, and sector
    returnAddress = ''

    streetMatch = _STREET_PATTERN.search(address)
    if streetMatch:
        returnAddress = (streetMatch.group(1) + ' ' + streetMatch.group(2)).strip()

    # Only extract number if we found a street
    if returnAddress:
        numberMatch = _NUMBER_PATTERN.search(address)
        if numberMatch:
            number = numberMatch.group(1).strip()
            returnAddress = returnAddress + ', ' + number
    
    # Extract sector if present
    sectorMatch = _SECTOR_PATTERN.search(address)
    sector = ''
    if sectorMatch:
        sector = ', Sector ' + sectorMatch.group(1)

    # Return the parsed address
    return returnAddress + sector + ', Bucuresti' if returnAddress else ', Bucuresti'

# Get coordinates using OSM
def validate_and_get_coordinates(geolocator, address):
    try:
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        else:
            # TODO: in case we don't have a match, we could try to remove the street type
            print(f"Location not available for '{address}'")
            return None, None
    except Exception as e:
        print(f"Error occurred while validating address '{address}': {e}")
        return None, None
    
# Sleep for a random number of seconds, mainly to avoid hitting api limits
def random_delay(min, max):
    sleep(randint(min, max))