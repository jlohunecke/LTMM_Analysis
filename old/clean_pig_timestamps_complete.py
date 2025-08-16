import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

def clean_pig_timestamps_complete():
    # Read the Excel file
    df = pd.read_excel('ReportHome75h.xlsx')
    
    # Get the header row (first row) and data rows
    header_row = df.iloc[0]
    data_rows = df.iloc[1:].reset_index(drop=True)
    
    # Map the columns properly
    column_mapping = {
        'pig_id': 'Unnamed: 0',
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
    
    # Extract pig information with timestamps
    pig_timestamps = []
    
    for idx, row in data_rows.iterrows():
        pig_id = row[column_mapping['pig_id']]
        
        # Get the base date from day_0
        base_date = None
        if pd.notna(row[column_mapping['day_0_date']]):
            try:
                base_date = pd.to_datetime(row[column_mapping['day_0_date']])
            except:
                pass
        
        # Process each day's data
        for day_num in range(4):  # 0, 1, 2, 3
            day_key = f'day_{day_num}'
            date_col = column_mapping[f'{day_key}_date']
            start_col = column_mapping[f'{day_key}_start']
            events_col = column_mapping[f'{day_key}_events']
            took_off_col = column_mapping[f'{day_key}_took_off']
            put_on_col = column_mapping[f'{day_key}_put_on']
            end_col = column_mapping[f'{day_key}_end'] if day_num == 0 else start_col
            
            # Calculate the correct date for each day
            if day_num == 0:
                if pd.notna(row[date_col]) and base_date is not None:
                    date_str = base_date.strftime('%Y-%m-%d')
                else:
                    continue
            else:
                # For days 1-3, calculate consecutive dates
                if base_date is None:
                    continue
                
                # Calculate the date for this day (day_1 = base_date + 1 day, etc.)
                day_date = base_date + timedelta(days=day_num)
                date_str = day_date.strftime('%Y-%m-%d')
                
                # Check if there's any time data for this day
                has_time_data = False
                for col in [start_col, events_col, took_off_col, put_on_col]:
                    if pd.notna(row[col]) and str(row[col]).strip() not in ['nan', 'None', '']:
                        has_time_data = True
                        break
                
                if not has_time_data:
                    continue
            
            # Initialize timestamp record
            timestamp_record = {
                'pig_id': pig_id,
                'day': day_key
            }
            
            # Process start_time
            if pd.notna(row[start_col]):
                start_time = str(row[start_col]).strip()
                if start_time != 'nan' and start_time != 'None' and start_time != '':
                    start_time_clean, start_event = clean_time_string_with_event(start_time)
                    if start_time_clean:
                        timestamp_record['start_time'] = f"{date_str} {start_time_clean}"
                        if start_event:
                            timestamp_record['start_event'] = start_event
            
            # Process events column (this is where most events are stored)
            if pd.notna(row[events_col]):
                events_time = str(row[events_col]).strip()
                if events_time != 'nan' and events_time != 'None' and events_time != '':
                    events_time_clean, events_event = clean_time_string_with_event(events_time)
                    if events_time_clean:
                        timestamp_record['events_time'] = f"{date_str} {events_time_clean}"
                        if events_event:
                            timestamp_record['events_event'] = events_event
            
            # Process end_time
            if day_num == 0 and pd.notna(row[end_col]):
                end_time = str(row[end_col]).strip()
                if end_time != 'nan' and end_time != 'None' and end_time != '':
                    end_time_clean, end_event = clean_time_string_with_event(end_time)
                    if end_time_clean:
                        timestamp_record['end_time'] = f"{date_str} {end_time_clean}"
                        if end_event:
                            timestamp_record['end_event'] = end_event
            elif day_num > 0 and pd.notna(row[start_col]):
                # For other days, use start time as end time
                start_time = str(row[start_col]).strip()
                if start_time != 'nan' and start_time != 'None' and start_time != '':
                    start_time_clean, start_event = clean_time_string_with_event(start_time)
                    if start_time_clean:
                        timestamp_record['end_time'] = f"{date_str} {start_time_clean}"
                        if start_event:
                            timestamp_record['end_event'] = start_event
            
            # Process took_off
            if pd.notna(row[took_off_col]):
                took_off_time = str(row[took_off_col]).strip()
                if took_off_time != 'nan' and took_off_time != 'None' and took_off_time != '':
                    took_off_clean, took_off_event = clean_time_string_with_event(took_off_time)
                    if took_off_clean:
                        timestamp_record['took_off'] = f"{date_str} {took_off_clean}"
                        if took_off_event:
                            timestamp_record['took_off_event'] = took_off_event
            
            # Process put_on
            if pd.notna(row[put_on_col]):
                put_on_time = str(row[put_on_col]).strip()
                if put_on_time != 'nan' and put_on_time != 'None' and put_on_time != '':
                    put_on_clean, put_on_event = clean_time_string_with_event(put_on_time)
                    if put_on_clean:
                        timestamp_record['put_on'] = f"{date_str} {put_on_clean}"
                        if put_on_event:
                            timestamp_record['put_on_event'] = put_on_event
            
            # Only add record if it has at least one timestamp
            if any(key in timestamp_record for key in ['start_time', 'end_time', 'events_time', 'took_off', 'put_on']):
                pig_timestamps.append(timestamp_record)
    
    return pig_timestamps

def clean_time_string_with_event(time_str):
    """Clean and standardize time strings while preserving events"""
    if not time_str or time_str == 'nan' or time_str == 'None':
        return None, None
    
    # Check for timestamp with event pattern (e.g., "08:30:00 - swimming and shower")
    event_pattern = r'^(\d{1,2}:\d{2}:\d{2})\s*[-–]\s*(.+)$'
    event_match = re.match(event_pattern, time_str)
    
    if event_match:
        time_part = event_match.group(1)
        event_part = event_match.group(2).strip()
        return time_part, event_part
    
    # Check for timestamp with event pattern without seconds (e.g., "08:30 - swimming and shower")
    event_pattern_no_sec = r'^(\d{1,2}:\d{2})\s*[-–]\s*(.+)$'
    event_match_no_sec = re.match(event_pattern_no_sec, time_str)
    
    if event_match_no_sec:
        time_part = event_match_no_sec.group(1) + ':00'
        event_part = event_match_no_sec.group(2).strip()
        return time_part, event_part
    
    # Handle pure time strings (no events)
    # Remove question marks and other punctuation
    clean_time = re.sub(r'\?', '', time_str)
    clean_time = re.sub(r'[^\d:]', '', clean_time)
    
    # Handle various time formats
    if re.match(r'^\d{1,2}:\d{2}:\d{2}$', clean_time):
        return clean_time, None
    elif re.match(r'^\d{1,2}:\d{2}$', clean_time):
        return clean_time + ':00', None
    elif re.match(r'^\d{1,2}:\d{2}:\d{2}:\d{2}$', clean_time):
        # Handle HH:MM:SS:SS format (remove last part)
        parts = clean_time.split(':')
        return f"{parts[0]}:{parts[1]}:{parts[2]}", None
    
    return None, None

def create_complete_timestamp_csv(pig_timestamps):
    """Create a CSV with timestamps and events"""
    if not pig_timestamps:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(pig_timestamps)
    
    # Ensure all timestamp and event columns exist
    for col in ['start_time', 'end_time', 'events_time', 'took_off', 'put_on']:
        if col not in df.columns:
            df[col] = None
        event_col = f'{col}_event'
        if event_col not in df.columns:
            df[event_col] = None
    
    # Reorder columns for better readability
    column_order = ['pig_id', 'day', 'start_time', 'start_event', 'end_time', 'end_event', 'events_time', 'events_event', 'took_off', 'took_off_event', 'put_on', 'put_on_event']
    # Only include columns that exist
    column_order = [col for col in column_order if col in df.columns]
    df = df[column_order]
    
    return df

if __name__ == "__main__":
    # Clean the data
    pig_timestamps = clean_pig_timestamps_complete()
    
    # Create complete CSV
    complete_df = create_complete_timestamp_csv(pig_timestamps)
    
    # Save to CSV file
    complete_df.to_csv('pig_timestamps_complete.csv', index=False)
    
    # Print summary
    print(f"Processed {len(pig_timestamps)} timestamp records")
    print(f"Unique pigs: {complete_df['pig_id'].nunique()}")
    
    # Show statistics by day
    print(f"\n=== RECORDS BY DAY ===")
    day_counts = complete_df['day'].value_counts().sort_index()
    for day, count in day_counts.items():
        print(f"{day}: {count} records")
    
    # Show sample of the data with events
    print(f"\n=== SAMPLE DATA WITH EVENTS ===")
    print(complete_df.head(20).to_string(index=False))
    
    # Show statistics
    print(f"\n=== TIMESTAMP STATISTICS ===")
    for col in ['start_time', 'end_time', 'events_time', 'took_off', 'put_on']:
        if col in complete_df.columns:
            count = complete_df[col].notna().sum()
            print(f"{col}: {count} records")
    
    # Show event statistics
    print(f"\n=== EVENT STATISTICS ===")
    for col in ['start_event', 'end_event', 'events_event', 'took_off_event', 'put_on_event']:
        if col in complete_df.columns:
            count = complete_df[col].notna().sum()
            print(f"{col}: {count} records")
    
    # Show some examples with events
    print(f"\n=== EXAMPLES WITH EVENTS ===")
    # Find records with events
    event_columns = [col for col in complete_df.columns if col.endswith('_event')]
    if event_columns:
        records_with_events = complete_df[complete_df[event_columns].notna().any(axis=1)]
        if len(records_with_events) > 0:
            print(f"Found {len(records_with_events)} records with events:")
            for _, row in records_with_events.head(10).iterrows():
                print(f"  {row['pig_id']} ({row['day']}):")
                for col in ['start_time', 'end_time', 'events_time', 'took_off', 'put_on']:
                    if col in complete_df.columns and pd.notna(row[col]):
                        event_col = f'{col}_event'
                        event_info = f" - {row[event_col]}" if pd.notna(row.get(event_col)) else ""
                        print(f"    {col}: {row[col]}{event_info}")
                print()
        else:
            print("No records found with events")
    else:
        print("No event columns found")


