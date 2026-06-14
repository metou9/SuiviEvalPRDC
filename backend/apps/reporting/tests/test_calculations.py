from apps.reporting import calculations as c


def test_physical_achievement_rate():
    assert c.physical_achievement_rate(50, 100) == 50.0
    assert c.physical_achievement_rate(10, 0) is None


def test_disbursement_and_realisation():
    assert c.disbursement_rate(75, 300) == 25.0
    assert c.financial_realisation_rate(150, 300) == 50.0


def test_reliquat_and_variance():
    assert c.reliquat(300, 120) == 180
    assert c.reliquat(100, 130) == -30  # dépassement
    assert c.variance(200, 180) == 20


def test_rag_increase():
    assert c.rag_status(95, 100, "INCREASE") == "GREEN"
    assert c.rag_status(70, 100, "INCREASE") == "AMBER"
    assert c.rag_status(20, 100, "INCREASE") == "RED"
    assert c.rag_status(10, 0, "INCREASE") == "GREY"


def test_rag_decrease():
    # lower is better: value 50 vs target 50 → 100% → green
    assert c.rag_status(50, 50, "DECREASE") == "GREEN"
    assert c.rag_status(0, 50, "DECREASE") == "GREEN"
    assert c.rag_status(200, 50, "DECREASE") == "RED"


def test_procurement_and_sla_rates():
    assert c.procurement_realisation_rate(3, 6) == 50.0
    assert c.grievance_sla_rate(8, 10) == 80.0
