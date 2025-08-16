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
    
    # Create a mapping of actual column names to their positions
    # Based on the header row we saw: ['#PIGD-', 'hybrid serial #', 'remarks', 'date', 'start ', 'events ', 'took off', 'put on', 'end time', ...]
    
    # Map the columns properly
    column_mapping = {
        'pig_id': 'Unnamed: 0',
        'serial_number': 'Unnamed: 1', 
        'remarks': 'Unnamed: 2',
        'day_0_date': '0 day',
        'day_0_start': 'Unnamed: 4',
        'day_0_events': 'Unnamed: 5',
        'day_0_took_off': 'Unnamed: 6',
        'day_0_put_on': 'Unnamed: 7',
        'day_0_end': 'Unnamed: 8',
        'day_1_date': '1st day',
        'day_1_start': 'Unnamed: 10',
        'day_1_events': 'Unnamed: 11',
        'day_1_took_off': 'Unnamed: 12',
        'day_1_put_on': 'Unnamed: 13',
        'day_2_date': '2nd day',
        'day_2_start': 'Unnamed: 15',
        'day_2_events': 'Unnamed: 16',
        'day_2_took_off': 'Unnamed: 17',
        'day_2_put_on': 'Unnamed: 18',
        'day_3_date': '3rd day',
        'day_3_start': 'Unnamed: 20',
        'day_3_events': 'Unnamed: 21',
        'day_3_took_off': 'Unnamed: 22',
        'day_3_put_on': 'Unnamed: 23'
    }
    
    # Extract pig information
    pig_data = []
    
    for idx, row in data_rows.iterrows():
        pig_id = row[column_mapping['pig_id']]
        serial_num = row[column_mapping['serial_number']]
        remarks = row[column_mapping['remarks']]
        
        # Process each day's data
        days_data = {}
        
        # Day 0
        if pd.notna(row[column_mapping['day_0_date']]):
            try:
                start_date = pd.to_datetime(row[column_mapping['day_0_date']])
                days_data['day_0'] = {
                    'date': start_date.strftime('%Y-%m-%d'),
                    'start_time': str(row[column_mapping['day_0_start']]) if pd.notna(row[column_mapping['day_0_start']]) else None,
                    'events': str(row[column_mapping['day_0_events']]) if pd.notna(row[column_mapping['day_0_events']]) else None,
                    'took_off': str(row[column_mapping['day_0_took_off']]) if pd.notna(row[column_mapping['day_0_took_off']]) else None,
                    'put_on': str(row[column_mapping['day_0_put_on']]) if pd.notna(row[column_mapping['day_0_put_on']]) else None,
                    'end_time': str(row[column_mapping['day_0_end']]) if pd.notna(row[column_mapping['day_0_end']]) else None
                }
            except Exception as e:
                days_data['day_0'] = {'date': str(row[column_mapping['day_0_date']]), 'error': f'Invalid date format: {e}'}
        
        # Day 1
        if pd.notna(row[column_mapping['day_1_date']]):
            try:
                start_date = pd.to_datetime(row[column_mapping['day_1_date']])
                days_data['day_1'] = {
                    'date': start_date.strftime('%Y-%m-%d'),
                    'start_time': str(row[column_mapping['day_1_start']]) if pd.notna(row[column_mapping['day_1_start']]) else None,
                    'events': str(row[column_mapping['day_1_events']]) if pd.notna(row[column_mapping['day_1_events']]) else None,
                    'took_off': str(row[column_mapping['day_1_took_off']]) if pd.notna(row[column_mapping['day_1_took_off']]) else None,
                    'put_on': str(row[column_mapping['day_1_put_on']]) if pd.notna(row[column_mapping['day_1_put_on']]) else None,
                    'end_time': str(row[column_mapping['day_1_start']]) if pd.notna(row[column_mapping['day_1_start']]) else None  # Using start as end for day 1
                }
            except Exception as e:
                days_data['day_1'] = {'date': str(row[column_mapping['day_1_date']]), 'error': f'Invalid date format: {e}'}
        
        # Day 2
        if pd.notna(row[column_mapping['day_2_date']]):
            try:
                start_date = pd.to_datetime(row[column_mapping['day_2_date']])
                days_data['day_2'] = {
                    'date': start_date.strftime('%Y-%m-%d'),
                    'start_time': str(row[column_mapping['day_2_start']]) if pd.notna(row[column_mapping['day_2_start']]) else None,
                    'events': str(row[column_mapping['day_2_events']]) if pd.notna(row[column_mapping['day_2_events']]) else None,
                    'took_off': str(row[column_mapping['day_2_took_off']]) if pd.notna(row[column_mapping['day_2_took_off']]) else None,
                    'put_on': str(row[column_mapping['day_2_put_on']]) if pd.notna(row[column_mapping['day_2_put_on']]) else None,
                    'end_time': str(row[column_mapping['day_2_start']]) if pd.notna(row[column_mapping['day_2_start']]) else None  # Using start as end for day 2
                }
            except Exception as e:
                days_data['day_2'] = {'date': str(row[column_mapping['day_2_date']]), 'error': f'Invalid date format: {e}'}
        
        # Day 3
        if pd.notna(row[column_mapping['day_3_date']]):
            try:
                start_date = pd.to_datetime(row[column_mapping['day_3_date']])
                days_data['day_3'] = {
                    'date': start_date.strftime('%Y-%m-%d'),
                    'start_time': str(row[column_mapping['day_3_start']]) if pd.notna(row[column_mapping['day_3_start']]) else None,
                    'events': str(row[column_mapping['day_3_events']]) if pd.notna(row[column_mapping['day_3_events']]) else None,
                    'took_off': str(row[column_mapping['day_3_took_off']]) if pd.notna(row[column_mapping['day_3_took_off']]) else None,
                    'put_on': str(row[column_mapping['day_3_put_on']]) if pd.notna(row[column_mapping['day_3_put_on']]) else None,
                    'end_time': str(row[column_mapping['day_3_start']]) if pd.notna(row[column_mapping['day_3_start']]) else None  # Using start as end for day 3
                }
            except Exception as e:
                days_data['day_3'] = {'date': str(row[column_mapping['day_3_date']]), 'error': f'Invalid date format: {e}'}
        
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
                    if time_value and time_value != 'nan' and time_value != 'None':
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
    
    # Show some debug info
    print(f"\nFirst pig data sample:")
    if pig_data:
        print(f"Pig ID: {pig_data[0]['pig_id']}")
        print(f"Serial: {pig_data[0]['serial_number']}")
        print(f"Days: {list(pig_data[0]['days_data'].keys())}")
        for day, data in pig_data[0]['days_data'].items():
            print(f"  {day}: {data}")


