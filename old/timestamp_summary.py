import pandas as pd

def summarize_timestamps():
    # Read the clean timestamp data
    df = pd.read_csv('pig_timestamps_clean.csv')
    
    print("=== PIG TIMESTAMP DATA SUMMARY ===\n")
    
    # Basic statistics
    print(f"Total records: {len(df)}")
    print(f"Unique pigs: {df['pig_id'].nunique()}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Count timestamps by type
    print(f"\n=== TIMESTAMP COUNTS ===")
    for col in ['start_time', 'end_time', 'took_off', 'put_on']:
        count = df[col].notna().sum()
        print(f"{col}: {count} records")
    
    # Show pigs with complete data (all 4 timestamps)
    print(f"\n=== PIGS WITH COMPLETE TIMESTAMP DATA ===")
    complete_data = df.dropna(subset=['start_time', 'end_time', 'took_off', 'put_on'])
    if len(complete_data) > 0:
        print(f"Found {len(complete_data)} records with all 4 timestamps:")
        for _, row in complete_data.head(10).iterrows():
            print(f"  {row['pig_id']}: {row['date']}")
            print(f"    Start: {row['start_time']}")
            print(f"    End: {row['end_time']}")
            print(f"    Took off: {row['took_off']}")
            print(f"    Put on: {row['put_on']}")
            print()
    else:
        print("No records found with all 4 timestamps")
    
    # Show pigs with start and end times
    print(f"\n=== PIGS WITH START AND END TIMES ===")
    start_end_data = df.dropna(subset=['start_time', 'end_time'])
    print(f"Found {len(start_end_data)} records with both start and end times:")
    for _, row in start_end_data.head(10).iterrows():
        print(f"  {row['pig_id']}: {row['start_time']} to {row['end_time']}")
    
    # Show sample of all data
    print(f"\n=== SAMPLE OF ALL DATA ===")
    print(df.head(10).to_string(index=False))

if __name__ == "__main__":
    summarize_timestamps()


