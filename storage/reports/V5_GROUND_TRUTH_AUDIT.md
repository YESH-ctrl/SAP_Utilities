# SAP Utilities RAG V5 Ground Truth Audit Report

## Executive Overview
Audited all 50 benchmark test questions against PostgreSQL document and chunk metadata.
Established explicit 3-level relevance targets (Source IDs, Primary Relevant Document IDs, Canonical URLs, Relevant Chunk IDs, and Graded Relevance).

## Multi-Level Ground Truth Relevance Schema
| Query ID | Question | Expected Source IDs | Primary Relevant Document Title | Relevant Doc Count | Relevant Chunk Count | Classification |
| :---: | :--- | :---: | :--- | :---: | :---: | :--- |
| #1 | How do I create an installment plan?... | `[23, 24, 25]` | Create Installment Plans Async... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #2 | How does clearing control work for inc... | `[19, 20, 21]` | Analyze Incoming Payments... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #3 | What is the process for automatic bill... | `[11, 12]` | ABAP OO Classes for Contract-R... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #4 | How are meter readings estimated?... | `[6, 7, 8, 9]` | Extrapolation for Demand Regis... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #5 | What happens during move-in?... | `[2, 3, 10]` | Disconnection Order Generation... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #6 | What happens during move-out?... | `[2, 4]` | Move-Out... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #7 | How does FI-CA dunning work?... | `[26]` | Dunning Grouping... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #8 | How are incoming payments processed?... | `[19, 22]` | Analyze Incoming Payments... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #9 | What are clearing types in SAP Utiliti... | `[20, 21]` | Clearing Control in Incoming P... | 3 | 3 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #10 | How does budget billing work?... | `[13, 15]` | Selling a Utilities Product... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #11 | What master data is required for SAP U... | `[1, 17, 18]` | Business Partner in the Contra... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #12 | How is device management configured fo... | `[5]` | Extrapolation for Demand Regis... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #13 | How to monitor meter reading results?... | `[7]` | Extrapolation for Demand Regis... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #14 | What are the details of the estimation... | `[8, 9]` | Estimation... | 2 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #15 | How is meter reading data processed du... | `[3, 10]` | Disconnection Order Generation... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #16 | What is the billing procedure in SAP U... | `[11, 16]` | ABAP OO Classes for Contract-R... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #17 | How is the invoicing procedure execute... | `[14, 16]` | Resolve Outsorted Billing Docu... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #18 | How to process budget billing plans?... | `[13, 15]` | Selling a Utilities Product... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #19 | What is a contract account business ob... | `[17, 18]` | Check Benefit Free Period... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #20 | How to process incoming payments from ... | `[22, 28]` | Processing Incoming Payments... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #21 | What is the installment plan overview?... | `[23]` | Create Installment Plans Async... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #22 | How to display and change installment ... | `[25]` | Displaying and Changing Instal... | 1 | 4 | `EXACT_DOCUMENT_TARGET` |
| #23 | How to submit receivables to a collect... | `[27, 28]` | Submission of Receivables to C... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #24 | What APIs exist for collection agency ... | `[28]` | Communicating with Collection ... | 1 | 5 | `EXACT_DOCUMENT_TARGET` |
| #25 | How does disconnection and reconnectio... | `[29]` | Disconnection/Reconnection of ... | 1 | 5 | `EXACT_DOCUMENT_TARGET` |
| #26 | What is a business partner contract ac... | `[1, 17, 18]` | Business Partner in the Contra... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #27 | How are dunning notices generated in F... | `[26]` | Dunning Grouping... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #28 | How to handle move-in and move-out con... | `[2, 3, 4]` | Move-in... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #29 | What is periodic billing and invoicing... | `[16]` | Resolve Outsorted Billing Docu... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #30 | How does automatic rate determination ... | `[11, 12]` | ABAP OO Classes for Contract-R... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #31 | What is a budget billing scheme?... | `[13]` | Selling a Utilities Product... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #32 | How are register groups assigned in de... | `[5]` | Extrapolation for Demand Regis... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #33 | How to handle manual meter reading ent... | `[6, 7]` | Extrapolation for Demand Regis... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #34 | What is clearing proposal in payment p... | `[19, 20]` | Analyze Incoming Payments... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #35 | How to reverse an invoicing document?... | `[14]` | Generation of Billable Items i... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #36 | What is dunning activity code?... | `[26]` | Dunning Grouping... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #37 | How to cancel an installment plan?... | `[23, 25]` | Create Installment Plans Async... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #38 | What is collection agency file transfe... | `[27, 28]` | Submission of Receivables to C... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #39 | How to process disconnection order?... | `[29]` | Disconnection/Reconnection of ... | 1 | 5 | `EXACT_DOCUMENT_TARGET` |
| #40 | What is connection object in master da... | `[1]` | Business Partner in the Contra... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #41 | What is premise in SAP Utilities?... | `[1]` | Business Partner in the Contra... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #42 | What is point of delivery POD?... | `[1]` | Business Partner in the Contra... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #43 | How to create a budget billing plan ma... | `[13, 15]` | Selling a Utilities Product... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #44 | What is out-of-sorting billing documen... | `[11, 16]` | ABAP OO Classes for Contract-R... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #45 | How to process payment lot in FI-CA?... | `[19, 22]` | Analyze Incoming Payments... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #46 | How to handle meter exchange procedure... | `[5]` | Extrapolation for Demand Regis... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #47 | What is plausible and implausible mete... | `[7, 8]` | Extrapolation for Demand Regis... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #48 | How does dunning proposal run work?... | `[26]` | Dunning Grouping... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #49 | How to release submission to collectio... | `[27]` | Submission of Receivables to C... | 3 | 5 | `MULTIPLE_VALID_DOCUMENT_TARGETS` |
| #50 | How to perform reconnection of utility... | `[29]` | Disconnection/Reconnection of ... | 1 | 5 | `EXACT_DOCUMENT_TARGET` |

## Ground Truth Classification Breakdown
- **EXACT_DOCUMENT_TARGET**: 5 questions
- **MULTIPLE_VALID_DOCUMENT_TARGETS**: 45 questions
- **AMBIGUOUS**: 0 questions
