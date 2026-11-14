"""Contract tests use temporary repositories and fixed reference literals."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from energy_bill_extraction_claim_audit.audit import audit, match_phrases, normalize, source_evidence
from energy_bill_extraction_claim_audit.phrases import ENERGYBILLEXTRACTION, NOENERGYBILLEXTRACTION, GENERIC_NAMES
from energy_bill_extraction_claim_audit.__main__ import main

EXPECTED_POS = ('energy bill extraction', 'extract energy bills', 'extracts energy bills', 'extracting energy bills', 'extract energy bill', 'extracts energy bill', 'extracting energy bill', 'energy bill parsing', 'energy bill parser', 'parse energy bills', 'parses energy bills', 'parse energy bill', 'parses energy bill', 'energy bill scanning', 'energy bill scanner', 'scan energy bills', 'scans energy bills', 'scan energy bill', 'scans energy bill', 'utility bill extraction', 'extract utility bills', 'extracts utility bills', 'extracting utility bills', 'extract utility bill', 'extracts utility bill', 'extracting utility bill', 'utility bill parsing', 'utility bill parser', 'parse utility bills', 'parses utility bills', 'parse utility bill', 'parses utility bill', 'utility bill scanning', 'utility bill scanner', 'scan utility bills', 'scans utility bills', 'scan utility bill', 'scans utility bill', 'electricity bill extraction', 'extract electricity bills', 'extracts electricity bills', 'extracting electricity bills', 'extract electricity bill', 'extracts electricity bill', 'extracting electricity bill', 'electricity bill parsing', 'electricity bill parser', 'parse electricity bills', 'parses electricity bills', 'parse electricity bill')
EXPECTED_NEG = ('no energy bill extraction', 'does not extract energy bills', 'does not extract energy bill', 'does not support energy bill extraction', 'without energy bill extraction', 'no energy bill parser', 'does not parse energy bills', 'does not parse energy bill', 'no utility bill extraction', 'does not extract utility bills', 'does not extract utility bill', 'does not support utility bill extraction', 'without utility bill extraction', 'no energy bill scanner', 'does not scan energy bills', 'does not scan energy bill', 'no electricity bill extraction', 'does not extract electricity bills', 'does not extract electricity bill', 'without electricity bill extraction', 'no electricity bill parser', 'does not parse electricity bills', 'does not parse electricity bill', 'energy bill extraction not supported')
EXPECTED_NAMES = ('extract_energy_bill', 'extract_energy_bills', 'parse_energy_bill', 'parse_energy_bills', 'extract_utility_bill', 'parse_utility_bill', 'extract_utility_bills', 'parse_utility_bills', 'extract_electricity_bill', 'parse_electricity_bill', 'extract_energy_bill_data', 'parse_energy_bill_data', 'energy_bill_extraction', 'energy_bill_extractor', 'energy_bill_parser', 'utility_bill_extraction', 'utility_bill_extractor', 'utility_bill_parser', 'extract_energy_bill_info', 'parse_energy_bill_info', 'energy_bill_scan', 'energy_bill_scanner', 'scan_energy_bill', 'scan_energy_bills')

class AuditTests(unittest.TestCase):
    def repo(self, files):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        for name, content in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        return root

    def cli(self, root, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(['audit', str(root), '--json', *args])
        return code, json.loads(out.getvalue())

    def test_phrase_oracle(self):
        self.assertEqual(ENERGYBILLEXTRACTION, EXPECTED_POS)
        self.assertEqual(NOENERGYBILLEXTRACTION, EXPECTED_NEG)
        self.assertEqual(GENERIC_NAMES, EXPECTED_NAMES)
        self.assertEqual((len(EXPECTED_POS), len(EXPECTED_NEG), len(set(EXPECTED_NAMES))), (50, 24, 24))

    def test_good(self):
        self.assertEqual(self.cli(self.repo({'README.md': 'energy bill extraction', 'app.py': 'x.extract_energy_bill()'}))[0], 0)

    def test_bad(self):
        code, result = self.cli(self.repo({'README.md': 'energy bill extraction'}))
        self.assertEqual(code, 2)
        self.assertEqual(result['findings'][0]['rule'], 'documented-energy-bill-extraction-claim-false')
        self.assertEqual(result['findings'][0]['severity'], 'HIGH')
        self.assertTrue(result['findings'][0]['message'])
        self.assertEqual(result['verdict'], 'FAIL')
        self.assertIn('test_evidence', result)
        self.assertIn('production_evidence', result)

    def test_denial(self):
        code, result = self.cli(self.repo({'README.md': 'no energy bill extraction', 'app.py': 'x.extract_energy_bill()'}))
        self.assertEqual(code, 2)
        self.assertEqual(result['findings'][0]['rule'], 'documented-no-energy-bill-extraction-claim-false')
        self.assertEqual(result['findings'][0]['severity'], 'HIGH')

    def test_no_source_denial(self):
        self.assertEqual(audit(self.repo({'README.md': 'no energy bill extraction'}))['verdict'], 'PASS')

    def test_no_claim(self):
        self.assertEqual(audit(self.repo({'README.md': 'neutral', 'app.py': 'x.extract_energy_bill()'}))['verdict'], 'PASS')

    def test_test_only(self):
        for filename in ('tests/helper.py', 'test_feature.py', 'feature_test.py'):
            with self.subTest(filename=filename):
                root = self.repo({'README.md': 'energy bill extraction', filename: 'x.extract_energy_bill()'})
                code, result = self.cli(root)
                self.assertEqual(code, 0)
                self.assertEqual(result['verdict'], 'PASS')
                self.assertEqual(result['findings'][0]['severity'], 'MEDIUM')
                code, result = self.cli(root, '--fail-on', 'medium')
                self.assertEqual(code, 2)
                self.assertEqual(result['verdict'], 'FAIL')

    def test_ignore_component_prefix(self):
        root = self.repo({'README.md': 'energy bill extraction', 'src/a.py': 'x.extract_energy_bill()'})
        self.assertEqual(self.cli(root, '--ignore', 'sr')[0], 0)
        self.assertEqual(self.cli(root, '--ignore', 'src')[0], 2)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['audit', str(root), '--ignore', '../outside']), 1)
            self.assertEqual(main(['audit', str(root), '--ignore', '/abs']), 1)

    def test_fences(self):
        for fence in ('```', '~~~', '   ````'):
            root = self.repo({'README.md': fence + '\nenergy bill extraction\n' + fence})
            self.assertEqual(audit(root)['verdict'], 'PASS')
        root = self.repo({'README.md': '`energy bill extraction`'})
        self.assertEqual(self.cli(root)[0], 2)

    def test_boundaries_longest_denial(self):
        yes, no = match_phrases('extract energy bills')
        self.assertEqual([p[0] for p in yes], ['extract energy bills'])
        self.assertFalse(match_phrases('preextract energy billsuffix')[0])
        yes, no = match_phrases('does not extract energy bills')
        self.assertEqual(yes, [])
        self.assertEqual([p[0] for p in no], ['does not extract energy bills'])
        self.assertEqual(match_phrases("doesn't extract energy bills")[0], [])
        self.assertEqual(normalize('ENERGY-BILL  extraction'), 'energy bill extraction')

    def test_invalid_encoding_declaration(self):
        root = self.repo({'README.md': 'energy bill extraction', 'app.py': '# coding: nonexistent-r205\nx.extract_energy_bill()'})
        self.assertEqual(self.cli(root)[0], 2)

    def test_attribute_assignment_preserves_import(self):
        self.assertTrue(source_evidence('import mindee\nmindee.setting = True\nmindee.Client()\nx.parse(EnergyBillV1)'))

    def test_single_module(self):
        root = self.repo({'README.md': 'energy bill extraction', 'one.py': 'import mindee\nc=mindee.Client()', 'two.py': 'x.parse(product.EnergyBillV1)'})
        self.assertEqual(self.cli(root)[0], 2)

    def test_paths_and_ignore(self):
        for folder in ('fixtures', 'docs', 'examples'):
            root = self.repo({'README.md': 'energy bill extraction', folder+'/a.py': 'x.extract_energy_bill()'})
            self.assertEqual(self.cli(root)[0], 2)
        root = self.repo({'nested/docs/a.md': 'energy bill extraction', 'other.md': 'no energy bill extraction', 'vendor/a.py': 'x.extract_energy_bill()'})
        self.assertEqual(self.cli(root)[0], 0)
        self.assertEqual(self.cli(root, '--ignore', 'vendor', '--ignore', 'unused')[0], 2)
        self.assertEqual(self.cli(root, '--ignore', 'nested')[0], 0)

    def test_symlinks(self):
        root = self.repo({'README.md': 'energy bill extraction'})
        outside = self.repo({'a.py': 'x.extract_energy_bill()', 'a.md': 'energy bill extraction'})
        (root/'link.py').symlink_to(outside/'a.py')
        (root/'linked').symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.cli(root)[0], 2)
        (root/'README.md').unlink()
        (root/'README.md').symlink_to(outside/'a.md')
        self.assertEqual(audit(root)['verdict'], 'PASS')

    def test_usage_io(self):
        for argv in ([], ['audit', '--fail-on', 'HIGH'], ['audit', '--unknown']):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                main(argv)
            self.assertEqual(caught.exception.code, 1)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['audit', '/nonexistent/r205']), 1)
        root = self.repo({})
        root.chmod(0)
        try:
            with self.assertRaises(OSError): audit(root)
        finally:
            root.chmod(0o700)

    def test_entry_points(self):
        root = self.repo({})
        command = [sys.executable, '-m', 'energy_bill_extraction_claim_audit']
        self.assertEqual(subprocess.check_output(command+['--version'], text=True).strip(), '0.1.0')
        result = subprocess.run(command+['audit', str(root), '--json'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['verdict'], 'PASS')

    def test_positive_000(self):
        self.assertTrue(source_evidence('x.extract_energy_bill()'))

    def test_positive_001(self):
        self.assertTrue(source_evidence('from provider import extract_energy_bill as run\nrun()'))

    def test_positive_002(self):
        self.assertTrue(source_evidence('x.extract_energy_bills()'))

    def test_positive_003(self):
        self.assertTrue(source_evidence('from provider import extract_energy_bills as run\nrun()'))

    def test_positive_004(self):
        self.assertTrue(source_evidence('x.parse_energy_bill()'))

    def test_positive_005(self):
        self.assertTrue(source_evidence('from provider import parse_energy_bill as run\nrun()'))

    def test_positive_006(self):
        self.assertTrue(source_evidence('x.parse_energy_bills()'))

    def test_positive_007(self):
        self.assertTrue(source_evidence('from provider import parse_energy_bills as run\nrun()'))

    def test_positive_008(self):
        self.assertTrue(source_evidence('x.extract_utility_bill()'))

    def test_positive_009(self):
        self.assertTrue(source_evidence('from provider import extract_utility_bill as run\nrun()'))

    def test_positive_010(self):
        self.assertTrue(source_evidence('x.parse_utility_bill()'))

    def test_positive_011(self):
        self.assertTrue(source_evidence('from provider import parse_utility_bill as run\nrun()'))

    def test_positive_012(self):
        self.assertTrue(source_evidence('x.extract_utility_bills()'))

    def test_positive_013(self):
        self.assertTrue(source_evidence('from provider import extract_utility_bills as run\nrun()'))

    def test_positive_014(self):
        self.assertTrue(source_evidence('x.parse_utility_bills()'))

    def test_positive_015(self):
        self.assertTrue(source_evidence('from provider import parse_utility_bills as run\nrun()'))

    def test_positive_016(self):
        self.assertTrue(source_evidence('x.extract_electricity_bill()'))

    def test_positive_017(self):
        self.assertTrue(source_evidence('from provider import extract_electricity_bill as run\nrun()'))

    def test_positive_018(self):
        self.assertTrue(source_evidence('x.parse_electricity_bill()'))

    def test_positive_019(self):
        self.assertTrue(source_evidence('from provider import parse_electricity_bill as run\nrun()'))

    def test_positive_020(self):
        self.assertTrue(source_evidence('x.extract_energy_bill_data()'))

    def test_positive_021(self):
        self.assertTrue(source_evidence('from provider import extract_energy_bill_data as run\nrun()'))

    def test_positive_022(self):
        self.assertTrue(source_evidence('x.parse_energy_bill_data()'))

    def test_positive_023(self):
        self.assertTrue(source_evidence('from provider import parse_energy_bill_data as run\nrun()'))

    def test_positive_024(self):
        self.assertTrue(source_evidence('x.energy_bill_extraction()'))

    def test_positive_025(self):
        self.assertTrue(source_evidence('from provider import energy_bill_extraction as run\nrun()'))

    def test_positive_026(self):
        self.assertTrue(source_evidence('x.energy_bill_extractor()'))

    def test_positive_027(self):
        self.assertTrue(source_evidence('from provider import energy_bill_extractor as run\nrun()'))

    def test_positive_028(self):
        self.assertTrue(source_evidence('x.energy_bill_parser()'))

    def test_positive_029(self):
        self.assertTrue(source_evidence('from provider import energy_bill_parser as run\nrun()'))

    def test_positive_030(self):
        self.assertTrue(source_evidence('x.utility_bill_extraction()'))

    def test_positive_031(self):
        self.assertTrue(source_evidence('from provider import utility_bill_extraction as run\nrun()'))

    def test_positive_032(self):
        self.assertTrue(source_evidence('x.utility_bill_extractor()'))

    def test_positive_033(self):
        self.assertTrue(source_evidence('from provider import utility_bill_extractor as run\nrun()'))

    def test_positive_034(self):
        self.assertTrue(source_evidence('x.utility_bill_parser()'))

    def test_positive_035(self):
        self.assertTrue(source_evidence('from provider import utility_bill_parser as run\nrun()'))

    def test_positive_036(self):
        self.assertTrue(source_evidence('x.extract_energy_bill_info()'))

    def test_positive_037(self):
        self.assertTrue(source_evidence('from provider import extract_energy_bill_info as run\nrun()'))

    def test_positive_038(self):
        self.assertTrue(source_evidence('x.parse_energy_bill_info()'))

    def test_positive_039(self):
        self.assertTrue(source_evidence('from provider import parse_energy_bill_info as run\nrun()'))

    def test_positive_040(self):
        self.assertTrue(source_evidence('x.energy_bill_scan()'))

    def test_positive_041(self):
        self.assertTrue(source_evidence('from provider import energy_bill_scan as run\nrun()'))

    def test_positive_042(self):
        self.assertTrue(source_evidence('x.energy_bill_scanner()'))

    def test_positive_043(self):
        self.assertTrue(source_evidence('from provider import energy_bill_scanner as run\nrun()'))

    def test_positive_044(self):
        self.assertTrue(source_evidence('x.scan_energy_bill()'))

    def test_positive_045(self):
        self.assertTrue(source_evidence('from provider import scan_energy_bill as run\nrun()'))

    def test_positive_046(self):
        self.assertTrue(source_evidence('x.scan_energy_bills()'))

    def test_positive_047(self):
        self.assertTrue(source_evidence('from provider import scan_energy_bills as run\nrun()'))

    def test_positive_048(self):
        self.assertTrue(source_evidence('import mindee\nfrom mindee.product.fr import EnergyBillV1\nc = mindee.Client()\nc.parse(product.EnergyBillV1)'))

    def test_positive_049(self):
        self.assertTrue(source_evidence('import mindee\nfrom mindee.product.fr import EnergyBillV1\nc = mindee.Client()\nc.parse(EnergyBillV1)'))

    def test_positive_050(self):
        self.assertTrue(source_evidence('import mindee\nfrom mindee.product.fr import EnergyBillV1\nc = mindee.Client()\nc.parse(mindee.product.fr.EnergyBillV1)'))

    def test_positive_051(self):
        self.assertTrue(source_evidence('import mindee\nfrom mindee.product.fr import EnergyBillV1\nc = mindee.Client()\nc.parse(mindee.v1.product.fr.EnergyBillV1)'))

    def test_positive_052(self):
        self.assertTrue(source_evidence('from mindee import Client as C\nc=C()\nx.parse(kind=product.EnergyBillV1)'))

    def test_positive_053(self):
        self.assertTrue(source_evidence('import mindee as m\nfrom mindee import Client as C\nC()\nx.parse(EnergyBillV1)'))

    def test_negative_000(self):
        self.assertEqual(source_evidence('import mindee'), [])

    def test_negative_001(self):
        self.assertEqual(source_evidence('import veryfi'), [])

    def test_negative_002(self):
        self.assertEqual(source_evidence('import azure.ai.documentintelligence'), [])

    def test_negative_003(self):
        self.assertEqual(source_evidence('import google.cloud.documentai'), [])

    def test_negative_004(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()'), [])

    def test_negative_005(self):
        self.assertEqual(source_evidence('extract_energy_bill()'), [])

    def test_negative_006(self):
        self.assertEqual(source_evidence('x.extract_energy_bill'), [])

    def test_negative_007(self):
        self.assertEqual(source_evidence('"x.extract_energy_bill()"'), [])

    def test_negative_008(self):
        self.assertEqual(source_evidence('# x.extract_energy_bill()'), [])

    def test_negative_009(self):
        self.assertEqual(source_evidence('this is invalid syntax !'), [])

    def test_negative_010(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.InvoiceV4)'), [])

    def test_negative_011(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.ReceiptV5)'), [])

    def test_negative_012(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.PassportV1)'), [])

    def test_negative_013(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.FinancialDocumentV1)'), [])

    def test_negative_014(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.BankCheckV1)'), [])

    def test_negative_015(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.BankAccountDetailsV2)'), [])

    def test_negative_016(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.PayslipV2)'), [])

    def test_negative_017(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.PayslipV3)'), [])

    def test_negative_018(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.HealthcareCardV1)'), [])

    def test_negative_019(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.BusinessCardV1)'), [])

    def test_negative_020(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.CustomV1)'), [])

    def test_negative_021(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.GeneratedV1)'), [])

    def test_negative_022(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.BillOf\x4cadingV1)'), [])

    def test_negative_023(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.\x52esumeV1)'), [])

    def test_negative_024(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.DeliveryNoteV1)'), [])

    def test_negative_025(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.DriverLicenseV1)'), [])

    def test_negative_026(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.IdCardV1)'), [])

    def test_negative_027(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.InternationalIdV2)'), [])

    def test_negative_028(self):
        self.assertEqual(source_evidence('import mindee\nc=mindee.Client()\nc.parse(product.\x43arte\x47riseV1)'), [])

    def test_negative_029(self):
        self.assertEqual(source_evidence("x.begin_analyze_document('prebuilt-invoice')"), [])

    def test_negative_030(self):
        self.assertEqual(source_evidence("x.begin_analyze_document('prebuilt-receipt')"), [])

    def test_negative_031(self):
        self.assertEqual(source_evidence("x.begin_analyze_document('prebuilt-layout')"), [])

    def test_negative_032(self):
        self.assertEqual(source_evidence("x.begin_analyze_document('prebuilt-read')"), [])

    def test_negative_033(self):
        self.assertEqual(source_evidence("x.begin_analyze_document('prebuilt-idDocument')"), [])

    def test_negative_034(self):
        self.assertEqual(source_evidence("x.begin_analyze_document('prebuilt-check.us')"), [])

    def test_negative_035(self):
        self.assertEqual(source_evidence("x.begin_analyze_document('prebuilt-tax.us')"), [])

    def test_negative_036(self):
        self.assertEqual(source_evidence("x.begin_analyze_document('prebuilt-bankStatement.us')"), [])

    def test_negative_037(self):
        self.assertEqual(source_evidence("x.begin_analyze_document('prebuilt-payStub.us')"), [])

    def test_negative_038(self):
        self.assertEqual(source_evidence("x.begin_analyze_document('prebuilt-healthInsuranceCard.us')"), [])

    def test_negative_039(self):
        self.assertEqual(source_evidence("x.begin_analyze_document('prebuilt-businessCard')"), [])

    def test_negative_040(self):
        self.assertEqual(source_evidence("x.begin_analyze_document('prebuilt-creditCard')"), [])

    def test_negative_041(self):
        self.assertEqual(source_evidence("x.begin_analyze_document('prebuilt-contract')"), [])

    def test_negative_042(self):
        self.assertEqual(source_evidence("x.begin_analyze_document('prebuilt-mortgage.us.1003')"), [])

    def test_negative_043(self):
        self.assertEqual(source_evidence('veryfi.Client()'), [])

    def test_negative_044(self):
        self.assertEqual(source_evidence('azure.DocumentIntelligenceClient()'), [])

    def test_negative_045(self):
        self.assertEqual(source_evidence('x.process_any_document()'), [])

    def test_negative_046(self):
        self.assertEqual(source_evidence('x.process_any_document_url()'), [])

    def test_negative_047(self):
        self.assertEqual(source_evidence('x.process_document()'), [])

    def test_negative_048(self):
        self.assertEqual(source_evidence('x.process_document_url()'), [])

    def test_negative_049(self):
        self.assertEqual(source_evidence('x.process_w2_document()'), [])

    def test_negative_050(self):
        self.assertEqual(source_evidence('x.process_w9_document()'), [])

    def test_negative_051(self):
        self.assertEqual(source_evidence('x.process_w8_document()'), [])

    def test_negative_052(self):
        self.assertEqual(source_evidence('x.process_check()'), [])

    def test_negative_053(self):
        self.assertEqual(source_evidence('x.process_check_url()'), [])

    def test_negative_054(self):
        self.assertEqual(source_evidence('x.process_check_with_remittance()'), [])

    def test_negative_055(self):
        self.assertEqual(source_evidence('x.process_bank_statement_document()'), [])

    def test_negative_056(self):
        self.assertEqual(source_evidence('x.process_bussines_card_document()'), [])

    def test_negative_057(self):
        self.assertEqual(source_evidence('x.classify_document()'), [])

    def test_negative_058(self):
        self.assertEqual(source_evidence('x.get_business_cards()'), [])

    def test_negative_059(self):
        self.assertEqual(source_evidence('x.process_energy_bill_document()'), [])

    def test_negative_060(self):
        self.assertEqual(source_evidence('x.batch_process_documents()'), [])

    def test_negative_061(self):
        self.assertEqual(source_evidence('x.analyze_document()'), [])

    def test_negative_062(self):
        self.assertEqual(source_evidence('x.analyze_expense()'), [])

    def test_negative_063(self):
        self.assertEqual(source_evidence('x.analyze_id()'), [])

    def test_negative_064(self):
        self.assertEqual(source_evidence('x.start_document_analysis()'), [])

    def test_negative_065(self):
        self.assertEqual(source_evidence('x.get_expense_analysis()'), [])

    def test_negative_066(self):
        self.assertEqual(source_evidence('x.extract_text()'), [])

    def test_negative_067(self):
        self.assertEqual(source_evidence('x.image_to_string()'), [])

    def test_negative_068(self):
        self.assertEqual(source_evidence('x.read_csv()'), [])

    def test_negative_069(self):
        self.assertEqual(source_evidence('x.read_excel()'), [])

    def test_negative_070(self):
        self.assertEqual(source_evidence('x.read_pdf()'), [])

    def test_negative_071(self):
        self.assertEqual(source_evidence('x.convert_into()'), [])

    def test_negative_072(self):
        self.assertEqual(source_evidence('x.extract_table()'), [])

    def test_negative_073(self):
        self.assertEqual(source_evidence('x.extract_tables()'), [])

    def test_negative_074(self):
        self.assertEqual(source_evidence('x.find_tables()'), [])

    def test_negative_075(self):
        self.assertEqual(source_evidence('x.find_table()'), [])

    def test_negative_076(self):
        self.assertEqual(source_evidence('x.get_meter_reading()'), [])

    def test_negative_077(self):
        self.assertEqual(source_evidence('requests.post("https://api.veryfi.com/api/v8/partner/documents")'), [])

    def test_negative_078(self):
        self.assertEqual(source_evidence('x.post("universal-ai", json={"model":"ocr/invoice_parser/affinda"})'), [])

    def test_negative_079(self):
        self.assertEqual(source_evidence('x.post("universal-ai", json={"model":"ocr/\x72esume_parser/affinda"})'), [])

    def test_negative_080(self):
        self.assertEqual(source_evidence('LlamaParse().parse("file")'), [])

    def test_negative_081(self):
        self.assertEqual(source_evidence('nanonets.ocr(model_id="opaque")'), [])

    def test_negative_082(self):
        self.assertEqual(source_evidence('docsumo.upload("file")'), [])

    def test_negative_083(self):
        self.assertEqual(source_evidence('mindee.ClientV2().enqueue_and_parse(model_id="opaque")'), [])

    def test_negative_084(self):
        self.assertEqual(source_evidence('re.search("total", text)'), [])

    def test_negative_085(self):
        self.assertEqual(source_evidence('str.parse("energy bill")'), [])

    def test_negative_086(self):
        self.assertEqual(source_evidence('subprocess.run(["mindee", "parse"])'), [])

    def test_negative_087(self):
        self.assertEqual(source_evidence('subprocess.run(["veryfi", "process"])'), [])

    def test_negative_088(self):
        self.assertEqual(source_evidence('def extract_energy_bill(): pass\nx.extract_energy_bill()'), [])

    def test_negative_089(self):
        self.assertEqual(source_evidence('from p import extract_energy_bill as e\ne = other\ne()'), [])

    def test_negative_090(self):
        self.assertEqual(source_evidence('from p import extract_energy_bill as e\ne: object = other\ne()'), [])

    def test_negative_091(self):
        self.assertEqual(source_evidence('from p import extract_energy_bill as e\nwith context() as e:\n e()'), [])

    def test_negative_092(self):
        self.assertEqual(source_evidence('from p import extract_energy_bill as e\nasync def f():\n async with context() as e:\n  e()'), [])

    def test_negative_093(self):
        self.assertEqual(source_evidence('import mindee\nclass Client: pass\nmindee.Client()\nx.parse(EnergyBillV1)'), [])

    def test_negative_094(self):
        self.assertEqual(source_evidence('from p import extract_energy_bill\nclass X:\n def extract_energy_bill(self): pass\nx.extract_energy_bill()'), [])


if __name__ == '__main__':
    unittest.main()
