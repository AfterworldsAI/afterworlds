"""Owner-approved D4 operating schedule and its boundary arithmetic.

All clocks use recorded UTC instants. "N calendar days" is the instant plus
N x 24 hours; a deadline is met at any instant up to and including it, and is
overdue strictly after it. An expiry ("7 days from availability", "30 days
from recording") takes effect at the instant itself. "24 calendar months" adds
months to the date and clamps the day to the target month's last day
(31 January + 1 month = 28/29 February; 29 February + 24 months = 28
February), keeping the time of day. These are service commitments, not a
statutory determination (CRD Issue 22 D4).
"""

from __future__ import annotations

import calendar
from datetime import datetime, timedelta

from afterworlds.remote.control_store import POLICY_VERSION
from afterworlds.remote.storage import (
    ANNUAL_REVIEW,
    BACKUP_LIFETIME,
    DELETION_BACKUP_DEADLINE,
)

__all__ = [
    "ANNUAL_REVIEW",
    "ARTIFACT_AVAILABILITY",
    "BACKUP_LIFETIME",
    "DELETION_BACKUP_DEADLINE",
    "EXPORT_PRODUCTION",
    "LIVE_DELETION",
    "LOG_RETENTION",
    "PARTIAL_CLEANUP",
    "POLICY_VERSION",
    "RECEIPT_RETENTION_MONTHS",
    "add_calendar_months",
    "is_expired",
    "is_overdue",
]

#: Export accessible within 7 calendar days of the verified request.
EXPORT_PRODUCTION = timedelta(days=7)
#: Completed hosted artifact available for 7 days from availability.
ARTIFACT_AVAILABILITY = timedelta(days=7)
#: Failed/partial staging removed within 24 hours.
PARTIAL_CLEANUP = timedelta(hours=24)
#: In-scope live data removed within 7 calendar days of confirmation.
LIVE_DELETION = timedelta(days=7)
#: Minimized receipts and closed-account entitlement history.
RECEIPT_RETENTION_MONTHS = 24
#: Content-free routine operational logs.
LOG_RETENTION = timedelta(days=30)


def add_calendar_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def is_overdue(deadline: datetime, now: datetime) -> bool:
    return now > deadline


def is_expired(expires_at: datetime, now: datetime) -> bool:
    return now >= expires_at
