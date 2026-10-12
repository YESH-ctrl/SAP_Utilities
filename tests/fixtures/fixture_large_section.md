# Automatic Meter Reading Estimation and Mass Processing

In SAP Utilities, when actual meter reading results are not available by the scheduled billing date, the system automatically estimates meter reading results using historical consumption patterns, extrapolation algorithms, and seasonal adjustment factors.

## Historical Estimation Principles

The estimation procedure uses weighted historical consumption periods. If previous year readings exist for the same period, the system applies the base period consumption to calculate the current period's expected quantity.

Paragraph 1: Automatic billing in SAP Utilities relies heavily on validated meter readings. When readings are missing or plausible checks fail, the system places the contract account on an exception queue for manual review or automatic estimation.

Paragraph 2: During mass estimation, the background job processes contract accounts in parallel chunks using background work processes. The batch job monitors memory consumption and database locks to prevent table contention in large utility installations.

Paragraph 3: Extrapolation algorithms support degree days, linear interpolation, and periodic consumption rules. Utility companies configure temperature curves and regional weather station assignments in Customizing under SAP Utilities -> Basic Functions -> Meter Reading -> Estimation.

Paragraph 4: Meter reading estimation can be triggered individually via Transaction E300 or in mass processing mode via Transaction E301. Mass processing supports parallel processing variants based on installation group ranges.

Paragraph 5: Once estimation completes, the system marks the meter reading document with status 'Estimated'. Estimated documents can be overridden by actual readings entered during billing correction runs.

Paragraph 6: Billing documents created using estimated meter readings carry an indicator flag in header table ERCH. If subsequent actual readings arrive, SAP Utilities performs dynamic billing reversal and rebilling.

Paragraph 7: Reversal processing uses standard transaction EA13 or mass reversal transaction EA20. Invoicing reversal triggers credit or debit adjustment documents in Contract Accounts Receivable and Payable (FI-CA).

Paragraph 8: Incoming customer payments against estimated bills are posted to FI-CA open items. Discrepancies between estimated and actual consumption are reconciled during the annual consumption settlement run.

Paragraph 9: Security deposits and installment plans are automatically updated if the estimated bill exceeds defined threshold percentages established in FI-CA Customizing.

Paragraph 10: Configuration requirements for automatic estimation include setting up estimation categories, gas day formulas, and calendar weighting factors in IMG transaction SPRO.
