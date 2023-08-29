import pandas as pd
import json

input_file = 'input.xlsx'
sheet_name = 'Sheet1'

# Read the Excel file
df = pd.read_excel(input_file, sheet_name=sheet_name)

# Filter out rows with null latitude and longitude
filtered_df = df.dropna(subset=['latitude', 'longitude'])

# Initialize a list to hold JSON entities
json_entities = []

# Create JSON entities
for index, row in filtered_df.iterrows():
    entity = {
        "title": row['Nume medic de familie'],
        "description": [
            f"Contract: {row['Nr. Contract']}",
            f"Denumire furnizor: {row['Denumire furnizor']}",
            f"Telefon: {row['Telefon']}",
            f"E-mail: {row['E-mail']}",
            f"Adresa punct de lucru: {row['Adresa punct de lucru']}",
            f"Parsed Address: {row['parsed_address']}"
        ],
        "latitude": row['latitude'],
        "longitude": row['longitude']
    }
    json_entities.append(entity)

# Save the data as JSON
output_file = 'output.json'
with open(output_file, 'w') as f:
    json.dump(json_entities, f, indent=4)

print(f"Filtered data has been saved to {output_file} in JSON format.")