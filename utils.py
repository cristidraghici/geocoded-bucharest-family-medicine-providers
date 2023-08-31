from unidecode import unidecode
import re

from random import randint
from time import sleep

# Extract street and number from addresses
def extract_street_name_and_number(address):
    # use alphanumeric characters
    address = unidecode(address)

    # put a comma before the number
    address = re.compile("nr", flags=re.I).sub(", nr", address)

    # ensure we have the proper prefix for the street
    streetTypeRegexList = [
        [r"((?:Calea|Cal)\s|(?:Cal\.))", 'Calea'],
        [r"((?:Piata|Pta)\s|(?:Pta\.))", 'Piata'],
        [r"((?:Drumul)\s)", 'Drumul'],
        [r"((?:Strada|Str)\s|(?:Str\.|Stra\.))", 'Strada'],
        [r"((?:Bulevardul|Bulevard|Bd|Bld|B-dul)\s|(?:Bd\.|Bld\.))", 'Bulevardul'],
        [r"((?:Soseaua|Sos)\s|(?:Sos\.))", 'Soseaua'],
        [r"((?:Splaiul|Spl)\s|(?:Spl\.))", 'Splaiul'],
        [r"((?:Aleea)\s|(?:Al\.))", 'Aleea'],
        [r"((?:Intarea|Int|Intr)\s|(?:Int\.|Intr\.))", 'Intrarea']
    ]

    for regex in streetTypeRegexList:
        address = re.sub(regex[0], f'{regex[1]} ', address, flags=re.I)

    # ensure we have the name for the number properly set
    address = re.sub(r"((?:Numarul|Nr)\s|(?:Nr\.))", 'Numarul ', address, flags=re.I)

    # commas and spaces
    while ",," in address:
        address = re.sub(r",,", ",", address)
    while "  " in address:
        address = re.sub(r"  ", " ", address)
    address = re.sub(r" ,", ",", address)
    
    # get the street and number
    returnAddress = ''

    streetMatch = re.match(r"(Calea|Piata|Drumul|Strada|Bulevardul|Soseaua|Splaiul|Aleea|Intrarea)(.*?)(?:,)", address)
    if (streetMatch):
        returnAddress = ''.join(streetMatch.group(1, 2))

    numberMatch = re.search(r"(Numarul )(.*?)(?:,)", address)
    if (numberMatch):
        returnAddress = f"{returnAddress}, {numberMatch.group(2)}"

    # return the parsed address
    return f"{returnAddress}, Bucuresti"

# Get coordinates using OSM
def validate_and_get_coordinates(geolocator, address):
    try:
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        else:
            print(f"Location not available for '{address}'")
            return None, None
    except Exception as e:
        print(f"Error occurred while validating address '{address}': {e}")
        return None, None
    
# Sleep for a random number of seconds, mainly to avoid hitting api limits
def random_delay(min, max):
    sleep(randint(min, max))