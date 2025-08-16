import pandas as pd

# Read the original CSV file
df = pd.read_csv('pig_timestamps_final.csv')

# Create new dataframe with all the required columns in the specified order
# Order: pig_id, day, start_time, take_off, put_on, end_time
new_df = df[['pig_id', 'day', 'start_time', 'took_off', 'put_on', 'end_time']].copy()

# Rename 'took_off' to 'take_off'
new_df = new_df.rename(columns={'took_off': 'take_off'})

# Save the new table
new_df.to_csv('pig_timestamps_new.csv', index=False)

print("Conversion completed!")
print(f"Original file had {len(df)} rows and {len(df.columns)} columns")
print(f"New file has {len(new_df)} rows and {len(new_df.columns)} columns")
print("\nNew columns in order:", list(new_df.columns))
print("\nFirst few rows of the new table:")
print(new_df.head(10))
