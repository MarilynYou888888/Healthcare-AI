#!/usr/bin/env python3
import argparse
import csv
import json
import random
from copy import deepcopy
from pathlib import Path


INPUT_HEADERS = {
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

REQUIRED_GOLD_DIMENSIONS = {
    "observed_variance",
    "expected_driver_family",
    "driver_roles",
    "timing_classification",
    "epistemic_state",
    "human_review_requirement",
    "forbidden_conclusion",
    "supporting_evidence",
    "assumption_change_proposal",
    "success_criteria",
}

REQUIRED_PROPOSAL_FIELDS = {
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

PROHIBITED_PATIENT_LEVEL_FIELDS = {
    "patient_name", "dob", "member_id", "claim_id", "encounter_id",
    "provider_id", "employee_id",
}

MONTHS = ["2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08"]
LOADED_AT = "2026-09-07T00:00:00Z"

CLINICS = [
    {"clinic_id": "CL001", "clinic_name": "Northgate Foot and Ankle", "market_id": "MKT001", "specialty": "Podiatry", "active_from": "2021-01", "active_to": "", "source": "synthetic:clinic_master_v1"},
    {"clinic_id": "CL002", "clinic_name": "Lakeside Foot and Ankle", "market_id": "MKT001", "specialty": "Podiatry", "active_from": "2021-07", "active_to": "", "source": "synthetic:clinic_master_v1"},
    {"clinic_id": "CL003", "clinic_name": "Riverbend Specialty Clinic", "market_id": "MKT001", "specialty": "Podiatry", "active_from": "2022-02", "active_to": "", "source": "synthetic:clinic_master_v1"},
    {"clinic_id": "CL004", "clinic_name": "Oak Park Specialty Clinic", "market_id": "MKT001", "specialty": "Podiatry", "active_from": "2022-09", "active_to": "", "source": "synthetic:clinic_master_v1"},
    {"clinic_id": "CL005", "clinic_name": "Naperville Specialty Clinic", "market_id": "MKT001", "specialty": "Podiatry", "active_from": "2023-01", "active_to": "", "source": "synthetic:clinic_master_v1"},
    {"clinic_id": "CL006", "clinic_name": "Aurora Specialty Clinic", "market_id": "MKT001", "specialty": "Podiatry", "active_from": "2023-06", "active_to": "", "source": "synthetic:clinic_master_v1"},
]

CASE_OVERVIEWS = [
    {"case_id": "C01", "scenario": "Provider PTO", "clinic_id": "CL001", "month": "2026-03", "target_type": "financial_variance", "target_id": "REV_NET_PATIENT", "core_behavior": "Temporary multi-step chain from availability to visits to revenue"},
    {"case_id": "C02", "scenario": "Provider departure", "clinic_id": "CL002", "month": "2026-04", "target_type": "financial_variance", "target_id": "REV_NET_PATIENT", "core_behavior": "Structural capacity loss over the remaining forecast horizon"},
    {"case_id": "C03", "scenario": "Weather closure", "clinic_id": "CL003", "month": "2026-05", "target_type": "financial_variance", "target_id": "REV_NET_PATIENT", "core_behavior": "Upstream external event must not become the primary financial driver"},
    {"case_id": "C04", "scenario": "Unexplained visit-volume miss", "clinic_id": "CL004", "month": "2026-06", "target_type": "financial_variance", "target_id": "REV_NET_PATIENT", "core_behavior": "Insufficient evidence must end unresolved"},
    {"case_id": "C05", "scenario": "Labor overtime", "clinic_id": "CL005", "month": "2026-06", "target_type": "financial_variance", "target_id": "EXP_CLINICAL_LABOR", "core_behavior": "Operating-expense variance linked to overtime evidence"},
    {"case_id": "C06", "scenario": "Payer-mix and reimbursement shift", "clinic_id": "CL006", "month": "2026-07", "target_type": "financial_variance", "target_id": "REV_NET_PATIENT", "core_behavior": "Revenue realization changes while visit volume remains on plan"},
    {"case_id": "C07", "scenario": "Accounting accrual timing", "clinic_id": "CL001", "month": "2026-07", "target_type": "financial_variance", "target_id": "EXP_CLINICAL_LABOR", "core_behavior": "Documented temporary accounting timing difference"},
    {"case_id": "C08", "scenario": "Missing operating input", "clinic_id": "CL004", "month": "2026-07", "target_type": "financial_variance", "target_id": "REV_NET_PATIENT", "core_behavior": "Data quality issue blocks causal interpretation"},
    {"case_id": "C09", "scenario": "Seasonal demand decline", "clinic_id": "CL003", "month": "2026-08", "target_type": "financial_variance", "target_id": "REV_NET_PATIENT", "core_behavior": "Recurring seasonal effect is not structural"},
    {"case_id": "C10", "scenario": "Multiple supported drivers", "clinic_id": "CL005", "month": "2026-08", "target_type": "financial_variance", "target_id": "REV_NET_PATIENT", "core_behavior": "Primary and contributing drivers without fabricated attribution"},
]


def success(after_human_review: bool) -> dict:
    return {
        "successful_investigation": True,
        "successfully_explained_variance_before_human_review": False,
        "successfully_explained_variance_after_gold_human_review": after_human_review,
    }


def human_review(gold_action: str) -> dict:
    return {
        "required": True,
        "analyst_status_at_system_output": "pending",
        "gold_human_action": gold_action,
        "allowed_actions": ["confirm", "reject", "request_more_evidence"],
    }


GOLD_FIXTURES = {
    "C01": {
        "observed_variance": [
            {"variance_type": "financial_variance", "id": "REV_NET_PATIENT", "actual": 154440, "forecast_or_expected": 175500, "absolute": -21060, "percentage": -0.12, "direction": "unfavorable"},
            {"variance_type": "operational_metric_variance", "id": "PATIENT_VISITS", "actual": 792, "forecast_or_expected": 900, "absolute": -108, "percentage": -0.12, "direction": "unfavorable"},
        ],
        "expected_driver_family": ["Demand & Volume", "Provider Availability"],
        "driver_roles": {"primary": "Demand & Volume", "contributing": ["Provider Availability"], "upstream_context": []},
        "timing_classification": {"classification": "temporary", "recurring": False, "structural": False, "forecast_horizon_end": "2026-12"},
        "epistemic_state": [
            {"subject": "Patient visits below expected", "state": "observed_fact"},
            {"subject": "Lower patient visits reduced net patient revenue", "driver_family": "Demand & Volume", "state": "supported_driver"},
            {"subject": "Provider PTO reduced availability", "driver_family": "Provider Availability", "state": "supported_driver"},
        ],
        "human_review_requirement": human_review("confirm"),
        "forbidden_conclusion": ["Provider PTO caused 100% of the revenue decline."],
        "expected_question": ["Did visit volume recover after the provider returned?"],
        "assumption_change_proposal": {"action": "scenario_test", "assumption": "Patient visit volume", "rationale": "Test a one-month reduction and return to baseline after PTO ends."},
        "contribution_estimate": None,
        "success_criteria": success(True),
    },
    "C02": {
        "observed_variance": [
            {"variance_type": "financial_variance", "id": "REV_NET_PATIENT", "actual": 152856, "forecast_or_expected": 191070, "absolute": -38214, "percentage": -0.20, "direction": "unfavorable"},
            {"variance_type": "operational_metric_variance", "id": "PROVIDER_AVAILABLE_DAYS", "actual": 16, "forecast_or_expected": 20, "absolute": -4, "percentage": -0.20, "direction": "unfavorable"},
        ],
        "expected_driver_family": ["Demand & Volume", "Provider Availability"],
        "driver_roles": {"primary": "Demand & Volume", "contributing": ["Provider Availability"], "upstream_context": []},
        "timing_classification": {"classification": "structural", "recurring": False, "structural": True, "forecast_horizon_end": "2026-12"},
        "epistemic_state": [
            {"subject": "Lower patient visits reduced net patient revenue", "driver_family": "Demand & Volume", "state": "supported_driver"},
            {"subject": "Provider departure reduced capacity through the forecast horizon", "driver_family": "Provider Availability", "state": "supported_driver"},
        ],
        "human_review_requirement": human_review("confirm"),
        "forbidden_conclusion": ["Revenue will permanently remain at the April level."],
        "expected_question": ["What replacement start date is included in the approved staffing plan?"],
        "assumption_change_proposal": {"action": "review", "assumption": "Provider capacity and patient visits", "rationale": "Revisit remaining-month capacity until the replacement starts."},
        "contribution_estimate": None,
        "success_criteria": success(True),
    },
    "C03": {
        "observed_variance": [
            {"variance_type": "financial_variance", "id": "REV_NET_PATIENT", "actual": 175875, "forecast_or_expected": 207030, "absolute": -31155, "percentage": -0.1505, "direction": "unfavorable"},
            {"variance_type": "operational_metric_variance", "id": "PATIENT_VISITS", "actual": 875, "forecast_or_expected": 1030, "absolute": -155, "percentage": -0.1505, "direction": "unfavorable"},
        ],
        "expected_driver_family": ["Demand & Volume", "Clinic Capacity & Operations", "External Disruption"],
        "driver_roles": {"primary": "Demand & Volume", "contributing": ["Clinic Capacity & Operations"], "upstream_context": ["External Disruption"]},
        "timing_classification": {"classification": "temporary", "recurring": False, "structural": False, "forecast_horizon_end": "2026-12"},
        "epistemic_state": [
            {"subject": "Weather closed the clinic for two days", "state": "observed_fact"},
            {"subject": "Lower patient visits reduced net patient revenue", "driver_family": "Demand & Volume", "state": "supported_driver"},
            {"subject": "Reduced clinic capacity contributed to lower visits", "driver_family": "Clinic Capacity & Operations", "state": "supported_driver"},
        ],
        "human_review_requirement": human_review("confirm"),
        "forbidden_conclusion": ["Weather is the primary driver of the revenue variance.", "The closure caused 100% of the revenue decline."],
        "expected_question": ["Did deferred visits return in June, or were they lost?"],
        "assumption_change_proposal": {"action": "scenario_test", "assumption": "Patient visit volume", "rationale": "Test a temporary May shortfall with possible June recovery."},
        "contribution_estimate": None,
        "success_criteria": success(True),
    },
    "C04": {
        "observed_variance": [
            {"variance_type": "financial_variance", "id": "REV_NET_PATIENT", "actual": 196656, "forecast_or_expected": 223380, "absolute": -26724, "percentage": -0.1196, "direction": "unfavorable"},
            {"variance_type": "operational_metric_variance", "id": "PATIENT_VISITS", "actual": 964, "forecast_or_expected": 1095, "absolute": -131, "percentage": -0.1196, "direction": "unfavorable"},
        ],
        "expected_driver_family": ["Unresolved"],
        "driver_roles": {"primary": None, "contributing": [], "upstream_context": []},
        "timing_classification": {"classification": "unresolved", "recurring": False, "structural": False, "forecast_horizon_end": "2026-12"},
        "epistemic_state": [
            {"subject": "Provider availability was on plan", "state": "observed_fact"},
            {"subject": "Provider availability explains the shortfall", "driver_family": "Provider Availability", "state": "rejected_driver"},
            {"subject": "Cause of visit shortfall", "driver_family": "Unresolved", "state": "unresolved_driver"},
        ],
        "human_review_requirement": human_review("request_more_evidence"),
        "forbidden_conclusion": ["Lower provider availability caused the decline.", "The volume miss is temporary."],
        "expected_question": ["What operating event or schedule change explains the missing visits?"],
        "assumption_change_proposal": {"action": "review", "assumption": "Patient visit volume", "rationale": "Do not change the baseline until operating evidence is available."},
        "contribution_estimate": None,
        "success_criteria": success(False),
    },
    "C05": {
        "observed_variance": [{"variance_type": "financial_variance", "id": "EXP_CLINICAL_LABOR", "actual": 105000, "forecast_or_expected": 90000, "absolute": 15000, "percentage": 0.1667, "direction": "unfavorable"}],
        "expected_driver_family": ["Workforce & Operating Expense"],
        "driver_roles": {"primary": "Workforce & Operating Expense", "contributing": [], "upstream_context": []},
        "timing_classification": {"classification": "temporary", "recurring": False, "structural": False, "forecast_horizon_end": "2026-12"},
        "epistemic_state": [{"subject": "Overtime increased clinical labor expense", "driver_family": "Workforce & Operating Expense", "state": "supported_driver"}],
        "human_review_requirement": human_review("confirm"),
        "forbidden_conclusion": ["Overtime explains the entire expense variance without an applicable labor-rate bridge."],
        "expected_question": ["Did overtime hours and expense normalize after the vacancy was filled?"],
        "assumption_change_proposal": {"action": "scenario_test", "assumption": "Clinical labor expense", "rationale": "Test temporary overtime until the vacancy is filled."},
        "contribution_estimate": None,
        "success_criteria": success(True),
    },
    "C06": {
        "observed_variance": [
            {"variance_type": "financial_variance", "id": "REV_NET_PATIENT", "actual": 234240, "forecast_or_expected": 256200, "absolute": -21960, "percentage": -0.0857, "direction": "unfavorable"},
            {"variance_type": "operational_metric_variance", "id": "PATIENT_VISITS", "actual": 1220, "forecast_or_expected": 1220, "absolute": 0, "percentage": 0, "direction": "on_plan"},
            {"variance_type": "forecast_assumption_variance", "id": "NET_REVENUE_PER_VISIT", "actual": 192, "forecast_or_expected": 210, "absolute": -18, "percentage": -0.0857, "direction": "unfavorable"},
        ],
        "expected_driver_family": ["Revenue Realization"],
        "driver_roles": {"primary": "Revenue Realization", "contributing": [], "upstream_context": []},
        "timing_classification": {"classification": "structural", "recurring": False, "structural": True, "forecast_horizon_end": "2026-12"},
        "epistemic_state": [
            {"subject": "Payer-mix shift reduced net revenue per visit", "driver_family": "Revenue Realization", "state": "supported_driver"},
            {"subject": "Lower visit volume caused the revenue variance", "driver_family": "Demand & Volume", "state": "rejected_driver"},
        ],
        "human_review_requirement": human_review("confirm"),
        "forbidden_conclusion": ["Lower visit volume caused the revenue variance."],
        "expected_question": ["Is the new payer mix expected to persist through December?"],
        "assumption_change_proposal": {"action": "review", "assumption": "Net revenue per visit", "rationale": "Review the remaining-month rate and payer-mix assumption."},
        "contribution_estimate": None,
        "success_criteria": success(True),
    },
    "C07": {
        "observed_variance": [{"variance_type": "financial_variance", "id": "EXP_CLINICAL_LABOR", "actual": 98000, "forecast_or_expected": 78000, "absolute": 20000, "percentage": 0.2564, "direction": "unfavorable"}],
        "expected_driver_family": ["Accounting & Timing"],
        "driver_roles": {"primary": "Accounting & Timing", "contributing": [], "upstream_context": []},
        "timing_classification": {"classification": "temporary", "recurring": False, "structural": False, "forecast_horizon_end": "2026-12"},
        "epistemic_state": [{"subject": "Documented accrual timing increased July expense", "driver_family": "Accounting & Timing", "state": "supported_driver"}],
        "human_review_requirement": human_review("confirm"),
        "forbidden_conclusion": ["The July expense variance reflects a permanent labor run-rate increase."],
        "expected_question": ["Did the documented accrual reverse in August as scheduled?"],
        "assumption_change_proposal": {"action": "retain", "assumption": "Clinical labor run rate", "rationale": "Retain the baseline if the documented reversal posts in August."},
        "contribution_estimate": {"amount": 20000, "unit": "USD", "basis": "documented accrual scheduled to reverse"},
        "success_criteria": success(True),
    },
    "C08": {
        "observed_variance": [{"variance_type": "financial_variance", "id": "REV_NET_PATIENT", "actual": 170755, "forecast_or_expected": 194040, "absolute": -23285, "percentage": -0.12, "direction": "unfavorable"}],
        "expected_driver_family": ["Data Quality Issue"],
        "driver_roles": {"primary": None, "contributing": [], "upstream_context": ["Data Quality Issue"]},
        "timing_classification": {"classification": "unresolved", "recurring": False, "structural": False, "forecast_horizon_end": "2026-12"},
        "epistemic_state": [{"subject": "July patient-visit input is missing", "state": "observed_fact"}, {"subject": "Business cause of revenue variance", "driver_family": "Unresolved", "state": "unresolved_driver"}],
        "human_review_requirement": human_review("request_more_evidence"),
        "forbidden_conclusion": ["The missing visit record means patient volume was zero.", "Provider availability caused the revenue decline."],
        "expected_question": ["Can the July visit feed be restored and reconciled before causal review?"],
        "assumption_change_proposal": {"action": "review", "assumption": "None until data is restored", "rationale": "Resolve the data-quality issue before changing forecast assumptions."},
        "contribution_estimate": None,
        "success_criteria": success(False),
    },
    "C09": {
        "observed_variance": [
            {"variance_type": "financial_variance", "id": "REV_NET_PATIENT", "actual": 189141, "forecast_or_expected": 210045, "absolute": -20904, "percentage": -0.0995, "direction": "unfavorable"},
            {"variance_type": "operational_metric_variance", "id": "PATIENT_VISITS", "actual": 941, "forecast_or_expected": 1045, "absolute": -104, "percentage": -0.0995, "direction": "unfavorable"},
        ],
        "expected_driver_family": ["Demand & Volume"],
        "driver_roles": {"primary": "Demand & Volume", "contributing": [], "upstream_context": []},
        "timing_classification": {"classification": "temporary", "recurring": True, "structural": False, "forecast_horizon_end": "2026-12"},
        "epistemic_state": [{"subject": "Approved seasonal pattern supports an August demand decline", "driver_family": "Demand & Volume", "state": "supported_driver"}],
        "human_review_requirement": human_review("confirm"),
        "forbidden_conclusion": ["The recurring August decline is a structural demand reduction."],
        "expected_question": ["Does September booking activity support the expected seasonal recovery?"],
        "assumption_change_proposal": {"action": "retain", "assumption": "Post-August patient visit baseline", "rationale": "Retain if forward bookings support seasonal recovery."},
        "contribution_estimate": None,
        "success_criteria": success(True),
    },
    "C10": {
        "observed_variance": [
            {"variance_type": "financial_variance", "id": "REV_NET_PATIENT", "actual": 204930, "forecast_or_expected": 241155, "absolute": -36225, "percentage": -0.1502, "direction": "unfavorable"},
            {"variance_type": "operational_metric_variance", "id": "PATIENT_VISITS", "actual": 990, "forecast_or_expected": 1165, "absolute": -175, "percentage": -0.1502, "direction": "unfavorable"},
        ],
        "expected_driver_family": ["Demand & Volume", "Provider Availability", "Clinic Capacity & Operations"],
        "driver_roles": {"primary": "Demand & Volume", "contributing": ["Provider Availability", "Clinic Capacity & Operations"], "upstream_context": []},
        "timing_classification": {"classification": "temporary", "recurring": False, "structural": False, "forecast_horizon_end": "2026-12"},
        "epistemic_state": [
            {"subject": "Lower patient visits reduced net patient revenue", "driver_family": "Demand & Volume", "state": "supported_driver"},
            {"subject": "Reduced provider availability contributed to lower visits", "driver_family": "Provider Availability", "state": "supported_driver"},
            {"subject": "Equipment outage reduced clinic capacity", "driver_family": "Clinic Capacity & Operations", "state": "supported_driver"},
        ],
        "human_review_requirement": human_review("confirm"),
        "forbidden_conclusion": ["Provider availability caused 60% of the revenue decline.", "The equipment outage caused 40% of the revenue decline."],
        "expected_question": ["How did appointment cancellations overlap with provider PTO and the equipment outage?"],
        "assumption_change_proposal": {"action": "scenario_test", "assumption": "Patient visit volume", "rationale": "Test a temporary August reduction without allocating unsupported contribution percentages."},
        "contribution_estimate": None,
        "success_criteria": success(True),
    },
}


def evidence_item(
    evidence_id: str,
    input_file: str,
    source: str,
    supports: str,
    **row_selector,
) -> dict:
    return {
        "evidence_id": evidence_id,
        "input_file": input_file,
        "row_selector": row_selector,
        "source": source,
        "supports": supports,
    }


CASE_EVIDENCE = {
    "C01": [
        evidence_item("C01-FIN-REV", "financial_values.csv", "synthetic:financial_model_v1", "Revenue variance", clinic_id="CL001", month="2026-03", account_id="REV_NET_PATIENT"),
        evidence_item("C01-OP-VISITS", "operational_values.csv", "synthetic:operations_dashboard_v1", "Demand and volume driver", clinic_id="CL001", month="2026-03", metric_id="PATIENT_VISITS"),
        evidence_item("C01-OP-AVAIL", "operational_values.csv", "synthetic:provider_capacity_summary_v1", "Provider availability driver", clinic_id="CL001", month="2026-03", metric_id="PROVIDER_AVAILABLE_DAYS"),
        evidence_item("C01-OP-PTO", "operational_values.csv", "synthetic:provider_capacity_summary_v1", "Provider PTO context", clinic_id="CL001", month="2026-03", metric_id="PROVIDER_PTO_DAYS"),
        evidence_item("C01-EVT-PTO", "operating_events.csv", "synthetic:provider_schedule_v1", "Temporary PTO timing", event_id="EVT001"),
    ],
    "C02": [
        evidence_item("C02-FIN-REV", "financial_values.csv", "synthetic:financial_model_v1", "Revenue variance", clinic_id="CL002", month="2026-04", account_id="REV_NET_PATIENT"),
        evidence_item("C02-OP-VISITS", "operational_values.csv", "synthetic:operations_dashboard_v1", "Demand and volume driver", clinic_id="CL002", month="2026-04", metric_id="PATIENT_VISITS"),
        evidence_item("C02-OP-AVAIL-APR", "operational_values.csv", "synthetic:provider_capacity_summary_v1", "Initial capacity loss", clinic_id="CL002", month="2026-04", metric_id="PROVIDER_AVAILABLE_DAYS"),
        evidence_item("C02-OP-AVAIL-AUG", "operational_values.csv", "synthetic:provider_capacity_summary_v1", "Capacity loss persists in closed months", clinic_id="CL002", month="2026-08", metric_id="PROVIDER_AVAILABLE_DAYS"),
        evidence_item("C02-EVT-DEPART", "operating_events.csv", "synthetic:workforce_plan_v1", "No replacement within forecast horizon", event_id="EVT002"),
    ],
    "C03": [
        evidence_item("C03-FIN-REV", "financial_values.csv", "synthetic:financial_model_v1", "Revenue variance", clinic_id="CL003", month="2026-05", account_id="REV_NET_PATIENT"),
        evidence_item("C03-OP-VISITS", "operational_values.csv", "synthetic:operations_dashboard_v1", "Demand and volume primary driver", clinic_id="CL003", month="2026-05", metric_id="PATIENT_VISITS"),
        evidence_item("C03-OP-CLOSURE", "operational_values.csv", "synthetic:operations_calendar_v1", "Clinic capacity contributing driver", clinic_id="CL003", month="2026-05", metric_id="CLINIC_CLOSURE_DAYS"),
        evidence_item("C03-EVT-WEATHER", "operating_events.csv", "synthetic:operations_incident_log_v1", "External disruption upstream context", event_id="EVT003"),
        evidence_item("C03-EVT-CLOSURE", "operating_events.csv", "synthetic:operations_calendar_v1", "Documented closure", event_id="EVT004"),
    ],
    "C04": [
        evidence_item("C04-FIN-REV", "financial_values.csv", "synthetic:financial_model_v1", "Revenue variance", clinic_id="CL004", month="2026-06", account_id="REV_NET_PATIENT"),
        evidence_item("C04-OP-VISITS", "operational_values.csv", "synthetic:operations_dashboard_v1", "Visit-volume shortfall", clinic_id="CL004", month="2026-06", metric_id="PATIENT_VISITS"),
        evidence_item("C04-OP-AVAIL", "operational_values.csv", "synthetic:provider_capacity_summary_v1", "Provider availability candidate is not supported", clinic_id="CL004", month="2026-06", metric_id="PROVIDER_AVAILABLE_DAYS"),
    ],
    "C05": [
        evidence_item("C05-FIN-LABOR", "financial_values.csv", "synthetic:financial_model_v1", "Labor expense variance", clinic_id="CL005", month="2026-06", account_id="EXP_CLINICAL_LABOR"),
        evidence_item("C05-OP-OT", "operational_values.csv", "synthetic:workforce_summary_v1", "Overtime driver", clinic_id="CL005", month="2026-06", metric_id="OVERTIME_HOURS"),
        evidence_item("C05-EVT-VACANCY", "operating_events.csv", "synthetic:workforce_plan_v1", "Temporary vacancy timing", event_id="EVT005"),
    ],
    "C06": [
        evidence_item("C06-FIN-REV", "financial_values.csv", "synthetic:financial_model_v1", "Revenue variance", clinic_id="CL006", month="2026-07", account_id="REV_NET_PATIENT"),
        evidence_item("C06-OP-VISITS", "operational_values.csv", "synthetic:operations_dashboard_v1", "Visit volume remained on plan", clinic_id="CL006", month="2026-07", metric_id="PATIENT_VISITS"),
        evidence_item("C06-OP-RATE", "operational_values.csv", "synthetic:revenue_cycle_summary_v1", "Net revenue per visit assumption variance", clinic_id="CL006", month="2026-07", metric_id="NET_REVENUE_PER_VISIT"),
        evidence_item("C06-OP-MIX", "operational_values.csv", "synthetic:revenue_cycle_summary_v1", "Payer-mix shift", clinic_id="CL006", month="2026-07", metric_id="COMMERCIAL_PAYER_MIX"),
        evidence_item("C06-EVT-CONTRACT", "operating_events.csv", "synthetic:revenue_cycle_review_v1", "Persistence through forecast horizon", event_id="EVT006"),
    ],
    "C07": [
        evidence_item("C07-FIN-JUL", "financial_values.csv", "synthetic:financial_model_v1", "July labor expense variance", clinic_id="CL001", month="2026-07", account_id="EXP_CLINICAL_LABOR"),
        evidence_item("C07-FIN-AUG", "financial_values.csv", "synthetic:financial_model_v1", "Documented August reversal", clinic_id="CL001", month="2026-08", account_id="EXP_CLINICAL_LABOR"),
        evidence_item("C07-EVT-ACCRUAL", "operating_events.csv", "synthetic:accounting_close_log_v1", "Accrual amount and reversal timing", event_id="EVT007"),
    ],
    "C08": [
        evidence_item("C08-FIN-REV", "financial_values.csv", "synthetic:financial_model_v1", "Revenue variance", clinic_id="CL004", month="2026-07", account_id="REV_NET_PATIENT"),
        evidence_item("C08-EVT-DQ", "operating_events.csv", "synthetic:data_quality_log_v1", "Visit input was withheld after validation failure", event_id="EVT008"),
    ],
    "C09": [
        evidence_item("C09-FIN-REV", "financial_values.csv", "synthetic:financial_model_v1", "Revenue variance", clinic_id="CL003", month="2026-08", account_id="REV_NET_PATIENT"),
        evidence_item("C09-OP-VISITS", "operational_values.csv", "synthetic:operations_dashboard_v1", "Recurring visit-volume decline", clinic_id="CL003", month="2026-08", metric_id="PATIENT_VISITS"),
        evidence_item("C09-EVT-SEASON", "operating_events.csv", "synthetic:approved_seasonality_calendar_v1", "Approved recurring seasonal pattern", event_id="EVT009"),
    ],
    "C10": [
        evidence_item("C10-FIN-REV", "financial_values.csv", "synthetic:financial_model_v1", "Revenue variance", clinic_id="CL005", month="2026-08", account_id="REV_NET_PATIENT"),
        evidence_item("C10-OP-VISITS", "operational_values.csv", "synthetic:operations_dashboard_v1", "Demand and volume primary driver", clinic_id="CL005", month="2026-08", metric_id="PATIENT_VISITS"),
        evidence_item("C10-OP-AVAIL", "operational_values.csv", "synthetic:provider_capacity_summary_v1", "Provider availability contributing driver", clinic_id="CL005", month="2026-08", metric_id="PROVIDER_AVAILABLE_DAYS"),
        evidence_item("C10-OP-CLOSURE", "operational_values.csv", "synthetic:operations_calendar_v1", "Clinic capacity contributing driver", clinic_id="CL005", month="2026-08", metric_id="CLINIC_CLOSURE_DAYS"),
        evidence_item("C10-EVT-PTO", "operating_events.csv", "synthetic:provider_schedule_v1", "Provider PTO context", event_id="EVT010"),
        evidence_item("C10-EVT-OUTAGE", "operating_events.csv", "synthetic:operations_incident_log_v1", "Equipment outage context", event_id="EVT011"),
    ],
}

FINANCIAL_IMPACT_MECHANISMS = {
    "C01": "Fewer visits at a stable revenue-per-visit rate reduce net patient revenue.",
    "C02": "Lower provider capacity reduces available appointments, visits, and net patient revenue.",
    "C03": "Clinic closure reduces appointment capacity; lower visits then reduce net patient revenue.",
    "C04": "Lower visits align with lower revenue, but the operating cause of the visit shortfall is unresolved.",
    "C05": "Additional overtime hours increase clinical labor expense.",
    "C06": "Stable visits at lower net revenue per visit reduce net patient revenue.",
    "C07": "A July accrual raises expense and its documented August reversal offsets the timing difference.",
    "C08": "The revenue variance is observed, but missing visit input blocks a supported operating mechanism.",
    "C09": "A recurring seasonal visit decline reduces August net patient revenue.",
    "C10": "Lower visits reduce net patient revenue; PTO and an equipment outage both constrain visit capacity.",
}

CONFIDENCE_LEVELS = {
    "C01": "moderate",
    "C02": "high",
    "C03": "high",
    "C04": "low",
    "C05": "moderate",
    "C06": "high",
    "C07": "high",
    "C08": "low",
    "C09": "moderate",
    "C10": "moderate",
}


def enrich_expected_contract(case: dict) -> dict:
    case_id = case["case_id"]
    expected = deepcopy(GOLD_FIXTURES[case_id])
    evidence = deepcopy(CASE_EVIDENCE[case_id])
    horizon_event_id = f"FCT{int(case['clinic_id'][2:]):03d}"
    expected["supporting_evidence"] = evidence
    expected["timing_classification"]["forecast_horizon_source"] = {
        "event_id": horizon_event_id,
        "source": "synthetic:forecast_governance_log_v1",
    }

    proposal = expected["assumption_change_proposal"]
    primary = expected["driver_roles"]["primary"]
    candidate_drivers = (
        ([primary] if primary else [])
        + expected["driver_roles"]["contributing"]
        + expected["driver_roles"]["upstream_context"]
    )
    if not candidate_drivers:
        candidate_drivers = expected["expected_driver_family"]
    proposal.update({
        "metric_or_account_affected": case["target_id"],
        "clinic_id": case["clinic_id"],
        "month": case["month"],
        "actual_vs_forecast_or_expected": deepcopy(expected["observed_variance"]),
        "candidate_operating_drivers": candidate_drivers,
        "supporting_evidence_ids": [item["evidence_id"] for item in evidence],
        "financial_impact_mechanism": FINANCIAL_IMPACT_MECHANISMS[case_id],
        "timing_classification": expected["timing_classification"]["classification"],
        "confidence_level": CONFIDENCE_LEVELS[case_id],
        "unresolved_questions": deepcopy(expected["expected_question"]),
        "analyst_approval_status": expected["human_review_requirement"][
            "analyst_status_at_system_output"
        ],
    })
    return expected


def write_csv(path: Path, headers: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def update_value_row(
    rows: list[dict],
    clinic_id: str,
    month: str,
    id_field: str,
    item_id: str,
    **updates,
) -> None:
    matches = [
        row for row in rows
        if row["clinic_id"] == clinic_id
        and row["month"] == month
        and row[id_field] == item_id
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one row for {clinic_id}/{month}/{item_id}")
    matches[0].update(updates)


def build_case_overviews(input_rows: dict[str, list[dict]]) -> list[dict]:
    financial_lookup = {
        (row["clinic_id"], row["month"], row["account_id"]): row
        for row in input_rows["financial_values.csv"]
    }
    rule_lookup = {
        row["account_or_metric_id"]: row
        for row in input_rows["review_rules.csv"]
    }
    cases = []
    for overview in CASE_OVERVIEWS:
        row = financial_lookup[
            (overview["clinic_id"], overview["month"], overview["target_id"])
        ]
        rule = rule_lookup[overview["target_id"]]
        actual = float(row["actual_value"])
        forecast = float(row["forecast_value"])
        absolute_variance = abs(actual - forecast)
        percentage_variance = 0 if forecast == 0 else absolute_variance / abs(forecast)
        reasons = []
        if absolute_variance >= float(rule["absolute_threshold"]):
            reasons.append("absolute_threshold")
        if percentage_variance >= float(rule["percentage_threshold"]):
            reasons.append("percentage_threshold")
        if rule["always_review"] == "true":
            reasons.append("critical_metric_rule")

        case = {
            field: overview[field]
            for field in (
                "case_id",
                "clinic_id",
                "month",
                "target_type",
                "target_id",
            )
        }
        case["review_queue"] = {
            "selected": bool(reasons),
            "selected_by": "configured_rule" if reasons else None,
            "selection_reasons": reasons,
            "analyst_override": False,
        }
        cases.append(case)
    return cases


def build_input_rows(seed: int) -> dict[str, list[dict]]:
    rng = random.Random(seed)
    financial_rows = []
    operational_rows = []
    for clinic_index, clinic in enumerate(CLINICS):
        base_visits = 900 + clinic_index * 60
        base_rate = 195 + clinic_index * 3
        base_labor = 78_000 + clinic_index * 3_000
        for month_index, month in enumerate(MONTHS):
            expected_visits = base_visits + month_index * 5
            forecast_revenue = expected_visits * base_rate
            actual_visits = expected_visits + rng.randint(-12, 12)
            actual_rate = base_rate + rng.randint(-1, 1)
            financial_rows.extend([
                {
                    "clinic_id": clinic["clinic_id"], "month": month,
                    "account_id": "REV_NET_PATIENT", "account_name": "Net patient revenue",
                    "actual_value": actual_visits * actual_rate, "forecast_value": forecast_revenue,
                    "unit": "currency", "currency": "USD", "source": "synthetic:financial_model_v1",
                    "loaded_at": LOADED_AT,
                },
                {
                    "clinic_id": clinic["clinic_id"], "month": month,
                    "account_id": "EXP_CLINICAL_LABOR", "account_name": "Clinical labor expense",
                    "actual_value": base_labor + rng.randint(-1_000, 1_000), "forecast_value": base_labor,
                    "unit": "currency", "currency": "USD", "source": "synthetic:financial_model_v1",
                    "loaded_at": LOADED_AT,
                },
            ])
            operational_rows.extend([
                {
                    "clinic_id": clinic["clinic_id"], "month": month,
                    "metric_id": "PATIENT_VISITS", "metric_name": "Patient visits",
                    "actual_value": actual_visits, "expected_value": expected_visits, "unit": "visits",
                    "source": "synthetic:operations_dashboard_v1", "loaded_at": LOADED_AT,
                },
                {
                    "clinic_id": clinic["clinic_id"], "month": month,
                    "metric_id": "PROVIDER_AVAILABLE_DAYS", "metric_name": "Provider available days",
                    "actual_value": 20, "expected_value": 20, "unit": "provider_days",
                    "source": "synthetic:provider_capacity_summary_v1", "loaded_at": LOADED_AT,
                },
                {
                    "clinic_id": clinic["clinic_id"], "month": month,
                    "metric_id": "PROVIDER_PTO_DAYS", "metric_name": "Provider PTO days",
                    "actual_value": 0, "expected_value": 0, "unit": "provider_days",
                    "source": "synthetic:provider_capacity_summary_v1", "loaded_at": LOADED_AT,
                },
                {
                    "clinic_id": clinic["clinic_id"], "month": month,
                    "metric_id": "CLINIC_CLOSURE_DAYS", "metric_name": "Clinic closure days",
                    "actual_value": 0, "expected_value": 0, "unit": "clinic_days",
                    "source": "synthetic:operations_calendar_v1", "loaded_at": LOADED_AT,
                },
                {
                    "clinic_id": clinic["clinic_id"], "month": month,
                    "metric_id": "OVERTIME_HOURS", "metric_name": "Overtime hours",
                    "actual_value": 40 + rng.randint(-5, 5), "expected_value": 40, "unit": "hours",
                    "source": "synthetic:workforce_summary_v1", "loaded_at": LOADED_AT,
                },
                {
                    "clinic_id": clinic["clinic_id"], "month": month,
                    "metric_id": "NET_REVENUE_PER_VISIT", "metric_name": "Net revenue per visit",
                    "actual_value": actual_rate, "expected_value": base_rate, "unit": "USD_per_visit",
                    "source": "synthetic:revenue_cycle_summary_v1", "loaded_at": LOADED_AT,
                },
                {
                    "clinic_id": clinic["clinic_id"], "month": month,
                    "metric_id": "COMMERCIAL_PAYER_MIX", "metric_name": "Commercial payer mix",
                    "actual_value": 0.45, "expected_value": 0.45, "unit": "proportion",
                    "source": "synthetic:revenue_cycle_summary_v1", "loaded_at": LOADED_AT,
                },
            ])

    financial_overrides = {
        ("CL001", "2026-03", "REV_NET_PATIENT"): (154440, 175500),
        ("CL002", "2026-04", "REV_NET_PATIENT"): (152856, 191070),
        ("CL002", "2026-05", "REV_NET_PATIENT"): (153648, 192060),
        ("CL002", "2026-06", "REV_NET_PATIENT"): (154440, 193050),
        ("CL002", "2026-07", "REV_NET_PATIENT"): (155232, 194040),
        ("CL002", "2026-08", "REV_NET_PATIENT"): (156024, 195030),
        ("CL003", "2026-05", "REV_NET_PATIENT"): (175875, 207030),
        ("CL004", "2026-06", "REV_NET_PATIENT"): (196656, 223380),
        ("CL005", "2026-06", "EXP_CLINICAL_LABOR"): (105000, 90000),
        ("CL006", "2026-07", "REV_NET_PATIENT"): (234240, 256200),
        ("CL001", "2026-07", "EXP_CLINICAL_LABOR"): (98000, 78000),
        ("CL001", "2026-08", "EXP_CLINICAL_LABOR"): (58000, 78000),
        ("CL004", "2026-07", "REV_NET_PATIENT"): (170755, 194040),
        ("CL003", "2026-08", "REV_NET_PATIENT"): (189141, 210045),
        ("CL005", "2026-08", "REV_NET_PATIENT"): (204930, 241155),
    }
    for (clinic_id, month, account_id), values in financial_overrides.items():
        update_value_row(
            financial_rows,
            clinic_id,
            month,
            "account_id",
            account_id,
            actual_value=values[0],
            forecast_value=values[1],
        )

    operational_overrides = {
        ("CL001", "2026-03", "PATIENT_VISITS"): (792, 900),
        ("CL001", "2026-03", "PROVIDER_AVAILABLE_DAYS"): (18, 20),
        ("CL001", "2026-03", "PROVIDER_PTO_DAYS"): (2, 0),
        ("CL002", "2026-04", "PATIENT_VISITS"): (772, 965),
        ("CL002", "2026-04", "PROVIDER_AVAILABLE_DAYS"): (16, 20),
        ("CL002", "2026-05", "PATIENT_VISITS"): (776, 970),
        ("CL002", "2026-05", "PROVIDER_AVAILABLE_DAYS"): (16, 20),
        ("CL002", "2026-06", "PATIENT_VISITS"): (780, 975),
        ("CL002", "2026-06", "PROVIDER_AVAILABLE_DAYS"): (16, 20),
        ("CL002", "2026-07", "PATIENT_VISITS"): (784, 980),
        ("CL002", "2026-07", "PROVIDER_AVAILABLE_DAYS"): (16, 20),
        ("CL002", "2026-08", "PATIENT_VISITS"): (788, 985),
        ("CL002", "2026-08", "PROVIDER_AVAILABLE_DAYS"): (16, 20),
        ("CL003", "2026-05", "PATIENT_VISITS"): (875, 1030),
        ("CL003", "2026-05", "CLINIC_CLOSURE_DAYS"): (2, 0),
        ("CL004", "2026-06", "PATIENT_VISITS"): (964, 1095),
        ("CL005", "2026-06", "OVERTIME_HOURS"): (160, 40),
        ("CL006", "2026-07", "PATIENT_VISITS"): (1220, 1220),
        ("CL006", "2026-07", "NET_REVENUE_PER_VISIT"): (192, 210),
        ("CL006", "2026-07", "COMMERCIAL_PAYER_MIX"): (0.32, 0.45),
        ("CL003", "2026-08", "PATIENT_VISITS"): (941, 1045),
        ("CL003", "2026-08", "NET_REVENUE_PER_VISIT"): (201, 201),
        ("CL005", "2026-08", "PATIENT_VISITS"): (990, 1165),
        ("CL005", "2026-08", "NET_REVENUE_PER_VISIT"): (207, 207),
        ("CL005", "2026-08", "PROVIDER_AVAILABLE_DAYS"): (18, 20),
        ("CL005", "2026-08", "PROVIDER_PTO_DAYS"): (1, 0),
        ("CL005", "2026-08", "CLINIC_CLOSURE_DAYS"): (2, 0),
    }
    for (clinic_id, month, metric_id), values in operational_overrides.items():
        update_value_row(
            operational_rows,
            clinic_id,
            month,
            "metric_id",
            metric_id,
            actual_value=values[0],
            expected_value=values[1],
        )

    operational_rows = [
        row for row in operational_rows
        if not (
            row["clinic_id"] == "CL004"
            and row["month"] == "2026-07"
            and row["metric_id"] == "PATIENT_VISITS"
        )
    ]

    operating_events = [
        {
            "event_id": f"FCT{index:03d}",
            "clinic_id": clinic["clinic_id"],
            "event_type": "forecast_horizon",
            "start_date": "2026-09-01",
            "end_date": "2026-12-31",
            "description": "Latest Approved Forecast extends through December 2026.",
            "source": "synthetic:forecast_governance_log_v1",
            "reported_at": LOADED_AT,
        }
        for index, clinic in enumerate(CLINICS, start=1)
    ] + [
        {
            "event_id": "EVT001", "clinic_id": "CL001", "event_type": "provider_pto",
            "start_date": "2026-03-10", "end_date": "2026-03-11",
            "description": "Approved provider PTO reduced scheduled provider availability by two days.",
            "source": "synthetic:provider_schedule_v1", "reported_at": "2026-03-01T12:00:00Z",
        },
        {
            "event_id": "EVT002", "clinic_id": "CL002", "event_type": "provider_departure",
            "start_date": "2026-04-05", "end_date": "2026-12-31",
            "description": "Provider departed; no replacement start date is approved within the forecast horizon.",
            "source": "synthetic:workforce_plan_v1", "reported_at": "2026-04-06T15:00:00Z",
        },
        {
            "event_id": "EVT003", "clinic_id": "CL003", "event_type": "weather_disruption",
            "start_date": "2026-05-15", "end_date": "2026-05-16",
            "description": "Severe weather affected local travel and clinic operations.",
            "source": "synthetic:operations_incident_log_v1", "reported_at": "2026-05-15T09:00:00Z",
        },
        {
            "event_id": "EVT004", "clinic_id": "CL003", "event_type": "clinic_closure",
            "start_date": "2026-05-15", "end_date": "2026-05-16",
            "description": "Clinic closed for two days because of the documented weather disruption.",
            "source": "synthetic:operations_calendar_v1", "reported_at": "2026-05-16T18:00:00Z",
        },
        {
            "event_id": "EVT005", "clinic_id": "CL005", "event_type": "temporary_staffing_vacancy",
            "start_date": "2026-06-01", "end_date": "2026-06-30",
            "description": "Temporary clinical staffing vacancy required approved overtime coverage.",
            "source": "synthetic:workforce_plan_v1", "reported_at": "2026-06-02T14:00:00Z",
        },
        {
            "event_id": "EVT006", "clinic_id": "CL006", "event_type": "payer_contract_change",
            "start_date": "2026-07-01", "end_date": "2026-12-31",
            "description": "Payer mix shifted toward lower-reimbursing plans and is expected to persist through December.",
            "source": "synthetic:revenue_cycle_review_v1", "reported_at": "2026-08-10T16:00:00Z",
        },
        {
            "event_id": "EVT007", "clinic_id": "CL001", "event_type": "accrual_timing",
            "start_date": "2026-07-31", "end_date": "2026-08-31",
            "description": "A documented USD 20,000 labor accrual posted in July and is scheduled to reverse in August.",
            "source": "synthetic:accounting_close_log_v1", "reported_at": "2026-08-05T17:00:00Z",
        },
        {
            "event_id": "EVT008", "clinic_id": "CL004", "event_type": "data_feed_failure",
            "start_date": "2026-07-01", "end_date": "2026-07-31",
            "description": "The July patient-visit aggregate failed validation and was withheld from the dataset.",
            "source": "synthetic:data_quality_log_v1", "reported_at": "2026-08-04T11:00:00Z",
        },
        {
            "event_id": "EVT009", "clinic_id": "CL003", "event_type": "seasonal_pattern",
            "start_date": "2026-08-01", "end_date": "2026-08-31",
            "description": "The approved seasonal calendar identifies a recurring August demand decline with September recovery.",
            "source": "synthetic:approved_seasonality_calendar_v1", "reported_at": "2026-01-15T13:00:00Z",
        },
        {
            "event_id": "EVT010", "clinic_id": "CL005", "event_type": "provider_pto",
            "start_date": "2026-08-11", "end_date": "2026-08-11",
            "description": "Approved provider PTO reduced August appointment capacity.",
            "source": "synthetic:provider_schedule_v1", "reported_at": "2026-08-01T12:00:00Z",
        },
        {
            "event_id": "EVT011", "clinic_id": "CL005", "event_type": "equipment_outage",
            "start_date": "2026-08-20", "end_date": "2026-08-21",
            "description": "A clinical equipment outage caused cancellations; overlap with PTO is not quantified.",
            "source": "synthetic:operations_incident_log_v1", "reported_at": "2026-08-22T10:00:00Z",
        },
    ]

    return {
        "clinics.csv": CLINICS,
        "financial_values.csv": financial_rows,
        "operational_values.csv": operational_rows,
        "operating_events.csv": operating_events,
        "review_rules.csv": [
            {"rule_id": "RR001", "account_or_metric_id": "REV_NET_PATIENT", "absolute_threshold": 15000, "percentage_threshold": 0.05, "always_review": "false", "effective_from": "2026-01", "effective_to": "", "source": "synthetic:review_policy_v1"},
            {"rule_id": "RR002", "account_or_metric_id": "EXP_CLINICAL_LABOR", "absolute_threshold": 10000, "percentage_threshold": 0.10, "always_review": "false", "effective_from": "2026-01", "effective_to": "", "source": "synthetic:review_policy_v1"},
            {"rule_id": "RR003", "account_or_metric_id": "PATIENT_VISITS", "absolute_threshold": 50, "percentage_threshold": 0.05, "always_review": "false", "effective_from": "2026-01", "effective_to": "", "source": "synthetic:review_policy_v1"},
            {"rule_id": "RR004", "account_or_metric_id": "PROVIDER_AVAILABLE_DAYS", "absolute_threshold": 1, "percentage_threshold": 0.05, "always_review": "true", "effective_from": "2026-01", "effective_to": "", "source": "synthetic:review_policy_v1"},
        ],
    }


def read_csv_rows(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_generated_benchmark(output_dir: Path) -> None:
    inputs_dir = output_dir / "inputs"
    gold_dir = output_dir / "gold"
    actual_input_names = {path.name for path in inputs_dir.glob("*.csv")}
    require(actual_input_names == set(INPUT_HEADERS), "Input table set does not match the contract")

    input_rows = {}
    for filename, expected_headers in INPUT_HEADERS.items():
        headers, rows = read_csv_rows(inputs_dir / filename)
        require(headers == expected_headers, f"Unexpected headers in {filename}")
        require(bool(rows), f"{filename} must not be empty")
        require(
            PROHIBITED_PATIENT_LEVEL_FIELDS.isdisjoint(headers),
            f"Patient-level field found in {filename}",
        )
        require(all(row["source"] for row in rows), f"Missing source in {filename}")
        input_rows[filename] = rows

    cases = json.loads((output_dir / "cases.json").read_text(encoding="utf-8"))
    require(len(cases) == 10, "Expected exactly 10 benchmark cases")
    require(
        [case["case_id"] for case in cases] == [f"C{index:02d}" for index in range(1, 11)],
        "Case identifiers must be C01 through C10",
    )
    require(
        all("scenario" not in case and "core_behavior" not in case for case in cases),
        "Public case manifest must not reveal expected conclusions",
    )

    financial_lookup = {
        (row["clinic_id"], row["month"], row["account_id"]): row
        for row in input_rows["financial_values.csv"]
    }
    operational_lookup = {
        (row["clinic_id"], row["month"], row["metric_id"]): row
        for row in input_rows["operational_values.csv"]
    }
    variance_types = set()
    for case in cases:
        fixture_path = gold_dir / f"{case['case_id']}.json"
        require(fixture_path.is_file(), f"Missing gold fixture for {case['case_id']}")
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        expected = fixture["expected"]
        require(
            REQUIRED_GOLD_DIMENSIONS.issubset(expected),
            f"Incomplete expected-answer contract for {case['case_id']}",
        )
        require(bool(expected["forbidden_conclusion"]), f"Missing forbidden conclusion for {case['case_id']}")
        require(expected["human_review_requirement"]["required"] is True, "Human review must be required")
        require(
            REQUIRED_PROPOSAL_FIELDS.issubset(expected["assumption_change_proposal"]),
            f"Incomplete assumption-change proposal for {case['case_id']}",
        )
        success_criteria = expected["success_criteria"]
        require(success_criteria["successful_investigation"] is True, "Investigation benchmark must be successful")
        require(
            success_criteria["successfully_explained_variance_before_human_review"] is False,
            "No variance may be successfully explained before human review",
        )

        for variance in expected["observed_variance"]:
            variance_types.add(variance["variance_type"])
            lookup = financial_lookup if variance["variance_type"] == "financial_variance" else operational_lookup
            id_field = "account_id" if variance["variance_type"] == "financial_variance" else "metric_id"
            key = (case["clinic_id"], case["month"], variance["id"])
            require(key in lookup, f"Observed variance lacks input row: {case['case_id']} {variance['id']}")
            row = lookup[key]
            actual = float(row["actual_value"])
            expected_value = float(
                row["forecast_value"] if id_field == "account_id" else row["expected_value"]
            )
            percentage = 0 if expected_value == 0 else round((actual - expected_value) / expected_value, 4)
            require(actual == variance["actual"], f"Actual mismatch in {case['case_id']}")
            require(expected_value == variance["forecast_or_expected"], f"Comparator mismatch in {case['case_id']}")
            require(actual - expected_value == variance["absolute"], f"Absolute variance mismatch in {case['case_id']}")
            require(percentage == variance["percentage"], f"Percentage variance mismatch in {case['case_id']}")

        primary = expected["driver_roles"]["primary"]
        if primary is not None:
            require(
                any(
                    state.get("driver_family") == primary
                    and state["state"] == "supported_driver"
                    for state in expected["epistemic_state"]
                ),
                f"Primary driver lacks supported state in {case['case_id']}",
            )

        for evidence in expected["supporting_evidence"]:
            source_rows = input_rows[evidence["input_file"]]
            matches = [
                row for row in source_rows
                if all(
                    row[field] == str(value)
                    for field, value in evidence["row_selector"].items()
                )
            ]
            require(len(matches) == 1, f"Evidence reference does not resolve: {evidence['evidence_id']}")
            require(matches[0]["source"] == evidence["source"], f"Evidence source mismatch: {evidence['evidence_id']}")

        horizon = expected["timing_classification"]["forecast_horizon_source"]
        horizon_matches = [
            event for event in input_rows["operating_events.csv"]
            if event["event_id"] == horizon["event_id"]
            and event["clinic_id"] == case["clinic_id"]
            and event["source"] == horizon["source"]
        ]
        require(len(horizon_matches) == 1, f"Forecast horizon source does not resolve: {case['case_id']}")

    require(
        variance_types == {
            "financial_variance",
            "operational_metric_variance",
            "forecast_assumption_variance",
        },
        "Benchmark must distinguish all three variance types",
    )
    require(len(list(gold_dir.glob("C*.json"))) == 10, "Expected exactly 10 gold fixtures")


def render_readme(seed: int) -> str:
    return f"""# Provider FP&A Synthetic Benchmark

This directory is a deterministic, reproducible evaluation fixture for the
clinic-month Provider FP&A MVP. It tests analytical boundaries, not prose
quality. All organizations, clinics, values, and events are fictional.

## Generate and validate

From the repository root:

```bash
python3 scripts/generate_synthetic_benchmark.py \\
  --output-dir data/synthetic_benchmark \\
  --seed {seed}
```

The generator validates schemas, source fields, case and gold counts, all three
variance types, and every numeric Observed Variance before reporting success.
Run the independent test suite with:

```bash
python3 -m unittest discover -s tests -v
```

The fixed seed is `{seed}`. Running the command twice with the same seed must
produce byte-identical files.

## Artifact contract

- `inputs/clinics.csv`: six fictional clinics and one market aggregation.
- `inputs/financial_values.csv`: clinic-month account actuals and Latest
  Approved Forecast values.
- `inputs/operational_values.csv`: clinic-month operating actuals and expected
  values.
- `inputs/operating_events.csv`: dated, source-attributed operating context.
- `inputs/review_rules.csv`: configurable absolute, percentage, and
  critical-metric rules. Materiality is not selected by an LLM.
- `cases.json`: the public 10-case manifest and review-queue selection metadata.
- `gold/C01.json` through `gold/C10.json`: system-hidden expected-answer
  fixtures. Do not expose these files to a system under evaluation.

Every input row carries a synthetic `source`. Value tables also carry a fixed
`loaded_at` timestamp so evidence provenance remains explicit and reproducible.

## Comparison and sign conventions

The core comparison is closed-month actual versus Latest Approved Forecast at
clinic x account or metric x month. Numeric variance is `actual - forecast` or,
for operating measures, `actual - expected`.

- Financial Variance: an account actual versus its approved forecast.
- Operational Metric Variance: an operating actual versus its expected value.
- Forecast Assumption Variance: an actual driver value versus the assumption
  embedded in the approved forecast.

A negative revenue variance is unfavorable; a positive expense variance is
unfavorable. Direction is explicit in gold fixtures rather than inferred from
the arithmetic sign alone.

## Expected-answer contract

Each gold fixture fixes seven scored dimensions:

1. Observed Variance
2. Expected Driver Family
3. Primary and Contributing Driver roles
4. Timing Classification
5. Epistemic State
6. Human Review Requirement
7. Forbidden Conclusion

Fixtures may also define an expected analyst question, an assumption-change
proposal, supported contribution estimate, and the two success criteria.
`Successfully Explained Variance` is a strict subset of `Successful
Investigation`; a correct unresolved result is successful investigation and is
not a successful explanation.

## Data boundary

No patient-level data is present. The benchmark contains only clinic-month
aggregates and dated operating context. It excludes names, dates of birth,
member IDs, claim IDs, encounter IDs, medical records, and claims-level PHI.
"""


def generate(output_dir: Path, seed: int) -> None:
    inputs_dir = output_dir / "inputs"
    gold_dir = output_dir / "gold"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    gold_dir.mkdir(parents=True, exist_ok=True)

    input_rows = build_input_rows(seed)
    for filename, headers in INPUT_HEADERS.items():
        write_csv(inputs_dir / filename, headers, input_rows[filename])

    cases = build_case_overviews(input_rows)
    private_case_lookup = {case["case_id"]: case for case in CASE_OVERVIEWS}
    (output_dir / "cases.json").write_text(
        json.dumps(cases, indent=2) + "\n", encoding="utf-8"
    )
    for case in cases:
        private_case = private_case_lookup[case["case_id"]]
        fixture = {
            "case_id": case["case_id"],
            "scenario": private_case["scenario"],
            "target": {
                "clinic_id": case["clinic_id"],
                "month": case["month"],
                "variance_type": case["target_type"],
                "target_id": case["target_id"],
            },
            "expected": enrich_expected_contract(case),
        }
        (gold_dir / f"{case['case_id']}.json").write_text(
            json.dumps(fixture, indent=2) + "\n", encoding="utf-8"
        )

    (output_dir / "README.md").write_text(render_readme(seed), encoding="utf-8")
    validate_generated_benchmark(output_dir)
    print(
        "Validation passed: 5 input tables, 10 cases, and 10 gold fixtures "
        f"(seed {seed})"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    generate(args.output_dir, args.seed)


if __name__ == "__main__":
    main()
