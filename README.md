# Documentation claim auditor

An offline static auditor comparing documentation promises with source call patterns.
It reads files without executing the inspected project, using no network or telemetry.

## Installation and usage

```sh
python3 -m pip install .
energy-bill-extraction-claim-audit audit .
python3 -m energy_bill_extraction_claim_audit audit . --json
energy-bill-extraction-claim-audit audit . --fail-on medium --ignore vendor --ignore build
energy-bill-extraction-claim-audit --version
```

Exit status is 0 when no finding reaches the selected threshold, 2 when a finding
reaches it, and 1 for usage or I/O errors. The default threshold is high.
The JSON report includes verdict, findings, locations, and production/test evidence.
Use `--verbose` for evidence details in the text report.

## Matching rules

The checked capability is recognized through exact phrases in root README.md and
Markdown files with a docs path component. Fenced blocks are skipped; inline code
counts. Paragraphs split at blank lines. Matching lowercases text, expands negative
contractions, replaces hyphens with spaces, and collapses whitespace. Word boundaries
apply, with longest matches first and alphabetical ties. Denial spans are removed
before positive matching.

Source is parsed as syntax trees, never executed. Symlinks are skipped. Test paths
are tracked separately; fixtures, docs, and examples cannot supply production evidence.
Invalid syntax supplies no evidence. Imports and local bindings are resolved within
one module; local definitions shadow route names. Missing production evidence yields
a high finding, or medium when evidence exists only in tests. A denial conflicts only
with production evidence. With no source, a positive promise fails and a denial passes.
No claim passes. Ignore options are repeatable relative path prefixes.

## Reference

```text
Finding rules:
documented-energy-bill-extraction-claim-false HIGH (MEDIUM for test-only evidence)
documented-no-energy-bill-extraction-claim-false HIGH

ENERGYBILLEXTRACTION (50, one per line):
energy bill extraction
extract energy bills
extracts energy bills
extracting energy bills
extract energy bill
extracts energy bill
extracting energy bill
energy bill parsing
energy bill parser
parse energy bills
parses energy bills
parse energy bill
parses energy bill
energy bill scanning
energy bill scanner
scan energy bills
scans energy bills
scan energy bill
scans energy bill
utility bill extraction
extract utility bills
extracts utility bills
extracting utility bills
extract utility bill
extracts utility bill
extracting utility bill
utility bill parsing
utility bill parser
parse utility bills
parses utility bills
parse utility bill
parses utility bill
utility bill scanning
utility bill scanner
scan utility bills
scans utility bills
scan utility bill
scans utility bill
electricity bill extraction
extract electricity bills
extracts electricity bills
extracting electricity bills
extract electricity bill
extracts electricity bill
extracting electricity bill
electricity bill parsing
electricity bill parser
parse electricity bills
parses electricity bills
parse electricity bill

NOENERGYBILLEXTRACTION (24, one per line):
no energy bill extraction
does not extract energy bills
does not extract energy bill
does not support energy bill extraction
without energy bill extraction
no energy bill parser
does not parse energy bills
does not parse energy bill
no utility bill extraction
does not extract utility bills
does not extract utility bill
does not support utility bill extraction
without utility bill extraction
no energy bill scanner
does not scan energy bills
does not scan energy bill
no electricity bill extraction
does not extract electricity bills
does not extract electricity bill
without electricity bill extraction
no electricity bill parser
does not parse electricity bills
does not parse electricity bill
energy bill extraction not supported

## Generic names (implementation MUST match exactly, 24, no duplicates)

extract_energy_bill, extract_energy_bills, parse_energy_bill, parse_energy_bills,
extract_utility_bill, parse_utility_bill, extract_utility_bills, parse_utility_bills,
extract_electricity_bill, parse_electricity_bill,
extract_energy_bill_data, parse_energy_bill_data,
energy_bill_extraction, energy_bill_extractor, energy_bill_parser,
utility_bill_extraction, utility_bill_extractor, utility_bill_parser,
extract_energy_bill_info, parse_energy_bill_info,
energy_bill_scan, energy_bill_scanner, scan_energy_bill, scan_energy_bills

## mindee names (implementation MUST match exactly)

mindee Client construction + parse call passing EnergyBillV1 (Name
exactly EnergyBillV1, or Attribute with attr exactly EnergyBillV1 such
as product.EnergyBillV1 / mindee.product.fr.EnergyBillV1 /
mindee.v1.product.fr.EnergyBillV1) as any argument; import gate
mindee. EnergyBillV1 is a 4.x-only fingerprint (4.22.0 wheel
inspected 2026-11-14: mindee/product/fr/energy_bill/energy_bill_v1.py
defines class EnergyBillV1(Inference), endpoint_name
"energy_bill_fra", endpoint_version "1", exported via
mindee.product.fr — NOT at the top-level mindee.product namespace;
its document is "Energy Bill API version 1.2" with fields
contract_id, delivery_point, due_date, energy_consumer (name,
address), energy_supplier (name, address), energy_usage (list:
consumption, description, start_date, end_date, unit, unit_price,
tax_rate, total), invoice_date, invoice_number, meter_details
(meter_number, meter_type), subscription (list: description,
start_date, end_date, unit_price, tax_rate, total),
taxes_and_contributions (list: description, tax_rate, total),
total_amount, total_before_taxes, total_taxes; the 5.4.0 wheel
inspected 2026-11-14 contains no energy_bill product directory
and zero "EnergyBill" hits in any .py file). The tool detects the
call in source, not the installed SDK version. A parse call passing
any other product (InvoiceV4, ReceiptV5, PassportV1,
FinancialDocumentV1, BankCheckV1, BankAccountDetailsV2, PayslipV2,
PayslipV3, HealthcareCardV1, BusinessCardV1, CustomV1, GeneratedV1,
BillOfLadingV1, ResumeV1, DeliveryNoteV1, DriverLicenseV1, IdCardV1,
InternationalIdV2, CarteGriseV1, or any other) is NOT evidence.

## veryfi names (implementation MUST match exactly)

NO veryfi route: veryfi has no energy bill method in the Python SDK.
The 5.1.0 wheel, inspected 2026-11-14, contains zero hits for
"energy" across all .py files, so a veryfi call of ANY kind is NOT
evidence. A call to the non-existent
process_energy_bill_document / process_energy_bill_document_url counts as
nothing. A raw HTTP call to
"https://api.veryfi.com/api/v8/partner/documents" is NOT evidence
either: it is Veryfi's generic documents endpoint, shared by
receipts, invoices, and other documents alike.

## azure names (implementation MUST match exactly)

NO azure route: Azure Document Intelligence has no energy bill or
utility bill model. The Microsoft Learn v4.0 (GA) model-overview
page, opened in the live browser and searched 2026-11-14,
contains zero hits for "energy bill", zero hits for "Energy Bill",
zero hits for "energy", and zero hits for "utility". A
begin_analyze_document call with ANY model id is NOT evidence.

## google document ai names (implementation MUST match exactly)

NO Google Document AI route: the Document AI processors list page,
opened and searched 2026-11-14, contains zero hits for
"Energy Bill" — there is no energy bill or utility bill processor, so a
process_document call with ANY processor is NOT evidence.

## eden ai / llamaparse / nanonets / docsumo / other vendor names (implementation MUST match exactly)

NO Eden AI route: Eden AI documents no energy bill parser
model, so a universal-ai call with ANY model id is NOT evidence.
NO LlamaParse route: LlamaParse is a generative parsing API with
no fixed static fingerprint naming energy bills. NO Nanonets route:
Nanonets document calls carry an opaque model_id in the URL path
(no fixed fingerprint — the model id is user-configured, not an
energy bill product). NO Docsumo route: Docsumo uploads go to a
generic endpoint with the document type configured in the
dashboard, not in the call. NO ABBYY Vantage / Rossum / Klippa /
Parseur / Extend route: opaque skill / queue / template / workflow
IDs. NO Textract route: Textract has no energy bill or utility
bill operation (AnalyzeID covers driver's licenses and passports).
NO smart-meter / utility API route: meter-reading endpoints and
utility account APIs return consumption from a meter or an
account, not fields extracted from an energy bill document. NO
mindee v2 extraction API route: configurable model id, no fixed
fingerprint.

## Documented matching hazards (honest limitations, also for the README)

- The bare phrases "energy bill extraction" / "extract energy
  bill" / "extract energy bills" are deliberately
  ENERGYBILLEXTRACTION phrases: in document-tool docs they almost
  always name energy bill extraction. But "energy bill" can
  also name a bill the tool merely stores, displays, or manages
  (an energy bill archive, an energy bill template library)
  without extracting fields from an energy bill document: a doc
  that means storing, displaying, or templating energy bills, not
  extracting fields from them, is a false positive; the tool
  flags the claim, only the code decides.
- "utility bill extraction" / "extract utility bill(s)" /
  "utility bill parsing" / "utility bill parser" are deliberately
  phrases: a utility bill IS the common name for an energy bill
  in many markets, so the name names the same document. But a
  "utility bill" is also a standard proof-of-address document: a
  doc that means verifying utility bills as proof of address, not
  extracting fields from them, is a false positive; the tool
  flags the claim, only the code decides.
- "electricity bill extraction" / "extract electricity bill(s)" /
  "electricity bill parsing" / "electricity bill parser" are
  deliberately phrases: an electricity bill is one kind of energy
  bill (the mindee product covers electricity and gas). A doc that
  means a different "electricity bill" — for example, a billing
  system that generates electricity bills rather than extracting
  fields from them — is a false positive; the tool flags the
  claim, only the code decides.
- "energy bill parsing" / "energy bill parser" are deliberately
  phrases: a doc can say "energy bill parser" about a tool that
  only renders an energy bill as formatted text, or an "energy
  bill parser" that is really a keyword highlighter over plain
  text. The tool flags the claim; only the code decides.
- "energy bill scanning" / "scan energy bill(s)" are
  deliberately phrases: "scanning" an energy bill can mean merely
  photographing it or OCRing it into raw text, with no structured
  field extraction. The tool flags the claim; only the code decides.
- The French phrase "facture d'energie" (and its extraction /
  parsing / scanning variants) is deliberately NOT in the phrase
  lists: the matcher does exact phrases after a normalisation
  that does not strip apostrophes, so a French apostrophe phrase
  would match unreliably across docs that write it with a straight
  quote, a curly quote, or no apostrophe at all. A doc that claims
  extraction using only the French name is missed; the English
  "energy bill", "utility bill", and "electricity bill" phrases
  are the checked ones.
- EnergyBillV1 v1.2 carries the field set listed in the mindee
  names section above (contract, delivery point, consumer,
  supplier, usage, invoice, meter, subscription, taxes, totals):
  it has NO payment status, NO bank account / direct debit
  details, and NO carbon / emissions fields. A tool that extracts
  those does so through some other route; this family checks for
  the EnergyBillV1 call, not for those fields. 
- A generic `extract_energy_bill(` / `parse_energy_bill(` /
  `extract_utility_bill(` call can name a string parser for text
  the user typed in rather than a document extractor: the tool
  counts the call, the claim plus the code decide — and a
  subprocess call invoking an external CLI is NOT evidence by
  design, so a thin wrapper that only calls subprocess fails.
- Mindee `parse` with EnergyBillV1 counts as evidence:
  EnergyBillV1 exists in mindee 4.22.0 (wheel inspected
  2026-11-14). The tool detects the call in source, not whether
  the call succeeds against a current API version. 
- Mindee `parse` with EnergyBillV1 IS a 4.x-only fingerprint:
  unlike the carte grise product, mindee 5.x removed the
  off-the-shelf energy bill product (5.4.0 wheel inspected
  2026-11-14 — no energy_bill product directory, zero
  "EnergyBill" hits in any .py file).
- Mindee `parse` with InvoiceV4 / ReceiptV5 / PassportV1 /
  FinancialDocumentV1 / BankCheckV1 / BankAccountDetailsV2 /
  PayslipV2 / PayslipV3 / HealthcareCardV1 / BusinessCardV1 /
  CustomV1 / GeneratedV1 / BillOfLadingV1 / ResumeV1 /
  DeliveryNoteV1 / DriverLicenseV1 / IdCardV1 /
  InternationalIdV2 / CarteGriseV1 is NOT detected: those are
  other document types.
- Mindee `parse` with CarteGriseV1 is NOT detected: a vehicle
  registration certificate is a different document from an energy
  bill.
- Azure `begin_analyze_document` with ANY model id is NOT
  detected: Azure Document Intelligence has no energy bill or
  utility bill model (the Learn v4.0 GA model-overview page
  contains zero hits for "energy bill", "energy", and "utility",
  verified 2026-11-14).
- Veryfi calls of ANY kind are NOT detected: veryfi has no energy
  bill method (5.1.0 wheel inspected 2026-11-14 — the word
  "energy" does not appear anywhere in the wheel), and its
  document APIs post to a generic documents endpoint shared
  across document types.
- Google Document AI `process_document` / `batch_process_documents`
  with ANY processor is NOT detected: Document AI has no energy
  bill or utility bill processor (the processors list page
  contains zero hits for "Energy Bill", verified 2026-11-14). Say
  so in the README.
- Eden AI universal-ai calls with ANY model id are NOT detected:
  Eden AI documents no energy bill parser model. 
- LlamaParse calls are NOT detected: its parsing API is
  generative with no fixed static fingerprint naming energy
  bills.
- Nanonets / Docsumo / ABBYY Vantage / Rossum / Klippa / Parseur /
  Extend calls are NOT detected: opaque model / skill / queue /
  template / workflow IDs, or a generic upload endpoint with the
  document type configured outside the call — no fixed fingerprint.
 
- Textract `analyze_document` / `analyze_expense` / `analyze_id` /
  `start_document_analysis` / `get_expense_analysis` are NOT
  detected: generic document, expense, and identity analysis are
  not energy bill extraction, and Textract has no energy bill or
  utility bill operation.
- Smart-meter / utility API calls are NOT detected: reading
  consumption from a meter or an account is not extracting fields
  from an energy bill document.
- A hand-rolled extraction from OCR text (`re.search` /
  `re.findall` on extracted text plus manual field assembly, no
  listed call) is NOT detected: the tool requires a listed call.
 
- The mindee CLI, the veryfi CLI, and any other external energy
  bill tool invoked through subprocess are NOT detected:
  subprocess calls invoking an external CLI are NOT evidence by
  design.
- Azure Document Intelligence, Mindee, and Veryfi are cloud APIs:
  the tool detects the client call in source, not whether
  credentials are configured or the call succeeds. 
- "extract energy bill text" / "extract text from energy bill"
  claims are NOT in the phrase lists: extracting plain text
  from an energy bill is text extraction, not energy bill
  field extraction.
- "energy bill template" / "energy bill form" claims are NOT
  in the phrase lists: templating or form-filling an energy bill
  is creating one, not extracting fields from one. 
- "energy bill tracking" / "energy bill payment" claims are
  NOT in the phrase lists: tracking or paying an energy bill is
  downstream of extraction, not extraction itself. 
- "utility bill verification" / "proof of address extraction" /
  "meter reading extraction" claims are NOT in the phrase lists:
  verifying a utility bill as proof of address, and reading a
  meter directly, are different operations from energy bill
  document extraction.
- "gas bill extraction" / "water bill extraction" claims are NOT
  in the phrase lists: this family covers energy bills, utility
  bills, and electricity bills as named in the phrase lists; gas
  and water bills are not listed.
- Invoice extraction claims ("extract invoices", "invoice
  extraction"), receipt extraction claims ("extract receipts",
  "receipt extraction"), ID document extraction claims ("extract
  passports", "passport extraction"), bank check extraction claims
  ("extract bank checks", "check extraction"), bank statement
  extraction claims ("extract bank statements", "statement
  extraction"), tax form extraction claims ("extract tax forms",
  "extract w2 forms", "1099 extraction"), pay stub extraction
  claims ("extract pay stubs", "payslip extraction"), health
  insurance card extraction claims ("extract health insurance
  cards", "health insurance card extraction"), business card
  extraction claims ("extract business cards", "business card
  extraction"), credit card extraction claims ("extract credit
  cards", "credit card extraction"), contract extraction claims
  ("extract contracts", "contract extraction"), mortgage
  extraction claims ("extract mortgages", "mortgage extraction"),
  resume extraction claims ("extract resumes", "resume
  extraction"), bill of lading extraction claims ("extract
  bills of lading", "bill of lading extraction"), delivery
  note extraction claims ("extract delivery notes", "delivery
  note extraction"), and carte grise extraction claims ("extract
  carte grises", "carte grise extraction") are NOT in the phrase
  lists: this family covers energy bills only. 
- As with every family: static pattern matching, not semantic
  judgement; dead code counts; alias chains the tracer cannot follow
  are missed; exact phrases only, not semantics; denial handling
  depends on the denial phrase list; each route must sit in a single
  module.

```
