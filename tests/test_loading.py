import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from provider_fpa.loading import load_datasets


INPUTS = Path(__file__).resolve().parents[1] / 'data/synthetic_benchmark/inputs'


class LoadingTests(unittest.TestCase):
    def test_loads_five_typed_datasets_with_lineage(self):
        data = load_datasets(INPUTS)
        self.assertEqual(len(data.clinics), 6)
        self.assertEqual(len(data.financial_values), 72)
        self.assertTrue(data.operational_values and data.operating_events and data.review_rules)
        row = data.financial_values[0]
        self.assertEqual(row.evidence.input_file, 'financial_values.csv')
        self.assertEqual(dict(row.evidence.row_selector)['clinic_id'], row.clinic_id)
        self.assertTrue(row.evidence.recorded_at)

    def test_duplicate_rows_missing_sources_and_person_fields_are_rejected(self):
        for mutation in ['duplicate', 'source', 'person_field', 'unknown_clinic', 'month']:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                shutil.copytree(INPUTS, root, dirs_exist_ok=True)
                path = root / 'financial_values.csv'
                with path.open() as handle:
                    reader = csv.DictReader(handle)
                    fields, rows = reader.fieldnames, list(reader)
                if mutation == 'duplicate':
                    rows.append(rows[0])
                elif mutation == 'source':
                    rows[0]['source'] = ''
                elif mutation == 'person_field':
                    fields = fields + ['patient_name']
                elif mutation == 'unknown_clinic':
                    rows[0]['clinic_id'] = 'UNKNOWN'
                else:
                    rows[0]['month'] = '2026-13'
                with path.open('w') as handle:
                    writer = csv.DictWriter(handle, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(rows)
                with self.assertRaises(ValueError):
                    load_datasets(root)
