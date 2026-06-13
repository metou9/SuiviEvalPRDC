"""Create the reporting SQL views (PostgreSQL only) and grant them to metabase_ro.

These views are the heart of the dashboards (06_dashboards_metabase.md). They only
surface CONSOLIDATED records. On non-PostgreSQL backends (e.g. SQLite dev/test) the
migration is a no-op so the rest of the schema still migrates.
"""
from django.db import migrations

V_INDICATOR_PROGRESS = """
CREATE OR REPLACE VIEW v_indicator_progress AS
WITH consolidated AS (
    SELECT meas.project_id, meas.indicator_id, meas.geo_unit_id,
           meas.period_year, meas.period_quarter, meas.period_month,
           meas.period_date, meas.value, meas.id
    FROM indicators_measurement meas
    WHERE meas.status = 'CONSOLIDATED'
),
per_period AS (
    SELECT c.project_id, c.indicator_id, c.geo_unit_id,
           c.period_year, c.period_quarter,
           ind.aggregation_method,
           SUM(c.value) AS sum_val,
           AVG(c.value) AS avg_val,
           MAX(c.value) AS max_val,
           MIN(c.value) AS min_val,
           (ARRAY_AGG(c.value ORDER BY c.period_month DESC NULLS LAST,
                                       c.period_date  DESC NULLS LAST,
                                       c.id           DESC))[1] AS last_val
    FROM consolidated c
    JOIN indicators_indicator ind ON ind.id = c.indicator_id
    GROUP BY c.project_id, c.indicator_id, c.geo_unit_id,
             c.period_year, c.period_quarter, ind.aggregation_method
),
period_value AS (
    SELECT pp.*,
           CASE pp.aggregation_method
               WHEN 'SUM'     THEN pp.sum_val
               WHEN 'AVERAGE' THEN pp.avg_val
               WHEN 'MAX'     THEN pp.max_val
               WHEN 'MIN'     THEN pp.min_val
               ELSE pp.last_val
           END AS period_value
    FROM per_period pp
),
cumulative AS (
    SELECT pv.*,
           CASE pv.aggregation_method
               WHEN 'SUM'     THEN SUM(pv.period_value) OVER w
               WHEN 'AVERAGE' THEN AVG(pv.period_value) OVER w
               WHEN 'MAX'     THEN MAX(pv.period_value) OVER w
               WHEN 'MIN'     THEN MIN(pv.period_value) OVER w
               ELSE                LAST_VALUE(pv.period_value) OVER w
           END AS cumulative_value
    FROM period_value pv
    WINDOW w AS (
        PARTITION BY pv.indicator_id, pv.geo_unit_id
        ORDER BY pv.period_year, pv.period_quarter NULLS FIRST
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )
),
target_geo AS (
    SELECT DISTINCT ON (t.indicator_id, t.geo_unit_id)
           t.indicator_id, t.geo_unit_id, t.value AS target_value
    FROM indicators_indicatortarget t
    JOIN core_milestone ms ON ms.id = t.milestone_id
    ORDER BY t.indicator_id, t.geo_unit_id, ms."order" DESC
),
target_national AS (
    SELECT DISTINCT ON (t.indicator_id)
           t.indicator_id, t.value AS target_value
    FROM indicators_indicatortarget t
    JOIN core_milestone ms ON ms.id = t.milestone_id
    WHERE t.geo_unit_id IS NULL
    ORDER BY t.indicator_id, ms."order" DESC
)
SELECT
    cu.project_id,
    cu.indicator_id,
    ind.code                                  AS indicator_code,
    ind.name                                  AS indicator_name,
    it.code                                   AS indicator_type,
    ind.unit,
    ind.direction,
    ind.program_node_id,
    pn.code                                   AS program_code,
    cu.geo_unit_id,
    gu.name                                   AS geo_name,
    gl.rank                                    AS geo_rank,
    cu.period_year,
    cu.period_quarter,
    cu.period_value,
    cu.cumulative_value,
    COALESCE(tg.target_value, tn.target_value) AS target_value,
    CASE
        WHEN COALESCE(tg.target_value, tn.target_value) IS NULL
          OR COALESCE(tg.target_value, tn.target_value) = 0 THEN NULL
        ELSE ROUND(100.0 * cu.cumulative_value
                   / COALESCE(tg.target_value, tn.target_value), 1)
    END                                       AS achievement_rate,
    CASE
        WHEN COALESCE(tg.target_value, tn.target_value) IS NULL
          OR COALESCE(tg.target_value, tn.target_value) = 0 THEN 'GREY'
        WHEN ind.direction = 'INCREASE' THEN
            CASE
                WHEN 100.0 * cu.cumulative_value / COALESCE(tg.target_value, tn.target_value) >= 90 THEN 'GREEN'
                WHEN 100.0 * cu.cumulative_value / COALESCE(tg.target_value, tn.target_value) >= 60 THEN 'AMBER'
                ELSE 'RED'
            END
        ELSE
            CASE
                WHEN cu.cumulative_value = 0 THEN 'GREEN'
                WHEN 100.0 * COALESCE(tg.target_value, tn.target_value) / cu.cumulative_value >= 90 THEN 'GREEN'
                WHEN 100.0 * COALESCE(tg.target_value, tn.target_value) / cu.cumulative_value >= 60 THEN 'AMBER'
                ELSE 'RED'
            END
    END                                       AS rag_status
FROM cumulative cu
JOIN indicators_indicator ind     ON ind.id = cu.indicator_id
JOIN indicators_indicatortype it  ON it.id  = ind.indicator_type_id
LEFT JOIN program_programnode pn  ON pn.id  = ind.program_node_id
LEFT JOIN geo_geounit gu          ON gu.id  = cu.geo_unit_id
LEFT JOIN geo_geolevel gl         ON gl.id  = gu.geo_level_id
LEFT JOIN target_geo tg           ON tg.indicator_id = cu.indicator_id
                                 AND tg.geo_unit_id IS NOT DISTINCT FROM cu.geo_unit_id
LEFT JOIN target_national tn      ON tn.indicator_id = cu.indicator_id;
"""

V_FINANCIAL_BY_CATEGORY = """
CREATE OR REPLACE VIEW v_financial_by_category AS
WITH spine AS (
    SELECT DISTINCT project_id, expense_category_id, fiscal_year
    FROM (
        SELECT project_id, expense_category_id, fiscal_year
        FROM finance_financialtransaction
        WHERE expense_category_id IS NOT NULL AND status = 'CONSOLIDATED'
        UNION
        SELECT project_id, expense_category_id, fiscal_year
        FROM finance_budgetline
        WHERE expense_category_id IS NOT NULL AND fiscal_year IS NOT NULL
    ) u
),
budget_total AS (
    SELECT project_id, expense_category_id, SUM(amount) AS budget_total
    FROM finance_budgetline
    WHERE expense_category_id IS NOT NULL
    GROUP BY project_id, expense_category_id
),
budget_annual AS (
    SELECT project_id, expense_category_id, fiscal_year, SUM(amount) AS budget_annual
    FROM finance_budgetline
    WHERE expense_category_id IS NOT NULL AND fiscal_year IS NOT NULL
    GROUP BY project_id, expense_category_id, fiscal_year
),
tx AS (
    SELECT project_id, expense_category_id, fiscal_year,
           SUM(amount) FILTER (WHERE kind = 'ENGAGEMENT')   AS engaged,
           SUM(amount) FILTER (WHERE kind = 'DISBURSEMENT')  AS disbursed,
           SUM(amount) FILTER (WHERE kind = 'REALIZATION')   AS realised
    FROM finance_financialtransaction
    WHERE expense_category_id IS NOT NULL AND status = 'CONSOLIDATED'
    GROUP BY project_id, expense_category_id, fiscal_year
)
SELECT
    s.project_id,
    s.expense_category_id,
    ec.code AS category_code,
    ec.name AS category_name,
    s.fiscal_year,
    COALESCE(ba.budget_annual, 0)            AS budget_annual,
    bt.budget_total,
    COALESCE(tx.engaged, 0)                  AS engaged_year,
    COALESCE(tx.disbursed, 0)                AS disbursed_year,
    COALESCE(tx.realised, 0)                 AS realised_year,
    SUM(COALESCE(tx.engaged, 0))   OVER w    AS engaged_cumulative,
    SUM(COALESCE(tx.disbursed, 0)) OVER w    AS disbursed_cumulative,
    SUM(COALESCE(tx.realised, 0))  OVER w    AS realised_cumulative,
    CASE WHEN bt.budget_total IS NULL OR bt.budget_total = 0 THEN NULL
         ELSE ROUND(100.0 * SUM(COALESCE(tx.disbursed, 0)) OVER w / bt.budget_total, 1)
    END                                      AS disbursement_rate,
    CASE WHEN bt.budget_total IS NULL OR bt.budget_total = 0 THEN NULL
         ELSE ROUND(100.0 * SUM(COALESCE(tx.realised, 0)) OVER w / bt.budget_total, 1)
    END                                      AS financial_realisation_rate,
    CASE WHEN COALESCE(ba.budget_annual, 0) = 0 THEN NULL
         ELSE ROUND(100.0 * COALESCE(tx.disbursed, 0) / ba.budget_annual, 1)
    END                                      AS disbursement_rate_annual,
    bt.budget_total - SUM(COALESCE(tx.disbursed, 0)) OVER w  AS reliquat_disbursed,
    bt.budget_total - SUM(COALESCE(tx.realised, 0))  OVER w  AS reliquat_realised
FROM spine s
JOIN finance_expensecategory ec ON ec.id = s.expense_category_id
LEFT JOIN budget_total bt ON bt.project_id = s.project_id
                         AND bt.expense_category_id = s.expense_category_id
LEFT JOIN budget_annual ba ON ba.project_id = s.project_id
                          AND ba.expense_category_id = s.expense_category_id
                          AND ba.fiscal_year = s.fiscal_year
LEFT JOIN tx ON tx.project_id = s.project_id
            AND tx.expense_category_id = s.expense_category_id
            AND tx.fiscal_year = s.fiscal_year
WINDOW w AS (PARTITION BY s.project_id, s.expense_category_id
             ORDER BY s.fiscal_year
             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW);
"""

V_FINANCIAL_BY_COMPONENT = """
CREATE OR REPLACE VIEW v_financial_by_component AS
WITH RECURSIVE node_root AS (
    SELECT id, project_id, parent_id, id AS root_id, code AS root_code, name AS root_name
    FROM program_programnode WHERE parent_id IS NULL
    UNION ALL
    SELECT n.id, n.project_id, n.parent_id, r.root_id, r.root_code, r.root_name
    FROM program_programnode n
    JOIN node_root r ON n.parent_id = r.id
),
spine AS (
    SELECT DISTINCT project_id, root_id, root_code, root_name, fiscal_year FROM (
        SELECT t.project_id, nr.root_id, nr.root_code, nr.root_name, t.fiscal_year
        FROM finance_financialtransaction t
        JOIN node_root nr ON nr.id = t.program_node_id
        WHERE t.program_node_id IS NOT NULL AND t.status = 'CONSOLIDATED'
        UNION
        SELECT b.project_id, nr.root_id, nr.root_code, nr.root_name, b.fiscal_year
        FROM finance_budgetline b
        JOIN node_root nr ON nr.id = b.program_node_id
        WHERE b.program_node_id IS NOT NULL AND b.fiscal_year IS NOT NULL
    ) u
),
budget_total AS (
    SELECT b.project_id, nr.root_id, SUM(b.amount) AS budget_total
    FROM finance_budgetline b JOIN node_root nr ON nr.id = b.program_node_id
    WHERE b.program_node_id IS NOT NULL
    GROUP BY b.project_id, nr.root_id
),
tx AS (
    SELECT t.project_id, nr.root_id, t.fiscal_year,
           SUM(t.amount) FILTER (WHERE t.kind = 'DISBURSEMENT') AS disbursed,
           SUM(t.amount) FILTER (WHERE t.kind = 'REALIZATION')  AS realised,
           SUM(t.amount) FILTER (WHERE t.kind = 'ENGAGEMENT')   AS engaged
    FROM finance_financialtransaction t JOIN node_root nr ON nr.id = t.program_node_id
    WHERE t.program_node_id IS NOT NULL AND t.status = 'CONSOLIDATED'
    GROUP BY t.project_id, nr.root_id, t.fiscal_year
)
SELECT
    s.project_id,
    s.root_id   AS program_node_id,
    s.root_code AS component_code,
    s.root_name AS component_name,
    s.fiscal_year,
    bt.budget_total,
    COALESCE(tx.engaged, 0)                  AS engaged_year,
    COALESCE(tx.disbursed, 0)                AS disbursed_year,
    COALESCE(tx.realised, 0)                 AS realised_year,
    SUM(COALESCE(tx.disbursed, 0)) OVER w    AS disbursed_cumulative,
    SUM(COALESCE(tx.realised, 0))  OVER w    AS realised_cumulative,
    CASE WHEN bt.budget_total IS NULL OR bt.budget_total = 0 THEN NULL
         ELSE ROUND(100.0 * SUM(COALESCE(tx.disbursed, 0)) OVER w / bt.budget_total, 1)
    END                                      AS disbursement_rate,
    CASE WHEN bt.budget_total IS NULL OR bt.budget_total = 0 THEN NULL
         ELSE ROUND(100.0 * SUM(COALESCE(tx.realised, 0)) OVER w / bt.budget_total, 1)
    END                                      AS financial_realisation_rate,
    bt.budget_total - SUM(COALESCE(tx.disbursed, 0)) OVER w AS reliquat_disbursed
FROM spine s
LEFT JOIN budget_total bt ON bt.project_id = s.project_id AND bt.root_id = s.root_id
LEFT JOIN tx ON tx.project_id = s.project_id AND tx.root_id = s.root_id
            AND tx.fiscal_year = s.fiscal_year
WINDOW w AS (PARTITION BY s.project_id, s.root_id
             ORDER BY s.fiscal_year
             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW);
"""

V_PROCUREMENT_STATUS = """
CREATE OR REPLACE VIEW v_procurement_status AS
WITH planned AS (
    SELECT project_id, expense_category_id, procurement_method_id,
           COUNT(*) AS planned_count,
           COALESCE(SUM(planned_amount), 0) AS planned_amount
    FROM procurement_ppmitem
    WHERE is_active
    GROUP BY project_id, expense_category_id, procurement_method_id
),
processes AS (
    SELECT project_id, expense_category_id, procurement_method_id,
           COUNT(*)                                              AS process_count,
           COUNT(*) FILTER (WHERE is_completed)                  AS completed_count,
           COUNT(*) FILTER (WHERE NOT is_completed)              AS in_progress_count,
           COALESCE(SUM(awarded_amount) FILTER (WHERE is_completed), 0)        AS awarded_amount,
           COALESCE(SUM(COALESCE(awarded_amount, estimated_amount)), 0)        AS engaged_amount
    FROM procurement_procurementprocess
    WHERE status = 'CONSOLIDATED'
    GROUP BY project_id, expense_category_id, procurement_method_id
)
SELECT
    COALESCE(p.project_id, pr.project_id)                       AS project_id,
    COALESCE(p.expense_category_id, pr.expense_category_id)     AS expense_category_id,
    ec.code AS category_code, ec.name AS category_name,
    COALESCE(p.procurement_method_id, pr.procurement_method_id) AS procurement_method_id,
    pm.code AS method_code, pm.name AS method_name,
    COALESCE(p.planned_count, 0)        AS planned_count,
    COALESCE(p.planned_amount, 0)       AS planned_amount,
    COALESCE(pr.process_count, 0)       AS process_count,
    COALESCE(pr.completed_count, 0)     AS completed_count,
    COALESCE(pr.in_progress_count, 0)   AS in_progress_count,
    COALESCE(pr.awarded_amount, 0)      AS awarded_amount,
    COALESCE(pr.engaged_amount, 0)      AS engaged_amount,
    CASE WHEN COALESCE(p.planned_count, 0) = 0 THEN NULL
         ELSE ROUND(100.0 * COALESCE(pr.completed_count, 0) / p.planned_count, 1)
    END                                 AS realisation_rate_count
FROM planned p
FULL OUTER JOIN processes pr
       ON p.project_id = pr.project_id
      AND p.expense_category_id  IS NOT DISTINCT FROM pr.expense_category_id
      AND p.procurement_method_id IS NOT DISTINCT FROM pr.procurement_method_id
LEFT JOIN finance_expensecategory ec
       ON ec.id = COALESCE(p.expense_category_id, pr.expense_category_id)
LEFT JOIN procurement_procurementmethod pm
       ON pm.id = COALESCE(p.procurement_method_id, pr.procurement_method_id);
"""

V_PROCUREMENT_DURATIONS = """
CREATE OR REPLACE VIEW v_procurement_durations AS
SELECT
    pp.project_id,
    se.procurement_process_id,
    pp.designation,
    se.procurement_stage_id,
    ps.code  AS stage_code,
    ps.name  AS stage_name,
    ps."order" AS stage_order,
    se.start_date,
    se.end_date,
    se.deadline,
    (se.end_date - se.start_date)                              AS duration_days,
    CASE WHEN se.end_date IS NULL AND se.start_date IS NOT NULL
         THEN (CURRENT_DATE - se.start_date) END               AS days_elapsed_open,
    (se.deadline IS NOT NULL AND se.end_date IS NULL AND CURRENT_DATE > se.deadline) AS is_overdue
FROM procurement_stageevent se
JOIN procurement_procurementprocess pp ON pp.id = se.procurement_process_id
JOIN procurement_procurementstage ps   ON ps.id = se.procurement_stage_id
WHERE pp.status = 'CONSOLIDATED';
"""

V_GRIEVANCE_SLA = """
CREATE OR REPLACE VIEW v_grievance_sla AS
WITH g AS (
    SELECT gr.project_id, gr.grievance_type_id,
           gt.code AS type_code, gt.name AS type_name,
           gr.level, gr.state, gr.received_at, gr.resolved_at,
           CASE WHEN gr.resolved_at IS NOT NULL
                THEN (gr.resolved_at - gr.received_at)
                     <= COALESCE(gt.sla_days, pj.grievance_sla_days)
           END AS within_sla
    FROM grievances_grievance gr
    JOIN grievances_grievancetype gt ON gt.id = gr.grievance_type_id
    JOIN core_project pj             ON pj.id = gr.project_id
    WHERE gr.status = 'CONSOLIDATED'
)
SELECT
    project_id, grievance_type_id, type_code, type_name, level,
    COUNT(*)                                              AS total,
    COUNT(*) FILTER (WHERE state = 'RECEIVED')            AS received,
    COUNT(*) FILTER (WHERE state = 'IN_PROGRESS')         AS in_progress,
    COUNT(*) FILTER (WHERE state IN ('RESOLVED','CLOSED')) AS resolved,
    COUNT(*) FILTER (WHERE state = 'REJECTED')            AS rejected,
    COUNT(*) FILTER (WHERE within_sla)                    AS resolved_within_sla,
    CASE WHEN COUNT(*) FILTER (WHERE resolved_at IS NOT NULL) = 0 THEN NULL
         ELSE ROUND(100.0 * COUNT(*) FILTER (WHERE within_sla)
                    / COUNT(*) FILTER (WHERE resolved_at IS NOT NULL), 1)
    END                                                  AS sla_rate
FROM g
GROUP BY project_id, grievance_type_id, type_code, type_name, level;
"""

V_ACTIVITY_ROLLUP = """
CREATE OR REPLACE VIEW v_activity_rollup AS
SELECT
    a.project_id,
    a.kind,
    a.geo_unit_id,     gu.name AS geo_name,
    a.program_node_id, pn.code AS program_code,
    EXTRACT(YEAR    FROM a.date)::int AS period_year,
    EXTRACT(QUARTER FROM a.date)::int AS period_quarter,
    EXTRACT(MONTH   FROM a.date)::int AS period_month,
    COUNT(*)                                  AS activity_count,
    COALESCE(SUM(a.total_participants), 0)    AS participants,
    COALESCE(SUM(a.women_count), 0)           AS women,
    COALESCE(SUM(a.youth_count), 0)           AS youth
FROM activities_activity a
LEFT JOIN geo_geounit gu       ON gu.id = a.geo_unit_id
LEFT JOIN program_programnode pn ON pn.id = a.program_node_id
WHERE a.status = 'CONSOLIDATED'
GROUP BY a.project_id, a.kind, a.geo_unit_id, gu.name,
         a.program_node_id, pn.code,
         EXTRACT(YEAR FROM a.date), EXTRACT(QUARTER FROM a.date),
         EXTRACT(MONTH FROM a.date);
"""

V_IMPACT_CHANGE = """
CREATE OR REPLACE VIEW v_impact_change AS
WITH impact_meas AS (
    SELECT meas.project_id, meas.indicator_id, meas.geo_unit_id,
           meas.period_year, meas.period_quarter, meas.period_month,
           meas.value, meas.id
    FROM indicators_measurement meas
    JOIN indicators_indicator ind     ON ind.id = meas.indicator_id
    JOIN indicators_indicatortype it  ON it.id  = ind.indicator_type_id
    WHERE it.code = 'IMPACT' AND meas.status = 'CONSOLIDATED'
),
ordered AS (
    SELECT im.*,
      ROW_NUMBER() OVER (PARTITION BY indicator_id, geo_unit_id
            ORDER BY period_year, period_quarter NULLS FIRST,
                     period_month NULLS FIRST, id)               AS rn_asc,
      ROW_NUMBER() OVER (PARTITION BY indicator_id, geo_unit_id
            ORDER BY period_year DESC, period_quarter DESC NULLS LAST,
                     period_month DESC NULLS LAST, id DESC)      AS rn_desc
    FROM impact_meas im
),
baseline AS (SELECT indicator_id, geo_unit_id, value AS baseline_value,
                    period_year AS baseline_year FROM ordered WHERE rn_asc = 1),
latest   AS (SELECT indicator_id, geo_unit_id, value AS latest_value,
                    period_year AS latest_year  FROM ordered WHERE rn_desc = 1)
SELECT
    ind.project_id,
    ind.id   AS indicator_id,
    ind.code AS indicator_code,
    ind.name AS indicator_name,
    ind.unit, ind.direction,
    b.geo_unit_id, gu.name AS geo_name,
    b.baseline_value, b.baseline_year,
    l.latest_value,  l.latest_year,
    (l.latest_value - b.baseline_value) AS change_abs,
    CASE WHEN b.baseline_value IS NULL OR b.baseline_value = 0 THEN NULL
         ELSE ROUND(100.0 * (l.latest_value - b.baseline_value) / ABS(b.baseline_value), 1)
    END AS change_pct,
    tn.target_value
FROM baseline b
JOIN latest l ON l.indicator_id = b.indicator_id
             AND l.geo_unit_id IS NOT DISTINCT FROM b.geo_unit_id
JOIN indicators_indicator ind ON ind.id = b.indicator_id
LEFT JOIN geo_geounit gu ON gu.id = b.geo_unit_id
LEFT JOIN LATERAL (
    SELECT t.value AS target_value
    FROM indicators_indicatortarget t
    JOIN core_milestone ms ON ms.id = t.milestone_id
    WHERE t.indicator_id = b.indicator_id
      AND t.geo_unit_id IS NOT DISTINCT FROM b.geo_unit_id
    ORDER BY ms."order" DESC
    LIMIT 1
) tn ON true;
"""

GRANT_SQL = """
GRANT USAGE ON SCHEMA public TO metabase_ro;
GRANT SELECT ON v_indicator_progress, v_financial_by_category, v_financial_by_component,
                v_procurement_status, v_procurement_durations, v_grievance_sla,
                v_activity_rollup, v_impact_change
              TO metabase_ro;
"""

ALL_VIEWS = [
    V_INDICATOR_PROGRESS,
    V_FINANCIAL_BY_CATEGORY,
    V_FINANCIAL_BY_COMPONENT,
    V_PROCUREMENT_STATUS,
    V_PROCUREMENT_DURATIONS,
    V_GRIEVANCE_SLA,
    V_ACTIVITY_ROLLUP,
    V_IMPACT_CHANGE,
]

VIEW_NAMES = [
    "v_indicator_progress", "v_financial_by_category", "v_financial_by_component",
    "v_procurement_status", "v_procurement_durations", "v_grievance_sla",
    "v_activity_rollup", "v_impact_change",
]


def create_views(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for sql in ALL_VIEWS:
            cursor.execute(sql)
        # Grant to the BI role if it exists (it may not in a bare dev cluster).
        cursor.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = 'metabase_ro'"
        )
        if cursor.fetchone():
            cursor.execute(GRANT_SQL)


def drop_views(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for name in VIEW_NAMES:
            cursor.execute(f"DROP VIEW IF EXISTS {name} CASCADE")


class Migration(migrations.Migration):

    dependencies = [
        ("reporting", "0001_initial"),
        ("indicators", "0001_initial"),
        ("finance", "0001_initial"),
        ("procurement", "0001_initial"),
        ("grievances", "0001_initial"),
        ("geo", "0001_initial"),
        ("program", "0001_initial"),
        ("core", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_views, drop_views)]
