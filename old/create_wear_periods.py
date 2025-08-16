import pandas as pd
import numpy as np
from datetime import datetime

def parse_datetime(date_str):
    """Parse datetime string in format 'M/D/YY H:MM' or 'M/D/YYYY H:MM'"""
    if pd.isna(date_str) or date_str.strip() == '':
        return None
    
    # Handle different date formats
    try:
        # Try MM/DD/YY format first
        return datetime.strptime(date_str.strip(), '%m/%d/%y %H:%M')
    except ValueError:
        try:
            # Try MM/DD/YYYY format
            return datetime.strptime(date_str.strip(), '%m/%d/%Y %H:%M')
        except ValueError:
            print(f"Could not parse date: {date_str}")
            return None

def create_wear_periods():
    """Create wear periods file from wear_times.csv"""
    
    # Read the wear_times.csv file
    df = pd.read_csv('wear_times.csv')
    
    # Clean column names
    df.columns = df.columns.str.strip()
    
    # Group by pig_id
    pig_groups = df.groupby('pig_id')
    
    wear_periods_data = []
    
    for pig_id, pig_data in pig_groups:
        print(f"Processing {pig_id}...")
        
        # Initialize wear periods for this pig
        wear_periods = []
        
        # Sort by day to ensure chronological order
        pig_data = pig_data.sort_values('day')
        
        for _, row in pig_data.iterrows():
            # Parse all datetime fields
            start_time = parse_datetime(row['start_time'])
            end_time = parse_datetime(row['end_time'])
            take_off_1 = parse_datetime(row['take_off_1'])
            put_on_1 = parse_datetime(row['put_on_1'])
            take_off_2 = parse_datetime(row['take_off_2'])
            put_on_2 = parse_datetime(row['put_on_2'])
            
            # Create wear periods for this day
            day_periods = []
            
            # First period: start_time to take_off_1 (if both exist)
            if start_time and take_off_1:
                day_periods.append((start_time, take_off_1))
            
            # Second period: put_on_1 to take_off_2 (if both exist)
            if put_on_1 and take_off_2:
                day_periods.append((put_on_1, take_off_2))
            elif put_on_1 and not take_off_2:
                # If no take_off_2, use end_time if available
                if end_time:
                    day_periods.append((put_on_1, end_time))
                else:
                    # If no end_time, this period continues to next day
                    day_periods.append((put_on_1, None))
            
            # Third period: put_on_2 to end_time (if both exist)
            if put_on_2 and end_time:
                day_periods.append((put_on_2, end_time))
            elif put_on_2 and not end_time:
                # If no end_time, this period continues to next day
                day_periods.append((put_on_2, None))
            
            # If no take_off/put_on events, but we have start and end times
            if not day_periods and start_time and end_time:
                day_periods.append((start_time, end_time))
            
            # If only start_time exists (continuous wear)
            if not day_periods and start_time and not end_time:
                day_periods.append((start_time, None))
            
            wear_periods.extend(day_periods)
        
        # Merge consecutive periods that span across days
        merged_periods = []
        if wear_periods:
            current_start = wear_periods[0][0]
            current_end = wear_periods[0][1]
            
            for start, end in wear_periods[1:]:
                # If current period has no end and new period has no start, they're consecutive
                if current_end is None and start is None:
                    # This is a continuation, keep current_start and update current_end
                    current_end = end
                elif current_end is None and start is not None:
                    # Gap between periods, end current and start new
                    merged_periods.append((current_start, None))  # End at end of day
                    current_start = start
                    current_end = end
                else:
                    # Normal case, end current and start new
                    merged_periods.append((current_start, current_end))
                    current_start = start
                    current_end = end
            
            # Add the last period
            merged_periods.append((current_start, current_end))
        
        # Create row for this pig
        pig_row = {'pig_id': pig_id}
        
        # Add wear periods as columns
        for i, (start, end) in enumerate(merged_periods, 1):
            pig_row[f'start_{i}'] = start.strftime('%m/%d/%Y %H:%M') if start else ''
            pig_row[f'end_{i}'] = end.strftime('%m/%d/%Y %H:%M') if end else ''
        
        wear_periods_data.append(pig_row)
    
    # Create DataFrame and save to CSV
    wear_periods_df = pd.DataFrame(wear_periods_data)
    
    # Reorder columns to have pig_id first, then start_1, end_1, start_2, end_2, etc.
    cols = ['pig_id']
    max_periods = max(len(row) - 1 for row in wear_periods_data) // 2  # -1 for pig_id, //2 for start/end pairs
    
    for i in range(1, max_periods + 1):
        cols.extend([f'start_{i}', f'end_{i}'])
    
    # Add any missing columns with empty values
    for col in cols:
        if col not in wear_periods_df.columns:
            wear_periods_df[col] = ''
    
    # Reorder columns
    wear_periods_df = wear_periods_df[cols]
    
    # Save to CSV
    wear_periods_df.to_csv('wear_periods.csv', index=False)
    print(f"Wear periods file created: wear_periods.csv")
    print(f"Total pigs processed: {len(wear_periods_data)}")
    
    return wear_periods_df

if __name__ == "__main__":
    wear_periods_df = create_wear_periods()
    print("\nFirst few rows of the wear periods file:")
    print(wear_periods_df.head())
