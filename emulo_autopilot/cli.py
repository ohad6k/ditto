import argparse
import getpass
import json
import sys
import time

import emulo

from .service import record_review, review_queue, status_snapshot
from .store import AutopilotStore


HISTORY_SCHEMA = "emulo.autopilot-history/v1"
PRODUCTION_CONTINUITY_SERVER = "https://emulo-production.ohad1306.workers.dev"


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

    commands.add_parser(
        "continuity-init",
        help="create local continuity keys and a portable encrypted recovery kit",
    )
    continuity_recover = commands.add_parser(
        "continuity-recover",
        help="recover continuity keys on a new device",
    )
    continuity_recover.add_argument("recovery_kit")
    continuity_connect = commands.add_parser(
        "continuity-connect",
        help="connect this device with a one-time account pairing code",
    )
    continuity_connect.add_argument("--label", required=True)
    continuity_connect.add_argument(
        "--server",
        default=PRODUCTION_CONTINUITY_SERVER,
    )
    commands.add_parser(
        "continuity-status",
        help="show local continuity setup, connection, head, and pending state",
    )
    commands.add_parser(
        "continuity-push",
        help="encrypt and push the active approved generation",
    )
    commands.add_parser(
        "continuity-retry",
        help="retry encrypted generations pending after an outage",
    )
    commands.add_parser(
        "continuity-pull",
        help="pull and activate a conflict-free remote generation",
    )
    return parser


def execute(args, clock=time.time, secret_reader=getpass.getpass):
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
    if args.command == "continuity-init":
        from .continuity_onboarding import initialize_continuity

        return initialize_continuity(home)
    if args.command == "continuity-recover":
        from .continuity_onboarding import recover_continuity

        recovery_secret = secret_reader("Recovery secret: ")
        return recover_continuity(home, args.recovery_kit, recovery_secret)
    if args.command == "continuity-connect":
        from .continuity_onboarding import connect_continuity

        pairing_code = secret_reader("Pairing code: ")
        return connect_continuity(
            home,
            args.server,
            pairing_code,
            args.label,
            emulo.EMULO_VERSION,
        )
    if args.command == "continuity-status":
        from .continuity_onboarding import continuity_status

        return continuity_status(home)
    if args.command in {"continuity-push", "continuity-retry", "continuity-pull"}:
        from .continuity import pull_remote_head, push_active, retry_pending
        from .continuity_onboarding import load_connected_continuity

        master_key, device_id, transport = load_connected_continuity(home)
        if args.command == "continuity-push":
            return push_active(store, master_key, device_id, transport)
        if args.command == "continuity-retry":
            return retry_pending(store, transport)
        result = pull_remote_head(store, master_key, transport)
        if result.get("status") == "conflict":
            return {
                **result,
                "message": (
                    "Local and remote history diverged. Neither branch was overwritten; "
                    "inspect both generations before choosing what to activate."
                ),
            }
        return result
    raise ValueError("unsupported Autopilot command")


def main(argv=None, clock=time.time, secret_reader=getpass.getpass):
    args = build_parser().parse_args(argv)
    try:
        result = execute(args, clock=clock, secret_reader=secret_reader)
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
