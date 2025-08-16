import pandas as pd
from datetime import datetime, timedelta

# Read the current CSV file
df = pd.read_csv('pig_timestamps_new.csv')

# Convert date columns to datetime
date_columns = ['start_time', 'take_off', 'put_on', 'end_time']
for col in date_columns:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# Create a new dataframe to store the corrected data
corrected_df = []

# Group by pig_id to process each pig separately
for pig_id, pig_data in df.groupby('pig_id'):
    # Get the base date from day_0 start_time
    day_0_data = pig_data[pig_data['day'] == 'day_0']
    
    if not day_0_data.empty and pd.notna(day_0_data['start_time'].iloc[0]):
        base_date = day_0_data['start_time'].iloc[0].date()
    else:
        # If no day_0 start_time, try to find any valid date from this pig
        all_dates = []
        for col in date_columns:
            valid_dates = pig_data[col].dropna()
            if not valid_dates.empty:
                all_dates.extend(valid_dates.dt.date.tolist())
        
        if all_dates:
            base_date = min(all_dates)  # Use the earliest date as base
        else:
            base_date = datetime.now().date()  # Fallback
    
    # Process each day for this pig
    for _, row in pig_data.iterrows():
        day_num = int(row['day'].split('_')[1])  # Extract day number (0, 1, 2, 3)
        target_date = base_date + timedelta(days=day_num)
        
        # Create new row with corrected dates
        new_row = row.copy()
        
        # Update all date columns to the correct date
        for col in date_columns:
            if pd.notna(row[col]):
                # Keep the time but change the date
                original_time = row[col].time()
                new_row[col] = datetime.combine(target_date, original_time)
        
        corrected_df.append(new_row)

# Create the corrected dataframe
corrected_df = pd.DataFrame(corrected_df)

# Save the corrected data
corrected_df.to_csv('pig_timestamps_corrected.csv', index=False)

print("Date correction completed!")
print(f"Original file had {len(df)} rows")
print(f"Corrected file has {len(corrected_df)} rows")

# Show sample of corrected data
print("\nSample of corrected data:")
sample_pig = corrected_df[corrected_df['pig_id'] == 'CO-001'].head(4)
for _, row in sample_pig.iterrows():
    print(f"{row['pig_id']}, {row['day']}: {row['start_time']}, {row['take_off']}, {row['put_on']}, {row['end_time']}")

