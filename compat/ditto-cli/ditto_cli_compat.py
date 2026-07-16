"""ditto is now emulo.

This package exists for one reason: anyone who ran `pip install ditto-cli`
should not be stranded on a name the project no longer uses. It depends on
emulo, prints a one-line notice, and forwards the command through, so existing
invocations keep working instead of hitting a dead end.
"""

import sys

NOTICE = (
    "ditto is now emulo. This command still works, but ditto-cli is no longer updated.\n"
    "Switch with:  pip install emulo   then run 'emulo' instead of 'ditto'.\n"
    "Why the rename: https://github.com/ohad6k/emulo/releases/tag/v0.5.0\n"
)


def main():
    # stderr, so the notice never contaminates piped stdout (the card, --dry-run counts)
    print(NOTICE, file=sys.stderr)
    try:
        import emulo
    except ImportError:
        print(
            "emulo is not installed, so there is nothing to forward to.\n"
            "Run:  pip install emulo",
            file=sys.stderr,
        )
        return 1
    # emulo.main() reads sys.argv itself, so every existing flag passes straight through
    emulo.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
