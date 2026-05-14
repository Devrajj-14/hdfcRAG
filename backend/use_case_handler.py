"""
Use Case Handler for HDFC Bank Loan Intelligence RAG Agent
Detects and optimizes queries based on three primary use cases
"""

from typing import Dict, List, Tuple
from .utils import get_logger

logger = get_logger(__name__)


class UseCaseHandler:
    """
    Handles use case detection and field prioritization for:
    - UC-1: Decision Explainer
    - UC-2: Grievance Handler  
    - UC-3: Policy Q&A Bot
    """
    
    def __init__(self):
        # Keywords for each use case
        self.uc1_keywords = [
            'why', 'explain', 'reason', 'decision', 'approved', 'rejected', 
            'factor', 'criteria', 'basis', 'determine', 'cibil', 'dti', 
            'debt', 'income', 'employment', 'credit score'
        ]
        
        self.uc2_keywords = [
            'complaint', 'feedback', 'grievance', 'dissatisfied', 'negative',
            'escalate', 'unhappy', 'issue', 'problem', 'concern', 'sentiment',
            'customer service', 'branch', 'agent', 'response'
        ]
        
        self.uc3_keywords = [
            'policy', 'requirement', 'regulation', 'rbi', 'npci', 'cibil',
            'compliance', 'institutional', 'swift', 'gstn', 'sebi',
            'guideline', 'rule', 'procedure', 'documentation', 'process'
        ]
    
    def detect_use_case(self, query: str) -> Tuple[str, float]:
        """
        Detect which use case the query belongs to
        
        Returns:
            Tuple of (use_case_name, confidence_score)
        """
        query_lower = query.lower()
        
        # Count keyword matches for each use case
        uc1_score = sum(1 for kw in self.uc1_keywords if kw in query_lower)
        uc2_score = sum(1 for kw in self.uc2_keywords if kw in query_lower)
        uc3_score = sum(1 for kw in self.uc3_keywords if kw in query_lower)
        
        scores = {
            'decision_explainer': uc1_score,
            'grievance_handler': uc2_score,
            'policy_qa': uc3_score
        }
        
        # Get the use case with highest score
        max_use_case = max(scores, key=scores.get)
        max_score = scores[max_use_case]
        
        # If no clear match, default to general
        if max_score == 0:
            return 'general', 0.0
        
        # Calculate confidence (normalize by total keywords)
        total_score = sum(scores.values())
        confidence = max_score / total_score if total_score > 0 else 0.0
        
        logger.info(f"Detected use case: {max_use_case} (confidence: {confidence:.2f})")
        return max_use_case, confidence
    
    def get_priority_fields(self, use_case: str) -> List[str]:
        """
        Get priority fields for a specific use case
        These fields should be emphasized in the context
        """
        priority_fields = {
            'decision_explainer': [
                'loan_id',
                'loan_status',
                'cibil_score',
                'debt_to_income_ratio',
                'purpose_of_loan',
                'employment_status',
                'application_text',
                'agent_notes',
                'credit_history',
                'applicant_income',
                'loan_amount',
                'default_history_count'
            ],
            'grievance_handler': [
                'loan_id',
                'customer_name',
                'customer_feedback',
                'agent_notes',
                'customer_sentiment',
                'loan_status',
                'region_branch',
                'default_history_count',
                'application_text',
                'state',
                'city'
            ],
            'policy_qa': [
                'institutional_relationships',
                'application_text',
                'region_branch',
                'purpose_of_loan',
                'organization_type',
                'state',
                'property_area',
                'business_type',
                'loan_amount',
                'employment_status'
            ],
            'general': [
                'loan_id',
                'customer_name',
                'loan_status',
                'application_text',
                'agent_notes'
            ]
        }
        
        return priority_fields.get(use_case, priority_fields['general'])
    
    def create_optimized_context(self, 
                                  retrieved_docs: List[Dict], 
                                  use_case: str,
                                  max_chars: int = 800) -> str:
        """
        Create optimized context based on use case
        Prioritizes relevant fields for each use case
        """
        priority_fields = self.get_priority_fields(use_case)
        context_parts = []
        
        for doc in retrieved_docs:
            if 'json_metadata' in doc:
                # Extract priority fields from JSON metadata
                metadata = doc['json_metadata']
                relevant_info = self._extract_priority_info(metadata, priority_fields)
                
                context_part = f"Source: {doc['source']}\n"
                context_part += f"Loan ID: {metadata.get('loan_id', 'N/A')}\n"
                context_part += relevant_info
                
                # Add full text if space allows
                remaining_chars = max_chars - len(context_part)
                if remaining_chars > 100:
                    context_part += f"\nFull Context: {doc['text'][:remaining_chars]}"
                
                context_parts.append(context_part)
            else:
                # Fallback for non-CSV documents
                context_parts.append(f"Source: {doc['source']}\nContent: {doc['text'][:max_chars]}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def _extract_priority_info(self, metadata: Dict, priority_fields: List[str]) -> str:
        """
        Extract priority information from JSON metadata
        """
        info_parts = []
        
        # Flatten nested metadata for easier access
        flat_metadata = self._flatten_metadata(metadata)
        
        for field in priority_fields:
            # Try to find the field in flattened metadata
            for key, value in flat_metadata.items():
                if field.lower() in key.lower() and value:
                    # Format the field name nicely
                    display_name = field.replace('_', ' ').title()
                    info_parts.append(f"{display_name}: {value}")
                    break
        
        return "\n".join(info_parts)
    
    def _flatten_metadata(self, metadata: Dict, parent_key: str = '') -> Dict:
        """
        Flatten nested dictionary for easier field access
        """
        items = []
        for k, v in metadata.items():
            new_key = f"{parent_key}_{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_metadata(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def get_use_case_prompt(self, use_case: str, question: str) -> str:
        """
        Get optimized system prompt for each use case
        """
        prompts = {
            'decision_explainer': f"""You are an HDFC Bank loan decision analyst. 
Analyze the provided loan application data and explain the decision factors clearly.
Focus on: CIBIL score, debt-to-income ratio, employment status, credit history, and agent notes.
Provide a transparent, factual explanation that a customer can understand.

Question: {question}

Provide a clear explanation based on the data provided.""",
            
            'grievance_handler': f"""You are an HDFC Bank customer service specialist.
Analyze customer feedback and grievances to identify issues and suggest resolutions.
Focus on: customer sentiment, feedback content, agent responses, branch performance, and escalation needs.
Be empathetic and solution-oriented.

Question: {question}

Provide a helpful response addressing the customer's concerns.""",
            
            'policy_qa': f"""You are an HDFC Bank policy expert.
Answer questions about loan policies, institutional requirements, and regulatory compliance.
Focus on: RBI, NPCI, CIBIL, SWIFT, GSTN regulations, branch policies, and state-specific requirements.
Provide accurate, authoritative information.

Question: {question}

Provide a clear, policy-based answer.""",
            
            'general': f"""You are an HDFC Bank loan intelligence assistant.
Answer the question based on the provided loan application data.
Be clear, accurate, and helpful.

Question: {question}

Provide a helpful response based on the data."""
        }
        
        return prompts.get(use_case, prompts['general'])
    
    def format_response_metadata(self, 
                                   use_case: str, 
                                   metadata_list: List[Dict]) -> List[Dict]:
        """
        Format metadata response based on use case
        Only include relevant fields for each use case
        """
        priority_fields = self.get_priority_fields(use_case)
        formatted_metadata = []
        
        for metadata in metadata_list:
            filtered = {}
            flat_metadata = self._flatten_metadata(metadata)
            
            # Include only priority fields
            for field in priority_fields:
                for key, value in flat_metadata.items():
                    if field.lower() in key.lower():
                        filtered[key] = value
            
            formatted_metadata.append(filtered)
        
        return formatted_metadata
