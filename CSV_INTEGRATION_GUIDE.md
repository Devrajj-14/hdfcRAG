# CSV Integration Guide for HDFC RAG System

## Overview

This document explains how CSV files are processed and aligned with JSON metadata in the HDFC RAG system.

## What Was Implemented

### 1. CSV Upload Support

The system now accepts CSV files containing HDFC loan application data with 40+ columns including:
- Customer demographics (name, age, gender, education, occupation)
- Financial information (income, expenses, EMIs, debt ratios)
- Loan details (amount, term, purpose, status)
- Credit profile (CIBIL score, credit history, previous loans)
- Application context (feedback, agent notes, sentiment)

### 2. Structured JSON Metadata

Each CSV row is automatically converted to a structured JSON object with the following hierarchy:

```json
{
  "loan_id": "HDFC100001",
  "bank": "HDFC Bank",
  "customer_info": {
    "name": "...",
    "gender": "...",
    "age": 36,
    "married": "...",
    "dependents": "...",
    "education": "...",
    "religion": "...",
    "occupation": "..."
  },
  "contact_info": {
    "phone": "...",
    "email": "...",
    "mobile_verified": "...",
    "email_verified": "..."
  },
  "location": {
    "state": "...",
    "city": "...",
    "pin_code": "...",
    "property_area": "...",
    "region_branch": "..."
  },
  "employment": {
    "status": "...",
    "organization_type": "...",
    "business_type": "...",
    "employment_length_years": 0
  },
  "financial_info": {
    "applicant_income": 0,
    "coapplicant_income": 0,
    "annual_household_income": 0,
    "monthly_expense": 0,
    "existing_emis": 0,
    "debt_to_income_ratio": 0
  },
  "loan_details": {
    "loan_amount": 0,
    "loan_term_months": 0,
    "purpose": "...",
    "loan_status": "...",
    "loan_to_annual_income": 0
  },
  "credit_profile": {
    "cibil_score": 0,
    "credit_history": 0,
    "number_of_previous_loans": 0,
    "default_history_count": 0
  },
  "assets_and_guarantor": {
    "asset_value": 0,
    "guarantor": "...",
    "cosigner_relationship": "..."
  },
  "application_details": {
    "application_text": "...",
    "customer_feedback": "...",
    "agent_notes": "...",
    "customer_sentiment": "..."
  },
  "institutional_relationships": "...",
  "aadhaar_synthetic": "..."
}
```

### 3. Dual Representation System

Each CSV record is stored with TWO representations:

#### A. Searchable Text (for embeddings)
A human-readable text format that gets embedded into the vector database:

```
Loan ID: HDFC100001
Bank: HDFC Bank
Customer: Rohan Verma, Male, Age 36
Education: Graduate, Occupation: Farmer
Married: No, Dependents: 2
Location: Dwarka, Delhi, PIN: 857743
Property Area: Urban, Branch: KOL-004
Employment: Salaried, Organization: Public
Applicant Income: ₹56976, Co-applicant Income: ₹0
Annual Household Income: ₹683712
Loan Amount: ₹8031545, Term: 360 months
Purpose: Home, Status: Approved
CIBIL Score: 699, Credit History: 1
Application: Applicant requests home loan...
Customer Feedback: Neutral — application was okay...
Agent Notes: Verified documents; requires guarantor...
```

#### B. JSON Metadata (for structured access)
The structured JSON object shown above, which is:
- Stored alongside the searchable text
- Returned in query responses
- Available for programmatic access

### 4. How It Works

#### Step 1: CSV Upload
```python
POST /v1/documents/upload
Content-Type: multipart/form-data
files: hdfc_loan_data.csv
```

#### Step 2: Processing Pipeline

1. **CSV Parsing**: Pandas reads the CSV file
2. **Row-by-Row Conversion**: Each row → JSON metadata object
3. **Text Generation**: JSON → searchable text representation
4. **Embedding**: Searchable text → vector embedding
5. **Storage**: Both representations stored in FAISS index

#### Step 3: Query & Retrieval

```python
POST /v1/query
{
  "question": "Show me approved home loans in Delhi"
}
```

1. **Query Embedding**: Question → vector
2. **Similarity Search**: Find closest matching loan records
3. **Context Building**: Retrieve both text and JSON metadata
4. **LLM Generation**: Generate answer using context
5. **Response**: Return answer + sources + JSON metadata

### 5. Key Benefits

✅ **Semantic Search**: Find loans by natural language queries
✅ **Structured Data**: Access exact field values via JSON
✅ **Flexible Queries**: Ask questions in any format
✅ **Rich Context**: LLM sees both narrative and structured data
✅ **Metadata Preservation**: All original CSV fields retained

### 6. Example Use Cases

**Query**: "Find rejected loans with CIBIL score below 600"
- System searches embedded text for semantic matches
- Returns JSON metadata with exact CIBIL scores
- LLM generates human-readable summary

**Query**: "Show me customers from Mumbai with high income"
- Semantic search finds location + income mentions
- JSON metadata provides exact income values
- Response includes structured customer_info

**Query**: "What's the common feedback for rejected applications?"
- Searches application_details.customer_feedback
- Aggregates patterns across multiple records
- LLM summarizes common themes

## Files Modified

1. **requirements.txt**: Added `pandas` and `openpyxl`
2. **backend/ingest.py**: 
   - Added `extract_csv_with_metadata()` method
   - Added `_create_searchable_text()` helper
   - Added `chunk_csv_records()` method
3. **backend/main.py**: 
   - Updated upload endpoint to handle CSV
   - Modified query response to include metadata
4. **backend/rag.py**: 
   - Updated search to preserve JSON metadata
5. **backend/utils.py**: 
   - Added `.csv` to ALLOWED_EXTENSIONS

## Testing

### Upload a CSV
```bash
curl -X POST "http://localhost:8000/v1/documents/upload" \
  -F "files=@your_hdfc_data.csv"
```

### Query the Data
```bash
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me all approved loans in Mumbai"
  }'
```

### Expected Response
```json
{
  "answer": "Based on the data, there are 3 approved loans in Mumbai...",
  "sources": ["your_hdfc_data.csv"],
  "metadata": [
    {
      "loan_id": "HDFC100001",
      "customer_info": {...},
      "location": {
        "city": "Mumbai",
        "state": "Maharashtra"
      },
      "loan_details": {
        "loan_status": "Approved"
      }
    }
  ]
}
```

## Next Steps

1. Upload your HDFC loan CSV file
2. Test queries against the data
3. Adjust the JSON structure if needed
4. Add custom fields to the metadata mapping

## Notes

- The system handles missing/null values gracefully
- All numeric fields are properly typed (int/float)
- Text fields are converted to strings
- The JSON structure can be customized in `ingest.py`
