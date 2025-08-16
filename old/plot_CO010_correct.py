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

def get_wear_periods_manual():
    """Manually define the correct wear periods based on the wear_times.csv data"""
    
    # Based on the wear_times.csv data for CO-010:
    # Day 0 (2011-01-05): start_time: 12:59, take_off_1: 14:30, put_on_1: 16:00
    # Day 1 (2011-01-06): all empty (continuous wear)
    # Day 2 (2011-01-07): take_off_1: 06:45, put_on_1: 10:10, end_time: 23:30
    # Day 3 (2011-01-08): start_time: 06:30, take_off_1: 07:00, put_on_1: 10:10, end_time: 13:00
    
    wear_periods = [
        # Day 0 (2011-01-05)
        (parse_timestamp('2011-01-05 12:59:00'), parse_timestamp('2011-01-05 14:30:00')),  # start_time to take_off_1
        (parse_timestamp('2011-01-05 16:00:00'), parse_timestamp('2011-01-05 23:59:00')),  # put_on_1 to end of day
        
        # Day 1 (2011-01-06) - continuous wear
        (parse_timestamp('2011-01-06 00:00:00'), parse_timestamp('2011-01-06 23:59:00')),
        
        # Day 2 (2011-01-07)
        (parse_timestamp('2011-01-07 00:00:00'), parse_timestamp('2011-01-07 06:45:00')),  # start of day to take_off_1
        (parse_timestamp('2011-01-07 10:10:00'), parse_timestamp('2011-01-07 23:30:00')),  # put_on_1 to end_time
        
        # Day 3 (2011-01-08)
        (parse_timestamp('2011-01-08 06:30:00'), parse_timestamp('2011-01-08 07:00:00')),  # start_time to take_off_1
        (parse_timestamp('2011-01-08 10:10:00'), parse_timestamp('2011-01-08 13:00:00')),  # put_on_1 to end_time
    ]
    
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
        gap_duration = (wear_periods[0][0] - data_start).total_seconds() / 60  # minutes
        if gap_duration > 1:  # Only include gaps longer than 1 minute
            non_wear_periods.append((data_start, wear_periods[0][0]))
    
    # Check gaps between wear periods
    for i in range(len(wear_periods) - 1):
        current_end = wear_periods[i][1]
        next_start = wear_periods[i + 1][0]
        if current_end < next_start:
            gap_duration = (next_start - current_end).total_seconds() / 60  # minutes
            if gap_duration > 1:  # Only include gaps longer than 1 minute
                non_wear_periods.append((current_end, next_start))
    
    # Check if there's a gap after the last wear period
    if wear_periods[-1][1] < data_end:
        gap_duration = (data_end - wear_periods[-1][1]).total_seconds() / 60  # minutes
        if gap_duration > 1:  # Only include gaps longer than 1 minute
            non_wear_periods.append((wear_periods[-1][1], data_end))
    
    return non_wear_periods

def plot_CO010_with_non_wear_periods():
    """Plot CO010 triaxial data with non-wear periods marked as red bands"""
    
    # Read the triaxial data
    print("Reading CO010 data...")
    data = pd.read_csv('minute_level/CO010.csv')
    data['timestamp'] = pd.to_datetime(data['timestamp']).dt.tz_localize(None)
    
    # Get wear periods using manual definition
    wear_periods = get_wear_periods_manual()
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
    output_filename = "CO010_triaxial_with_non_wear_periods_correct.png"
    fig.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"\nSaved plot as {output_filename}")
    
    # Show the plot
    plt.show()
    
    return fig

if __name__ == "__main__":
    plot_CO010_with_non_wear_periods()
