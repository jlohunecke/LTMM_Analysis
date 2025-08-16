import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Read the Excel file
df = pd.read_excel('ReportHome75h.xlsx')

# Define the column mappings for each day
# Based on the Excel structure we observed
day_mappings = {
    'day_0': {
        'date': '0 day',
        'start': 'Unnamed: 4', 
        'took_off': 'Unnamed: 5',
        'put_on': 'Unnamed: 6',
        'end_time': 'Unnamed: 7'
    },
    'day_1': {
        'start_time': '1st day',
        'took_off': 'Unnamed: 9',
        'put_on': 'Unnamed: 10', 
        'end_time': 'Unnamed: 11'
    },
    'day_2': {
        'start_time': '2nd day',
        'took_off': 'Unnamed: 13',
        'put_on': 'Unnamed: 14',
        'end_time': 'Unnamed: 15'
    },
    'day_3': {
        'start_time': '3rd day',
        'took_off': 'Unnamed: 17',
        'put_on': 'Unnamed: 18',
        'end_time': 'Unnamed: 19'
    }
}

# Extract data
extracted_data = []

for _, row in df.iterrows():
    pig_id = row['Unnamed: 0']
    
    # Skip header rows and empty rows
    if pd.isna(pig_id) or pig_id == '#PIGD-' or not str(pig_id).startswith('CO-'):
        continue
    
    # Get base date from day_0
    base_date = row['0 day']
    if pd.isna(base_date):
        continue
    
    # Convert to datetime if it's not already
    if isinstance(base_date, str):
        try:
            base_date = pd.to_datetime(base_date)
        except:
            continue
    
    # Process each day
    for day_name, col_mapping in day_mappings.items():
        day_num = int(day_name.split('_')[1])
        
        # Calculate the target date
        if day_num == 0:
            target_date = base_date
        else:
            target_date = base_date + pd.Timedelta(days=day_num)
        
        # Extract values for this day
        day_data = {
            'pig_id': pig_id,
            'day': day_name,
            'start_time': None,
            'take_off': None,
            'put_on': None,
            'end_time': None
        }
        
        # Map the columns
        for our_col, excel_col in col_mapping.items():
            value = row[excel_col]
            if pd.notna(value) and str(value).strip() != '':
                # Keep the original value as string to preserve notes and question marks
                day_data[our_col] = str(value)
        
        extracted_data.append(day_data)

# Create DataFrame
result_df = pd.DataFrame(extracted_data)

# Save to CSV
result_df.to_csv('pig_timestamps_from_excel.csv', index=False)

print("Extraction completed!")
print(f"Extracted {len(result_df)} rows")
print(f"Columns: {list(result_df.columns)}")

# Show sample data
print("\nSample data:")
sample_pig = result_df[result_df['pig_id'] == 'CO-001']
for _, row in sample_pig.iterrows():
    print(f"{row['pig_id']}, {row['day']}: start={row['start_time']}, take_off={row['take_off']}, put_on={row['put_on']}, end={row['end_time']}")
