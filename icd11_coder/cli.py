"""
Command-Line Interface for ICD11-Coder: WHO ICD-11 Linearization & Post-Coordination Cluster Agent.
"""
import argparse
import csv
import sys
from pathlib import Path
from .models import FrontierPayload
from .agents import ICD11CoderCoordinator

coordinator = ICD11CoderCoordinator()


def _safe_resolve_path(path_str: str, must_exist: bool = False) -> Path:
    """Resolve a user-supplied path safely, preventing path traversal outside cwd."""
    cwd = Path.cwd().resolve()
    p = Path(path_str).resolve()
    if must_exist and not p.exists():
        raise FileNotFoundError(f"Input file not found: {path_str}")
    try:
        p.relative_to(cwd)
    except ValueError:
        raise ValueError(f"Path '{path_str}' resolves outside the working directory (path traversal blocked)")
    return p


def main(argv=None):
    parser = argparse.ArgumentParser(prog="who-icd11-multilingual-auto-coder", description="ICD11-Coder: WHO ICD-11 Linearization & Post-Coordination Cluster Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="TARGET-GEN-01")
    p_audit.add_argument("--primary", type=float, default=29.4)
    p_audit.add_argument("--secondary", type=float, default=15.1)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = FrontierPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = coordinator.process(payload)
        print("=" * 80)
        print(f"  ICD11-CODER: WHO ICD-11 LINEARIZATION & POST-COORDINATION CLUSTER AGENT")
        print(f"  Domain: Medical Informatics | Standard: WHO ICD-11 MMS Specification")
        print(f"  Task: {dossier['task_id']} | Status: [{dossier['overall_status']}] | Total Alerts: {dossier['total_alerts']}")
        print("=" * 80)
        for a in dossier["alerts"]:
            print(f"\n  [{a['status']}] from {a['origin_agent']}:")
            print(f"  Summary: {a['summary']}")
            print(f"  Details: {a['technical_details']}")
            print(f"  Action:  {a['actionable_remediation']}")
        print("\n" + "=" * 80)
        return 0

    if args.command == "chat":
        ans = coordinator.query_supervisory_chat(" ".join(args.query))
        print(f"\n[ICD11CoderCoordinator]:\n{ans}\n")
        return 0

    if args.command == "batch":
        try:
            in_path = _safe_resolve_path(args.input, must_exist=True)
            out_path = _safe_resolve_path(args.output)
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        try:
            with open(in_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames or [])
                rows = list(reader)
        except Exception as e:
            print(f"Error reading input file: {e}", file=sys.stderr)
            return 1

        out_fields = fieldnames + ["overall_status", "total_alerts", "critical_count", "consensus_summary"]
        out_rows = []
        errors = 0
        for idx, r in enumerate(rows):
            try:
                payload = FrontierPayload(
                    task_id=r.get("task_id", f"TASK-{idx+1:03d}"),
                    target_identifier=r.get("target_identifier", f"TARGET-{idx+1:03d}"),
                    primary_metric=float(r.get("primary_metric", 15.0) or 15.0),
                    secondary_metric=float(r.get("secondary_metric", 5.0) or 5.0),
                    status_descriptor=r.get("status_descriptor", "NOMINAL"),
                    is_critical_flag=str(r.get("is_critical_flag", "")).lower() in ("true", "1", "yes"),
                )
                dossier = coordinator.process(payload)
                row_dict = dict(r)
                row_dict["overall_status"] = dossier["overall_status"]
                row_dict["total_alerts"] = dossier["total_alerts"]
                row_dict["critical_count"] = dossier["critical_count"]
                row_dict["consensus_summary"] = dossier["consensus_summary"]
                out_rows.append(row_dict)
            except Exception as e:
                print(f"Warning: Row {idx+1} skipped due to error: {e}", file=sys.stderr)
                errors += 1

        try:
            with open(out_path, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=out_fields)
                writer.writeheader()
                writer.writerows(out_rows)
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            return 1

        print(f"Processed {len(out_rows)} records -> {out_path}" + (f" ({errors} errors)" if errors else ""))
        return 0

    if args.command == "serve":
        try:
            import uvicorn
            from .server import create_app
            app = create_app()
            if app:
                print(f"Starting ICD11-Coder: WHO ICD-11 Linearization & Post-Coordination Cluster Agent on http://{args.host}:{args.port}")
                uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("FastAPI / uvicorn not installed. Run 'pip install fastapi uvicorn'")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
