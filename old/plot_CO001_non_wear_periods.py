import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np

def parse_timestamp(timestamp_str):
    """Parse timestamp string to datetime object"""
    if pd.isna(timestamp_str) or timestamp_str == '':
        return None
    try:
        # Handle different timestamp formats
        if 'T' in str(timestamp_str):
            return pd.to_datetime(timestamp_str)
        else:
            return pd.to_datetime(timestamp_str)
    except:
        return None

def get_wear_periods(wear_times_df, pig_id, data_df):
    """Extract wear periods for a specific pig"""
    pig_data = wear_times_df[wear_times_df['pig_id'] == pig_id].copy()
    wear_periods = []
    
    print(f"Processing {len(pig_data)} rows for {pig_id}")
    
    for idx, row in pig_data.iterrows():
        periods = []
        print(f"\nRow {idx}:")
        print(f"  start_time: {row['start_time']}")
        print(f"  take_off_1: {row['take_off_1']}")
        print(f"  put_on_1: {row['put_on_1']}")
        print(f"  take_off_2: {row['take_off_2']}")
        print(f"  put_on_2: {row['put_on_2']}")
        print(f"  end_time: {row['end_time']}")
        
        # Extract day from the row to get the actual data range for that day
        day_str = row['day']
        if day_str == 'day_0':
            day_date = '2011-01-05'
        elif day_str == 'day_1':
            day_date = '2011-01-06'
        elif day_str == 'day_2':
            day_date = '2011-01-07'
        elif day_str == 'day_3':
            day_date = '2011-01-08'
        else:
            day_date = '2011-01-05'  # Default fallback
        
        # Get the actual data range for this day from the triaxial data
        day_start = parse_timestamp(f"{day_date} 00:00:00")
        day_end = parse_timestamp(f"{day_date} 23:59:59")
        
        # Filter data for this day
        day_data = data_df[(data_df['timestamp'] >= day_start) & (data_df['timestamp'] <= day_end)]
        
        print(f"  Data for {day_date}: {len(day_data)} records")
        
        if len(day_data) > 0:
            actual_start = day_data['timestamp'].min()
            actual_end = day_data['timestamp'].max()
        else:
            # If no data for this day, use the day boundaries
            actual_start = day_start
            actual_end = day_end
        
        # Get or create start_time (use actual data start if missing)
        if not pd.isna(row['start_time']) and str(row['start_time']).strip() != '':
            start_time = parse_timestamp(row['start_time'])
        else:
            start_time = actual_start
        
        # Get or create end_time (use actual data end if missing)
        if not pd.isna(row['end_time']) and str(row['end_time']).strip() != '':
            end_time = parse_timestamp(row['end_time'])
        else:
            end_time = actual_end
        
        print(f"  Actual data range for {day_date}: {actual_start} to {actual_end}")
        print(f"  Using start_time: {start_time}")
        print(f"  Using end_time: {end_time}")
        
        # Build wear periods based on the correct logic
        # Case 1: If there's a start_time and take_off_1, wear from start_time to take_off_1
        if (not pd.isna(row['start_time']) and str(row['start_time']).strip() != '' and
            not pd.isna(row['take_off_1']) and str(row['take_off_1']).strip() != ''):
            start = parse_timestamp(row['start_time'])
            take_off = parse_timestamp(row['take_off_1'])
            if start and take_off and start < take_off:
                periods.append((start, take_off))
                print(f"  Added wear period 1: {start} to {take_off}")
        
        # Case 2: If there's a put_on_1 and take_off_2, wear from put_on_1 to take_off_2
        if (not pd.isna(row['put_on_1']) and str(row['put_on_1']).strip() != '' and
            not pd.isna(row['take_off_2']) and str(row['take_off_2']).strip() != ''):
            put_on = parse_timestamp(row['put_on_1'])
            take_off = parse_timestamp(row['take_off_2'])
            if put_on and take_off and put_on < take_off:
                periods.append((put_on, take_off))
                print(f"  Added wear period 2: {put_on} to {take_off}")
        
        # Case 3: If there's a put_on_1 but no take_off_2, wear from put_on_1 to end_time
        elif (not pd.isna(row['put_on_1']) and str(row['put_on_1']).strip() != ''):
            put_on = parse_timestamp(row['put_on_1'])
            if put_on and end_time and put_on < end_time:
                periods.append((put_on, end_time))
                print(f"  Added wear period 3: {put_on} to {end_time}")
        
        # Case 4: If no take_off_1 and no put_on_1, the entire day is a wear period
        elif ((pd.isna(row['take_off_1']) or str(row['take_off_1']).strip() == '') and
              (pd.isna(row['put_on_1']) or str(row['put_on_1']).strip() == '')):
            if start_time and end_time and start_time < end_time:
                periods.append((start_time, end_time))
                print(f"  Added continuous wear period: {start_time} to {end_time}")
        
        wear_periods.extend(periods)
    
    return wear_periods

def get_non_wear_periods(wear_periods, data_start, data_end):
    """Calculate non-wear periods based on wear periods and data range"""
    non_wear_periods = []
    
    # Sort wear periods by start time
    wear_periods = sorted(wear_periods, key=lambda x: x[0])
    
    # If no wear periods, the entire data range is non-wear
    if not wear_periods:
        non_wear_periods.append((data_start, data_end))
        return non_wear_periods
    
    # Check if there's a gap before the first wear period
    if wear_periods[0][0] > data_start:
        non_wear_periods.append((data_start, wear_periods[0][0]))
    
    # Check gaps between wear periods
    for i in range(len(wear_periods) - 1):
        current_end = wear_periods[i][1]
        next_start = wear_periods[i + 1][0]
        if current_end < next_start:
            non_wear_periods.append((current_end, next_start))
    
    # Check if there's a gap after the last wear period
    if wear_periods[-1][1] < data_end:
        non_wear_periods.append((wear_periods[-1][1], data_end))
    
    return non_wear_periods

def plot_CO010_with_non_wear_periods():
    """Plot CO010 triaxial data with non-wear periods marked as red bands"""
    
    # Read the triaxial data
    print("Reading CO010 data...")
    data = pd.read_csv('minute_level/CO010.csv')
    data['timestamp'] = pd.to_datetime(data['timestamp']).dt.tz_localize(None)
    
    # Read wear times data
    print("Reading wear times data...")
    wear_times_df = pd.read_csv('wear_times.csv')
    
    # Clean column names (remove spaces)
    wear_times_df.columns = wear_times_df.columns.str.strip()
    
    # Clean pig_id column (remove spaces)
    wear_times_df['pig_id'] = wear_times_df['pig_id'].str.strip()
    
    # Get wear periods for CO-010
    wear_periods = get_wear_periods(wear_times_df, 'CO-010', data)
    print(f"Found {len(wear_periods)} wear periods for CO-010")
    
    # Get non-wear periods
    data_start = data['timestamp'].min()
    data_end = data['timestamp'].max()
    non_wear_periods = get_non_wear_periods(wear_periods, data_start, data_end)
    print(f"Found {len(non_wear_periods)} non-wear periods")
    
    # Print wear and non-wear periods for debugging
    print("\nWear periods:")
    for i, (start, end) in enumerate(wear_periods):
        print(f"  {i+1}: {start} to {end}")
    
    print("\nNon-wear periods:")
    for i, (start, end) in enumerate(non_wear_periods):
        print(f"  {i+1}: {start} to {end}")
    
    # Create the plot
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('CO010 Triaxial Data with Non-Wear Periods Marked (Red Bands)', fontsize=16)
    
    # Plot X, Y, Z data
    ax1.plot(data['timestamp'], data['x'], label='X-axis', alpha=0.7)
    ax1.set_ylabel('X-axis (g)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(data['timestamp'], data['y'], label='Y-axis', alpha=0.7, color='orange')
    ax2.set_ylabel('Y-axis (g)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    ax3.plot(data['timestamp'], data['z'], label='Z-axis', alpha=0.7, color='green')
    ax3.set_ylabel('Z-axis (g)')
    ax3.set_xlabel('Time')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Add red bands for non-wear periods
    for i, (start_time, end_time) in enumerate(non_wear_periods):
        # Only show bands that overlap with the data time range
        if start_time <= data['timestamp'].max() and end_time >= data['timestamp'].min():
            label = 'Non-Wear Period' if i == 0 else ""
            ax1.axvspan(start_time, end_time, alpha=0.3, color='red', label=label)
            ax2.axvspan(start_time, end_time, alpha=0.3, color='red', label=label)
            ax3.axvspan(start_time, end_time, alpha=0.3, color='red', label=label)
    
    # Format x-axis
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    ax3.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
    
    # Add legend for non-wear periods
    if non_wear_periods:
        ax1.legend()
        ax2.legend()
        ax3.legend()
    
    plt.tight_layout()
    
    # Save the plot
    output_filename = "CO010_triaxial_with_non_wear_periods.png"
    fig.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"\nSaved plot as {output_filename}")
    
    # Show the plot
    plt.show()
    
    return fig

if __name__ == "__main__":
    plot_CO010_with_non_wear_periods()
