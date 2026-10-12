# SAP Utilities Embedding Report

## Corpus
- **Sources**: 29
- **Documents**: 965
- **Sections**: 5051
- **Chunks**: 6689

## Model
- **Model**: `BAAI/bge-m3`
- **Version**: `1.0`
- **Dimension**: `1024`
- **Device**: `cpu`
- **Max Tokens**: `8192`

## Processing
- **Total Eligible Chunks**: 6689
- **Newly Embedded**: 116
- **Already Embedded**: 6573
- **Failed**: 0
- **Skipped**: 0
- **Truncated**: 114

## Performance
- **Batches**: 8
- **Total Time**: 23166.409s
- **Average Batch Time**: 2895.4s
- **Database Insertion Time**: 12.68s
- **Chunks / Second**: 0.01
- **Tokens / Second**: 40.75
- **Max Source Tokens**: 13577
- **Max Embedded Tokens**: 8192

## Database
- **Total Vectors**: 6689
- **Vector Dimension**: 1024
- **Dimension Mismatches**: 0
- **Duplicate Vectors**: 0
- **Missing Vectors**: 0
- **Null Vectors**: 0
- **Invalid Vectors**: 0
- **HNSW Cosine Index Valid**: `True`

## Source Coverage
| Source ID | Title | Chunks | Embeddings | Coverage % |
| :--- | :--- | :--- | :--- | :--- |
| #1  | Utilities Master Data               | 445 | 445 | 100.0% |
| #2  | Move In Out Overview                | 50 | 50 | 100.0% |
| #3  | Move In Process                     | 30 | 30 | 100.0% |
| #4  | Move Out Process                    | 18 | 18 | 100.0% |
| #5  | Device Management Overview          | 724 | 724 | 100.0% |
| #6  | Reading Meters                      | 6 | 6 | 100.0% |
| #7  | Monitoring Meter Reading Results    | 311 | 311 | 100.0% |
| #8  | Meter Reading Estimation            | 5 | 5 | 100.0% |
| #9  | Estimation Procedure Details        | 5 | 5 | 100.0% |
| #10 | Meter Reading Data During Move In   | 75 | 75 | 100.0% |
| #11 | SAP Utilities Billing Procedure     | 2283 | 2283 | 100.0% |
| #12 | Automatic Billing                   | 12 | 12 | 100.0% |
| #13 | Budget Billing Plan                 | 1067 | 1067 | 100.0% |
| #14 | SAP Utilities Invoicing Procedure   | 242 | 242 | 100.0% |
| #15 | Processing Budget Billing Plans     | 268 | 268 | 100.0% |
| #16 | Periodic Billing and Invoicing Anal | 272 | 272 | 100.0% |
| #17 | Contract Accounts Overview          | 123 | 123 | 100.0% |
| #18 | Contract Account Business Object    | 168 | 168 | 100.0% |
| #19 | Analyze Incoming Payments           | 103 | 103 | 100.0% |
| #20 | Clearing Control in Incoming Paymen | 30 | 30 | 100.0% |
| #21 | Clearing Types                      | 57 | 57 | 100.0% |
| #22 | Processing Incoming Payments from E | 43 | 43 | 100.0% |
| #23 | Installment Plan Overview           | 68 | 68 | 100.0% |
| #24 | Creating Installment Plans          | 64 | 64 | 100.0% |
| #25 | Displaying and Changing Installment | 4 | 4 | 100.0% |
| #26 | FI CA Dunning                       | 158 | 158 | 100.0% |
| #27 | Submission of Receivables to Collec | 47 | 47 | 100.0% |
| #28 | Collection Agency APIs and Enterpri | 5 | 5 | 100.0% |
| #29 | Disconnection Reconnection of a Uti | 6 | 6 | 100.0% |

## Truncation Statistics
- **Total Truncated Chunks**: 114
| Source ID | Truncated Chunks |
| :--- | :--- |
| #26 | 29 |
| #21 | 19 |
| #23 | 11 |
| #24 | 10 |
| #19 | 17 |
| #20 | 10 |
| #25 | 1 |
| #27 | 8 |
| #22 | 8 |
| #28 | 1 |

## Tests
- **pytest**: All 14 embedding test suites passed (28/28 total suite tests passed).

## Final Verdict
**EMBEDDINGS_COMPLETE**
