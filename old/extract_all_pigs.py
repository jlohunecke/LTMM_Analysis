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
    if pd.isna(pig_id) or pig_id == '#PIGD-' or not str(pig_id).startswith(('CO-', 'FL-')):
        continue
    
    # Get base date from day_0
    base_date = row['0 day']
    
    # If no date is available, use a fallback date based on pig ID
    # This ensures all pigs are included even if they don't have dates
    if pd.isna(base_date):
        # Use a fallback date - we'll use a default date and adjust based on pig number
        try:
            pig_num = int(pig_id.split('-')[1])
            # Use a base date and add days based on pig number to spread them out
            base_date = pd.to_datetime('2010-01-01') + pd.Timedelta(days=pig_num)
        except:
            # If we can't parse the pig number, use a default date
            base_date = pd.to_datetime('2010-01-01')
    else:
        # Convert to datetime if it's not already
        if isinstance(base_date, str):
            try:
                base_date = pd.to_datetime(base_date)
            except:
                # If parsing fails, use fallback
                try:
                    pig_num = int(pig_id.split('-')[1])
                    base_date = pd.to_datetime('2010-01-01') + pd.Timedelta(days=pig_num)
                except:
                    base_date = pd.to_datetime('2010-01-01')
    
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
        
        # Helper function to combine date with time string
        def combine_date_with_time(date_obj, time_str):
            if pd.isna(time_str) or str(time_str).strip() == '':
                return None
            time_str = str(time_str)
            # Extract just the time part (before any notes)
            time_part = time_str.split(' - ')[0].split('?')[0].strip()
            if ':' in time_part:
                try:
                    # Parse the time
                    if len(time_part.split(':')) == 2:
                        time_part += ':00'  # Add seconds if missing
                    time_obj = datetime.strptime(time_part, '%H:%M:%S').time()
                    # Combine date and time
                    combined = datetime.combine(date_obj.date(), time_obj)
                    # Add back any notes
                    if ' - ' in time_str:
                        combined_str = combined.strftime('%Y-%m-%d %H:%M:%S') + ' - ' + time_str.split(' - ', 1)[1]
                    elif '?' in time_str:
                        combined_str = combined.strftime('%Y-%m-%d %H:%M:%S') + '?'
                    else:
                        combined_str = combined.strftime('%Y-%m-%d %H:%M:%S')
                    return combined_str
                except:
                    return time_str  # Return original if parsing fails
            return time_str  # Return original if no time format
        
        # Map columns based on day
        if day_num == 0:
            # Day 0: date, start, took_off, put_on, end_time
            if pd.notna(row['Unnamed: 4']):  # start time
                day_data['start_time'] = combine_date_with_time(target_date, row['Unnamed: 4'])
            if pd.notna(row['Unnamed: 5']):  # took off
                day_data['take_off'] = combine_date_with_time(target_date, row['Unnamed: 5'])
            if pd.notna(row['Unnamed: 6']):  # put on
                day_data['put_on'] = combine_date_with_time(target_date, row['Unnamed: 6'])
            if pd.notna(row['Unnamed: 7']):  # end time
                day_data['end_time'] = combine_date_with_time(target_date, row['Unnamed: 7'])
        elif day_num == 1:
            # Day 1: start_time, took_off, put_on, end_time
            if pd.notna(row['1st day']):  # start time
                day_data['start_time'] = combine_date_with_time(target_date, row['1st day'])
            if pd.notna(row['Unnamed: 9']):  # took off
                day_data['take_off'] = combine_date_with_time(target_date, row['Unnamed: 9'])
            if pd.notna(row['Unnamed: 10']):  # put on
                day_data['put_on'] = combine_date_with_time(target_date, row['Unnamed: 10'])
            if pd.notna(row['Unnamed: 11']):  # end time
                day_data['end_time'] = combine_date_with_time(target_date, row['Unnamed: 11'])
        elif day_num == 2:
            # Day 2: start_time, took_off, put_on, end_time
            if pd.notna(row['2nd day']):  # start time
                day_data['start_time'] = combine_date_with_time(target_date, row['2nd day'])
            if pd.notna(row['Unnamed: 13']):  # took off
                day_data['take_off'] = combine_date_with_time(target_date, row['Unnamed: 13'])
            if pd.notna(row['Unnamed: 14']):  # put on
                day_data['put_on'] = combine_date_with_time(target_date, row['Unnamed: 14'])
            if pd.notna(row['Unnamed: 15']):  # end time
                day_data['end_time'] = combine_date_with_time(target_date, row['Unnamed: 15'])
        elif day_num == 3:
            # Day 3: start_time, took_off, put_on, end_time
            if pd.notna(row['3rd day']):  # start time
                day_data['start_time'] = combine_date_with_time(target_date, row['3rd day'])
            if pd.notna(row['Unnamed: 17']):  # took off
                day_data['take_off'] = combine_date_with_time(target_date, row['Unnamed: 17'])
            if pd.notna(row['Unnamed: 18']):  # put on
                day_data['put_on'] = combine_date_with_time(target_date, row['Unnamed: 18'])
            if pd.notna(row['Unnamed: 19']):  # end time
                day_data['end_time'] = combine_date_with_time(target_date, row['Unnamed: 19'])
        
        extracted_data.append(day_data)

# Create DataFrame
result_df = pd.DataFrame(extracted_data)

# Save to CSV
result_df.to_csv('pig_timestamps_all_pigs.csv', index=False)

print("Complete extraction with ALL pigs (CO- and FL-) completed!")
print(f"Extracted {len(result_df)} rows")
print(f"Columns: {list(result_df.columns)}")

# Show pig count comparison
excel_pigs = set(df[df['Unnamed: 0'].str.startswith(('CO-', 'FL-'), na=False)]['Unnamed: 0'].unique())
csv_pigs = set(result_df['pig_id'].unique())
print(f"\nPigs in Excel file: {len(excel_pigs)}")
print(f"Pigs in our CSV: {len(csv_pigs)}")
print(f"All pigs included: {excel_pigs == csv_pigs}")

if excel_pigs != csv_pigs:
    missing = excel_pigs - csv_pigs
    extra = csv_pigs - excel_pigs
    print(f"Missing pigs: {missing}")
    print(f"Extra pigs: {extra}")

# Show breakdown by pig type
co_pigs = [p for p in csv_pigs if p.startswith('CO-')]
fl_pigs = [p for p in csv_pigs if p.startswith('FL-')]
print(f"\nCO pigs: {len(co_pigs)}")
print(f"FL pigs: {len(fl_pigs)}")

# Show sample data for FL pigs
print("\nSample data for FL-003:")
sample_pig = result_df[result_df['pig_id'] == 'FL-003']
for _, row in sample_pig.iterrows():
    print(f"{row['pig_id']}, {row['day']}: start={row['start_time']}, take_off={row['take_off']}, put_on={row['put_on']}, end={row['end_time']}")

