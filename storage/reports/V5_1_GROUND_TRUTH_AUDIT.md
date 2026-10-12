# V5.1 Ground-Truth Audit & Canonical Benchmark Report

## Summary Overview
- **Total Benchmark Queries**: `50`
- **Canonical Benchmark Dataset**: `evaluation/datasets/retrieval_benchmark_v5_1.json`
- **Dataset SHA-256 Checksum**: `53ff3a94da1692a286bd66479543d5dc16114cd33a44c71d02125578749f0a26`
- **SHA-256 Lock File**: `evaluation/datasets/retrieval_benchmark_v5_1.sha256`

## Ground-Truth Classification Distribution
- `EXACT_DOCUMENT_TARGET`: 5 queries (10.0%)
- `MULTIPLE_VALID_DOCUMENT_TARGETS`: 45 queries (90.0%)
- `SOURCE_ONLY_TARGET`: 0 queries (0.0%)
- `AMBIGUOUS`: 0 queries (0.0%)

## Detailed 50 Benchmark Queries Ground-Truth Audit Table
| ID | Query | Classification | Expected Sources | Primary Target Document Title | Primary Chunk ID |
| :---: | :--- | :---: | :---: | :--- | :---: |
| `1` | "How do I create an installment plan?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[23,24,25]` | Create Installment Plans Asynchronously from SD Data | `11941` |
| `2` | "How does clearing control work for incoming payments?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[19,20,21]` | Analyze Incoming Payments | `11649` |
| `3` | "What is the process for automatic billing?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[11,12]` | ABAP OO Classes for Contract-Related Simulation Scenarios | `9320` |
| `4` | "How are meter readings estimated?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[6,7,8,9]` | Extrapolation for Demand Registers | `6847` |
| `5` | "What happens during move-in?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[2,3,10]` | Disconnection Order Generation | `7162` |
| `6` | "What happens during move-out?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[2,4]` | Move-Out | `6070` |
| `7` | "How does FI-CA dunning work?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[26]` | Dunning Grouping | `12039` |
| `8` | "How are incoming payments processed?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[19,22]` | Analyze Incoming Payments | `11649` |
| `9` | "What are clearing types in SAP Utilities?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[20,21]` | Clearing Control in Incoming Payments | `11752` |
| `10` | "How does budget billing work?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[13,15]` | Selling a Utilities Product | `10195` |
| `11` | "What master data is required for SAP Utilities?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[1,17,18]` | Business Partner in the Contract Partner Role (MKK) | `5556` |
| `12` | "How is device management configured for meters?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[5]` | Extrapolation for Demand Registers | `6400` |
| `13` | "How to monitor meter reading results?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[7]` | Extrapolation for Demand Registers | `6847` |
| `14` | "What are the details of the estimation procedure?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[8,9]` | Estimation | `7129` |
| `15` | "How is meter reading data processed during move-in?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[3,10]` | Disconnection Order Generation | `7162` |
| `16` | "What is the billing procedure in SAP Utilities?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[11,16]` | ABAP OO Classes for Contract-Related Simulation Scenarios | `9320` |
| `17` | "How is the invoicing procedure executed?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[14,16]` | Resolve Outsorted Billing Documents (F2186) | `11112` |
| `18` | "How to process budget billing plans?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[13,15]` | Selling a Utilities Product | `10195` |
| `19` | "What is a contract account business object?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[17,18]` | Check Benefit Free Period | `11566` |
| `20` | "How to process incoming payments from a collection agency?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[22,28]` | Processing Incoming Payments | `11839` |
| `21` | "What is the installment plan overview?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[23]` | Create Installment Plans Asynchronously from SD Data | `11941` |
| `22` | "How to display and change installment plans?" | `EXACT_DOCUMENT_TARGET` | `[25]` | Displaying and Changing Installment Plans | `12014` |
| `23` | "How to submit receivables to a collection agency?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[27,28]` | Submission of Receivables to Collection Agency | `12205` |
| `24` | "What APIs exist for collection agency enterprise services?" | `EXACT_DOCUMENT_TARGET` | `[28]` | Communicating with Collection Agencies by Using Enterprise Services or APIs | `12223` |
| `25` | "How does disconnection and reconnection of a utility installation work?" | `EXACT_DOCUMENT_TARGET` | `[29]` | Disconnection/Reconnection of a Utility Installation | `12228` |
| `26` | "What is a business partner contract account relationship?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[1,17,18]` | Business Partner in the Contract Partner Role (MKK) | `5556` |
| `27` | "How are dunning notices generated in FI-CA?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[26]` | Dunning Grouping | `12039` |
| `28` | "How to handle move-in and move-out concurrently?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[2,3,4]` | Move-in | `6040` |
| `29` | "What is periodic billing and invoicing analysis?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[16]` | Resolve Outsorted Billing Documents (F2186) | `11112` |
| `30` | "How does automatic rate determination work in billing?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[11,12]` | ABAP OO Classes for Contract-Related Simulation Scenarios | `9320` |
| `31` | "What is a budget billing scheme?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[13]` | Selling a Utilities Product | `10195` |
| `32` | "How are register groups assigned in device management?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[5]` | Extrapolation for Demand Registers | `6400` |
| `33` | "How to handle manual meter reading entry?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[6,7]` | Extrapolation for Demand Registers | `6847` |
| `34` | "What is clearing proposal in payment processing?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[19,20]` | Analyze Incoming Payments | `11649` |
| `35` | "How to reverse an invoicing document?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[14]` | Generation of Billable Items in Convergent Invoicing | `10616` |
| `36` | "What is dunning activity code?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[26]` | Dunning Grouping | `12039` |
| `37` | "How to cancel an installment plan?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[23,25]` | Create Installment Plans Asynchronously from SD Data | `11941` |
| `38` | "What is collection agency file transfer format?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[27,28]` | Submission of Receivables to Collection Agency | `12205` |
| `39` | "How to process disconnection order?" | `EXACT_DOCUMENT_TARGET` | `[29]` | Disconnection/Reconnection of a Utility Installation | `12228` |
| `40` | "What is connection object in master data?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[1]` | Business Partner in the Contract Partner Role (MKK) | `5556` |
| `41` | "What is premise in SAP Utilities?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[1]` | Business Partner in the Contract Partner Role (MKK) | `5556` |
| `42` | "What is point of delivery POD?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[1]` | Business Partner in the Contract Partner Role (MKK) | `5556` |
| `43` | "How to create a budget billing plan manually?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[13,15]` | Selling a Utilities Product | `10195` |
| `44` | "What is out-of-sorting billing document check?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[11,16]` | ABAP OO Classes for Contract-Related Simulation Scenarios | `9320` |
| `45` | "How to process payment lot in FI-CA?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[19,22]` | Analyze Incoming Payments | `11649` |
| `46` | "How to handle meter exchange procedure?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[5]` | Extrapolation for Demand Registers | `6400` |
| `47` | "What is plausible and implausible meter reading result?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[7,8]` | Extrapolation for Demand Registers | `6847` |
| `48` | "How does dunning proposal run work?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[26]` | Dunning Grouping | `12039` |
| `49` | "How to release submission to collection agency?" | `MULTIPLE_VALID_DOCUMENT_TARGETS` | `[27]` | Submission of Receivables to Collection Agency | `12205` |
| `50` | "How to perform reconnection of utility service?" | `EXACT_DOCUMENT_TARGET` | `[29]` | Disconnection/Reconnection of a Utility Installation | `12228` |