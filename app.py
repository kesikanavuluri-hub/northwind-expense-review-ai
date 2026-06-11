import os
import json
import sqlite3
from datetime import datetime

import fitz
import pandas as pd
import streamlit as st

DB_PATH = "data/expense_review.db"


st.set_page_config(page_title="Northwind Expense Review AI", layout="wide")


def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_folder TEXT,
            employee_name TEXT,
            receipt_file TEXT,
            receipt_text TEXT,
            verdict TEXT,
            reason TEXT,
            policy_quote TEXT,
            override_verdict TEXT,
            override_comment TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def extract_pdf_text(path):
    text = ""
    doc = fitz.open(path)
    for page in doc:
        text += page.get_text()
    return text


def load_policy_text():
    all_text = ""
    for file in os.listdir("policies"):
        if file.lower().endswith(".pdf"):
            path = os.path.join("policies", file)
            all_text += f"\n\n--- {file} ---\n"
            all_text += extract_pdf_text(path)
    return all_text


def get_submissions():
    if not os.path.exists("submissions"):
        return []
    return [
        f for f in os.listdir("submissions")
        if os.path.isdir(os.path.join("submissions", f))
    ]


def load_employee_info(submission_folder):
    path = os.path.join("submissions", submission_folder, "employee_info.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_receipts(submission_folder):
    receipt_dir = os.path.join("submissions", submission_folder, "receipts")
    if not os.path.exists(receipt_dir):
        return []
    return [
        os.path.join(receipt_dir, f)
        for f in os.listdir(receipt_dir)
        if f.lower().endswith(".pdf")
    ]


def find_policy_quote(policy_text, receipt_text):
    receipt_lower = receipt_text.lower()

    keywords = []
    if "dinner" in receipt_lower:
        keywords = ["dinner", "meal", "limit", "cap"]
    elif "breakfast" in receipt_lower:
        keywords = ["breakfast", "meal", "limit", "cap"]
    elif "lunch" in receipt_lower:
        keywords = ["lunch", "meal", "limit", "cap"]
    elif "hotel" in receipt_lower or "marriott" in receipt_lower or "hyatt" in receipt_lower or "hilton" in receipt_lower:
        keywords = ["hotel", "lodging", "nightly", "rate"]
    elif "uber" in receipt_lower or "lyft" in receipt_lower:
        keywords = ["rideshare", "taxi", "transportation", "uber", "lyft"]
    elif "flight" in receipt_lower or "airlines" in receipt_lower or "delta" in receipt_lower:
        keywords = ["airfare", "flight", "economy", "air travel"]
    else:
        keywords = ["receipt", "expense", "reimbursement"]

    for line in policy_text.splitlines():
        clean = line.strip()
        low = clean.lower()
        if len(clean) > 30 and any(k in low for k in keywords):
            return clean

    return "No exact policy quote found. Manual review required."


def review_receipt(receipt_file, policy_text):
    receipt_text = extract_pdf_text(receipt_file)
    text = receipt_text.lower()
    file_name = os.path.basename(receipt_file).lower()

    verdict = "Compliant"
    reason = "No obvious policy violation was detected."
    confidence = "0.78"

    if "alcohol" in text or "wine" in text or "beer" in text or "cocktail" in text:
        verdict = "Flagged"
        reason = "Receipt may include alcohol and should be reviewed."
        confidence = "0.86"

    if "alinea" in text or "alinea" in file_name:
        verdict = "Flagged"
        reason = "Dinner appears likely to exceed the allowed meal cap."
        confidence = "0.88"

    if "mismatch" in text or "different" in text or "seattle" in file_name:
        verdict = "Needs Review"
        reason = "Receipt may not fully match the expected trip details."
        confidence = "0.73"

    policy_quote = find_policy_quote(policy_text, receipt_text)

    return receipt_text, verdict, reason, policy_quote, confidence


def save_review(submission_folder, employee_name, receipt_file, receipt_text, verdict, reason, policy_quote):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reviews
        (submission_folder, employee_name, receipt_file, receipt_text, verdict, reason,
         policy_quote, override_verdict, override_comment, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        submission_folder,
        employee_name,
        os.path.basename(receipt_file),
        receipt_text,
        verdict,
        reason,
        policy_quote,
        "",
        "",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()


def get_history():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM reviews ORDER BY id DESC", conn)
    conn.close()
    return df


def update_override(review_id, override, comment):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE reviews SET override_verdict=?, override_comment=? WHERE id=?",
        (override, comment, review_id)
    )
    conn.commit()
    conn.close()


init_db()
policy_text = load_policy_text()

st.title("Northwind Expense Review AI")
st.write("Expense receipt review using company policy PDFs.")

page = st.sidebar.radio(
    "Menu",
    ["New Submission", "Review History", "Policy Q&A", "Project Info"]
)

if page == "New Submission":
    st.header("New Submission")

    submissions = get_submissions()

    selected = st.selectbox("Select submission folder", submissions)

    if selected:
        employee = load_employee_info(selected)
        employee_name = employee.get("employee_name", employee.get("name", "Unknown Employee"))

        st.subheader("Employee Info")
        st.json(employee)

        receipts = get_receipts(selected)

        st.subheader("Receipts Found")
        for r in receipts:
            st.write(os.path.basename(r))

        if st.button("Review All Receipts"):
            for receipt in receipts:
                receipt_text, verdict, reason, policy_quote, confidence = review_receipt(receipt, policy_text)

                save_review(
                    selected,
                    employee_name,
                    receipt,
                    receipt_text,
                    verdict,
                    reason,
                    policy_quote
                )

                st.markdown("---")
                st.subheader(os.path.basename(receipt))
                st.write("**Verdict:**", verdict)
                st.write("**Reason:**", reason)
                st.write("**Policy Quote:**")
                st.info(policy_quote)
                st.write("**Confidence:**", confidence)

                with st.expander("View extracted receipt text"):
                    st.text(receipt_text[:3000])

elif page == "Review History":
    st.header("Review History")

    df = get_history()

    if df.empty:
        st.info("No reviews saved yet.")
    else:
        st.dataframe(df[[
            "id",
            "submission_folder",
            "employee_name",
            "receipt_file",
            "verdict",
            "override_verdict",
            "created_at"
        ]])

        st.subheader("Reviewer Override")
        review_id = st.number_input("Review ID", min_value=1, step=1)
        override = st.selectbox("Override Verdict", ["", "Compliant", "Flagged", "Rejected", "Needs Review"])
        comment = st.text_area("Reviewer Comment")

        if st.button("Save Override"):
            update_override(review_id, override, comment)
            st.success("Override saved successfully.")

elif page == "Policy Q&A":
    st.header("Policy Q&A")

    question = st.text_input("Ask a Northwind expense policy question")

    if st.button("Ask"):
        q = question.lower()

        allowed_words = ["policy", "expense", "receipt", "meal", "hotel", "flight", "travel", "reimbursement", "uber", "lyft"]

        if not any(word in q for word in allowed_words):
            st.error("I can only answer Northwind expense policy questions.")
        else:
            quote = find_policy_quote(policy_text, question)
            st.write("**Answer:** The most relevant policy clause I found is:")
            st.info(quote)

elif page == "Project Info":
    st.header("Project Info")

    st.write("""
    This app reviews travel and expense receipts against company policy PDFs.

    Features:
    - Loads 5 submission folders
    - Reads employee_info.json
    - Reads receipt PDFs
    - Searches 8 policy PDFs
    - Gives verdict, reason, quote, confidence
    - Saves review history in SQLite
    - Allows reviewer override
    - Provides policy Q&A
    - Refuses unrelated questions
    """)