# hdfcRAG

A RAG (Retrieval-Augmented Generation) system for HDFC Bank loan applications with structured CSV support and JSON metadata.

## Overview

This project implements a Retrieval-Augmented Generation system designed specifically for HDFC Bank loan application data. It supports:

- **CSV Upload**: Upload loan application data in CSV format
- **Structured JSON Metadata**: Automatically converts CSV rows to structured JSON for better retrieval
- **Document Support**: PDF, DOCX, TXT, MD files
- **Semantic Search**: Find relevant loan applications using natural language queries
- **AI-Powered Responses**: Get intelligent answers about loan applications

## Features

### CSV Data Structure

The system processes HDFC loan application CSVs with the following structure:

**Customer Information:**
- Loan_ID, Bank, Customer_Name, Gender, Age, Married, Dependents, Education, Religion, Occupation

**Contact & Location:**
- Phone_Number, Email, Mobile_Verified, Email_Verified
- State, City, PIN_Code, Property_Area, Region_Branch

**Employment & Financial:**
- Employment_Status, Organization_Type, Business_Type, Employment_Length_Years
- Applicant_Income, Coapplicant_Income, Annual_Household_Income, Monthly_Expense
- Existing_EMIs, Debt_to_Income_Ratio

**Loan Details:**
- Loan_Amount, Loan_Term_Months, Purpose_of_Loan, Loan_Status
- Loan_to_Annual_Income

**Credit Profile:**
- CIBIL_Score, Credit_History, Number_of_Previous_Loans, Default_History_Count

**Application Context:**
- Application_Text, Customer_Feedback, Agent_Notes, Customer_Sentiment
- Institutional_Relationships

### JSON Metadata Structure

Each CSV row is converted to structured JSON metadata:

```json
{
  "loan_id": "HDFC100001",
  "bank": "HDFC Bank",
  "customer_info": {
    "name": "Rohan Verma",
    "gender": "Male",
    "age": 36,
    "education": "Graduate",
    "occupation": "Farmer"
  },
  "financial_info": {
    "applicant_income": 56976,
    "annual_household_income": 683712,
    "debt_to_income_ratio": 0.098
  },
  "loan_details": {
    "loan_amount": 8031545,
    "loan_term_months": 360,
    "purpose": "Home",
    "loan_status": "Approved"
  },
  "credit_profile": {
    "cibil_score": 699,
    "credit_history": 1
  }
}
```

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
# Start the backend server
python -m backend.main

# Or using uvicorn directly
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage

### 1. Upload CSV Data

```bash
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@hdfc_loan_data.csv"
```

### 2. Query the System

```bash
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me approved loans for customers in Mumbai with CIBIL score above 700"}'
```

### 3. Example Queries

- "Find all rejected loan applications with low CIBIL scores"
- "Show me home loan applications from Delhi"
- "What are the common reasons for loan rejection?"
- "List customers with high debt-to-income ratio"
- "Find loan applications with negative customer sentiment"

### Response Format

```json
{
  "answer": "Based on the data, there are 3 approved loans...",
  "sources": ["hdfc_loan_data.csv"],
  "metadata": [
    {
      "loan_id": "HDFC100001",
      "customer_info": {...},
      "loan_details": {...}
    }
  ]
}
```

## Architecture

- **FastAPI**: REST API framework
- **FAISS**: Vector similarity search
- **Sentence Transformers**: Text embeddings (all-MiniLM-L6-v2)
- **Pandas**: CSV processing and data manipulation
- **LLM**: Local language model for answer generation

## Project Structure

```
hdfcRAG/
├── backend/
│   ├── main.py          # FastAPI application
│   ├── ingest.py        # Document & CSV processing
│   ├── rag.py           # Vector search engine
│   ├── inference.py     # LLM inference
│   └── utils.py         # Utilities
├── ui/
│   └── web/
│       └── index.html   # Web interface
├── requirements.txt     # Python dependencies
└── README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
