import pandas as pd
import psycopg2
import os

# Config
EXCEL_FILE = 'Accounts through 0625.xlsx'
DB_NAME = 'healthtech'
DB_USER = 'postgres'
DB_PASSWORD = 'OMT8459sl!'
DB_HOST = 'localhost'
DB_PORT = '5432'

# Read spreadsheet
print('Reading spreadsheet...')
df = pd.read_excel(EXCEL_FILE)

# Rename columns for DB
col_map = {
    'Account Number': 'sample_number',
    'Practice Name': 'practice_name',
    'Sales Rep': 'sales_rep',
    'Territory': 'territory',
}
df = df.rename(columns=col_map)

# Only keep relevant columns
df = df[list(col_map.values())]

# Connect to DB
print('Connecting to database...')
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cursor = conn.cursor()

# Insert rows
print('Inserting rows...')
for _, row in df.iterrows():
    cursor.execute(
        '''INSERT INTO practice_samples (sample_number, practice_name, sales_rep, territory)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT (sample_number) DO UPDATE SET
               practice_name = EXCLUDED.practice_name,
               sales_rep = EXCLUDED.sales_rep,
               territory = EXCLUDED.territory''',
        (row['sample_number'], row['practice_name'], row['sales_rep'], row['territory'])
    )
conn.commit()
cursor.close()
conn.close()
print('Import complete!') 