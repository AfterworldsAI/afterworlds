"""Entitlement enumerations — CRD Issue 13."""

from __future__ import annotations

from enum import StrEnum


class HostedAccessPlan(StrEnum):
    STARTER_ACCESS = "starter_access"
    SUBSCRIPTION = "subscription"


class RuntimeAccessPath(StrEnum):
    HOSTED = "hosted"
    BYOK = "byok"


class HostedUnavailableReason(StrEnum):
    NO_SUBSCRIPTION = "no_subscription"
    SUBSCRIPTION_INACTIVE = "subscription_inactive"
    CREDITS_EXHAUSTED = "credits_exhausted"


class HostedAccessDeactivationReason(StrEnum):
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    PAYMENT_FAILED = "payment_failed"
    ADMIN_ACTION = "admin_action"
    ACCOUNT_CLOSED = "account_closed"


class CloudServicesDeactivationReason(StrEnum):
    NATURAL_EXPIRY = "natural_expiry"
    NON_RENEWAL = "non_renewal"
    PAYMENT_FAILED = "payment_failed"
    ADMIN_ACTION = "admin_action"


class CloudServiceOperation(StrEnum):
    HOSTED_STORAGE_WRITE = "hosted_storage_write"
    SYNC = "sync"
    BACKUP = "backup"
    REMOTE_ACCESS = "remote_access"
    HOSTED_INGESTION = "hosted_ingestion"
    # Read / export / download are NOT in this enum and must never be gated.


class EntitlementEventType(StrEnum):
    HOSTED_ACCESS_ACTIVATED = "hosted_access_activated"
    HOSTED_ACCESS_DEACTIVATED = "hosted_access_deactivated"
    SUBSCRIPTION_CREDIT_GRANT = "subscription_credit_grant"
    TOP_UP_CREDIT_GRANT = "top_up_credit_grant"
    CREDIT_DEDUCTION = "credit_deduction"
    BYOK_LICENSE_ACTIVATED = "byok_license_activated"
    CLOUD_SERVICES_ACTIVATED = "cloud_services_activated"
    CLOUD_SERVICES_LAPSED = "cloud_services_lapsed"
    MANUAL_CREDIT_ADJUSTMENT = "manual_credit_adjustment"


class PipelinePassId(StrEnum):
    INTENT_CLASSIFIER = "intent_classifier"
    INPUT_SAFETY = "input_safety"
    PLANNER = "planner"
    RPG_ADJUDICATION = "rpg_adjudication"
    BRANCHING_WRITER = "branching_writer"
    BRANCHING_OOC_CONFIG_EXTRACTOR = "branching_ooc_config_extractor"
    WRITING_OOC_CONFIG_EXTRACTOR = "writing_ooc_config_extractor"
    WRITER = "writer"
    OUTPUT_SAFETY = "output_safety"
    EXTRACTOR = "extractor"
    CONTRADICTION = "contradiction"


class ModelTier(StrEnum):
    HAIKU = "haiku"
    SONNET = "sonnet"
