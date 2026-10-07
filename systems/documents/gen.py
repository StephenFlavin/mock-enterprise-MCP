"""Documents system - no custom data tables, all tools work from master data."""


def generate(g):
    """
    No background data generation needed - all tools are read-only and work from master data.
    Returns empty dictionary for custom tables.
    """
    return {}
