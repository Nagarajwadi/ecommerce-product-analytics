import sqlite3
import pandas as pd
from pathlib import Path
import sys


# ------------------------------------------------------------
# File paths
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "data" / "product_analytics.db"
SQL_DIR = BASE_DIR / "sql"


# ------------------------------------------------------------
# Get SQL filename from command line
# ------------------------------------------------------------

if len(sys.argv) != 2:
    print("Usage:")
    print("python sql/run_query.py <sql_file>")
    print()
    print("Example:")
    print("python sql/run_query.py funnel_analysis.sql")
    sys.exit(1)


sql_file = SQL_DIR / sys.argv[1]


# ------------------------------------------------------------
# Validate SQL file
# ------------------------------------------------------------

if not sql_file.exists():
    print(f"ERROR: SQL file not found: {sql_file}")
    sys.exit(1)


# ------------------------------------------------------------
# Load SQL query
# ------------------------------------------------------------

with open(sql_file, "r") as file:
    query = file.read()


# ------------------------------------------------------------
# Connect to database
# ------------------------------------------------------------

connection = sqlite3.connect(DB_PATH)


# ------------------------------------------------------------
# Execute query
# ------------------------------------------------------------

results = pd.read_sql_query(query, connection)


# ------------------------------------------------------------
# Close connection
# ------------------------------------------------------------

connection.close()


# ------------------------------------------------------------
# Display results
# ------------------------------------------------------------

print()
print(f"QUERY: {sql_file.name}")
print("=" * (len(sql_file.name) + 7))
print(results.to_string(index=False))
print()