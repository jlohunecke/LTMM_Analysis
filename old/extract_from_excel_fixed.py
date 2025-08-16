import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Read the Excel file
df = pd.read_excel('ReportHome75h.xlsx')

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
    for day_num in range(4):
        day_name = f'day_{day_num}'
        
        # Calculate the target date
        if day_num == 0:
            target_date = base_date
        else:
            target_date = base_date + pd.Timedelta(days=day_num)
        
        # Extract values for this day based on the Excel structure
        day_data = {
            'pig_id': pig_id,
            'day': day_name,
            'start_time': None,
            'take_off': None,
            'put_on': None,
            'end_time': None
        }
        
        # Map columns based on day
        if day_num == 0:
            # Day 0: date, start, took_off, put_on, end_time
            if pd.notna(row['Unnamed: 4']):  # start time
                day_data['start_time'] = str(row['Unnamed: 4'])
            if pd.notna(row['Unnamed: 5']):  # took off
                day_data['take_off'] = str(row['Unnamed: 5'])
            if pd.notna(row['Unnamed: 6']):  # put on
                day_data['put_on'] = str(row['Unnamed: 6'])
            if pd.notna(row['Unnamed: 7']):  # end time
                day_data['end_time'] = str(row['Unnamed: 7'])
        elif day_num == 1:
            # Day 1: start_time, took_off, put_on, end_time
            if pd.notna(row['1st day']):  # start time
                day_data['start_time'] = str(row['1st day'])
            if pd.notna(row['Unnamed: 9']):  # took off
                day_data['take_off'] = str(row['Unnamed: 9'])
            if pd.notna(row['Unnamed: 10']):  # put on
                day_data['put_on'] = str(row['Unnamed: 10'])
            if pd.notna(row['Unnamed: 11']):  # end time
                day_data['end_time'] = str(row['Unnamed: 11'])
        elif day_num == 2:
            # Day 2: start_time, took_off, put_on, end_time
            if pd.notna(row['2nd day']):  # start time
                day_data['start_time'] = str(row['2nd day'])
            if pd.notna(row['Unnamed: 13']):  # took off
                day_data['take_off'] = str(row['Unnamed: 13'])
            if pd.notna(row['Unnamed: 14']):  # put on
                day_data['put_on'] = str(row['Unnamed: 14'])
            if pd.notna(row['Unnamed: 15']):  # end time
                day_data['end_time'] = str(row['Unnamed: 15'])
        elif day_num == 3:
            # Day 3: start_time, took_off, put_on, end_time
            if pd.notna(row['3rd day']):  # start time
                day_data['start_time'] = str(row['3rd day'])
            if pd.notna(row['Unnamed: 17']):  # took off
                day_data['take_off'] = str(row['Unnamed: 17'])
            if pd.notna(row['Unnamed: 18']):  # put on
                day_data['put_on'] = str(row['Unnamed: 18'])
            if pd.notna(row['Unnamed: 19']):  # end time
                day_data['end_time'] = str(row['Unnamed: 19'])
        
        extracted_data.append(day_data)

# Create DataFrame
result_df = pd.DataFrame(extracted_data)

# Save to CSV
result_df.to_csv('pig_timestamps_from_excel_fixed.csv', index=False)

print("Extraction completed!")
print(f"Extracted {len(result_df)} rows")
print(f"Columns: {list(result_df.columns)}")

# Show sample data
print("\nSample data for CO-001:")
sample_pig = result_df[result_df['pig_id'] == 'CO-001']
for _, row in sample_pig.iterrows():
    print(f"{row['pig_id']}, {row['day']}: start={row['start_time']}, take_off={row['take_off']}, put_on={row['put_on']}, end={row['end_time']}")

print("\nSample data for CO-002:")
sample_pig = result_df[result_df['pig_id'] == 'CO-002']
for _, row in sample_pig.iterrows():
    print(f"{row['pig_id']}, {row['day']}: start={row['start_time']}, take_off={row['take_off']}, put_on={row['put_on']}, end={row['end_time']}")

