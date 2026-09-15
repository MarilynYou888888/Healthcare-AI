import unittest
from decimal import Decimal
from provider_fpa.benchmark import load_company


class PublicBenchmarkTests(unittest.TestCase):
    def test_both_companies_have_source_linked_normalized_revenue(self):
        for ticker, expected in [('HCA', '75600000000'), ('THC', '21310000000')]:
            company = load_company(ticker)
            metric = next(m for m in company.metrics if m.metric_id == 'REVENUE')
            self.assertEqual(metric.value, Decimal(expected))
            self.assertEqual(metric.unit, 'USD')
            self.assertTrue(metric.source_url.startswith('https://'))
            self.assertTrue(metric.source_locator)
            self.assertEqual(metric.provenance_kind, 'reported')

    def test_public_records_are_immutable_and_serialization_is_detached(self):
        from dataclasses import FrozenInstanceError
        company=load_company('HCA')
        with self.assertRaises(FrozenInstanceError):
            company.metrics[0].value=Decimal(0)
        payload=company.payload()
        payload['metrics'][0]['value']='0'
        self.assertNotEqual(company.metrics[0].value,Decimal(0))

    def test_missing_history_stays_missing_and_scopes_are_not_blended(self):
        from provider_fpa.benchmark import derived_ratio
        company=load_company('THC')
        missing=next(m for m in company.metrics if m.period=='FY2023')
        self.assertIsNone(missing.value)
        self.assertIn('Not disclosed',missing.missing_reason)
        revenue=next(m for m in company.metrics if m.metric_id=='SEGMENT_REVENUE' and m.business_segment=='Hospital Operations')
        volume=next(m for m in company.metrics if m.metric_id=='ADJUSTED_ADMISSIONS' and m.period=='FY2025')
        with self.assertRaises(ValueError):derived_ratio(revenue,volume,'BAD','Bad ratio')
        margin=next(m for m in company.metrics if m.metric_id=='SEGMENT_ADJUSTED_EBITDA_RATIO' and m.business_segment=='Hospital Operations')
        self.assertEqual(margin.value.quantize(Decimal('.0001')),Decimal('.1574'))
        self.assertEqual(margin.parent_metric_ids,('SEGMENT_ADJUSTED_EBITDA','SEGMENT_REVENUE'))
        self.assertIn('denominator',margin.source_locator)

    def test_input_duplicates_units_and_missing_lineage_fail_explicitly(self):
        import csv
        from provider_fpa.benchmark import DATA_ROOT, normalize_records
        with (DATA_ROOT/'hca/financial_metrics.csv').open() as f: row=next(csv.DictReader(f))
        for records in ([row,row],[dict(row,value='75600')],[dict(row,source_url='')],[dict(row,raw_value='',value='0')],[dict(row,raw_value='NaN',value='NaN')]):
            with self.subTest(records=records),self.assertRaises(ValueError):normalize_records(records)

    def test_hca_percentage_and_payer_denominator_are_preserved(self):
        metrics=load_company('HCA').metrics
        occupancy=next(m for m in metrics if m.metric_id=='OCCUPANCY')
        self.assertEqual(occupancy.value,Decimal('.73'))
        self.assertEqual(occupancy.raw_unit,'percent')
        self.assertIn('beds in service',occupancy.metric_definition)
        payers=[m for m in metrics if m.group=='payer_mix']
        self.assertEqual(sum(m.value for m in payers),Decimal(1))
        self.assertTrue(all('admissions' in m.metric_definition for m in payers))
        tenet_payers=[m for m in load_company('THC').metrics if m.group=='payer_mix']
        self.assertTrue(all(m.unit=='USD' and 'not admission share' in m.metric_definition for m in tenet_payers))

    def test_public_periods_distinguish_year_end_counts_from_annual_flows(self):
        for ticker, count_id in [('HCA','HOSPITALS'),('THC','LICENSED_BEDS')]:
            metrics=load_company(ticker).metrics
            count=next(m for m in metrics if m.metric_id==count_id)
            revenue=next(m for m in metrics if m.metric_id=='REVENUE')
            self.assertEqual(count.payload()['period_type'],'instant')
            self.assertEqual(count.payload()['period_start'],'2025-12-31')
            self.assertEqual(revenue.payload()['period_type'],'duration')
            self.assertEqual(revenue.payload()['period_start'],'2025-01-01')
            self.assertEqual(revenue.payload()['period_end'],'2025-12-31')
