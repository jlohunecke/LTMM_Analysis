# LTMM Analysis

This repository contains analysis scripts and data for the LTMM (Long-Term Monitoring) project.

## Project Structure

- `minute_level/` - Contains minute-level data files for different subjects (CO001-CO042, FL004-FL036)
- `old/` - Legacy scripts and files from previous analysis iterations
- `exploration.ipynb` - Main Jupyter notebook for data exploration and analysis
- `complete_wear_periods_reformatted.csv` - Processed wear period data
- `ReportHome75h.xlsx` - Original data source

## Data Files

The project contains accelerometer data from multiple subjects, with both CO (Control) and FL (Flight) groups represented. Each subject has minute-level triaxial accelerometer data.

## Analysis Scripts

- `exploration.ipynb` - Main analysis notebook
- Various Python scripts in the `old/` directory for data processing and visualization

## Getting Started

1. Clone this repository
2. Install required dependencies (if any)
3. Open `exploration.ipynb` to begin analysis

## Notes

- The `.gitignore` file is configured to exclude common Python artifacts and output files
- Data files are included in version control (CSV and Excel files)
- Output images and plots are excluded from version control
