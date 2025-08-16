import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

def clean_pig_data():
    # Read the Excel file
    df = pd.read_excel('ReportHome75h.xlsx')
    
    # Get the header row (first row) and data rows
    header_row = df.iloc[0]
    data_rows = df.iloc[1:].reset_index(drop=True)
    
    # Create clean column names
    clean_columns = []
    for i, col in enumerate(header_row):
        if pd.isna(col) or col == '':
            clean_columns.append(f'col_{i}')
        else:
            clean_columns.append(str(col).strip())
    
    # Assign clean column names
    data_rows.columns = clean_columns
    
    # Extract pig information
    pig_data = []
    
    for idx, row in data_rows.iterrows():
        pig_id = row['#PIGD-']
        serial_num = row['hybrid serial #']
        remarks = row['remarks']
        
        # Process each day's data
        days_data = {}
        
        # Day 0
        if '0 day' in row and pd.notna(row['0 day']):
            try:
                start_date = pd.to_datetime(row['0 day'])
                days_data['day_0'] = {
                    'date': start_date.strftime('%Y-%m-%d'),
                    'start_time': str(row['start ']) if pd.notna(row['start ']) else None,
                    'events': str(row['events ']) if pd.notna(row['events ']) else None,
                    'took_off': str(row['took off']) if pd.notna(row['took off']) else None,
                    'put_on': str(row['put on']) if pd.notna(row['put on']) else None,
                    'end_time': str(row['end time']) if pd.notna(row['end time']) else None
                }
            except:
                days_data['day_0'] = {'date': str(row['0 day']), 'error': 'Invalid date format'}
        
        # Day 1
        if '1st day' in row and pd.notna(row['1st day']):
            try:
                start_date = pd.to_datetime(row['1st day'])
                days_data['day_1'] = {
                    'date': start_date.strftime('%Y-%m-%d'),
                    'start_time': str(row['start time']) if pd.notna(row['start time']) else None,
                    'events': str(row['events ']) if pd.notna(row['events ']) else None,
                    'took_off': str(row['took off']) if pd.notna(row['took off']) else None,
                    'put_on': str(row['put on']) if pd.notna(row['put on']) else None,
                    'end_time': str(row['end time']) if pd.notna(row['end time']) else None
                }
            except:
                days_data['day_1'] = {'date': str(row['1st day']), 'error': 'Invalid date format'}
        
        # Day 2
        if '2nd day' in row and pd.notna(row['2nd day']):
            try:
                start_date = pd.to_datetime(row['2nd day'])
                days_data['day_2'] = {
                    'date': start_date.strftime('%Y-%m-%d'),
                    'start_time': str(row['start time']) if pd.notna(row['start time']) else None,
                    'events': str(row['events ']) if pd.notna(row['events ']) else None,
                    'took_off': str(row['took off']) if pd.notna(row['took off']) else None,
                    'put_on': str(row['put on']) if pd.notna(row['put on']) else None,
                    'end_time': str(row['end time']) if pd.notna(row['end time']) else None
                }
            except:
                days_data['day_2'] = {'date': str(row['2nd day']), 'error': 'Invalid date format'}
        
        # Day 3
        if '3rd day' in row and pd.notna(row['3rd day']):
            try:
                start_date = pd.to_datetime(row['3rd day'])
                days_data['day_3'] = {
                    'date': start_date.strftime('%Y-%m-%d'),
                    'start_time': str(row['start time']) if pd.notna(row['start time']) else None,
                    'events': str(row['events ']) if pd.notna(row['events ']) else None,
                    'took_off': str(row['took off']) if pd.notna(row['took off']) else None,
                    'put_on': str(row['put on']) if pd.notna(row['put on']) else None,
                    'end_time': str(row['end time']) if pd.notna(row['end time']) else None
                }
            except:
                days_data['day_3'] = {'date': str(row['3rd day']), 'error': 'Invalid date format'}
        
        pig_data.append({
            'pig_id': pig_id,
            'serial_number': serial_num,
            'remarks': remarks,
            'days_data': days_data
        })
    
    return pig_data

def create_machine_readable_csv(pig_data):
    """Create a flat CSV format for machine processing"""
    rows = []
    
    for pig in pig_data:
        pig_id = pig['pig_id']
        serial_num = pig['serial_number']
        remarks = pig['remarks']
        
        for day_key, day_data in pig['days_data'].items():
            if 'error' not in day_data:
                row = {
                    'pig_id': pig_id,
                    'serial_number': serial_num,
                    'remarks': remarks,
                    'day': day_key,
                    'date': day_data.get('date'),
                    'start_time': day_data.get('start_time'),
                    'events': day_data.get('events'),
                    'took_off': day_data.get('took_off'),
                    'put_on': day_data.get('put_on'),
                    'end_time': day_data.get('end_time')
                }
                rows.append(row)
    
    return pd.DataFrame(rows)

def create_timestamp_data(pig_data):
    """Create data with proper datetime timestamps"""
    timestamp_rows = []
    
    for pig in pig_data:
        pig_id = pig['pig_id']
        serial_num = pig['serial_number']
        remarks = pig['remarks']
        
        for day_key, day_data in pig['days_data'].items():
            if 'error' not in day_data and day_data.get('date'):
                base_date = datetime.strptime(day_data['date'], '%Y-%m-%d')
                
                # Process each time field
                for time_field in ['start_time', 'took_off', 'put_on', 'end_time']:
                    time_value = day_data.get(time_field)
                    if time_value and time_value != 'nan':
                        # Clean time value
                        time_str = str(time_value).strip()
                        
                        # Handle various time formats
                        if re.match(r'\d{1,2}:\d{2}:\d{2}', time_str):
                            try:
                                time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
                                full_timestamp = datetime.combine(base_date, time_obj)
                                
                                timestamp_rows.append({
                                    'pig_id': pig_id,
                                    'serial_number': serial_num,
                                    'remarks': remarks,
                                    'day': day_key,
                                    'date': base_date.strftime('%Y-%m-%d'),
                                    'event_type': time_field,
                                    'time': time_str,
                                    'timestamp': full_timestamp.isoformat(),
                                    'events': day_data.get('events')
                                })
                            except:
                                pass
                        elif re.match(r'\d{1,2}:\d{2}', time_str):
                            try:
                                time_obj = datetime.strptime(time_str, '%H:%M').time()
                                full_timestamp = datetime.combine(base_date, time_obj)
                                
                                timestamp_rows.append({
                                    'pig_id': pig_id,
                                    'serial_number': serial_num,
                                    'remarks': remarks,
                                    'day': day_key,
                                    'date': base_date.strftime('%Y-%m-%d'),
                                    'event_type': time_field,
                                    'time': time_str,
                                    'timestamp': full_timestamp.isoformat(),
                                    'events': day_data.get('events')
                                })
                            except:
                                pass
    
    return pd.DataFrame(timestamp_rows)

if __name__ == "__main__":
    # Clean the data
    pig_data = clean_pig_data()
    
    # Create machine-readable formats
    flat_df = create_machine_readable_csv(pig_data)
    timestamp_df = create_timestamp_data(pig_data)
    
    # Save to CSV files
    flat_df.to_csv('pig_wear_times_flat.csv', index=False)
    timestamp_df.to_csv('pig_wear_times_timestamps.csv', index=False)
    
    # Print summary
    print(f"Processed {len(pig_data)} pigs")
    print(f"Created {len(flat_df)} wear time records")
    print(f"Created {len(timestamp_df)} timestamp records")
    
    # Show sample of the data
    print("\nSample of flat data:")
    print(flat_df.head(10))
    
    print("\nSample of timestamp data:")
    print(timestamp_df.head(10))


