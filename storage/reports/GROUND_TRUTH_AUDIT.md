# SAP Utilities RAG Ground Truth Audit Report

## Overview
Audited all 50 benchmark test questions against PostgreSQL document and chunk metadata.
Established multi-level ground truth mapping (Source IDs, Document IDs, Document Titles, Canonical URLs, Chunk IDs).

## Multi-Level Ground Truth Mapping
| ID | Question | Expected Source IDs | Expected Document Count | Expected Chunk Count | Ground Truth Classification |
| :---: | :--- | :---: | :---: | :---: | :--- |
| #1 | How do I create an installment plan?... | `[23, 24, 25]` | 22 | 10 | `VALID_SOURCE_LABEL` |
| #2 | How does clearing control work for incom... | `[19, 20, 21]` | 49 | 10 | `VALID_SOURCE_LABEL` |
| #3 | What is the process for automatic billin... | `[11, 12]` | 256 | 10 | `VALID_SOURCE_LABEL` |
| #4 | How are meter readings estimated?... | `[6, 7, 8, 9]` | 60 | 10 | `VALID_SOURCE_LABEL` |
| #5 | What happens during move-in?... | `[2, 3, 10]` | 29 | 10 | `VALID_SOURCE_LABEL` |
| #6 | What happens during move-out?... | `[2, 4]` | 12 | 10 | `VALID_SOURCE_LABEL` |
| #7 | How does FI-CA dunning work?... | `[26]` | 32 | 10 | `VALID_SOURCE_LABEL` |
| #8 | How are incoming payments processed?... | `[19, 22]` | 28 | 10 | `VALID_SOURCE_LABEL` |
| #9 | What are clearing types in SAP Utilities... | `[20, 21]` | 29 | 10 | `VALID_SOURCE_LABEL` |
| #10 | How does budget billing work?... | `[13, 15]` | 155 | 10 | `DOCUMENTALLY_RELEVANT_BUT_SOURCE_MISMATCH` |
| #11 | What master data is required for SAP Uti... | `[1, 17, 18]` | 127 | 10 | `AMBIGUOUS` |
| #12 | How is device management configured for ... | `[5]` | 135 | 10 | `VALID_SOURCE_LABEL` |
| #13 | How to monitor meter reading results?... | `[7]` | 57 | 10 | `VALID_SOURCE_LABEL` |
| #14 | What are the details of the estimation p... | `[8, 9]` | 2 | 10 | `DOCUMENTALLY_RELEVANT_BUT_SOURCE_MISMATCH` |
| #15 | How is meter reading data processed duri... | `[3, 10]` | 21 | 10 | `VALID_SOURCE_LABEL` |
| #16 | What is the billing procedure in SAP Uti... | `[11, 16]` | 284 | 10 | `VALID_SOURCE_LABEL` |
| #17 | How is the invoicing procedure executed?... | `[14, 16]` | 78 | 10 | `VALID_SOURCE_LABEL` |
| #18 | How to process budget billing plans?... | `[13, 15]` | 155 | 10 | `VALID_SOURCE_LABEL` |
| #19 | What is a contract account business obje... | `[17, 18]` | 45 | 10 | `VALID_SOURCE_LABEL` |
| #20 | How to process incoming payments from a ... | `[22, 28]` | 9 | 10 | `VALID_SOURCE_LABEL` |
| #21 | What is the installment plan overview?... | `[23]` | 11 | 10 | `VALID_SOURCE_LABEL` |
| #22 | How to display and change installment pl... | `[25]` | 1 | 4 | `VALID_SOURCE_LABEL` |
| #23 | How to submit receivables to a collectio... | `[27, 28]` | 9 | 10 | `VALID_SOURCE_LABEL` |
| #24 | What APIs exist for collection agency en... | `[28]` | 1 | 5 | `VALID_SOURCE_LABEL` |
| #25 | How does disconnection and reconnection ... | `[29]` | 1 | 6 | `VALID_SOURCE_LABEL` |
| #26 | What is a business partner contract acco... | `[1, 17, 18]` | 127 | 10 | `AMBIGUOUS` |
| #27 | How are dunning notices generated in FI-... | `[26]` | 32 | 10 | `VALID_SOURCE_LABEL` |
| #28 | How to handle move-in and move-out concu... | `[2, 3, 4]` | 19 | 10 | `AMBIGUOUS` |
| #29 | What is periodic billing and invoicing a... | `[16]` | 29 | 10 | `DOCUMENTALLY_RELEVANT_BUT_SOURCE_MISMATCH` |
| #30 | How does automatic rate determination wo... | `[11, 12]` | 256 | 10 | `VALID_SOURCE_LABEL` |
| #31 | What is a budget billing scheme?... | `[13]` | 106 | 10 | `VALID_SOURCE_LABEL` |
| #32 | How are register groups assigned in devi... | `[5]` | 135 | 10 | `VALID_SOURCE_LABEL` |
| #33 | How to handle manual meter reading entry... | `[6, 7]` | 58 | 10 | `VALID_SOURCE_LABEL` |
| #34 | What is clearing proposal in payment pro... | `[19, 20]` | 30 | 10 | `VALID_SOURCE_LABEL` |
| #35 | How to reverse an invoicing document?... | `[14]` | 49 | 10 | `VALID_SOURCE_LABEL` |
| #36 | What is dunning activity code?... | `[26]` | 32 | 10 | `VALID_SOURCE_LABEL` |
| #37 | How to cancel an installment plan?... | `[23, 25]` | 12 | 10 | `VALID_SOURCE_LABEL` |
| #38 | What is collection agency file transfer ... | `[27, 28]` | 9 | 10 | `VALID_SOURCE_LABEL` |
| #39 | How to process disconnection order?... | `[29]` | 1 | 6 | `VALID_SOURCE_LABEL` |
| #40 | What is connection object in master data... | `[1]` | 82 | 10 | `VALID_SOURCE_LABEL` |
| #41 | What is premise in SAP Utilities?... | `[1]` | 82 | 10 | `VALID_SOURCE_LABEL` |
| #42 | What is point of delivery POD?... | `[1]` | 82 | 10 | `DOCUMENTALLY_RELEVANT_BUT_SOURCE_MISMATCH` |
| #43 | How to create a budget billing plan manu... | `[13, 15]` | 155 | 10 | `VALID_SOURCE_LABEL` |
| #44 | What is out-of-sorting billing document ... | `[11, 16]` | 284 | 10 | `VALID_SOURCE_LABEL` |
| #45 | How to process payment lot in FI-CA?... | `[19, 22]` | 28 | 10 | `VALID_SOURCE_LABEL` |
| #46 | How to handle meter exchange procedure?... | `[5]` | 135 | 10 | `VALID_SOURCE_LABEL` |
| #47 | What is plausible and implausible meter ... | `[7, 8]` | 58 | 10 | `VALID_SOURCE_LABEL` |
| #48 | How does dunning proposal run work?... | `[26]` | 32 | 10 | `VALID_SOURCE_LABEL` |
| #49 | How to release submission to collection ... | `[27]` | 8 | 10 | `VALID_SOURCE_LABEL` |
| #50 | How to perform reconnection of utility s... | `[29]` | 1 | 6 | `VALID_SOURCE_LABEL` |

## Summary Statistics
- **VALID_SOURCE_LABEL**: 43 questions (86.0%)
- **DOCUMENTALLY_RELEVANT_BUT_SOURCE_MISMATCH**: 4 questions (8.0%)
- **AMBIGUOUS**: 3 questions (6.0%)
