import sqlite3
import pandas as pd

conn = sqlite3.connect("data/expense_review.db")

df = pd.read_sql_query(
    "SELECT * FROM reviews",
    conn
)

conn.close()

print("Northwind Expense Review AI Evaluation")
print("--------------------------------------")
print("Total Reviews:", len(df))

if len(df) > 0:
    print("Compliant:", len(df[df["verdict"] == "Compliant"]))
    print("Flagged:", len(df[df["verdict"] == "Flagged"]))
    print("Needs Review:", len(df[df["verdict"] == "Needs Review"]))

print("Evaluation Complete")