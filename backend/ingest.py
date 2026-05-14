import os
import json
from typing import List
from fastapi import UploadFile
import pypdf
import docx
import pandas as pd
from .utils import get_logger

logger = get_logger(__name__)

class DocumentIngester:
    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def extract_text(self, file: UploadFile) -> str:
        """Extract text from various file formats including CSV"""
        filename = file.filename.lower()
        content = ""
        
        try:
            if filename.endswith('.pdf'):
                reader = pypdf.PdfReader(file.file)
                for page in reader.pages:
                    content += page.extract_text() + "\n"
            elif filename.endswith('.docx'):
                doc = docx.Document(file.file)
                content = "\n".join([para.text for para in doc.paragraphs])
            elif filename.endswith('.txt') or filename.endswith('.md'):
                content = (await file.read()).decode('utf-8')
            elif filename.endswith('.csv'):
                # CSV files are handled separately - return empty string
                # They will be processed by extract_csv_with_metadata
                return ""
            else:
                logger.warning(f"Unsupported file type: {filename}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
            return ""
            
        return self.clean_text(content)
    
    async def extract_csv_with_metadata(self, file: UploadFile) -> List[dict]:
        """
        Extract CSV data and convert each row to structured JSON metadata
        for HDFC loan applications
        """
        try:
            # Read CSV file
            content = await file.read()
            df = pd.read_csv(pd.io.common.BytesIO(content))
            
            logger.info(f"CSV loaded: {len(df)} rows, {len(df.columns)} columns")
            
            structured_records = []
            
            for idx, row in df.iterrows():
                # Create structured JSON metadata for each loan application
                json_metadata = {
                    "loan_id": str(row.get('Loan_ID', '')),
                    "bank": str(row.get('Bank', '')),
                    "customer_info": {
                        "name": str(row.get('Customer_Name', '')),
                        "gender": str(row.get('Gender', '')),
                        "age": int(row.get('Age', 0)) if pd.notna(row.get('Age')) else 0,
                        "married": str(row.get('Married', '')),
                        "dependents": str(row.get('Dependents', '')),
                        "education": str(row.get('Education', '')),
                        "religion": str(row.get('Religion', '')),
                        "occupation": str(row.get('Occupation', ''))
                    },
                    "contact_info": {
                        "phone": str(row.get('Phone_Number', '')),
                        "email": str(row.get('Email', '')),
                        "mobile_verified": str(row.get('Mobile_Verified', '')),
                        "email_verified": str(row.get('Email_Verified', ''))
                    },
                    "location": {
                        "state": str(row.get('State', '')),
                        "city": str(row.get('City', '')),
                        "pin_code": str(row.get('PIN_Code', '')),
                        "property_area": str(row.get('Property_Area', '')),
                        "region_branch": str(row.get('Region_Branch', ''))
                    },
                    "employment": {
                        "status": str(row.get('Employment_Status', '')),
                        "organization_type": str(row.get('Organization_Type', '')),
                        "business_type": str(row.get('Business_Type', '')),
                        "employment_length_years": int(row.get('Employment_Length_Years', 0)) if pd.notna(row.get('Employment_Length_Years')) else 0
                    },
                    "financial_info": {
                        "applicant_income": float(row.get('Applicant_Income', 0)) if pd.notna(row.get('Applicant_Income')) else 0,
                        "coapplicant_income": float(row.get('Coapplicant_Income', 0)) if pd.notna(row.get('Coapplicant_Income')) else 0,
                        "annual_household_income": float(row.get('Annual_Household_Income', 0)) if pd.notna(row.get('Annual_Household_Income')) else 0,
                        "monthly_expense": float(row.get('Monthly_Expense', 0)) if pd.notna(row.get('Monthly_Expense')) else 0,
                        "existing_emis": float(row.get('Existing_EMIs', 0)) if pd.notna(row.get('Existing_EMIs')) else 0,
                        "debt_to_income_ratio": float(row.get('Debt_to_Income_Ratio', 0)) if pd.notna(row.get('Debt_to_Income_Ratio')) else 0
                    },
                    "loan_details": {
                        "loan_amount": float(row.get('Loan_Amount', 0)) if pd.notna(row.get('Loan_Amount')) else 0,
                        "loan_term_months": int(row.get('Loan_Term_Months', 0)) if pd.notna(row.get('Loan_Term_Months')) else 0,
                        "purpose": str(row.get('Purpose_of_Loan', '')),
                        "loan_status": str(row.get('Loan_Status', '')),
                        "loan_to_annual_income": float(row.get('Loan_to_Annual_Income', 0)) if pd.notna(row.get('Loan_to_Annual_Income')) else 0
                    },
                    "credit_profile": {
                        "cibil_score": int(row.get('CIBIL_Score', 0)) if pd.notna(row.get('CIBIL_Score')) else 0,
                        "credit_history": int(row.get('Credit_History', 0)) if pd.notna(row.get('Credit_History')) else 0,
                        "number_of_previous_loans": int(row.get('Number_of_Previous_Loans', 0)) if pd.notna(row.get('Number_of_Previous_Loans')) else 0,
                        "default_history_count": int(row.get('Default_History_Count', 0)) if pd.notna(row.get('Default_History_Count')) else 0
                    },
                    "assets_and_guarantor": {
                        "asset_value": float(row.get('Asset_Value', 0)) if pd.notna(row.get('Asset_Value')) else 0,
                        "guarantor": str(row.get('Guarantor', '')),
                        "cosigner_relationship": str(row.get('Co-signer_Relationship', ''))
                    },
                    "application_details": {
                        "application_text": str(row.get('Application_Text', '')),
                        "customer_feedback": str(row.get('Customer_Feedback', '')),
                        "agent_notes": str(row.get('Agent_Notes', '')),
                        "customer_sentiment": str(row.get('Customer_Sentiment', ''))
                    },
                    "institutional_relationships": str(row.get('Institutional_Relationships', '')),
                    "aadhaar_synthetic": str(row.get('Aadhaar_Synthetic', ''))
                }
                
                # Create a searchable text representation
                searchable_text = self._create_searchable_text(json_metadata)
                
                structured_records.append({
                    "json_metadata": json_metadata,
                    "searchable_text": searchable_text,
                    "source": file.filename
                })
            
            logger.info(f"Converted {len(structured_records)} CSV rows to structured JSON metadata")
            return structured_records
            
        except Exception as e:
            logger.error(f"Error processing CSV file {file.filename}: {e}")
            return []
    
    def _create_searchable_text(self, json_metadata: dict) -> str:
        """
        Convert structured JSON metadata to searchable text for embedding
        """
        customer = json_metadata.get('customer_info', {})
        loan = json_metadata.get('loan_details', {})
        financial = json_metadata.get('financial_info', {})
        credit = json_metadata.get('credit_profile', {})
        location = json_metadata.get('location', {})
        employment = json_metadata.get('employment', {})
        app_details = json_metadata.get('application_details', {})
        
        text_parts = [
            f"Loan ID: {json_metadata.get('loan_id')}",
            f"Bank: {json_metadata.get('bank')}",
            f"Customer: {customer.get('name')}, {customer.get('gender')}, Age {customer.get('age')}",
            f"Education: {customer.get('education')}, Occupation: {customer.get('occupation')}",
            f"Married: {customer.get('married')}, Dependents: {customer.get('dependents')}",
            f"Location: {location.get('city')}, {location.get('state')}, PIN: {location.get('pin_code')}",
            f"Property Area: {location.get('property_area')}, Branch: {location.get('region_branch')}",
            f"Employment: {employment.get('status')}, Organization: {employment.get('organization_type')}",
            f"Business Type: {employment.get('business_type')}, Experience: {employment.get('employment_length_years')} years",
            f"Applicant Income: ₹{financial.get('applicant_income')}, Co-applicant Income: ₹{financial.get('coapplicant_income')}",
            f"Annual Household Income: ₹{financial.get('annual_household_income')}",
            f"Monthly Expense: ₹{financial.get('monthly_expense')}, Existing EMIs: ₹{financial.get('existing_emis')}",
            f"Debt to Income Ratio: {financial.get('debt_to_income_ratio')}",
            f"Loan Amount: ₹{loan.get('loan_amount')}, Term: {loan.get('loan_term_months')} months",
            f"Purpose: {loan.get('purpose')}, Status: {loan.get('loan_status')}",
            f"CIBIL Score: {credit.get('cibil_score')}, Credit History: {credit.get('credit_history')}",
            f"Previous Loans: {credit.get('number_of_previous_loans')}, Defaults: {credit.get('default_history_count')}",
            f"Application: {app_details.get('application_text')}",
            f"Customer Feedback: {app_details.get('customer_feedback')}",
            f"Agent Notes: {app_details.get('agent_notes')}",
            f"Sentiment: {app_details.get('customer_sentiment')}",
            f"Institutional Relationships: {json_metadata.get('institutional_relationships')}"
        ]
        
        return "\n".join([part for part in text_parts if part])
    
    def chunk_csv_records(self, records: List[dict]) -> List[dict]:
        """
        Create chunks from CSV records with JSON metadata
        Each record becomes one chunk with its full JSON metadata
        """
        chunks = []
        
        for idx, record in enumerate(records):
            chunk = {
                "text": record["searchable_text"],  # For embedding
                "json_metadata": record["json_metadata"],  # Structured data
                "parent_text": record["searchable_text"],  # For LLM context
                "source": record["source"],
                "parent_id": f"csv_record_{record['json_metadata'].get('loan_id', idx)}",
                "record_type": "loan_application"
            }
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} chunks from CSV records")
        return chunks

    def clean_text(self, text: str) -> str:
        # Preserve newlines so section headers stay intact.
        # Only collapse multiple blank lines into one.
        import re
        text = re.sub(r'\r\n', '\n', text)          # normalise Windows line endings
        text = re.sub(r'[ \t]+', ' ', text)          # collapse horizontal whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)       # max one blank line between sections
        return text.strip()

    def chunk_text(self, text: str, source: str) -> List[dict]:
        """
        Section-aware hierarchical chunking.

        For structured documents (with == SECTION == headers) each section
        is kept as its own parent chunk so information about one hostel block
        never bleeds into another block's chunk.

        For unstructured documents we fall back to the original sliding-window
        word-based parent→child approach.
        """
        import re
        chunks = []

        # ── 1. Try section-based splitting on == HEADER == markers ──────────
        sections = re.split(r'(?=^==\s+)', text, flags=re.MULTILINE)
        sections = [s.strip() for s in sections if s.strip()]

        if len(sections) > 1:
            # Structured document: one parent per section
            for idx, section in enumerate(sections):
                parent_id   = f"parent_{source}_{idx}"
                parent_text = section

                # Build fine-grained child chunks from this section for FAISS
                words = section.split()
                child_size    = 80   # words per child embedding
                child_overlap = 20

                for j in range(0, len(words), child_size - child_overlap):
                    child_words = words[j:j + child_size]
                    if not child_words:
                        continue
                    chunks.append({
                        "text":        " ".join(child_words),  # embedded in FAISS
                        "parent_text": parent_text,            # returned to LLM
                        "source":      source,
                        "parent_id":   parent_id,
                    })

            logger.info(f"Section-aware: {len(sections)} sections → {len(chunks)} child chunks from {source}")
            return chunks

        # ── 2. Fallback: sliding-window word-based chunking ──────────────────
        words = text.split()
        if not words:
            return []

        parent_chunk_size    = 800
        parent_chunk_overlap = 150
        child_chunk_size     = 200
        child_chunk_overlap  = 50

        parent_id_counter = 0
        for i in range(0, len(words), parent_chunk_size - parent_chunk_overlap):
            parent_chunk_words = words[i:i + parent_chunk_size]
            parent_text        = " ".join(parent_chunk_words)
            parent_id          = f"parent_{source}_{parent_id_counter}"
            parent_id_counter += 1

            for j in range(0, len(parent_chunk_words), child_chunk_size - child_chunk_overlap):
                child_words = parent_chunk_words[j:j + child_chunk_size]
                if not child_words:
                    continue
                chunks.append({
                    "text":        " ".join(child_words),
                    "parent_text": parent_text,
                    "source":      source,
                    "parent_id":   parent_id,
                })

        logger.info(f"Flat fallback: {len(chunks)} hierarchical child chunks from {source}")
        return chunks

