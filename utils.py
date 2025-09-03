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
    sd_crit=0.02,
    range_crit=0.05,
    window_length=5,
    window_skip=30,
    min_duration_minutes_wear=15,
    verbose=False
):
    """
    Recompute wear periods using the AccelThresholdWearDetection algorithm.
    
    This function uses a more sophisticated wear detection algorithm based on
    standard deviation and range thresholds within sliding windows, as described
    in the CosinorAge methodology.
    
    Parameters
    ----------
    input_dir : str
        Directory containing the input CSV files
    output_file : str
        Output CSV file for wear periods
    sd_crit : float
        Standard deviation criterion for wear detection (default: 0.02 = 20 mg)
        Lower values = stricter detection, higher values = more lenient
    range_crit : float
        Range criterion for wear detection (default: 0.05 = 50 mg)
        Lower values = stricter detection, higher values = more lenient
    window_length : int
        Length of the sliding window in seconds (default: 5)
        For minute-level data, this represents the number of minutes in each rolling window
        Should be at least 3-5 for meaningful standard deviation calculations
    window_skip : int
        Number of seconds to skip between consecutive windows (default: 30)
        Controls temporal resolution of detection
    min_duration_minutes_wear : int
        Minimum duration in minutes for a wear period to be considered valid (default: 15)
        Prevents detection of very brief wear periods
    verbose : bool
        Whether to print progress information (default: False)
    """
    # No external dependencies needed for the custom algorithm
    
    def detect_wear_periods_advanced(df, sf=1.0/60, sd_crit=0.005, range_crit=0.02, 
                                   window_length=60, window_skip=30):
        """
        Detect wear periods using a custom algorithm optimized for minute-level data.
        
        This algorithm is specifically designed for low-frequency accelerometer data
        and uses rolling statistics with appropriate window sizes.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with timestamp index and ['x', 'y', 'z'] columns
        sf : float
            Sampling frequency in Hz (default: 1/60 for minute-level data)
        sd_crit : float
            Standard deviation criterion for wear detection (in g units)
        range_crit : float
            Range criterion for wear detection (in g units)
        window_length : int
            Length of rolling window in samples (not seconds for minute-level data)
        window_skip : int
            Not used for minute-level data, kept for compatibility
            
        Returns
        -------
        list of tuples
            List of (start_time, end_time) wear periods
        """
        import numpy as np
        
        # For minute-level data, we need to use sample-based windows, not time-based
        # Convert window_length from seconds to samples, but ensure minimum meaningful size
        window_samples = max(3, int(window_length * sf))  # At least 3 samples for meaningful std
        
        # Calculate rolling statistics for each axis
        rolling_std_x = df['x'].rolling(window=window_samples, center=True, min_periods=1).std()
        rolling_std_y = df['y'].rolling(window=window_samples, center=True, min_periods=1).std()
        rolling_std_z = df['z'].rolling(window=window_samples, center=True, min_periods=1).std()
        
        # Calculate rolling range for each axis
        rolling_range_x = df['x'].rolling(window=window_samples, center=True, min_periods=1).max() - \
                         df['x'].rolling(window=window_samples, center=True, min_periods=1).min()
        rolling_range_y = df['y'].rolling(window=window_samples, center=True, min_periods=1).max() - \
                         df['y'].rolling(window=window_samples, center=True, min_periods=1).min()
        rolling_range_z = df['z'].rolling(window=window_samples, center=True, min_periods=1).max() - \
                         df['z'].rolling(window=window_samples, center=True, min_periods=1).min()
        
        # Combined wear mask: wear if ANY axis meets criteria
        wear_mask = (
            (rolling_std_x >= sd_crit) | 
            (rolling_std_y >= sd_crit) | 
            (rolling_std_z >= sd_crit) |
            (rolling_range_x >= range_crit) | 
            (rolling_range_y >= range_crit) | 
            (rolling_range_z >= range_crit)
        )
        
        # Find continuous wear periods
        wear_periods = []
        start_idx = None
        
        for i, is_wear in enumerate(wear_mask):
            if is_wear and start_idx is None:
                start_idx = i
            elif not is_wear and start_idx is not None:
                if i - start_idx >= 1:  # At least 1 sample
                    start_time = df.index[start_idx]
                    end_time = df.index[i-1]
                    wear_periods.append((start_time, end_time))
                start_idx = None
        
        # Handle case where wear period extends to the end
        if start_idx is not None and start_idx < len(df) - 1:
            start_time = df.index[start_idx]
            end_time = df.index[-1]
            wear_periods.append((start_time, end_time))
        
        return wear_periods
    
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
    
    def filter_wear_periods(wear_periods, min_duration_minutes):
        """Filter wear periods by minimum duration."""
        min_duration_seconds = min_duration_minutes * 60
        return [
            (s, e) for s, e in wear_periods
            if (e - s).total_seconds() >= min_duration_seconds
        ]
    
    # === Build new wear_periods dataframe ===
    rows = []
    csv_files = sorted(glob.glob(os.path.join(input_dir, "*.csv")))
    
    if verbose:
        print(f"Processing {len(csv_files)} files...")
    
    for i, file_path in enumerate(csv_files):
        if verbose:
            print(f"Processing file {i+1}/{len(csv_files)}: {os.path.basename(file_path)}")
        
        pig_id = os.path.basename(file_path).split(".")[0]
        pig_id = pig_id.replace("_", "-")
        if pig_id.startswith("CO") and not pig_id.startswith("CO-"):
            pig_id = pig_id[:2] + "-" + pig_id[2:]  # normalize CO001 -> CO-001

        try:
            df = pd.read_csv(file_path, parse_dates=['timestamp'])
            df = df.set_index('timestamp')
            
            # Skip files with insufficient data
            if len(df) < window_length * 2:  # Need at least 2 windows worth of data
                if verbose:
                    print(f"  Skipping {pig_id}: insufficient data ({len(df)} samples)")
                continue
            
            # Detect wear periods using advanced algorithm
            wear_periods = detect_wear_periods_advanced(
                df, 
                sf=1.0/60,  # 1 sample per minute
                sd_crit=sd_crit,
                range_crit=range_crit,
                window_length=window_length,
                window_skip=window_skip
            )
            
            if verbose:
                print(f"  {pig_id}: raw detection found {len(wear_periods)} periods")
                if len(wear_periods) > 0:
                    print(f"    Sample periods: {wear_periods[:2]}")
                else:
                    # Show some statistics to help debug
                    sample_std_x = df['x'].rolling(window=min(5, len(df)), center=True, min_periods=1).std().mean()
                    sample_std_y = df['y'].rolling(window=min(5, len(df)), center=True, min_periods=1).std().mean()
                    sample_std_z = df['z'].rolling(window=min(5, len(df)), center=True, min_periods=1).std().mean()
                    sample_range_x = (df['x'].rolling(window=min(5, len(df)), center=True, min_periods=1).max() - 
                                    df['x'].rolling(window=min(5, len(df)), center=True, min_periods=1).min()).mean()
                    sample_range_y = (df['y'].rolling(window=min(5, len(df)), center=True, min_periods=1).max() - 
                                    df['y'].rolling(window=min(5, len(df)), center=True, min_periods=1).min()).mean()
                    sample_range_z = (df['z'].rolling(window=min(5, len(df)), center=True, min_periods=1).max() - 
                                    df['z'].rolling(window=min(5, len(df)), center=True, min_periods=1).min()).mean()
                    print(f"    Sample stats - Std: x={sample_std_x:.4f}, y={sample_std_y:.4f}, z={sample_std_z:.4f}")
                    print(f"    Sample stats - Range: x={sample_range_x:.4f}, y={sample_range_y:.4f}, z={sample_range_z:.4f}")
                    print(f"    Thresholds - Std: {sd_crit:.4f}, Range: {range_crit:.4f}")
                    
                    # Show what the actual rolling window calculation is doing
                    window_samples = max(1, int(window_length * (1.0/60)))
                    print(f"    Rolling window size: {window_samples} samples")
                    
                    # Check a few specific rolling calculations
                    if len(df) >= 3:
                        test_std_x = df['x'].rolling(window=window_samples, center=True, min_periods=1).std().iloc[:5]
                        test_std_y = df['y'].rolling(window=window_samples, center=True, min_periods=1).std().iloc[:5]
                        test_std_z = df['z'].rolling(window=window_samples, center=True, min_periods=1).std().iloc[:5]
                        print(f"    First 5 rolling std values - x: {[f'{x:.4f}' for x in test_std_x]}")
                        print(f"    First 5 rolling std values - y: {[f'{y:.4f}' for y in test_std_y]}")
                        print(f"    First 5 rolling std values - z: {[f'{z:.4f}' for z in test_std_z]}")
                        
                        # Check how many values actually meet the criteria
                        rolling_std_x = df['x'].rolling(window=window_samples, center=True, min_periods=1).std()
                        rolling_std_y = df['y'].rolling(window=window_samples, center=True, min_periods=1).std()
                        rolling_std_z = df['z'].rolling(window=window_samples, center=True, min_periods=1).std()
                        
                        std_criteria_met = (rolling_std_x >= sd_crit) | (rolling_std_y >= sd_crit) | (rolling_std_z >= sd_crit)
                        print(f"    Samples meeting std criteria: {std_criteria_met.sum()}/{len(df)} ({std_criteria_met.sum()/len(df)*100:.1f}%)")
            
            # Merge overlapping periods and filter by minimum duration
            wear_periods = merge_intervals(wear_periods)
            wear_periods = filter_wear_periods(wear_periods, min_duration_minutes_wear)
            
            if verbose:
                print(f"  {pig_id}: after filtering: {len(wear_periods)} wear periods")
            
            # Create row for this pig
            row = {"pig_id": pig_id}
            for j, (s, e) in enumerate(wear_periods, start=1):
                row[f"wear_start_{j}"] = s
                row[f"wear_end_{j}"] = e
            rows.append(row)
            
        except Exception as e:
            if verbose:
                print(f"  Error processing {pig_id}: {str(e)}")
            continue
    
    # Create and save the new wear periods dataframe
    new_wear_df = pd.DataFrame(rows)
    new_wear_df.to_csv(output_file, index=False)
    
    if verbose:
        print(f"Wear periods saved to {output_file}")
        print(f"Total pigs processed: {len(new_wear_df)}")
    
    return new_wear_df

def recompute_wear_periods_simple(
    input_dir="minute_level",
    output_file="wear_periods_recomputed.csv",
    threshold=0.005,
    min_duration_minutes_nonwear=30,
    min_duration_minutes_wear=30
):
    """
    Simple wear period detection using rolling standard deviation threshold.
    This is a fallback method when the advanced algorithm is not available.
    """
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
    For each pig_id in the wear CSV, find the corresponding CSV file in input_dir and plot the specified axis timeseries.
    Wear periods are highlighted in green, and valid wear hours are displayed in the title.
    
    Parameters:
        wear_csv (str): Path to CSV file containing 'pig_id' and wear_start_/wear_end_ columns
        input_dir (str): Directory containing timestamped x-axis data CSVs
        axis (str): Which axis to plot ('x', 'y', 'z', or 'enmo')
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

        # Handle ENMO axis computation
        if axis == 'enmo':
            # Compute ENMO: sqrt(x² + y² + z²) - 1, clipped to non-negative values
            enmo = np.sqrt(df['x']**2 + df['y']**2 + df['z']**2) - 1
            enmo = enmo.clip(lower=0)
            plot_data = enmo
            axis_label = 'ENMO'
        else:
            plot_data = df[f'{axis}']
            axis_label = f'{axis} axis'

        plt.figure(figsize=(12, 2))
        plt.plot(ts, plot_data, label=f"{file_label} {axis_label}")
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
        plt.ylabel(f'{axis_label} data')
        plt.title(f'{axis_label} data for {file_label} (valid wear hours: {round(wear_hours)}/{round(total_hours)})')
        plt.show()

def smart_fill_non_wear(df, wear_mask, day_start="07:00", day_end="19:00"):
    """
    Smart filling strategy with multiple fallback methods:
    1. Same time on other days
    2. Same time ±30 minutes on other days  
    3. Rolling mean from nearby wear periods
    4. Time-aware filling (day vs night)
    """
    import datetime
    
    df_filled = df.copy()
    non_wear_mask = ~wear_mask
    
    # Add time components
    ts = pd.to_datetime(df_filled['timestamp'])
    df_filled['hour'] = ts.dt.hour
    df_filled['minute'] = ts.dt.minute
    df_filled['day_of_week'] = ts.dt.dayofweek
    
    # Parse day boundaries
    day_start_time = datetime.datetime.strptime(day_start, "%H:%M").time()
    day_end_time = datetime.datetime.strptime(day_end, "%H:%M").time()
    
    for idx in df_filled.index[non_wear_mask]:
        current_time = df_filled.loc[idx]
        hour, minute = current_time['hour'], current_time['minute']
        day_of_week = current_time['day_of_week']
        
        # Strategy 1: Exact same time on other days
        same_time_mask = (
            (df_filled['hour'] == hour) & 
            (df_filled['minute'] == minute) & 
            (df_filled['day_of_week'] != day_of_week) &  # Different day
            wear_mask
        )
        
        if same_time_mask.sum() >= 2:  # Need at least 2 samples
            for col in ['x', 'y', 'z']:
                df_filled.loc[idx, col] = df_filled.loc[same_time_mask, col].mean()
            continue
            
        # Strategy 2: Same time ±30 minutes on other days
        time_diff = abs(df_filled['hour'] - hour) + abs(df_filled['minute'] - minute) / 60
        nearby_time_mask = (
            (time_diff <= 0.5) & 
            (df_filled['day_of_week'] != day_of_week) &
            wear_mask
        )
        
        if nearby_time_mask.sum() >= 3:
            for col in ['x', 'y', 'z']:
                df_filled.loc[idx, col] = df_filled.loc[nearby_time_mask, col].mean()
            continue
            
        # Strategy 3: Rolling mean from nearby wear periods (within 2 hours)
        time_diff = abs(df_filled['hour'] - hour) + abs(df_filled['minute'] - minute) / 60
        nearby_wear_mask = (time_diff <= 2) & wear_mask
        
        if nearby_wear_mask.sum() >= 5:
            for col in ['x', 'y', 'z']:
                df_filled.loc[idx, col] = df_filled.loc[nearby_wear_mask, col].mean()
            continue
            
        # Strategy 4: Time-aware filling (day vs night)
        current_time_obj = ts.loc[idx].time()
        is_day = (day_start_time <= current_time_obj < day_end_time)
        
        if is_day:
            # Day: use mean of all daytime wear periods
            day_mask = wear_mask & (
                ts.dt.time.apply(lambda t: day_start_time <= t < day_end_time)
            )
            if day_mask.any():
                for col in ['x', 'y', 'z']:
                    df_filled.loc[idx, col] = df_filled.loc[day_mask, col].mean()
            else:
                # Fallback to overall wear mean
                for col in ['x', 'y', 'z']:
                    df_filled.loc[idx, col] = df_filled.loc[wear_mask, col].mean()
        else:
            # Night: use mean of all nighttime wear periods
            night_mask = wear_mask & (
                ts.dt.time.apply(lambda t: not (day_start_time <= t < day_end_time))
            )
            if night_mask.any():
                for col in ['x', 'y', 'z']:
                    df_filled.loc[idx, col] = df_filled.loc[night_mask, col].mean()
            else:
                # Fallback to overall wear mean
                for col in ['x', 'y', 'z']:
                    df_filled.loc[idx, col] = df_filled.loc[wear_mask, col].mean()
    
    return df_filled

def save_modified_timeseries(
    wear_csv, 
    input_dir, 
    output_dir="minute_level_modified", 
    max_wear_periods=1000,
    day_start="07:00",
    day_end="19:00",
    smart=False
):
    """
    For each pig_id in wear_df, locate the matching timeseries CSV,
    truncate at last wear period or file end, fill non-wear with wear mean during day
    and 0 during night (cutoff times settable by parameter),
    save modified data.

    Parameters
    ----------
    wear_csv : str
        Path to CSV file with pig_id and wear_start_/wear_end_ columns
    input_dir : str
        Directory containing the input CSV files
    output_dir : str
        Directory where modified CSVs will be saved
    max_wear_periods : int
        Maximum number of wear_start_/wear_end_ columns to check
    day_start : str
        Start of day period in "HH:MM" (inclusive)
    day_end : str
        End of day period in "HH:MM" (exclusive)
    smart : bool
        If True, use smart filling strategy (same time on other days, etc.)
        If False, use simple day/night filling (original behavior)
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

        # Compute average during wear for each axis
        wear_mean_x = df_valid.loc[wear_mask_valid, 'x'].mean() if wear_mask_valid.any() else df_valid['x'].mean()
        wear_mean_y = df_valid.loc[wear_mask_valid, 'y'].mean() if wear_mask_valid.any() else df_valid['y'].mean()
        wear_mean_z = df_valid.loc[wear_mask_valid, 'z'].mean() if wear_mask_valid.any() else df_valid['z'].mean()

        # Determine day/night for each timestamp
        # Day: day_start <= time < day_end, else night
        times = ts_valid.dt.time
        is_day = times.apply(
            lambda t: (day_start_time <= t < day_end_time)
            if day_start_time < day_end_time
            else (t >= day_start_time or t < day_end_time)
        )

        # Fill non-wear periods using either smart or simple strategy
        df_filled = df_valid.copy()
        non_wear_mask = ~wear_mask_valid

        if smart and non_wear_mask.any():
            # Use smart filling strategy
            #print(f"Using smart filling for {pig_id} ({non_wear_mask.sum()} non-wear periods)")
            df_filled = smart_fill_non_wear(df_filled, wear_mask_valid, day_start, day_end)
        else:
            # Use simple day/night filling (original behavior)
            #if non_wear_mask.any():
                #print(f"Using simple filling for {pig_id} ({non_wear_mask.sum()} non-wear periods)")
            
            # Set up boolean masks for non-wear during day and night
            non_wear_day_mask = non_wear_mask & is_day.values
            non_wear_night_mask = non_wear_mask & (~is_day.values)

            # Apply modifications to x axis
            df_filled.loc[non_wear_day_mask, 'x'] = wear_mean_x
            df_filled.loc[non_wear_night_mask, 'x'] = 0.0
            
            # Apply modifications to y axis
            df_filled.loc[non_wear_day_mask, 'y'] = wear_mean_y
            df_filled.loc[non_wear_night_mask, 'y'] = 0.0
            
            # Apply modifications to z axis
            df_filled.loc[non_wear_day_mask, 'z'] = wear_mean_z
            df_filled.loc[non_wear_night_mask, 'z'] = 0.0

        # Save to CSV
        cols_to_save = [c for c in ['timestamp', 'x', 'y', 'z'] if c in df_filled.columns]
        output_path = os.path.join(output_dir, file_label)
        df_filled[cols_to_save].to_csv(output_path, index=False)

def compare_cohorts_daily_signal(
    co_pattern="CO*.csv", 
    fl_pattern="FL*.csv", 
    folder="minute_level_modified", 
    columns=None, 
    window=30,
    plot_minmax=False
):
    """
    Load, process, and plot comparison of two cohorts using quartiles as 2D whisker plots.
    
    Parameters:
        co_pattern: str, filename pattern for CO cohort
        fl_pattern: str, filename pattern for FL cohort
        folder: str, folder containing the CSV files
        columns: list of str, columns to plot (default: ['x','y','z','enmo'])
        window: int, rolling window size for smoothing
        plot_minmax: bool, whether to plot min/max whiskers (default: False)
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
    # Group by hour and compute quartiles
    # ----------------------
    def group_by_hour_quartiles(df, column):
        # Use proper pandas aggregation methods
        grouped = df.groupby('hour')[column].agg(['mean']).reset_index()
        # Add quantiles using the quantile method
        grouped['q25'] = df.groupby('hour')[column].quantile(0.25).values
        grouped['q50'] = df.groupby('hour')[column].quantile(0.50).values
        grouped['q75'] = df.groupby('hour')[column].quantile(0.75).values
        
        # Add min/max if requested
        if plot_minmax:
            grouped['min'] = df.groupby('hour')[column].min().values
            grouped['max'] = df.groupby('hour')[column].max().values
        
        # Apply rolling window smoothing to all columns
        stats_to_smooth = ['mean', 'q25', 'q50', 'q75']
        if plot_minmax:
            stats_to_smooth.extend(['min', 'max'])
        
        for stat in stats_to_smooth:
            grouped[stat] = grouped[stat].rolling(window=window, center=True, min_periods=1).mean()
        return grouped
    
    # ----------------------
    # Plot
    # ----------------------
    for column in columns:
        co_grouped = group_by_hour_quartiles(co_data, column)
        fl_grouped = group_by_hour_quartiles(fl_data, column)
        
        plt.figure(figsize=(12, 3))
        
        # Plot CO cohort
        co_hours = co_grouped['hour']
        co_mean = co_grouped['mean']
        co_q1 = co_grouped['q25']
        co_q2 = co_grouped['q50']
        co_q3 = co_grouped['q75']
        
        # Plot min/max whiskers if requested
        if plot_minmax:
            co_min = co_grouped['min']
            co_max = co_grouped['max']
            plt.plot(co_hours, co_min, color='blue', alpha=0.7, linewidth=0.8, label='CO min/max')
            plt.plot(co_hours, co_max, color='blue', alpha=0.7, linewidth=0.8)
        
        # Plot IQR box (Q1 to Q3)
        plt.fill_between(co_hours, co_q1, co_q3, color='blue', alpha=0.3, label='CO IQR')
        
        # Plot mean as solid line
        plt.plot(co_hours, co_mean, color='blue', linewidth=2, label='CO mean')
        
        # Plot median as dashed line
        plt.plot(co_hours, co_q2, color='blue', linewidth=2, linestyle='--', label='CO median')
        
        # Plot FL cohort
        fl_hours = fl_grouped['hour']
        fl_mean = fl_grouped['mean']
        fl_q1 = fl_grouped['q25']
        fl_q2 = fl_grouped['q50']
        fl_q3 = fl_grouped['q75']
        
        # Plot min/max whiskers if requested
        if plot_minmax:
            fl_min = fl_grouped['min']
            fl_max = fl_grouped['max']
            plt.plot(fl_hours, fl_min, color='red', alpha=0.7, linewidth=0.8, label='FL min/max')
            plt.plot(fl_hours, fl_max, color='red', alpha=0.7, linewidth=0.8)
        
        # Plot IQR box (Q1 to Q3)
        plt.fill_between(fl_hours, fl_q1, fl_q3, color='red', alpha=0.3, label='FL IQR')
        
        # Plot mean as solid line
        plt.plot(fl_hours, fl_mean, color='red', linewidth=2, label='FL mean')
        
        # Plot median as dashed line
        plt.plot(fl_hours, fl_q2, color='red', linewidth=2, linestyle='--', label='FL median')
        
        plt.xlabel('Hour of Day')
        plt.ylabel(column)
        title_suffix = " with Min/Max" if plot_minmax else ""
        plt.title(f'Comparison of {column} Daily Signal: Mean (solid), Median (dashed), and IQR{title_suffix}')
        plt.legend()
        plt.xlim(0, 24)
        plt.grid(alpha=0.3)
        
        ticks = np.arange(0, 25, 6)
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

def plot_cohort_feature_comparison(co_features, fl_features, title=None, plot_minmax=True):
    """
    Plots a horizontal bar chart comparing two cohorts for a set of features using quartiles, mean, max, and median.
    
    Args:
        co_features: Object with method `get_individual_features()` returning individual feature data for CO cohort.
        fl_features: Object with method `get_individual_features()` returning individual feature data for FL cohort.
        title: Optional string for the plot title.
        plot_minmax: bool, whether to plot min/max whiskers (default: True)
    """
    # Extract features to DataFrames
    df_co = extract_features_to_dataframe(co_features.get_individual_features())
    df_fl = extract_features_to_dataframe(fl_features.get_individual_features())
    
    # Get numeric features (exclude individual_id)
    numeric_cols = df_co.select_dtypes(include=[np.number]).columns
    numeric_cols = [col for col in numeric_cols if col != 'individual_id']
    
    fig, axes = plt.subplots(len(numeric_cols), 1, figsize=(12, len(numeric_cols)), sharex=False)
    if len(numeric_cols) == 1:
        axes = [axes]
    
    # Prepare comparison data
    comparison_data = []
    for feat in numeric_cols:
        # Compute summary statistics for CO cohort
        co_stats = df_co[feat].describe()
        # Compute summary statistics for FL cohort
        fl_stats = df_fl[feat].describe()
        
        comparison_data.append({
            'feature': feat,
            'co_mean': co_stats.get('mean', 0),
            'co_median': co_stats.get('50%', 0),
            'co_q1': co_stats.get('25%', 0),
            'co_q3': co_stats.get('75%', 0),
            'co_min': co_stats.get('min', 0),
            'co_max': co_stats.get('max', 0),
            'fl_mean': fl_stats.get('mean', 0),
            'fl_median': fl_stats.get('50%', 0),
            'fl_q1': fl_stats.get('25%', 0),
            'fl_q3': fl_stats.get('75%', 0),
            'fl_min': fl_stats.get('min', 0),
            'fl_max': fl_stats.get('max', 0)
        })
    
    # Plot each feature
    for i, data in enumerate(comparison_data):
        ax = axes[i]
        
        # Plot CO cohort
        co_x_pos = 0.75
        # Plot min/max whiskers if requested
        if plot_minmax:
            ax.plot([data['co_min'], data['co_max']], [co_x_pos, co_x_pos], color='blue', linewidth=2, alpha=0.7)
        # Plot IQR box
        ax.plot([data['co_q1'], data['co_q3']], [co_x_pos, co_x_pos], color='blue', linewidth=6, alpha=0.5)
        # Plot mean as circle
        ax.plot(data['co_mean'], co_x_pos, 'o', color='blue', markersize=8, label='CO cohort' if i == 0 else "")
        # Plot median as square
        ax.plot(data['co_median'], co_x_pos, 's', color='blue', markersize=6, alpha=0.8, label='CO cohort' if i == 0 else "")
        
        # Plot FL cohort
        fl_x_pos = 0.25
        # Plot min/max whiskers if requested
        if plot_minmax:
            ax.plot([data['fl_min'], data['fl_max']], [fl_x_pos, fl_x_pos], color='red', linewidth=2, alpha=0.7)
        # Plot IQR box
        ax.plot([data['fl_q1'], data['fl_q3']], [fl_x_pos, fl_x_pos], color='red', linewidth=6, alpha=0.5)
        # Plot mean as circle
        ax.plot(data['fl_mean'], fl_x_pos, 'o', color='red', markersize=8, label='FL cohort' if i == 0 else "")
        # Plot median as square
        ax.plot(data['fl_median'], fl_x_pos, 's', color='red', markersize=6, alpha=0.8, label='FL cohort' if i == 0 else "")
    
        # Special handling for cosinor_acrophase_time: set full 24-hour range and HH:MM format
        if data['feature'] == 'cosinor_acrophase_time':
            # Set x-axis to cover full 24-hour period (0 to 1440 minutes)
            ax.set_xlim(0, 1440)
            # Set custom x-axis ticks for every 4 hours (0, 4, 8, 12, 16, 20, 24)
            x_ticks = [0, 240, 480, 720, 960, 1200, 1440]
            x_tick_labels = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00']
            ax.set_xticks(x_ticks)
            ax.set_xticklabels(x_tick_labels)
        else:
            # Set individual x-axis scale for other features
            all_vals = [data['co_min'], data['co_max'], data['fl_min'], data['fl_max']]
            margin = 0.1 * (max(all_vals) - min(all_vals))
            ax.set_xlim(min(all_vals) - margin, max(all_vals) + margin)
        
        ax.set_ylim(0, 1)
        ax.set_yticks([])
        ax.set_ylabel(data['feature'], rotation=0, labelpad=80, fontsize=9, va='center')
        ax.grid(True, alpha=0.3, axis='x')
    
    # Create custom legend handles in desired order
    from matplotlib.lines import Line2D
    custom_handles = [
        Line2D([0], [0], marker='o', color='blue', markersize=8, linestyle='', label='CO cohort (mean)'),
        Line2D([0], [0], marker='s', color='blue', markersize=6, linestyle='', label='CO cohort (median)'),
        Line2D([0], [0], marker='o', color='red', markersize=8, linestyle='', label='FL cohort (mean)'),
        Line2D([0], [0], marker='s', color='red', markersize=6, linestyle='', label='FL cohort (median)')
    ]
    
    # Legend above first subplot
    axes[0].legend(handles=custom_handles, loc='lower center', bbox_to_anchor=(0.5, 1.05), ncol=2)
    
    title_suffix = " with Min/Max" if plot_minmax else ""
    plt.suptitle(title or f'Cohort Comparison: Quartiles, Mean, and Median per Feature{title_suffix}', fontsize=14)
    plt.tight_layout(rect=[0.05,0,0.95,0.97])
    plt.show()

def extract_features_to_dataframe(individual_features):
    """
    Extract individual features from the nested structure and organize into a DataFrame.
    
    Parameters:
        individual_features: List of dictionaries from get_individual_features()
    
    Returns:
        pd.DataFrame: DataFrame with one row per individual and columns for each feature
    """
    rows = []
    
    for i, individual in enumerate(individual_features):
        row = {'individual_id': i}
        
        # Extract cosinor features
        if 'cosinor' in individual:
            cosinor = individual['cosinor']
            row.update({
                'cosinor_mesor': cosinor.get('mesor', np.nan),
                'cosinor_amplitude': cosinor.get('amplitude', np.nan),
                'cosinor_acrophase': cosinor.get('acrophase', np.nan),
                'cosinor_acrophase_time': cosinor.get('acrophase_time', np.nan)
            })
        
        # Extract nonparametric features
        if 'nonparam' in individual:
            nonparam = individual['nonparam']
            row.update({
                'nonparam_IS': nonparam.get('IS', np.nan),
                'nonparam_IV': nonparam.get('IV', np.nan),
                'nonparam_M10_mean': np.mean(nonparam.get('M10', [np.nan])) if nonparam.get('M10') else np.nan,
                'nonparam_L5_mean': np.mean(nonparam.get('L5', [np.nan])) if nonparam.get('L5') else np.nan,
                'nonparam_RA_mean': np.mean(nonparam.get('RA', [np.nan])) if nonparam.get('RA') else np.nan
            })
        
        # Extract physical activity features
        if 'physical_activity' in individual:
            pa = individual['physical_activity']
            row.update({
                'pa_sedentary_mean': np.mean(pa.get('sedentary', [np.nan])) if pa.get('sedentary') else np.nan,
                'pa_light_mean': np.mean(pa.get('light', [np.nan])) if pa.get('light') else np.nan,
                'pa_moderate_mean': np.mean(pa.get('moderate', [np.nan])) if pa.get('moderate') else np.nan,
                'pa_vigorous_mean': np.mean(pa.get('vigorous', [np.nan])) if pa.get('vigorous') else np.nan
            })
        
        # Extract sleep features
        if 'sleep' in individual:
            sleep = individual['sleep']
            row.update({
                'sleep_TST_mean': np.mean(sleep.get('TST', [np.nan])) if sleep.get('TST') else np.nan,
                'sleep_WASO_mean': np.mean(sleep.get('WASO', [np.nan])) if sleep.get('WASO') else np.nan,
                'sleep_PTA_mean': np.mean(sleep.get('PTA', [np.nan])) if sleep.get('PTA') else np.nan,
                'sleep_NWB_mean': np.mean(sleep.get('NWB', [np.nan])) if sleep.get('NWB') else np.nan,
                'sleep_SOL_mean': np.mean(sleep.get('SOL', [np.nan])) if sleep.get('SOL') else np.nan,
                'sleep_SRI': sleep.get('SRI', np.nan)
            })
        
        # Extract cosinorage features
        if 'cosinorage' in individual:
            cosinorage = individual['cosinorage']
            row.update({
                'cosinorage_value': cosinorage.get('cosinorage', np.nan),
                'cosinorage_advance': cosinorage.get('cosinorage_advance', np.nan)
            })
        
        rows.append(row)
    
    return pd.DataFrame(rows)

def compute_feature_summary_stats(features_df):
    """
    Compute summary statistics (min, max, quartiles, mean, median) for all features.
    
    Parameters:
        features_df: DataFrame from extract_features_to_dataframe()
    
    Returns:
        pd.DataFrame: Summary statistics for each feature
    """
    # Exclude non-numeric columns
    numeric_cols = features_df.select_dtypes(include=[np.number]).columns
    numeric_cols = [col for col in numeric_cols if col != 'individual_id']
    
    summary_stats = []
    
    for col in numeric_cols:
        stats = features_df[col].describe()
        summary_stats.append({
            'feature': col,
            'count': stats['count'],
            'mean': stats['mean'],
            'std': stats['std'],
            'min': stats['min'],
            '25%': stats['25%'],
            '50%': stats['50%'],
            '75%': stats['75%'],
            'max': stats['max']
        })
    
    return pd.DataFrame(summary_stats)

def plot_feature_distributions(features_df, features_to_plot=None, figsize=(15, 10)):
    """
    Plot distributions of features as histograms with summary statistics.
    
    Parameters:
        features_df: DataFrame from extract_features_to_dataframe()
        features_to_plot: List of feature names to plot (if None, plots all numeric features)
        figsize: Tuple for figure size
    """
    # Exclude non-numeric columns
    numeric_cols = features_df.select_dtypes(include=[np.number]).columns
    numeric_cols = [col for col in numeric_cols if col != 'individual_id']
    
    if features_to_plot is None:
        features_to_plot = numeric_cols
    else:
        features_to_plot = [f for f in features_to_plot if f in numeric_cols]
    
    n_features = len(features_to_plot)
    n_cols = 3
    n_rows = (n_features + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    elif n_cols == 1:
        axes = axes.reshape(-1, 1)
    
    for i, feature in enumerate(features_to_plot):
        row = i // n_cols
        col = i % n_cols
        ax = axes[row, col]
        
        # Plot histogram
        ax.hist(features_df[feature].dropna(), bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        
        # Add summary statistics as text
        stats = features_df[feature].describe()
        stats_text = f'Mean: {stats["mean"]:.3f}\nMedian: {stats["50%"]:.3f}\nStd: {stats["std"]:.3f}'
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_title(feature)
        ax.set_xlabel('Value')
        ax.set_ylabel('Frequency')
        ax.grid(True, alpha=0.3)
    
    # Hide empty subplots
    for i in range(n_features, n_rows * n_cols):
        row = i // n_cols
        col = i % n_cols
        axes[row, col].set_visible(False)
    
    plt.tight_layout()
    plt.show()