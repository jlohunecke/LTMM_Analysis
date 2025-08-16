import pandas as pd

def search_events():
    # Read the Excel file
    df = pd.read_excel('ReportHome75h.xlsx')
    
    print("Searching for entries with swimming/shower:")
    for idx, row in df.iterrows():
        for col in df.columns:
            if pd.notna(row[col]):
                value_str = str(row[col]).lower()
                if 'swimming' in value_str or 'shower' in value_str:
                    print(f'Row {idx}, Col {col}: {row[col]}')
    
    print("\nSearching for entries with hyphens (potential events):")
    for idx, row in df.iterrows():
        for col in df.columns:
            if pd.notna(row[col]):
                value_str = str(row[col])
                if '-' in value_str and ':' in value_str:
                    print(f'Row {idx}, Col {col}: {row[col]}')

if __name__ == "__main__":
    search_events()


