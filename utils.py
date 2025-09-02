import pandas as pd
import glob
import os
import re
import matplotlib.pyplot as plt
import numpy as np
import cosinorage as csa

def recompute_wear_periods(
    input_dir="minute_level",
    output_file="wear_periods_recomputed.csv",
    threshold=0.005,
    min_duration_minutes_nonwear=30,
    min_duration_minutes_wear=30
):
    def detect_non_wear_mask_periods(df, threshold=0.01, min_duration_minutes_nonwear=30):
        """Detect non-wear periods based on low rolling std of norm(x, y, z) signal."""
        # Compute the norm over x, y, z axes
        norm = (df['x']**2 + df['y']**2 + df['z']**2)**0.5
        norm = pd.Series(norm, index=df.index)
        rolling_std = norm.rolling('15min').std()
        mask = rolling_std < threshold
        periods = []
        start = None
        for t, is_non in mask.items():
            if is_non and start is None:
                start = t
            elif not is_non and start is not None:
                if (t - start).total_seconds() >= min_duration_minutes_nonwear*60:
                    periods.append((start, t))
                start = None
        # Handle case where non-wear goes to the end
        if start is not None and (df.index[-1] - start).total_seconds() >= min_duration_minutes_nonwear*60:
            periods.append((start, df.index[-1]))
        return periods

    def merge_intervals(intervals):
        """Merge overlapping intervals."""
        if not intervals:
            return []
        intervals = sorted(intervals)
        merged = [list(intervals[0])]
        for s, e in intervals[1:]:
            if s <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], e)
            else:
                merged.append([s, e])
        return [(s, e) for s, e in merged]

    def detect_wear_periods(df, threshold=0.1, min_duration_minutes_nonwear=15, min_duration_minutes_wear=30):
        """Wear = complement of non-wear within data window, with minimum wear period duration enforced."""
        nonwears = detect_non_wear_mask_periods(df, threshold, min_duration_minutes_nonwear)
        nonwears = merge_intervals(nonwears)
        if not nonwears:
            return [(df.index.min(), df.index.max())]

        wear_periods = []
        cur_start = df.index.min()
        for s, e in nonwears:
            if s > cur_start:
                wear_periods.append((cur_start, s))
            cur_start = e
        if cur_start < df.index.max():
            wear_periods.append((cur_start, df.index.max()))

        # Enforce minimum wear period duration
        min_wear_seconds = min_duration_minutes_wear * 60
        filtered_wear_periods = [
            (s, e) for s, e in merge_intervals(wear_periods)
            if (e - s).total_seconds() >= min_wear_seconds
        ]
        return filtered_wear_periods

    # === Build new wear_periods dataframe ===
    rows = []
    csv_files = sorted(glob.glob(os.path.join(input_dir, "*.csv")))
    for file_path in csv_files:
        pig_id = os.path.basename(file_path).split(".")[0]
        pig_id = pig_id.replace("_", "-")
        if pig_id.startswith("CO") and not pig_id.startswith("CO-"):
            pig_id = pig_id[:2] + "-" + pig_id[2:]  # normalize CO001 -> CO-001

        df = pd.read_csv(file_path, parse_dates=['timestamp'])
        df = df.set_index('timestamp')

        wear_ints = detect_wear_periods(
            df,
            threshold=threshold,
            min_duration_minutes_nonwear=min_duration_minutes_nonwear,
            min_duration_minutes_wear=min_duration_minutes_wear
        )

        row = {"pig_id": pig_id}
        for i, (s, e) in enumerate(wear_ints, start=1):
            row[f"wear_start_{i}"] = s
            row[f"wear_end_{i}"] = e
        rows.append(row)

    new_wear_df = pd.DataFrame(rows)
    new_wear_df.to_csv(output_file, index=False)
    return new_wear_df

def plot_pig_wear_timeseries(
    wear_csv, 
    input_dir, 
    axis='x',
    limit=None
):
    """
    For each pig_id in the wear CSV, find the corresponding CSV file in input_dir and plot the x-axis timeseries.
    Wear periods are highlighted in green, and valid wear hours are displayed in the title.
    
    Parameters:
        wear_csv (str): Path to CSV file containing 'pig_id' and wear_start_/wear_end_ columns
        input_dir (str): Directory containing timestamped x-axis data CSVs
        axis (str): Which axis to plot ('x', 'y', or 'z')
        limit (int or None): Maximum number of pigs to plot
    """
    import pandas as pd
    import os
    import glob
    import re
    import matplotlib.pyplot as plt

    wear_df = pd.read_csv(wear_csv)
    wear_df.columns = [c.strip() for c in wear_df.columns]
    wear_df = wear_df.map(lambda x: x.strip() if isinstance(x, str) else x)
    csv_files = sorted(glob.glob(os.path.join(input_dir, "*.csv")))

    for idx, row in wear_df.iterrows():
        if limit is not None and idx >= limit:
            break

        pig_id = row['pig_id']
        # Accept both CO-001.csv and CO_001.csv, case-insensitive
        pig_id_pattern = pig_id.replace("-", "[-_]?")
        pattern = re.compile(rf"{pig_id_pattern}\.csv$", re.IGNORECASE)
        matching_files = [f for f in csv_files if pattern.search(os.path.basename(f))]
        if not matching_files:
            print(f"No file found for pig_id {pig_id}")
            continue
        csv_file = matching_files[0]

        df = pd.read_csv(csv_file)
        ts = pd.to_datetime(df['timestamp'])
        file_label = os.path.basename(csv_file)

        plt.figure(figsize=(12, 2))
        plt.plot(ts, df[f'{axis}'], label=f"{file_label} {axis}")
        plt.axvline(ts.min(), color='g', linestyle='--', label='Min timestamp')
        plt.axvline(ts.max(), color='r', linestyle='--', label='Max timestamp')

        # Plot wear periods as green bands and collect valid wear intervals
        wear_intervals = []
        n_max_wear_periods = (wear_df.shape[1] - 1) // 2

        for i in range(1, n_max_wear_periods + 1):
            start_col = f'wear_start_{i}'
            end_col = f'wear_end_{i}'
            start = row[start_col] if pd.notna(row[start_col]) else ''
            end = row[end_col] if pd.notna(row[end_col]) else ''
            if start and end:
                start_dt = pd.to_datetime(start)
                end_dt = pd.to_datetime(end)
                # Only consider wear periods before the signal ends
                end_dt = min(end_dt, ts.max())
                if start_dt > ts.max():
                    continue
                plt.axvspan(start_dt, end_dt, color='green', alpha=0.2)
                wear_intervals.append((start_dt, end_dt))

        # Calculate valid wear hours
        wear_hours = sum((end - start).total_seconds() / 3600.0 for start, end in wear_intervals)

        # Calculate total hours covered by the timeseries
        total_hours = ((ts.max().floor('h') - ts.min().floor('h')).total_seconds() / 3600.0) if not ts.empty else 0.0

        plt.xlabel('Timestamp')
        plt.ylabel(f'{axis} axis data')
        plt.title(f'{axis} axis data for {file_label} (valid wear hours: {round(wear_hours)}/{round(total_hours)})')
        plt.show()

def save_modified_timeseries(
    wear_csv, 
    input_dir, 
    output_dir="minute_level_modified", 
    max_wear_periods=1000,
    day_start="07:00",
    day_end="19:00"
):
    """
    For each pig_id in wear_df, locate the matching timeseries CSV,
    truncate at last wear period or file end, fill non-wear with wear mean during day
    and 0 during night (cutoff times settable by parameter),
    save modified data.

    Parameters
    ----------
    wear_df : pd.DataFrame
        DataFrame with pig_id and wear_start_/wear_end_ columns
    csv_files : list
        List of candidate CSV files containing timestamped x,y,z data
    output_dir : str
        Directory where modified CSVs will be saved
    max_wear_periods : int
        Maximum number of wear_start_/wear_end_ columns to check
    day_start : str
        Start of day period in "HH:MM" (inclusive)
    day_end : str
        End of day period in "HH:MM" (exclusive)
    """
    import datetime

    wear_df = pd.read_csv(wear_csv)
    wear_df.columns = [c.strip() for c in wear_df.columns]
    wear_df = wear_df.map(lambda x: x.strip() if isinstance(x, str) else x)
    csv_files = sorted(glob.glob(os.path.join(input_dir, "*.csv")))

    os.makedirs(output_dir, exist_ok=True)

    # Parse day_start and day_end as time objects
    day_start_time = datetime.datetime.strptime(day_start, "%H:%M").time()
    day_end_time = datetime.datetime.strptime(day_end, "%H:%M").time()

    for idx, row in wear_df.iterrows():
        pig_id = row['pig_id']
        # Accept both CO-001.csv and CO_001.csv, case-insensitive
        pig_id_pattern = pig_id.replace("-", "[-_]?")
        pattern = re.compile(rf"{pig_id_pattern}\.csv$", re.IGNORECASE)
        matching_files = [f for f in csv_files if pattern.search(os.path.basename(f))]
        if not matching_files:
            print(f"No file found for pig_id {pig_id}")
            continue
        csv_file = matching_files[0]

        df = pd.read_csv(csv_file)
        ts = pd.to_datetime(df['timestamp'])
        file_label = os.path.basename(csv_file)

        # Build wear mask
        wear_mask = pd.Series(False, index=df.index)
        wear_periods = []
        last_wear_end = None
        
        max_wear_periods_eff = wear_df.shape[1] // 2 if max_wear_periods is None else max_wear_periods

        for i in range(1, max_wear_periods_eff + 1):
            start_col, end_col = f'wear_start_{i}', f'wear_end_{i}'
            start = row[start_col] if start_col in row and pd.notna(row[start_col]) else None
            end = row[end_col] if end_col in row and pd.notna(row[end_col]) else None
            if start is not None and end is not None:
                start_dt, end_dt = pd.to_datetime(start), pd.to_datetime(end)
                mask = (ts >= start_dt) & (ts <= end_dt)
                wear_mask = wear_mask | mask
                wear_periods.append((start_dt, end_dt))
                if last_wear_end is None or end_dt > last_wear_end:
                    last_wear_end = end_dt

        # Truncate at cutoff
        cutoff = min(last_wear_end, ts.max()) if last_wear_end is not None else ts.max()
        valid_mask = ts <= cutoff
        ts_valid = ts[valid_mask]
        df_valid = df.loc[valid_mask].copy()
        wear_mask_valid = wear_mask[valid_mask]

        # Compute average during wear
        wear_mean = df_valid.loc[wear_mask_valid, 'x'].mean() if wear_mask_valid.any() else df_valid['x'].mean()

        # Determine day/night for each timestamp
        # Day: day_start <= time < day_end, else night
        times = ts_valid.dt.time
        is_day = times.apply(
            lambda t: (day_start_time <= t < day_end_time)
            if day_start_time < day_end_time
            else (t >= day_start_time or t < day_end_time)
        )

        # Fill non-wear: day with mean, night with 0
        df_filled = df_valid.copy()
        non_wear_mask = ~wear_mask_valid

        # Set up boolean masks for non-wear during day and night
        non_wear_day_mask = non_wear_mask & is_day.values
        non_wear_night_mask = non_wear_mask & (~is_day.values)

        df_filled.loc[non_wear_day_mask, 'x'] = wear_mean
        df_filled.loc[non_wear_night_mask, 'x'] = 0.0

        # Save to CSV
        cols_to_save = [c for c in ['timestamp', 'x', 'y', 'z'] if c in df_filled.columns]
        output_path = os.path.join(output_dir, file_label)
        df_filled[cols_to_save].to_csv(output_path, index=False)

def compare_cohorts_daily_signal(
    co_pattern="CO*.csv", 
    fl_pattern="FL*.csv", 
    folder="minute_level_modified", 
    columns=None, 
    window=30
):
    """
    Load, process, and plot comparison of two cohorts.
    
    Parameters:
        co_pattern: str, filename pattern for CO cohort
        fl_pattern: str, filename pattern for FL cohort
        folder: str, folder containing the CSV files
        columns: list of str, columns to plot (default: ['x','y','z','enmo'])
        window: int, rolling window size for smoothing
    """
    if columns is None:
        columns = ['x','y','z','enmo']
    
    # ----------------------
    # Load files
    # ----------------------
    def load_and_concat(file_list):
        all_data = []
        for f in file_list:
            df = pd.read_csv(f, parse_dates=['timestamp'])
            all_data.append(df)
        data = pd.concat(all_data)
        # fractional hour
        data['hour'] = data['timestamp'].dt.hour + data['timestamp'].dt.minute/60 + data['timestamp'].dt.second/3600
        # ENMO
        data['enmo'] = np.sqrt(data['x']**2 + data['y']**2 + data['z']**2) - 1
        data['enmo'] = data['enmo'].clip(lower=0)
        return data

    co_files = glob.glob(f"{folder}/{co_pattern}")
    fl_files = glob.glob(f"{folder}/{fl_pattern}")

    co_data = load_and_concat(co_files)
    fl_data = load_and_concat(fl_files)
    
    # ----------------------
    # Group by hour
    # ----------------------
    def group_by_hour(df, column):
        grouped = df.groupby('hour')[[column]].agg(['mean','std']).reset_index()
        grouped[(column,'mean')] = grouped[(column,'mean')].rolling(window=window, center=True, min_periods=1).mean()
        grouped[(column,'std')] = grouped[(column,'std')].rolling(window=window, center=True, min_periods=1).mean()
        return grouped
    
    # ----------------------
    # Plot
    # ----------------------
    for column in columns:
        co_grouped = group_by_hour(co_data, column)
        fl_grouped = group_by_hour(fl_data, column)
        
        plt.figure(figsize=(12,3))
        plt.plot(co_grouped['hour'], co_grouped[(column,'mean')], color='blue', label='CO mean')
        plt.fill_between(co_grouped['hour'],
                         co_grouped[(column,'mean')] - co_grouped[(column,'std')],
                         co_grouped[(column,'mean')] + co_grouped[(column,'std')],
                         color='blue', alpha=0.3, label='CO ±1 std')
        
        plt.plot(fl_grouped['hour'], fl_grouped[(column,'mean')], color='red', label='FL mean')
        plt.fill_between(fl_grouped['hour'],
                         fl_grouped[(column,'mean')] - fl_grouped[(column,'std')],
                         fl_grouped[(column,'mean')] + fl_grouped[(column,'std')],
                         color='red', alpha=0.3, label='FL ±1 std')
        
        plt.xlabel('Hour of Day')
        plt.ylabel(column)
        plt.title(f'Comparison of {column} Average Daily Signal ±1 STD')
        plt.legend()
        plt.xlim(0, 24)
        plt.grid(alpha=0.3)
        
        ticks = np.arange(0,25,6)
        tick_labels = [f'{int(t):02d}:00' for t in ticks]
        plt.xticks(ticks, tick_labels)
        plt.show()

def load_cohort_data(modified_dir="minute_level_modified", header_dir="headers", pattern="CO*.csv", preprocess_args=None):
    """
    Load accelerometer data handlers and age/gender info for a specific cohort.
    
    Parameters:
        modified_dir: str, folder with CSV files
        header_dir: str, folder with corresponding header (.hea) files
        pattern: str, filename pattern to select cohort files (e.g., 'CO*.csv' or 'FL*.csv')
        preprocess_args: dict, optional preprocessing arguments for the data handler
    
    Returns:
        data_handlers: list of GenericDataHandler objects
        cosinor_age_inputs: list of dicts with 'age', 'gender', and 'gt_cosinor_age'
    """
    if preprocess_args is None:
        preprocess_args = {}

    data_handlers = []
    cosinor_age_inputs = []

    for file_path in glob.glob(os.path.join(modified_dir, pattern)):
        try:
            fname = os.path.basename(file_path)
            header_path = os.path.join(header_dir, fname.replace('.csv', '.hea'))

            if os.path.isfile(file_path) and os.path.isfile(header_path):
                handler = csa.datahandlers.GenericDataHandler(
                    file_path=file_path,
                    data_format='csv',
                    data_type='accelerometer-g',
                    time_format='datetime',
                    time_column='timestamp',
                    time_zone="UTC",
                    data_columns=['x', 'y', 'z'],
                    preprocess_args=preprocess_args,
                    verbose=False
                )
                data_handlers.append(handler)

                age, gender = None, "unknown"
                with open(header_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("#Age:"):
                            try:
                                age = float(line.split(":", 1)[1])
                            except ValueError:
                                pass
                        elif line.startswith("#Sex:"):
                            g = line.split(":", 1)[1].strip().upper()
                            if g == "M":
                                gender = "male"
                            elif g == "F":
                                gender = "female"

                cosinor_age_inputs.append(
                    {"age": age, "gender": gender, "gt_cosinor_age": None}
                )

        except Exception as e:
            print(f"Error processing {fname}: {e}")

    return data_handlers, cosinor_age_inputs