"""Local investigation and benchmark CLI. Outputs JSON to stdout."""

import argparse
import json
import sys

from provider_fpa.engine import investigate
from provider_fpa.loading import load_datasets
from provider_fpa.narrative import generate_narrative
from provider_fpa.presentation import investigation_payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    investigation = commands.add_parser('investigate')
    investigation.add_argument('--inputs', required=True)
    investigation.add_argument('--clinic', required=True)
    investigation.add_argument('--month', required=True)
    investigation.add_argument('--target', required=True)
    investigation.add_argument('--type', default='financial_variance', choices=[
        'financial_variance', 'operational_metric_variance', 'forecast_assumption_variance',
    ])
    narrative = commands.add_parser('narrative')
    narrative.add_argument('--inputs', required=True)
    narrative.add_argument('--clinic', required=True)
    narrative.add_argument('--month', required=True)
    narrative.add_argument('--target', required=True)
    narrative.add_argument('--type', default='financial_variance', choices=[
        'financial_variance', 'operational_metric_variance', 'forecast_assumption_variance',
    ])
    benchmark = commands.add_parser('benchmark')
    benchmark.add_argument('--directory', required=True)
    args = parser.parse_args()
    try:
        if args.command in {'investigate', 'narrative'}:
            result = investigate(load_datasets(args.inputs), args.clinic, args.month, args.target, args.type)
            output = (generate_narrative(result).to_dict() if args.command == 'narrative'
                      else investigation_payload(result))
            status = 0
        else:
            # Gold access exists only in this evaluator command, not investigation.
            from provider_fpa.evaluation import run_benchmark

            reports = run_benchmark(args.directory)
            output = {'passed_cases': sum(r.passed for r in reports), 'total_cases': len(reports),
                      'passed_dimensions': sum(p for r in reports for _, p in r.dimensions),
                      'total_dimensions': sum(len(r.dimensions) for r in reports),
                      'cases': [{'case_id': r.case_id, 'passed': r.passed,
                                 'dimensions': dict(r.dimensions), 'mismatches': list(r.mismatches)} for r in reports]}
            status = 0 if all(r.passed for r in reports) else 1
        print(json.dumps(output, indent=2, allow_nan=False))
        return status
    except (ValueError, OSError) as exc:
        print(f'Investigation error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
