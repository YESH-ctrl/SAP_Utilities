-- =============================================================================
-- SAP UTILITIES RAG PIPELINE - SEED DATA MIGRATION
-- Migration: 002_seed_reference_sources.sql
-- Purpose: Populate initial 29 reference PDFs from manifest.json, create root
--          documents (depth=0, parent_id=NULL), and initialize pending crawl jobs.
-- Idempotent script: Safe to run multiple times without duplication.
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- 1. INSERT REFERENCE SOURCES (29 SAP Utilities PDFs)
-- -----------------------------------------------------------------------------
INSERT INTO sources (source_file, title, category, seed_url, product, version, source_type, metadata)
VALUES
('01_Utilities_Master_Data.pdf', 'Utilities Master Data', 'Utilities Master Data', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/021b182b0c47416c8fafed67ebfd78a9/0a6ace53118d4308e10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_001", "max_depth": 2}'),
('02_Move_In_Out_Overview.pdf', 'Move In Out Overview', 'Move-In / Move-Out', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/f4a255a5de524e3992155767996fb1fd/8082ce53118d4308e10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_002", "max_depth": 2}'),
('03_Move_In_Process.pdf', 'Move In Process', 'Move-In / Move-Out', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/f4a255a5de524e3992155767996fb1fd/0981ce53118d4308e10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_003", "max_depth": 2}'),
('04_Move_Out_Process.pdf', 'Move Out Process', 'Move-In / Move-Out', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/f4a255a5de524e3992155767996fb1fd/0f81ce53118d4308e10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_004", "max_depth": 2}'),
('05_Device_Management_Overview.pdf', 'Device Management Overview', 'Device Management', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/021b182b0c47416c8fafed67ebfd78a9/8990d0533f8e4308e10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_005", "max_depth": 2}'),
('06_Reading_Meters.pdf', 'Reading Meters', 'Meter Reading', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/2ac7fe29a0c94cdd88fb80c2cb9f7758/bc90d0533f8e4308e10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_006", "max_depth": 2}'),
('07_Monitoring_Meter_Reading_Results.pdf', 'Monitoring Meter Reading Results', 'Meter Reading', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/2ac7fe29a0c94cdd88fb80c2cb9f7758/4d76765c1e012b8ae10000000a42189b.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_007", "max_depth": 2}'),
('08_Meter_Reading_Estimation.pdf', 'Meter Reading Estimation', 'Meter Reading', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/2ac7fe29a0c94cdd88fb80c2cb9f7758/d090d0533f8e4308e10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_008", "max_depth": 2}'),
('09_Estimation_Procedure_Details.pdf', 'Estimation Procedure Details', 'Meter Reading', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/2ac7fe29a0c94cdd88fb80c2cb9f7758/bf74c1d28fd54f77b228772b98b72fba.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_009", "max_depth": 2}'),
('10_Meter_Reading_Data_During_Move_In.pdf', 'Meter Reading Data During Move In', 'Meter Reading', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/f4a255a5de524e3992155767996fb1fd/b781ce53118d4308e10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_010", "max_depth": 2}'),
('11_SAP_Utilities_Billing_Procedure.pdf', 'SAP Utilities Billing Procedure', 'Billing & Invoicing', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/ed84b70c199d4470ae2e5ccb93b2e45b/147bce53118d4308e10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_011", "max_depth": 2}'),
('12_Automatic_Billing.pdf', 'Automatic Billing', 'Billing & Invoicing', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/ed84b70c199d4470ae2e5ccb93b2e45b/297bce53118d4308e10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_012", "max_depth": 2}'),
('13_Budget_Billing_Plan.pdf', 'Budget Billing Plan', 'Billing & Invoicing', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/021b182b0c47416c8fafed67ebfd78a9/c1a5e8aee73440ee971a768af5b9ea1b.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_013", "max_depth": 2}'),
('14_SAP_Utilities_Invoicing_Procedure.pdf', 'SAP Utilities Invoicing Procedure', 'Billing & Invoicing', 'https://help.sap.com/docs/sap_s4hana_on-premise/a003b275c98148ee8a4c3fafe9588fe3/cc7bce53118d4308e10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_014", "max_depth": 2}'),
('15_Processing_Budget_Billing_Plans.pdf', 'Processing Budget Billing Plans', 'Billing & Invoicing', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/a003b275c98148ee8a4c3fafe9588fe3/147cce53118d4308e10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_015", "max_depth": 2}'),
('16_Periodic_Billing_and_Invoicing_Analysis.pdf', 'Periodic Billing and Invoicing Analysis', 'Billing & Invoicing', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/021b182b0c47416c8fafed67ebfd78a9/549661e6541f403ea56196782e040bcc.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_016", "max_depth": 2}'),
('17_Contract_Accounts_Overview.pdf', 'Contract Accounts Overview', 'Contract Accounts & FI-CA', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/e52c8ee6197147ec97dfc2eb8c46a3ad/0bfcc5536a51204be10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_017", "max_depth": 2}'),
('18_Contract_Account_Business_Object.pdf', 'Contract Account Business Object', 'Contract Accounts & FI-CA', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/9442486404b54071b4ebeab6a16628e7/b1a202c9bb3011da2b24000f20dac9ef.html?version=2025.001', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_018", "max_depth": 2}'),
('19_Analyze_Incoming_Payments.pdf', 'Analyze Incoming Payments', 'Incoming Payments & Clearing', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/9442486404b54071b4ebeab6a16628e7/063bf3eb68e347efa5c0fc1d389f70f7.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_019", "max_depth": 2}'),
('20_Clearing_Control_in_Incoming_Payments.pdf', 'Clearing Control in Incoming Payments', 'Incoming Payments & Clearing', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/9442486404b54071b4ebeab6a16628e7/edcd0c5823854d3296f2591e9f5d118c.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_020", "max_depth": 2}'),
('21_Clearing_Types.pdf', 'Clearing Types', 'Incoming Payments & Clearing', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/9442486404b54071b4ebeab6a16628e7/e63529e1a3fd42e3a0e2c009ac783e0d.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_021", "max_depth": 2}'),
('22_Processing_Incoming_Payments_from_External_Cash_Desks.pdf', 'Processing Incoming Payments from External Cash Desks', 'Incoming Payments & Clearing', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/9442486404b54071b4ebeab6a16628e7/3d0ac5536a51204be10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_022", "max_depth": 2}'),
('23_Installment_Plan_Overview.pdf', 'Installment Plan Overview', 'Installment Plans', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/9442486404b54071b4ebeab6a16628e7/730dc5536a51204be10000000a174cb4.html?version=2025.001', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_023", "max_depth": 2}'),
('24_Creating_Installment_Plans.pdf', 'Creating Installment Plans', 'Installment Plans', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/9442486404b54071b4ebeab6a16628e7/790dc5536a51204be10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_024", "max_depth": 2}'),
('25_Displaying_and_Changing_Installment_Plans.pdf', 'Displaying and Changing Installment Plans', 'Installment Plans', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/9442486404b54071b4ebeab6a16628e7/630dc5536a51204be10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_025", "max_depth": 2}'),
('26_FI_CA_Dunning.pdf', 'FI CA Dunning', 'Dunning & Collections', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/9442486404b54071b4ebeab6a16628e7/b1ffc5536a51204be10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_026", "max_depth": 2}'),
('27_Submission_of_Receivables_to_Collection_Agency.pdf', 'Submission of Receivables to Collection Agency', 'Dunning & Collections', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/9442486404b54071b4ebeab6a16628e7/10e7c5536a51204be10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_027", "max_depth": 2}'),
('28_Collection_Agency_APIs_and_Enterprise_Services.pdf', 'Collection Agency APIs and Enterprise Services', 'Dunning & Collections', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/9442486404b54071b4ebeab6a16628e7/9c9c2344851f412f823d5f8a9dc7c694.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_028", "max_depth": 2}'),
('29_Disconnection_Reconnection_of_a_Utility_Installation.pdf', 'Disconnection Reconnection of a Utility Installation', 'Disconnection / Reconnection', 'https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/f4a255a5de524e3992155767996fb1fd/8682ce53118d4308e10000000a174cb4.html', 'SAP S/4HANA On-Premise', 'On-Premise', 'reference_pdf', '{"manifest_id": "sap_utilities_029", "max_depth": 2}')
ON CONFLICT (source_file) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 2. CREATE ROOT DOCUMENTS FOR EACH SEED SOURCE (depth=0, parent_id=NULL)
-- -----------------------------------------------------------------------------
INSERT INTO documents (source_id, parent_id, title, url, canonical_url, source_pdf, depth, document_type, status, metadata)
SELECT
    s.id,
    NULL,
    s.title,
    s.seed_url,
    s.seed_url,
    s.source_file,
    0,
    'root',
    'pending',
    jsonb_build_object('is_seed', true, 'category', s.category)
FROM sources s
ON CONFLICT (canonical_url) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 3. INITIALIZE PENDING CRAWL JOBS FOR ROOT SEED URLS
-- -----------------------------------------------------------------------------
INSERT INTO crawl_jobs (source_id, document_id, url, parent_document_id, depth, status, priority)
SELECT
    s.id,
    d.id,
    s.seed_url,
    NULL,
    0,
    'pending',
    10
FROM sources s
JOIN documents d ON d.canonical_url = s.seed_url
ON CONFLICT (url) WHERE status IN ('pending', 'queued', 'crawling') DO NOTHING;

COMMIT;
