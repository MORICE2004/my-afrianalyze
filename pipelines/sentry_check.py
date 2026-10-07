r"""Send one controlled test error to Sentry and print its event id, to prove error reporting end to end.

    $env:SENTRY_DSN = "<from the Sentry project>"; .venv\Scripts\python -m pipelines.sentry_check

Then find the event id in Sentry and check: it is there, it names this release, and it carries no request
body, cookie, auth header or user (packages/core/telemetry.py scrubs them). Exit 1 if Sentry is not set up.
"""
from __future__ import annotations

import sys

from packages.core import telemetry


class SentryCheckError(RuntimeError):
    """Raised on purpose by pipelines.sentry_check; not a real failure."""


def main() -> int:
    if not telemetry.init_sentry():
        print("SENTRY_DSN is not set; nothing was sent.")
        return 1
    import sentry_sdk

    try:
        raise SentryCheckError("AfriEdge controlled test error (pipelines.sentry_check)")
    except SentryCheckError as exc:
        event_id = sentry_sdk.capture_exception(exc)
    sentry_sdk.flush(timeout=10)
    print(f"Sent test error, event id {event_id}, release {telemetry.release() or 'not set'}.")
    return 0 if event_id else 1


if __name__ == "__main__":
    sys.exit(main())
