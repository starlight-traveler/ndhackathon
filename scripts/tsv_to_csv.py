import csv
import sqlite3
import sys
import os

def create_food_db(tsv_file, db_file='food.db'):
    if not os.path.exists(tsv_file):
        print(f"TSV file '{tsv_file}' not found.")
        return

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food (
            id TEXT PRIMARY KEY,
            name TEXT,
            alternate_names TEXT,
            description TEXT,
            type TEXT,
            source TEXT,
            serving TEXT,
            nutrition_100g TEXT,
            ean_13 TEXT,
            labels TEXT,
            package_size TEXT,
            ingredients TEXT,
            ingredient_analysis TEXT
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_food_name ON food(name)')

    with open(tsv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        batch_size = 1000
        batch = []

        for i, row in enumerate(reader, start=1):
            batch.append((
                row.get('id'),
                row.get('name'),
                row.get('alternate_names'),
                row.get('description'),
                row.get('type'),
                row.get('source'),
                row.get('serving'),
                row.get('nutrition_100g'),
                row.get('ean_13'),
                row.get('labels'),
                row.get('package_size'),
                row.get('ingredients'),
                row.get('ingredient_analysis')
            ))

            if len(batch) == batch_size:
                cursor.executemany('''
                    INSERT OR REPLACE INTO food VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', batch)
                conn.commit()
                print(f"Inserted {i} rows...")
                batch.clear()

        if batch:
            cursor.executemany('''
                INSERT OR REPLACE INTO food VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', batch)
            conn.commit()
            print(f"Inserted total {i} rows.")

    conn.close()
    print(f"Database '{db_file}' created successfully.")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python create_food_db.py <path_to_your_tsv_file>")
        sys.exit(1)

    create_food_db(sys.argv[1])
