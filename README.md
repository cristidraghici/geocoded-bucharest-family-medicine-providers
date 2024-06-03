# geocoded-bucharest-family-medicine-providers

> Family medicine in Bucharest on a map

## About

The `output.json` file contains information about the family medicine doctors in bucharest, together with geolocation information. This file will contain the most recent list of family medicine doctors.

It will have the following structure:

```python
data = [
    {
        "title": str,  # str
        "description": [str],  # list of str
        "latitude": float,  # float
        "longitude": float  # float
    },
    ...
]
```

## How to use

The source list is not consistent, nor in a proper format. This is why we will start with separate parsers which can later be merged if needed. It's also the reason why we store the source in this repo.

To run the script:

- `python geocode_medical_addresses.py`

The source list for the family doctors is available here: [http://cas.cnas.ro/casmb/page/lista-cabinete-medicina-de-familie.html](http://cas.cnas.ro/casmb/page/lista-cabinete-medicina-de-familie.html). We usually download the list and then make a minimal cleanup in the file (remove the formatting, put the columns in the right order), then update the `./geocode_medical_addresses.py` file with the new filename for the source.
