import argparse
import json
import sys
import time

import emulo

from .service import record_review, review_queue, status_snapshot
from .store import AutopilotStore


HISTORY_SCHEMA = "emulo.autopilot-history/v1"


def _utc_seconds(clock):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(clock()))


def build_parser():
    parser = argparse.ArgumentParser(prog="emulo-autopilot")
    parser.add_argument("--emulo-home")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="show bounded local health and counts")
    commands.add_parser("queue", help="show local candidates and review state")
    commands.add_parser("history", help="show immutable local generations")

    review = commands.add_parser("review", help="record an explicit review decision")
    review.add_argument("candidate_id")
    review.add_argument("decision", choices=("approve", "reject"))
    review.add_argument("--reason", required=True)

    activate = commands.add_parser(
        "activate", help="activate explicitly approved candidates"
    )
    activate.add_argument("candidate_ids", nargs="+")

    rollback = commands.add_parser(
        "rollback", help="create a new generation from an ancestor"
    )
    rollback.add_argument("generation_id")

    recover = commands.add_parser(
        "recover-lock", help="remove only an inspected exact lock ID"
    )
    recover.add_argument("operation_id")
    return parser


def execute(args, clock=time.time):
    home = emulo.resolve_emulo_home(args.emulo_home)
    store = AutopilotStore(home)
    if args.command == "status":
        return status_snapshot(store)
    if args.command == "queue":
        return review_queue(store)
    if args.command == "history":
        head = store.get_head()
        return {
            "schema_version": HISTORY_SCHEMA,
            "active_generation_id": (
                None if head is None else head["generation_id"]
            ),
            "generations": store.list_generations(),
        }
    if args.command == "review":
        return record_review(
            store,
            args.candidate_id,
            args.decision,
            args.reason,
            _utc_seconds(clock),
        )
    if args.command == "activate":
        return store.activate(args.candidate_ids, _utc_seconds(clock))
    if args.command == "rollback":
        return store.rollback(args.generation_id, _utc_seconds(clock))
    if args.command == "recover-lock":
        recovered = store.recover_lock(args.operation_id)
        return {
            "operation_id": recovered["operation_id"],
            "operation": recovered["operation"],
            "created_at": recovered["created_at"],
        }
    raise ValueError("unsupported Autopilot command")


def main(argv=None, clock=time.time):
    args = build_parser().parse_args(argv)
    try:
        result = execute(args, clock=clock)
    except (OSError, RuntimeError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "error", "error": str(exc)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
