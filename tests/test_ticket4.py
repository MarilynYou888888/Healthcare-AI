"""Ticket 4 integration: landing, export, clear-session, and preserved demo entry."""
import unittest

from playwright.sync_api import expect

try:
    from test_import import ImportTests
except ModuleNotFoundError:
    from tests.test_import import ImportTests


class Ticket4Tests(ImportTests):
    def test_end_to_end_export_clear_and_demo_entry(self):
        self.page.get_by_label('Choose CSV or XLSX').set_input_files('web/sample-import.xlsx')
        for sheet, role in [('Planning Assumptions', 'planning'), ('Actual vs Forecast', 'performance'), ('Operating Events', 'events')]:
            self.page.get_by_label('Dataset role — ' + sheet, exact=True).select_option(role)
        self.page.get_by_role('button', name='Map columns', exact=True).click()
        self.page.get_by_role('button', name='Validate data', exact=True).click()
        expect(self.page.locator('#import-validation')).to_contain_text('0 errors')
        self.page.get_by_label('I reviewed all warnings').check()
        self.page.get_by_role('button', name='Preview normalized data', exact=True).click()
        self.page.get_by_label('I confirm the normalized data').check()
        self.page.get_by_role('button', name='Confirm import', exact=True).click()
        self.page.locator('#import-open-workflows').click()
        expect(self.page.locator('#user-analysis')).to_be_visible()
        self.page.get_by_role('button', name='Scenario Model', exact=True).click()
        self.page.get_by_label('Provider FTE scenario', exact=True).fill('3.5')
        expect(self.page.locator('#commentary-summary')).to_contain_text('Provider FTE changed')
        with self.page.expect_download() as download:
            self.page.get_by_role('button', name='Export Scenario Summary CSV', exact=True).click()
        artifact = download.value
        self.assertTrue(artifact.suggested_filename.endswith('-scenario-summary.csv'))
        self.page.get_by_role('button', name='Clear Uploaded Data', exact=True).last.click()
        self.page.wait_for_url('**/')
        expect(self.page.locator('.entry-choice')).to_contain_text('Explore Demo')
        expect(self.page.locator('.entry-choice')).to_contain_text('Use My Data')
        expect(self.page.get_by_role('tab', name='Executive Summary', exact=True)).to_be_visible()


if __name__ == '__main__':
    unittest.main()
