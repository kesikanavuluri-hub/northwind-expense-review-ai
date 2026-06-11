# Northwind Expense Review AI

## Overview

Northwind Expense Review AI is a Streamlit-based application that reviews employee travel expense receipts against company policy documents.

The application extracts receipt information, compares expenses against policy rules, generates compliance decisions, provides policy citations, and stores review history in SQLite.

## Features

* Employee submission review
* Receipt PDF processing
* Policy PDF search
* Compliance verdict generation
* Policy citation display
* Reviewer override workflow
* SQLite persistence
* Policy Q&A
* Review history tracking

## Technology Stack

* Python
* Streamlit
* SQLite
* Pandas
* PyMuPDF

## How to Run

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Architecture

1. Load policy PDFs
2. Load employee submission
3. Extract receipt text
4. Match against policy documents
5. Generate verdict
6. Save results to SQLite
7. Allow reviewer override

## Evaluation

Run:

```bash
python eval_harness.py
```

## Future Improvements

* OCR for image receipts
* LLM-based RAG retrieval
* Better policy citations
* Authentication
* Analytics dashboard

## Scaling Considerations

For 10,000+ submissions/day:

* Cloud object storage
* Managed database
* Background processing
* Queue-based architecture
* Vector database retrieval
* Monitoring and alerting
