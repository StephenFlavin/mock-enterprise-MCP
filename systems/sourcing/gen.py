"""Sourcing and RFQ data: mostly seed-based with minimal generated background."""
from datetime import datetime, time, timedelta


def generate(g):
    # Minimal generation - rely on seed data for all story-critical records
    r = g.rng
    products = g.master("products")

    # Only generate empty tables that don't have seed data
    # All critical data is in seed CSVs for story scenarios

    return {
        "rfq": [],
        "rfq_responses": [],
        "rfx_events": [],
        "rfx_responses": [],
        "tender_scorecard_templates": [],
        "scorecard_criteria": [],
        "sourcing_awards": [],
        "rfq_clarifications": []
    }
