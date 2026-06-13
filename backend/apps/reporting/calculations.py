"""Canonical rate calculations + RAG thresholds (the manual's §2.2.2 definitions).

The authoritative computation lives in the SQL views (06_dashboards_metabase.md).
This module mirrors them for the ``/dashboards/*`` endpoints and tests.
"""
from decimal import Decimal

# RAG thresholds (achievement % of target).
RAG_GREEN_MIN = 90
RAG_AMBER_MIN = 60


def _pct(numerator, denominator):
    if not denominator:
        return None
    return round(100.0 * float(numerator) / float(denominator), 1)


def physical_achievement_rate(cumulative_realized, target):
    """Taux de réalisation physique = cumulative / target × 100."""
    return _pct(cumulative_realized, target)


def disbursement_rate(disbursed, budget):
    """Taux de décaissement = Σ décaissements / budget × 100."""
    return _pct(disbursed, budget)


def financial_realisation_rate(realised, budget):
    """Taux de réalisation financière = Σ réalisations consolidées / budget × 100."""
    return _pct(realised, budget)


def reliquat(budget, spent):
    """Reliquat (negative ⇒ dépassement/overrun)."""
    if budget is None:
        return None
    return Decimal(str(budget)) - Decimal(str(spent or 0))


def variance(planned, realized):
    """Écart = planned − realized."""
    if planned is None or realized is None:
        return None
    return Decimal(str(planned)) - Decimal(str(realized))


def procurement_realisation_rate(realised_count, planned_count):
    return _pct(realised_count, planned_count)


def grievance_sla_rate(resolved_within_sla, total_resolved):
    return _pct(resolved_within_sla, total_resolved)


def rag_status(cumulative_value, target, direction="INCREASE"):
    """Traffic-light status given improvement direction."""
    if target in (None, 0):
        return "GREY"
    cv = float(cumulative_value or 0)
    target = float(target)
    if direction == "INCREASE":
        achievement = 100.0 * cv / target
    else:  # DECREASE: lower is better
        if cv == 0:
            return "GREEN"
        achievement = 100.0 * target / cv
    if achievement >= RAG_GREEN_MIN:
        return "GREEN"
    if achievement >= RAG_AMBER_MIN:
        return "AMBER"
    return "RED"
