import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os
import glob
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

def get_wear_periods(wear_times_df, pig_id):
    """Extract wear periods for a specific pig"""
    pig_data = wear_times_df[wear_times_df['pig_id'] == pig_id].copy()
    wear_periods = []
    
    for _, row in pig_data.iterrows():
        periods = []
        
        # Check if there's a start_time and end_time for the day
        if not pd.isna(row['start_time']) and not pd.isna(row['end_time']):
            start = parse_timestamp(row['start_time'])
            end = parse_timestamp(row['end_time'])
            if start and end:
                periods.append((start, end))
        
        # Check take_off and put_on periods
        if not pd.isna(row['take_off_1']) and not pd.isna(row['put_on_1']):
            take_off = parse_timestamp(row['take_off_1'])
            put_on = parse_timestamp(row['put_on_1'])
            if take_off and put_on:
                periods.append((take_off, put_on))
        
        if not pd.isna(row['take_off_2']) and not pd.isna(row['put_on_2']):
            take_off = parse_timestamp(row['take_off_2'])
            put_on = parse_timestamp(row['put_on_2'])
            if take_off and put_on:
                periods.append((take_off, put_on))
        
        wear_periods.extend(periods)
    
    return wear_periods

def plot_triaxial_with_wear_times(pig_id, data_file, wear_times_df):
    """Plot triaxial data with wear times marked as red bands"""
    
    # Read the triaxial data
    print(f"Reading data for {pig_id} from {data_file}")
    data = pd.read_csv(data_file)
    data['timestamp'] = pd.to_datetime(data['timestamp']).dt.tz_localize(None)
    
    # Get wear periods for this pig
    wear_periods = get_wear_periods(wear_times_df, pig_id)
    
    # Create the plot
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 10), sharex=True)
    fig.suptitle(f'Triaxial Data for {pig_id} with Wear Times Marked', fontsize=16)
    
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
    
    # Add red bands for wear periods
    for start_time, end_time in wear_periods:
        # Only show bands that overlap with the data time range
        if start_time <= data['timestamp'].max() and end_time >= data['timestamp'].min():
            ax1.axvspan(start_time, end_time, alpha=0.3, color='red', label='Wear Period' if start_time == wear_periods[0][0] else "")
            ax2.axvspan(start_time, end_time, alpha=0.3, color='red', label='Wear Period' if start_time == wear_periods[0][0] else "")
            ax3.axvspan(start_time, end_time, alpha=0.3, color='red', label='Wear Period' if start_time == wear_periods[0][0] else "")
    
    # Format x-axis
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    ax3.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
    
    # Add legend for wear periods
    if wear_periods:
        ax1.legend()
        ax2.legend()
        ax3.legend()
    
    plt.tight_layout()
    return fig

def main():
    # Read wear times data
    print("Reading wear times data...")
    wear_times_df = pd.read_csv('wear_times.csv')
    
    # Get list of CSV files in minute_level directory
    csv_files = glob.glob('minute_level/*.csv')
    
    if not csv_files:
        print("No CSV files found in minute_level directory")
        return
    
    print(f"Found {len(csv_files)} CSV files")
    
    # Process each file
    for csv_file in csv_files:
        # Extract pig ID from filename (remove .csv and get the name)
        pig_id = os.path.basename(csv_file).replace('.csv', '')
        
        # Convert pig_id to match wear_times.csv format (add dash if needed)
        if pig_id.startswith('CO') and len(pig_id) == 5:
            wear_times_pig_id = f"{pig_id[:2]}-{pig_id[2:]}"
        elif pig_id.startswith('FL') and len(pig_id) == 5:
            wear_times_pig_id = f"{pig_id[:2]}-{pig_id[2:]}"
        else:
            wear_times_pig_id = pig_id
        
        # Check if this pig has wear time data
        if wear_times_pig_id in wear_times_df['pig_id'].values:
            print(f"\nProcessing {pig_id}...")
            
            # Create the plot
            fig = plot_triaxial_with_wear_times(wear_times_pig_id, csv_file, wear_times_df)
            
            # Save the plot
            output_filename = f"{pig_id}_triaxial_with_wear_times.png"
            fig.savefig(output_filename, dpi=300, bbox_inches='tight')
            print(f"Saved plot as {output_filename}")
            
            # Show the plot
            plt.show()
            
            # Close the figure to free memory
            plt.close(fig)
        else:
            print(f"Skipping {pig_id} - no wear time data available")

if __name__ == "__main__":
    main()
