import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

def clean_pig_timestamps_simple():
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
        
        # Process each day's data
        for day_num in range(4):  # 0, 1, 2, 3
            day_key = f'day_{day_num}'
            date_col = column_mapping[f'{day_key}_date']
            start_col = column_mapping[f'{day_key}_start']
            took_off_col = column_mapping[f'{day_key}_took_off']
            put_on_col = column_mapping[f'{day_key}_put_on']
            end_col = column_mapping[f'{day_key}_end'] if day_num == 0 else start_col
            
            if pd.notna(row[date_col]):
                try:
                    start_date = pd.to_datetime(row[date_col])
                    date_str = start_date.strftime('%Y-%m-%d')
                    
                    # Initialize timestamp record
                    timestamp_record = {
                        'pig_id': pig_id,
                        'day': day_key
                    }
                    
                    # Process start_time
                    if pd.notna(row[start_col]):
                        start_time = str(row[start_col]).strip()
                        if start_time != 'nan' and start_time != 'None':
                            start_time_clean = clean_time_string(start_time)
                            if start_time_clean:
                                timestamp_record['start_time'] = f"{date_str} {start_time_clean}"
                    
                    # Process end_time
                    if day_num == 0 and pd.notna(row[end_col]):
                        end_time = str(row[end_col]).strip()
                        if end_time != 'nan' and end_time != 'None':
                            end_time_clean = clean_time_string(end_time)
                            if end_time_clean:
                                timestamp_record['end_time'] = f"{date_str} {end_time_clean}"
                    elif day_num > 0 and pd.notna(row[start_col]):
                        # For other days, use start time as end time
                        start_time = str(row[start_col]).strip()
                        if start_time != 'nan' and start_time != 'None':
                            start_time_clean = clean_time_string(start_time)
                            if start_time_clean:
                                timestamp_record['end_time'] = f"{date_str} {start_time_clean}"
                    
                    # Process took_off
                    if pd.notna(row[took_off_col]):
                        took_off_time = str(row[took_off_col]).strip()
                        if took_off_time != 'nan' and took_off_time != 'None':
                            took_off_clean = clean_time_string(took_off_time)
                            if took_off_clean:
                                timestamp_record['took_off'] = f"{date_str} {took_off_clean}"
                    
                    # Process put_on
                    if pd.notna(row[put_on_col]):
                        put_on_time = str(row[put_on_col]).strip()
                        if put_on_time != 'nan' and put_on_time != 'None':
                            put_on_clean = clean_time_string(put_on_time)
                            if put_on_clean:
                                timestamp_record['put_on'] = f"{date_str} {put_on_clean}"
                    
                    # Only add record if it has at least one timestamp
                    if any(key in timestamp_record for key in ['start_time', 'end_time', 'took_off', 'put_on']):
                        pig_timestamps.append(timestamp_record)
                        
                except Exception as e:
                    # Skip records with date parsing errors
                    pass
    
    return pig_timestamps

def clean_time_string(time_str):
    """Clean and standardize time strings"""
    if not time_str or time_str == 'nan' or time_str == 'None':
        return None
    
    # Remove common text annotations
    time_str = re.sub(r'\s*shower\s*', '', time_str, flags=re.IGNORECASE)
    time_str = re.sub(r'\s*rest\s*', '', time_str, flags=re.IGNORECASE)
    time_str = re.sub(r'\s*fall\s*', '', time_str, flags=re.IGNORECASE)
    time_str = re.sub(r'\s*slept with it\s*', '', time_str, flags=re.IGNORECASE)
    time_str = re.sub(r'\s*date\s*', '', time_str, flags=re.IGNORECASE)
    time_str = re.sub(r'\s*swimming and shower\s*', '', time_str, flags=re.IGNORECASE)
    time_str = re.sub(r'\s*sometime in the evening\s*', '', time_str, flags=re.IGNORECASE)
    
    # Remove question marks and other punctuation
    time_str = re.sub(r'\?', '', time_str)
    time_str = re.sub(r'[^\d:]', '', time_str)
    
    # Handle various time formats
    if re.match(r'^\d{1,2}:\d{2}:\d{2}$', time_str):
        return time_str
    elif re.match(r'^\d{1,2}:\d{2}$', time_str):
        return time_str + ':00'
    elif re.match(r'^\d{1,2}:\d{2}:\d{2}:\d{2}$', time_str):
        # Handle HH:MM:SS:SS format (remove last part)
        parts = time_str.split(':')
        return f"{parts[0]}:{parts[1]}:{parts[2]}"
    
    return None

def create_simple_timestamp_csv(pig_timestamps):
    """Create a simple CSV with just pig_id, day, and timestamps"""
    if not pig_timestamps:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(pig_timestamps)
    
    # Ensure all timestamp columns exist
    for col in ['start_time', 'end_time', 'took_off', 'put_on']:
        if col not in df.columns:
            df[col] = None
    
    # Reorder columns for better readability
    column_order = ['pig_id', 'day', 'start_time', 'end_time', 'took_off', 'put_on']
    df = df[column_order]
    
    return df

if __name__ == "__main__":
    # Clean the data
    pig_timestamps = clean_pig_timestamps_simple()
    
    # Create simple CSV
    simple_df = create_simple_timestamp_csv(pig_timestamps)
    
    # Save to CSV file
    simple_df.to_csv('pig_timestamps_simple.csv', index=False)
    
    # Print summary
    print(f"Processed {len(pig_timestamps)} timestamp records")
    print(f"Unique pigs: {simple_df['pig_id'].nunique()}")
    
    # Show statistics by day
    print(f"\n=== RECORDS BY DAY ===")
    day_counts = simple_df['day'].value_counts().sort_index()
    for day, count in day_counts.items():
        print(f"{day}: {count} records")
    
    # Show sample of the data
    print(f"\n=== SAMPLE DATA ===")
    print(simple_df.head(15).to_string(index=False))
    
    # Show statistics
    print(f"\n=== TIMESTAMP STATISTICS ===")
    for col in ['start_time', 'end_time', 'took_off', 'put_on']:
        count = simple_df[col].notna().sum()
        print(f"{col}: {count} records")
    
    # Show some examples with all timestamps
    print(f"\n=== EXAMPLES WITH ALL TIMESTAMPS ===")
    complete_records = simple_df.dropna(subset=['start_time', 'end_time', 'took_off', 'put_on'])
    if len(complete_records) > 0:
        print(f"Found {len(complete_records)} records with all 4 timestamps:")
        for _, row in complete_records.head(5).iterrows():
            print(f"  {row['pig_id']} ({row['day']}):")
            print(f"    Start: {row['start_time']}")
            print(f"    End: {row['end_time']}")
            print(f"    Took off: {row['took_off']}")
            print(f"    Put on: {row['put_on']}")
            print()
    else:
        print("No records found with all 4 timestamps")


