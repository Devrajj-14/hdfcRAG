# HDFC Bank Loan Intelligence RAG Agent - Use Cases

## Overview
This document defines the three primary use cases for the HDFC Bank Loan Intelligence RAG Agent, built for the Groq Cloud LLaMA 3 Challenge.

**Challenge Context:**
- **Organization**: HDFC Bank
- **Platform**: Groq Cloud with LLaMA 3
- **Focus**: Customer Success & Internal Engineering
- **Time Constraint**: 3-Hour Sprint
- **Classification**: Confidential - Internal Use Only

---

## UC-1: Decision Explainer 🎯

### Purpose
Provide transparent explanations for loan approval/rejection decisions to customers and internal teams.

### Key Fields
| Field | Purpose |
|-------|---------|
| `Application_Text` | Original loan request context |
| `Agent_Notes` | Internal decision rationale |
| `Loan_Status` | Approved/Rejected outcome |
| `CIBIL_Score` | Credit score (primary factor) |
| `Debt_to_Income_Ratio` | Financial health indicator |
| `Purpose_of_Loan` | Home/Business/Personal/Auto/Medical/Education |
| `Employment_Status` | Salaried/Self-Employed/Unemployed/Retired |

### Example Queries
```
1. "Why was loan HDFC100005 rejected despite having a guarantor?"
2. "Explain the approval decision for Rohan Verma's home loan"
3. "What factors led to rejection of loans with CIBIL score above 650?"
4. "Compare approved vs rejected applications for self-employed applicants"
5. "Why do unemployed applicants get rejected even with high asset values?"
```

### Expected Output
```json
{
  "answer": "Loan HDFC100005 was rejected primarily due to...",
  "decision_factors": {
    "cibil_score": 594,
    "dti_ratio": 0.0,
    "employment_status": "Self-Employed",
    "loan_status": "Rejected",
    "key_reason": "Credit history flag (0) and previous default history"
  },
  "agent_notes": "Recommend conditional approval pending site valuation",
  "sources": ["hdfc_loan_data.csv"]
}
```

### Business Value
- **Transparency**: Clear explanations build customer trust
- **Compliance**: Audit trail for regulatory requirements
- **Training**: Help agents understand decision patterns
- **Appeals**: Support for loan reconsideration requests

---

## UC-2: Grievance Handler 🛠️

### Purpose
Efficiently manage customer complaints, track sentiment, and escalate unresolved issues.

### Key Fields
| Field | Purpose |
|-------|---------|
| `Customer_Feedback` | Customer's complaint/concern |
| `Agent_Notes` | Agent's response and actions taken |
| `Customer_Sentiment` | Positive/Negative/Neutral |
| `Loan_Status` | Current application status |
| `Region_Branch` | Branch responsible (e.g., DEL-001, MUM-002) |
| `Default_History_Count` | Past payment issues |

### Example Queries
```
1. "Show me all negative feedback from Delhi branch with unresolved issues"
2. "Find customers who complained about credit score errors"
3. "List all 'Very dissatisfied' customers from last month"
4. "Which branches have the most grievances?"
5. "Show me escalated cases requiring relationship manager review"
```

### Expected Output
```json
{
  "answer": "Found 5 negative feedback cases from Delhi branch...",
  "grievances": [
    {
      "loan_id": "HDFC100009",
      "customer_name": "Rehan Siddiqui",
      "feedback": "Complained about credit score errors and wants manual review",
      "sentiment": "Positive",
      "branch": "KOL-004",
      "agent_action": "Recommend conditional approval pending site valuation",
      "status": "Rejected"
    }
  ],
  "summary": {
    "total_grievances": 5,
    "negative_sentiment": 3,
    "escalated": 2,
    "branches_affected": ["DEL-001", "KOL-004"]
  }
}
```

### Business Value
- **Customer Retention**: Quick resolution prevents churn
- **Pattern Detection**: Identify systemic issues
- **Branch Performance**: Track regional service quality
- **Escalation Management**: Prioritize critical cases

---

## UC-3: Policy Q&A Bot 📚

### Purpose
Answer policy-related questions about loan products, institutional requirements, and regulatory compliance.

### Key Fields
| Field | Purpose |
|-------|---------|
| `Application_Text` | Loan context and requirements |
| `Institutional_Relationships` | RBI, NPCI, CIBIL, SWIFT, GSTN, SEBI integrations |
| `Region_Branch` | Branch-specific policies |
| `Purpose_of_Loan` | Loan product type |
| `Organization_Type` | Public/Private/MNC/Government/Startup |
| `State` | State-specific regulations |

### Example Queries
```
1. "What are the NPCI integration requirements for business loans in Maharashtra?"
2. "Explain RBI regulatory requirements for home loans above 50 lakhs"
3. "What documents are needed for CIBIL credit checks?"
4. "Which branches handle SWIFT international transfers?"
5. "What are the GSTN tax linkage requirements for self-employed applicants?"
6. "Compare loan policies for Government vs Private sector employees"
```

### Expected Output
```json
{
  "answer": "NPCI integration requirements for business loans in Maharashtra include...",
  "policy_details": {
    "institutional_requirements": [
      "NPCI: UPI integrations for digital payments",
      "GSTN: Tax linkage for business verification",
      "CIBIL: Credit bureau checks"
    ],
    "state_regulations": "Maharashtra specific compliance",
    "applicable_branches": ["MUM-002", "PUNE-006"],
    "organization_types": ["Private", "Startup", "MNC"]
  },
  "related_applications": 3,
  "sources": ["hdfc_loan_data.csv"]
}
```

### Business Value
- **Agent Enablement**: Quick access to policy information
- **Consistency**: Standardized answers across branches
- **Compliance**: Ensure regulatory adherence
- **Efficiency**: Reduce policy lookup time

---

## Technical Implementation

### Use Case Routing
The system can automatically detect which use case a query belongs to:

```python
def detect_use_case(query: str) -> str:
    query_lower = query.lower()
    
    # UC-1: Decision Explainer
    if any(word in query_lower for word in ['why', 'explain', 'reason', 'decision', 'approved', 'rejected', 'factor']):
        return "decision_explainer"
    
    # UC-2: Grievance Handler
    elif any(word in query_lower for word in ['complaint', 'feedback', 'grievance', 'dissatisfied', 'negative', 'escalate']):
        return "grievance_handler"
    
    # UC-3: Policy Q&A
    elif any(word in query_lower for word in ['policy', 'requirement', 'regulation', 'rbi', 'npci', 'cibil', 'compliance']):
        return "policy_qa"
    
    else:
        return "general"
```

### Field Prioritization by Use Case

**UC-1 (Decision Explainer)** - Focus on:
- Credit metrics (CIBIL, DTI, Credit History)
- Employment and income
- Agent decision notes

**UC-2 (Grievance Handler)** - Focus on:
- Customer sentiment and feedback
- Agent response and escalation
- Branch and regional patterns

**UC-3 (Policy Q&A)** - Focus on:
- Institutional relationships
- Regulatory requirements
- Branch and state policies

---

## Query Examples by Use Case

### UC-1: Decision Explainer
```
✅ "Why was HDFC100002 rejected with CIBIL score 707?"
✅ "Explain approval factors for home loans in Urban areas"
✅ "What's the typical DTI ratio for approved business loans?"
✅ "Compare employment status impact on loan decisions"
```

### UC-2: Grievance Handler
```
✅ "Show negative feedback from BLR-003 branch"
✅ "Find customers complaining about documentation delays"
✅ "List all escalated cases requiring manual CIBIL review"
✅ "Which agents have the most customer complaints?"
```

### UC-3: Policy Q&A
```
✅ "What are NPCI requirements for UPI integration?"
✅ "Explain RBI regulatory oversight for home loans"
✅ "Which states require additional GSTN verification?"
✅ "What institutional relationships are needed for international transfers?"
```

---

## Success Metrics

### UC-1: Decision Explainer
- **Accuracy**: 95%+ correct factor identification
- **Completeness**: All decision factors mentioned
- **Clarity**: Non-technical language for customers

### UC-2: Grievance Handler
- **Response Time**: < 2 seconds
- **Sentiment Detection**: 90%+ accuracy
- **Escalation Routing**: 100% critical cases flagged

### UC-3: Policy Q&A
- **Policy Coverage**: All institutional relationships documented
- **Consistency**: Same answer for same question
- **Source Attribution**: Clear policy references

---

## Integration with Groq Cloud

### LLaMA 3 Optimization
- **Fast Inference**: Groq's LPU for sub-second responses
- **Context Window**: Efficient use of 8K token context
- **Streaming**: Real-time response generation

### Prompt Engineering
Each use case has optimized prompts:

**UC-1**: "Analyze the loan decision factors and explain in clear terms..."
**UC-2**: "Identify customer concerns and suggest resolution steps..."
**UC-3**: "Provide policy information based on institutional requirements..."

---

## Confidentiality & Compliance

⚠️ **CONFIDENTIAL - INTERNAL USE ONLY**

- All customer data is synthetic (Aadhaar_Synthetic field)
- No real PII is stored or processed
- Compliant with RBI data protection guidelines
- Audit logs maintained for all queries

---

## Next Steps

1. ✅ Implement use case detection
2. ✅ Optimize field weighting per use case
3. ✅ Add specialized prompts for each UC
4. ✅ Create evaluation dataset
5. ✅ Deploy on Groq Cloud with LLaMA 3
