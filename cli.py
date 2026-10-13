"""
Command Line Interface for Who Icd11 Multilingual Auto Coder.
"""
import argparse
import csv
import os
import sys
from pathlib import Path
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.base import AuditLogger

supervisor = SystemSupervisor(model_provider="mock")


def _safe_resolve_path(path_str: str, must_exist: bool = False) -> Path:
    """Resolve a user-supplied path safely, preventing path traversal outside cwd."""
    cwd = Path.cwd().resolve()
    p = Path(path_str).resolve()
    # Prevent path traversal: resolved path must be within cwd or its subdirectories
    try:
        p.relative_to(cwd)
    except ValueError:
        raise ValueError(f"Path '{path_str}' resolves outside the working directory (path traversal blocked)")
    if must_exist and not p.is_file():
        raise FileNotFoundError(f"Input file not found: {path_str}")
    return p


def main(argv=None):
    parser = argparse.ArgumentParser(prog="who-icd11-multilingual-auto-coder", description="Who Icd11 Multilingual Auto Coder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="KEY-TARGET-01")
    p_audit.add_argument("--primary", type=float, default=28.5)
    p_audit.add_argument("--secondary", type=float, default=14.2)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Verify Audit
    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print("=" * 80)
        print(f"  WHO ICD11 MULTILINGUAL AUTO CODER")
        print(f"  Domain: Clinical & Biomedical AI | Standard: CAP / CLSI / ISO Standards")
        print(f"  Dossier ID: {dossier.dossier_id} | Urgency: [{dossier.overall_urgency.value}]")
        print("=" * 80)
        for a in dossier.alerts:
            print(f"\n  [{a.urgency.value}] from {a.origin_worker}:")
            print(f"  Summary: {a.summary}")
            print(f"  Details: {a.technical_details}")
            print(f"  Action:  {a.actionable_remediation}")
        print(f"\n  HMAC-SHA256 Audit Hash: {dossier.audit_hash}")
        print("=" * 80)
        return 0

    if args.command == "chat":
        ans = supervisor.query_supervisory_chat(" ".join(args.query))
        print(f"\n[Who Icd11 Multilingual Auto Coder Supervisor]:\n{ans}\n")
        return 0

    if args.command == "verify-audit":
        trail = AuditLogger.get_trail()
        valid = AuditLogger.verify_integrity()
        print(f"Audit Trail Blocks: {len(trail)} | Cryptographic Integrity Verified: {valid}")
        return 0

    if args.command == "batch":
        try:
            in_path = _safe_resolve_path(args.input, must_exist=True)
            out_path = _safe_resolve_path(args.output)
            if in_path == out_path:
                raise ValueError("Input and output must be different files")
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        try:
            with open(in_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames or [])
                if not reader.fieldnames or not {"task_id", "target_identifier", "primary_metric"}.issubset(reader.fieldnames):
                    raise ValueError("CSV must contain task_id, target_identifier, primary_metric")
                rows = list(reader)
        except Exception as e:
            print(f"Error reading input file: {e}", file=sys.stderr)
            return 1

        out_fields = list(dict.fromkeys(fieldnames + ["overall_urgency", "integrity_status", "total_alerts", "audit_hash"]))
        out_rows = []
        errors = 0
        for idx, r in enumerate(rows):
            try:
                payload = SystemTaskPayload(
                    task_id=r.get("task_id", f"TASK-{idx+1:03d}"),
                    target_identifier=r.get("target_identifier", f"TARGET-{idx+1:03d}"),
                    primary_metric=float(r.get("primary_metric", 15.0) or 15.0),
                    secondary_metric=float(r.get("secondary_metric", 5.0) or 5.0),
                    status_descriptor=r.get("status_descriptor", "NOMINAL"),
                    is_critical_flag=str(r.get("is_critical_flag", "")).lower() in ("true", "1", "yes"),
                )
                dossier = supervisor.process_task(payload)
                row_dict = dict(r)
                row_dict["overall_urgency"] = dossier.overall_urgency.value
                row_dict["integrity_status"] = dossier.integrity_status.value
                row_dict["total_alerts"] = dossier.total_alerts
                row_dict["audit_hash"] = dossier.audit_hash
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
        return 1 if errors else 0

    if args.command == "serve":
        import uvicorn
        from agents.api import app
        print(f"Starting Who Icd11 Multilingual Auto Coder API server on http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
