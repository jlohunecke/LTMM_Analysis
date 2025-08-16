import pandas as pd
import numpy as np
from datetime import datetime

def analyze_pig_data():
    # Read the cleaned data
    flat_df = pd.read_csv('pig_wear_times_flat.csv')
    timestamp_df = pd.read_csv('pig_wear_times_timestamps.csv')
    
    print("=== PIG WEAR TIME DATA ANALYSIS ===\n")
    
    # Basic statistics
    print(f"Total pigs processed: {flat_df['pig_id'].nunique()}")
    print(f"Total wear time records: {len(flat_df)}")
    print(f"Total timestamp events: {len(timestamp_df)}")
    
    # Unique pigs
    unique_pigs = flat_df['pig_id'].unique()
    print(f"\nUnique pig IDs: {len(unique_pigs)}")
    print("Sample pig IDs:", unique_pigs[:10].tolist())
    
    # Date range
    if 'date' in flat_df.columns:
        dates = pd.to_datetime(flat_df['date'].dropna())
        if len(dates) > 0:
            print(f"\nDate range: {dates.min().strftime('%Y-%m-%d')} to {dates.max().strftime('%Y-%m-%d')}")
    
    # Event types
    if 'event_type' in timestamp_df.columns:
        event_counts = timestamp_df['event_type'].value_counts()
        print(f"\nEvent types:")
        for event, count in event_counts.items():
            print(f"  {event}: {count}")
    
    # Days with data
    day_counts = flat_df['day'].value_counts()
    print(f"\nDays with data:")
    for day, count in day_counts.items():
        print(f"  {day}: {count} records")
    
    # Sample of complete records
    print(f"\n=== SAMPLE COMPLETE RECORDS ===")
    complete_records = flat_df.dropna(subset=['start_time', 'end_time'])
    if len(complete_records) > 0:
        print(complete_records.head(10).to_string(index=False))
    else:
        print("No complete records found (with both start and end times)")
    
    # Sample of timestamp data
    print(f"\n=== SAMPLE TIMESTAMP EVENTS ===")
    print(timestamp_df.head(15).to_string(index=False))
    
    # Summary by pig
    print(f"\n=== SUMMARY BY PIG ===")
    pig_summary = flat_df.groupby('pig_id').agg({
        'day': 'count',
        'date': lambda x: x.nunique(),
        'start_time': lambda x: x.notna().sum(),
        'end_time': lambda x: x.notna().sum()
    }).rename(columns={
        'day': 'total_records',
        'date': 'unique_dates',
        'start_time': 'start_times_recorded',
        'end_time': 'end_times_recorded'
    })
    
    print(pig_summary.head(10))
    
    # Save summary
    pig_summary.to_csv('pig_summary.csv')
    print(f"\nSummary saved to 'pig_summary.csv'")

if __name__ == "__main__":
    analyze_pig_data()


