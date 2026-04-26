"""Shared enumerations used across the UNMAPPED platform."""

from enum import StrEnum


class RegionType(StrEnum):
    URBAN_FORMAL = "urban_formal"
    URBAN_INFORMAL = "urban_informal"
    RURAL_AGRICULTURAL = "rural_agricultural"
    CUSTOM = "custom"


class OpportunityType(StrEnum):
    FORMAL_EMPLOYMENT = "formal_employment"
    INFORMAL_EMPLOYMENT = "informal_employment"
    SELF_EMPLOYMENT = "self_employment"
    APPRENTICESHIP = "apprenticeship"
    MICRO_ENTERPRISE = "micro_enterprise"
    GIG_WORK = "gig_work"
    COOPERATIVE = "cooperative"
    PUBLIC_WORKS = "public_works"
