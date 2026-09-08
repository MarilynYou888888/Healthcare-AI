import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "scripts" / "generate_synthetic_benchmark.py"
SEED = "20260907"


class SyntheticBenchmarkCliTests(unittest.TestCase):
    def run_generator(self, output_dir: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(GENERATOR),
                "--output-dir",
                str(output_dir),
                "--seed",
                SEED,
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_cli_creates_the_confirmed_benchmark_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "benchmark"
            result = self.run_generator(output_dir)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "Validation passed: 5 input tables, 10 cases, and 10 gold fixtures",
                result.stdout,
            )

            expected_inputs = {
                "clinics.csv",
                "financial_values.csv",
                "operational_values.csv",
                "operating_events.csv",
                "review_rules.csv",
            }
            self.assertEqual(
                {path.name for path in (output_dir / "inputs").glob("*.csv")},
                expected_inputs,
            )
            self.assertTrue((output_dir / "cases.json").is_file())
            self.assertTrue((output_dir / "README.md").is_file())
            self.assertEqual(len(list((output_dir / "gold").glob("C*.json"))), 10)

            cases = json.loads((output_dir / "cases.json").read_text())
            self.assertEqual([case["case_id"] for case in cases], [f"C{i:02d}" for i in range(1, 11)])

    def test_cli_output_is_deterministic_and_matches_the_minimum_data_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first"
            second = Path(tmp) / "second"
            self.assertEqual(self.run_generator(first).returncode, 0)
            self.assertEqual(self.run_generator(second).returncode, 0)

            first_files = sorted(path.relative_to(first) for path in first.rglob("*") if path.is_file())
            second_files = sorted(path.relative_to(second) for path in second.rglob("*") if path.is_file())
            self.assertEqual(first_files, second_files)
            for relative_path in first_files:
                self.assertEqual(
                    (first / relative_path).read_bytes(),
                    (second / relative_path).read_bytes(),
                    str(relative_path),
                )

            expected_headers = {
                "clinics.csv": [
                    "clinic_id", "clinic_name", "market_id", "specialty", "active_from", "active_to", "source"
                ],
                "financial_values.csv": [
                    "clinic_id", "month", "account_id", "account_name", "actual_value", "forecast_value",
                    "unit", "currency", "source", "loaded_at"
                ],
                "operational_values.csv": [
                    "clinic_id", "month", "metric_id", "metric_name", "actual_value", "expected_value",
                    "unit", "source", "loaded_at"
                ],
                "operating_events.csv": [
                    "event_id", "clinic_id", "event_type", "start_date", "end_date", "description",
                    "source", "reported_at"
                ],
                "review_rules.csv": [
                    "rule_id", "account_or_metric_id", "absolute_threshold", "percentage_threshold",
                    "always_review", "effective_from", "effective_to", "source"
                ],
            }
            prohibited_fields = {"patient_name", "dob", "member_id", "claim_id", "encounter_id", "provider_id", "employee_id"}

            tables = {}
            for filename, headers in expected_headers.items():
                with (first / "inputs" / filename).open(newline="", encoding="utf-8") as handle:
                    reader = csv.DictReader(handle)
                    self.assertEqual(reader.fieldnames, headers)
                    self.assertTrue(prohibited_fields.isdisjoint(reader.fieldnames or []))
                    tables[filename] = list(reader)

            self.assertEqual(len(tables["clinics.csv"]), 6)
            self.assertEqual(
                sorted({row["month"] for row in tables["financial_values.csv"]}),
                ["2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08"],
            )
            for filename, rows in tables.items():
                self.assertTrue(rows, filename)
                self.assertTrue(all(row["source"] for row in rows), filename)

    def test_each_case_has_a_complete_expected_answer_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "benchmark"
            self.assertEqual(self.run_generator(output_dir).returncode, 0)

            cases = json.loads((output_dir / "cases.json").read_text())
            expected_scenarios = [
                "Provider PTO",
                "Provider departure",
                "Weather closure",
                "Unexplained visit-volume miss",
                "Labor overtime",
                "Payer-mix and reimbursement shift",
                "Accounting accrual timing",
                "Missing operating input",
                "Seasonal demand decline",
                "Multiple supported drivers",
            ]
            self.assertTrue(all("scenario" not in case for case in cases))
            self.assertTrue(all("core_behavior" not in case for case in cases))

            required_dimensions = {
                "observed_variance",
                "expected_driver_family",
                "driver_roles",
                "timing_classification",
                "epistemic_state",
                "human_review_requirement",
                "forbidden_conclusion",
            }
            gold = {}
            observed_variance_types = set()
            for case in cases:
                fixture = json.loads((output_dir / "gold" / f"{case['case_id']}.json").read_text())
                self.assertEqual(fixture["case_id"], case["case_id"])
                self.assertTrue(required_dimensions.issubset(fixture["expected"]))
                self.assertTrue(fixture["expected"]["forbidden_conclusion"])
                self.assertTrue(fixture["expected"]["human_review_requirement"]["required"])
                self.assertFalse(
                    fixture["expected"]["success_criteria"][
                        "successfully_explained_variance_before_human_review"
                    ]
                )
                observed_variance_types.update(
                    variance["variance_type"]
                    for variance in fixture["expected"]["observed_variance"]
                )
                gold[case["case_id"]] = fixture

            self.assertEqual(
                [gold[f"C{index:02d}"]["scenario"] for index in range(1, 11)],
                expected_scenarios,
            )

            self.assertEqual(observed_variance_types, {
                "financial_variance",
                "operational_metric_variance",
                "forecast_assumption_variance",
            })

            self.assertEqual(gold["C03"]["expected"]["driver_roles"], {
                "primary": "Demand & Volume",
                "contributing": ["Clinic Capacity & Operations"],
                "upstream_context": ["External Disruption"],
            })
            self.assertIn(
                "Weather is the primary driver of the revenue variance.",
                gold["C03"]["expected"]["forbidden_conclusion"],
            )
            self.assertTrue(any(
                state["state"] == "unresolved_driver"
                for state in gold["C04"]["expected"]["epistemic_state"]
            ))
            self.assertTrue(gold["C04"]["expected"]["success_criteria"]["successful_investigation"])
            self.assertFalse(
                gold["C04"]["expected"]["success_criteria"][
                    "successfully_explained_variance_after_gold_human_review"
                ]
            )
            c09_timing = gold["C09"]["expected"]["timing_classification"]
            self.assertEqual(c09_timing["classification"], "temporary")
            self.assertTrue(c09_timing["recurring"])
            self.assertFalse(c09_timing["structural"])
            self.assertEqual(c09_timing["forecast_horizon_end"], "2026-12")
            self.assertIsNone(gold["C10"]["expected"]["contribution_estimate"])

            proposal_fields = {
                "action",
                "metric_or_account_affected",
                "clinic_id",
                "month",
                "actual_vs_forecast_or_expected",
                "candidate_operating_drivers",
                "supporting_evidence_ids",
                "financial_impact_mechanism",
                "timing_classification",
                "confidence_level",
                "unresolved_questions",
                "analyst_approval_status",
            }
            for fixture in gold.values():
                expected = fixture["expected"]
                self.assertTrue(expected["supporting_evidence"])
                self.assertTrue(proposal_fields.issubset(expected["assumption_change_proposal"]))
                primary = expected["driver_roles"]["primary"]
                if primary is not None:
                    self.assertTrue(any(
                        state.get("driver_family") == primary
                        and state["state"] == "supported_driver"
                        for state in expected["epistemic_state"]
                    ))
                self.assertIn(
                    "forecast_horizon_source",
                    expected["timing_classification"],
                )

    def test_gold_variances_and_evidence_are_grounded_in_input_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "benchmark"
            self.assertEqual(self.run_generator(output_dir).returncode, 0)

            def read_csv(filename):
                with (output_dir / "inputs" / filename).open(newline="", encoding="utf-8") as handle:
                    return list(csv.DictReader(handle))

            financial = read_csv("financial_values.csv")
            operational = read_csv("operational_values.csv")
            events = read_csv("operating_events.csv")
            evidence_tables = {
                "financial_values.csv": financial,
                "operational_values.csv": operational,
                "operating_events.csv": events,
            }
            cases = json.loads((output_dir / "cases.json").read_text())

            def matching_row(rows, clinic_id, month, id_field, item_id):
                matches = [
                    row for row in rows
                    if row["clinic_id"] == clinic_id
                    and row["month"] == month
                    and row[id_field] == item_id
                ]
                self.assertEqual(len(matches), 1, (clinic_id, month, item_id))
                return matches[0]

            for case in cases:
                fixture = json.loads(
                    (output_dir / "gold" / f"{case['case_id']}.json").read_text()
                )
                for evidence in fixture["expected"]["supporting_evidence"]:
                    rows = evidence_tables[evidence["input_file"]]
                    matches = [
                        row for row in rows
                        if all(
                            row[field] == str(value)
                            for field, value in evidence["row_selector"].items()
                        )
                    ]
                    self.assertEqual(len(matches), 1, evidence["evidence_id"])
                    self.assertEqual(matches[0]["source"], evidence["source"])

                horizon = fixture["expected"]["timing_classification"][
                    "forecast_horizon_source"
                ]
                horizon_matches = [
                    event for event in events
                    if event["event_id"] == horizon["event_id"]
                    and event["clinic_id"] == case["clinic_id"]
                    and event["source"] == horizon["source"]
                ]
                self.assertEqual(len(horizon_matches), 1)

                for variance in fixture["expected"]["observed_variance"]:
                    if variance["variance_type"] == "financial_variance":
                        row = matching_row(
                            financial,
                            case["clinic_id"],
                            case["month"],
                            "account_id",
                            variance["id"],
                        )
                        actual = float(row["actual_value"])
                        expected = float(row["forecast_value"])
                    else:
                        row = matching_row(
                            operational,
                            case["clinic_id"],
                            case["month"],
                            "metric_id",
                            variance["id"],
                        )
                        actual = float(row["actual_value"])
                        expected = float(row["expected_value"])

                    self.assertEqual(actual, variance["actual"])
                    self.assertEqual(expected, variance["forecast_or_expected"])
                    self.assertEqual(actual - expected, variance["absolute"])
                    percentage = 0 if expected == 0 else round((actual - expected) / expected, 4)
                    self.assertEqual(percentage, variance["percentage"])

            c03_events = [
                event for event in events
                if event["clinic_id"] == "CL003"
                and event["start_date"].startswith("2026-05")
            ]
            self.assertEqual(
                {event["event_type"] for event in c03_events},
                {"weather_disruption", "clinic_closure"},
            )

            c08_visits = [
                row for row in operational
                if row["clinic_id"] == "CL004"
                and row["month"] == "2026-07"
                and row["metric_id"] == "PATIENT_VISITS"
            ]
            self.assertEqual(c08_visits, [])
            self.assertTrue(
                any(
                    event["clinic_id"] == "CL004"
                    and event["event_type"] == "data_feed_failure"
                    for event in events
                )
            )

            c02_future_availability = [
                float(row["actual_value"]) for row in operational
                if row["clinic_id"] == "CL002"
                and row["month"] in {"2026-05", "2026-06", "2026-07", "2026-08"}
                and row["metric_id"] == "PROVIDER_AVAILABLE_DAYS"
            ]
            self.assertEqual(c02_future_availability, [16.0, 16.0, 16.0, 16.0])

            c07_reversal = matching_row(
                financial,
                "CL001",
                "2026-08",
                "account_id",
                "EXP_CLINICAL_LABOR",
            )
            self.assertEqual(float(c07_reversal["actual_value"]), 58000)
            self.assertEqual(float(c07_reversal["forecast_value"]), 78000)

            c10_events = [event for event in events if event["clinic_id"] == "CL005"]
            self.assertTrue({"provider_pto", "equipment_outage"}.issubset(
                {event["event_type"] for event in c10_events}
            ))

    def test_review_queue_selection_is_rule_driven(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "benchmark"
            self.assertEqual(self.run_generator(output_dir).returncode, 0)

            with (output_dir / "inputs" / "financial_values.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                financial = list(csv.DictReader(handle))
            with (output_dir / "inputs" / "review_rules.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                rules = {
                    row["account_or_metric_id"]: row
                    for row in csv.DictReader(handle)
                }
            cases = json.loads((output_dir / "cases.json").read_text())

            self.assertTrue(any(row["always_review"] == "true" for row in rules.values()))
            for case in cases:
                rows = [
                    row for row in financial
                    if row["clinic_id"] == case["clinic_id"]
                    and row["month"] == case["month"]
                    and row["account_id"] == case["target_id"]
                ]
                self.assertEqual(len(rows), 1)
                row = rows[0]
                rule = rules[case["target_id"]]
                actual = float(row["actual_value"])
                forecast = float(row["forecast_value"])
                absolute_trigger = abs(actual - forecast) >= float(rule["absolute_threshold"])
                percentage_trigger = abs((actual - forecast) / forecast) >= float(
                    rule["percentage_threshold"]
                )
                self.assertTrue(absolute_trigger or percentage_trigger)
                self.assertEqual(case["review_queue"]["selected"], True)
                self.assertEqual(case["review_queue"]["selected_by"], "configured_rule")
                self.assertFalse(case["review_queue"]["analyst_override"])

    def test_readme_documents_the_reproducible_evaluation_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "benchmark"
            self.assertEqual(self.run_generator(output_dir).returncode, 0)
            readme = (output_dir / "README.md").read_text(encoding="utf-8")

            required_phrases = {
                "--seed 20260907",
                "actual - forecast",
                "Financial Variance",
                "Operational Metric Variance",
                "Forecast Assumption Variance",
                "Observed Variance",
                "Forbidden Conclusion",
                "system-hidden",
                "No patient-level data",
                "python3 -m unittest discover -s tests -v",
            }
            for phrase in required_phrases:
                self.assertIn(phrase, readme)


if __name__ == "__main__":
    unittest.main()
