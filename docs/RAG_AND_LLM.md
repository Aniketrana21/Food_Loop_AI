# FoodLoop AI - Provider-Agnostic LLM Layer & Vector RAG

## 1. Provider-Agnostic LLM Architecture

FoodLoop AI adopts a decoupled, multi-provider strategy:

```
[Application Layer]
        │
        ▼
[LLMService Interface]
        │
   ┌────┴──────────────────────────┐
   ▼                               ▼
[Gemini Provider]          [OpenAI Provider]  
(gemini-1.5-flash)         (gpt-4o-mini)      
   │                               │
   └───────────────┬───────────────┘
                   ▼
       [Intelligent Fallback Engine]
```

### Core LLM Responsibilities:
1. **Bulk Food Rescue Recipe Synthesizer**: Converts raw donor surplus into balanced, high-yield community recipes tailored for shelters (e.g. 50-200 portions).
2. **Cold-Chain Safety & Danger Zone Advisory**: Checks whether food has spent too long in the 4°C-60°C temperature zone and issues immediate disposal or reheating directives.
3. **Automated Donor-to-Shelter Communication**: Generates formal handover manifests and tax-deductible contribution acknowledgments.

---

## 2. Vector Retrieval-Augmented Generation (RAG)

### Knowledge Base Scope:
- **Federal Laws**: Bill Emerson Good Samaritan Food Donation Act (42 U.S. Code § 1791)
- **Food Codes**: FDA Food Code 2022 (Chapter 3: Food Safety & Temperature Danger Zones)
- **Allergen Regulations**: FASTER Act and FALCPA 9 major allergens
- **Logistics SOPs**: Cold Chain Courier Protocol, Cambro Handling, Temperature Logging
- **Tax Law**: Internal Revenue Code Section 170(e)(3) Enhanced Deductions

### Retrieval Pipeline:
1. **Query Normalization & Vectorization**: Generates normalized semantic vector representations.
2. **Cosine Similarity Matching**: Computes distance across indexed regulatory chunks.
3. **Keyword Boosting**: Enhances retrieval accuracy for critical legal and food safety terms.
4. **Citation Generation**: Formats output with verified citations (USDA, FDA, IRS) and confidence scores.
