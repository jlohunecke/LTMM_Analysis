import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os

# Set up the plotting style
plt.style.use('default')
plt.rcParams['figure.figsize'] = (15, 10)
plt.rcParams['font.size'] = 10

def load_wear_periods(file_path):
    """Load wear periods data and convert to datetime objects"""
    df = pd.read_csv(file_path)
    
    # Clean up column names (remove extra spaces)
    df.columns = df.columns.str.strip()
    
    wear_periods = {}
    
    for _, row in df.iterrows():
        pig_id = row['pig_id'].strip()
        periods = []
        
        # Check each wear period pair (up to 10 periods)
        for i in range(1, 11):
            start_col = f'wear_start_{i}'
            end_col = f'wear_end_{i}'
            
            if start_col in df.columns and end_col in df.columns:
                start_time = row[start_col]
                end_time = row[end_col]
                
                # Skip if either start or end time is empty
                if pd.isna(start_time) or pd.isna(end_time) or start_time == '' or end_time == '':
                    continue
                
                try:
                    start_dt = pd.to_datetime(start_time.strip())
                    end_dt = pd.to_datetime(end_time.strip())
                    periods.append((start_dt, end_dt))
                except:
                    continue
        
        wear_periods[pig_id] = periods
    
    return wear_periods

def load_triaxial_data(pig_id):
    """Load triaxial data for a specific pig"""
    file_path = f"minute_level/{pig_id}.csv"
    
    if not os.path.exists(file_path):
        print(f"Warning: File {file_path} not found")
        return None
    
    try:
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def plot_CO002_with_wear_periods():
    """Plot CO-002 with wear periods marked as green bands"""
    
    # Load wear periods data
    print("Loading wear periods data...")
    wear_periods = load_wear_periods('complete_wear_periods_reformatted.csv')
    
    # Check CO-002 specifically
    co002_wear_periods = wear_periods.get('CO-002', [])
    print(f"\nCO-002 wear periods: {len(co002_wear_periods)}")
    for i, (start, end) in enumerate(co002_wear_periods):
        print(f"  Period {i+1}: {start} to {end}")
    
    # Load triaxial data for CO002 (without dash)
    print("\nLoading triaxial data for CO002...")
    triaxial_data = load_triaxial_data('CO002')
    
    if triaxial_data is not None:
        print(f"Triaxial data loaded: {len(triaxial_data)} records")
        print(f"Time range: {triaxial_data['timestamp'].min()} to {triaxial_data['timestamp'].max()}")
        
        # Create the plot
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True)
        fig.suptitle('CO-002 Triaxial Time Series with Wear Periods', fontsize=16, fontweight='bold')
        
        # Plot X-axis data
        ax1.plot(triaxial_data['timestamp'], triaxial_data['x'], 'b-', linewidth=0.8, alpha=0.8, label='X-axis')
        ax1.set_ylabel('X-axis (g)', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Plot Y-axis data
        ax2.plot(triaxial_data['timestamp'], triaxial_data['y'], 'r-', linewidth=0.8, alpha=0.8, label='Y-axis')
        ax2.set_ylabel('Y-axis (g)', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Plot Z-axis data
        ax3.plot(triaxial_data['timestamp'], triaxial_data['z'], 'g-', linewidth=0.8, alpha=0.8, label='Z-axis')
        ax3.set_ylabel('Z-axis (g)', fontweight='bold')
        ax3.set_xlabel('Time', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        # Add wear period bands to all subplots
        print(f"\nAdding {len(co002_wear_periods)} wear period bands...")
        for i, (start_time, end_time) in enumerate(co002_wear_periods):
            print(f"  Adding band {i+1}: {start_time} to {end_time}")
            
            # Check if wear period overlaps with data
            if start_time <= triaxial_data['timestamp'].max() and end_time >= triaxial_data['timestamp'].min():
                print(f"    Period overlaps with data - adding green band")
                for ax in [ax1, ax2, ax3]:
                    ax.axvspan(start_time, end_time, alpha=0.3, color='green', label='Wear Period' if ax == ax1 else "")
            else:
                print(f"    Period does not overlap with data")
        
        # Format x-axis
        ax3.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d\n%H:%M'))
        ax3.xaxis.set_major_locator(plt.matplotlib.dates.HourLocator(interval=6))
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the plot
        plt.savefig('CO-002_triaxial_with_wear_periods.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("\nPlot saved as CO-002_triaxial_with_wear_periods.png")
    else:
        print("No triaxial data available for CO002")

if __name__ == "__main__":
    plot_CO002_with_wear_periods()
