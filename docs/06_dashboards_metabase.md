# 06 — Dashboards & Metabase

This document defines the **reporting layer**: the SQL views that pre-compute the manual's rates, how
Metabase is provisioned against them, the dashboard catalogue mapped to the manual's *tableaux de
bord*, and how the application embeds those dashboards.

> **Golden rule.** Dashboards never read base tables. They read the **views** defined here. The views
> only count records in the `CONSOLIDATED` state (the end of the *collect → validate → audit →
> consolidate* lifecycle in `03_rbac_and_workflow.md`), so "official" dashboards never show
> un-validated data. Every view exposes a `project_id` column; Metabase **locks** that parameter
> per request (see §6.4) so a viewer can only ever see their own project.

---

## 6.1 How the views are delivered

- The views live in the **`reporting`** app and are created by **Django migrations** using
  `migrations.RunSQL(sql, reverse_sql)`. Keep one migration per view (or one well-commented migration
  that creates them all) so they version cleanly. Use `CREATE OR REPLACE VIEW` so re-running is safe.
- A small follow-up statement grants read access to the BI role created in
  `07_deployment.md` (`deploy/postgres/init.sql` creates `metabase_ro`):

  ```sql
  GRANT USAGE ON SCHEMA public TO metabase_ro;
  GRANT SELECT ON v_indicator_progress, v_financial_by_category, v_financial_by_component,
                  v_procurement_status, v_procurement_durations, v_grievance_sla,
                  v_activity_rollup, v_impact_change
                TO metabase_ro;
  ```

  Put this grant in the same migration that creates the views (idempotent), so a fresh deploy is
  self-contained.
- **Table names** below follow Django's default `"<app>_<model>"` convention (e.g. `Measurement` in
  the `indicators` app → `indicators_measurement`, FK columns are `<field>_id`). If you override
  `db_table` anywhere, update the SQL to match.
- `"order"` is quoted because `order` is a SQL reserved word.

### How the cumulative-vs-current-period split works (Modèle 1)

The manual's execution dashboards show, for every metric, **cumul depuis le début du projet** plus
**année / trimestre / mois en cours**. SQL views can't take a "current period" argument, so the views
expose **one row per period** *and* a **running cumulative** column computed with a window function.
The dashboard then:

- shows the **cumulative** column as *cumul depuis le début*, and
- uses a **period filter** (year / quarter) to isolate the *période en cours* row, whose period value
  is *résultat de la période*.

This keeps the heavy logic in SQL, lets Metabase pick any period (not just "now"), and matches the
manual exactly.

### RAG thresholds

The traffic-light thresholds are inlined in `v_indicator_progress` (`≥90 % green`, `60–90 % amber`,
`<60 % red` for `INCREASE`; inverted for `DECREASE`). These mirror the constants documented in
`reporting/calculations.py` (`04_backend_spec.md` §4.4). If a project needs different thresholds,
change them in one place and `CREATE OR REPLACE` the view (a future enhancement can read them from a
small `reporting_threshold` config table).

---

## 6.2 The reporting views

### 6.2.1 `v_indicator_progress` — physical results, taux de réalisation, RAG

Grain: one row per **indicator × geo unit × year × quarter** (consolidated measurements), carrying the
period value, the running cumulative (respecting the indicator's `aggregation_method`), the reference
target, the achievement rate and the RAG status.

```sql
CREATE OR REPLACE VIEW v_indicator_progress AS
WITH consolidated AS (
    SELECT meas.project_id, meas.indicator_id, meas.geo_unit_id,
           meas.period_year, meas.period_quarter, meas.period_month,
           meas.period_date, meas.value, meas.id
    FROM indicators_measurement meas
    WHERE meas.status = 'CONSOLIDATED'
),
per_period AS (          -- collapse same-period rows to a single period value
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
               ELSE pp.last_val            -- LAST, MANUAL
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
               ELSE                LAST_VALUE(pv.period_value) OVER w   -- LAST, MANUAL
           END AS cumulative_value
    FROM period_value pv
    WINDOW w AS (
        PARTITION BY pv.indicator_id, pv.geo_unit_id
        ORDER BY pv.period_year, pv.period_quarter NULLS FIRST
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )
),
target_geo AS (          -- reference (closing = highest-order milestone) target, per indicator+geo
    SELECT DISTINCT ON (t.indicator_id, t.geo_unit_id)
           t.indicator_id, t.geo_unit_id, t.value AS target_value
    FROM indicators_indicatortarget t
    JOIN core_milestone ms ON ms.id = t.milestone_id
    ORDER BY t.indicator_id, t.geo_unit_id, ms."order" DESC
),
target_national AS (     -- fallback: project-wide target (geo_unit IS NULL)
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
        ELSE  -- DECREASE: lower is better → achievement = target / value
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
```

### 6.2.2 `v_financial_by_category` — budget vs disbursed vs realised, by expense category

Implements **taux de décaissement**, **taux de réalisation financière**, **reliquat/dépassement**, with
per-fiscal-year rows and a running cumulative. `budget_total` is life-of-project (all budget lines for
the category); `budget_annual` is that year's lines.

```sql
CREATE OR REPLACE VIEW v_financial_by_category AS
WITH spine AS (          -- every (category, year) that has a budget line or a consolidated tx
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
```

> `reliquat_*` negative ⇒ **dépassement** (overrun), exactly as the manual defines it.

### 6.2.3 `v_financial_by_component` — same, rolled up to the top-level composante

A recursive CTE maps every `ProgramNode` to its **root component**, so spending booked at a
sub-component or action rolls up to its composante (the manual reports finances *par composante*).

```sql
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
```

### 6.2.4 `v_procurement_status` — planned vs realised, by category & method

```sql
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
```

### 6.2.5 `v_procurement_durations` — days per stage per process

```sql
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
```

### 6.2.6 `v_grievance_sla` — MGP counts and % within SLA

```sql
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
```

### 6.2.7 `v_activity_rollup` — activity counts by kind / geo / period

Feeds count-type indicators (e.g. *nombre de sessions de formation*, *nombre d'activités de cohésion
sociale*) and the activity tiles on dashboards.

```sql
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
```

### 6.2.8 `v_impact_change` — baseline vs latest, per impact indicator

```sql
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
```

---

## 6.3 Metabase provisioning (step by step)

Metabase runs as a container (see `07_deployment.md`) and is reached at `https://<host>/metabase`
through the host nginx. Do this once per environment (and capture it in the runbook):

1. **First-run setup.** Open `/metabase`, create the admin user, skip the "add your data" wizard if it
   appears (you'll add the DB explicitly next).
2. **Add the application database (read-only).** *Admin settings → Databases → Add database →
   PostgreSQL*:
   - Host `db` (the compose service name), Port `5432`, Database name `mse`.
   - User `metabase_ro`, password from `.env` (`METABASE_DB_RO_PASSWORD`).
   - This role can only `SELECT` the `v_*` views (granted in §6.1), so Metabase physically cannot read
     base tables or write anything.
   - After it syncs, you'll see the eight views as "tables".
3. **Set the Site URL.** *Admin → Settings → General → Site URL* = `https://<host>/metabase`. Embed
   URLs are built relative to this, so it must match the public path. (`MB_SITE_URL` env in `07`
   pre-seeds this.)
4. **Enable static (signed) embedding.** *Admin → Settings → Embedding → Static embedding → Enable*.
   Copy the **secret key** → put it in the backend env as `METABASE_EMBEDDING_SECRET` (used by the
   token endpoint in `04_backend_spec.md` §4.6). This is the OSS feature — **no Pro/Enterprise license
   needed.**
5. **Build the questions and dashboards** in §6.4 below. For each dashboard:
   - Add it to the embeddable list: *dashboard → Sharing → Embed → Static embedding → Publish*.
   - Configure each **parameter** as **Locked** or **Editable**:
     - `project_id` → **Locked** (always supplied by the backend token; never user-editable).
     - `fiscal_year`, `indicator_type`, `program_node`, `status` → **Editable** *or* Locked, but their
       **parameter slug must exactly match** the whitelist keys in `MetabaseEmbedView`
       (`fiscal_year`, `indicator_type`, `program_node`, `status`). Metabase derives the slug from the
       parameter name; rename parameters so the slugs line up.
   - Note the dashboard's **numeric ID** (visible in its URL). You'll need it for the frontend env
     (`VITE_MB_DASHBOARD_*`).
6. **Record the IDs.** Fill the table in §6.5 and the frontend `.env` accordingly.

> **Re-deployments.** Metabase keeps its own metadata in the `metabaseappdb` database (created by
> `init.sql`), so dashboards survive container restarts. To move dashboards between environments,
> export with `Admin → Settings → … → Serialization` (or recreate from this spec — they're simple
> questions over the views).

---

## 6.4 Dashboard catalogue (mapped to the manual's *tableaux de bord*)

All dashboards lock `project_id`. "Filter → column" shows which view column each dashboard parameter
maps to.

| # | Dashboard (slug) | Manual reference | Primary view(s) | Filters → column | Key cards |
|---|---|---|---|---|---|
| 1 | **Résultats physiques** (`results-physical`) | Modèle 1 — tableaux de bord sur les résultats physiques | `v_indicator_progress`, `v_activity_rollup` | `fiscal_year`→`period_year`, `indicator_type`→`indicator_type`, `program_node`→`program_code` | Cumul vs période en cours per indicator; achievement rate; RAG gauge; activity counts by kind |
| 2 | **Cadre de résultats** (`results-framework`) | Indicateurs ODP/PDO + intermédiaires (Tableaux 1–4) | `v_indicator_progress` | `indicator_type`, `program_node` | RAG table PDO then by component; target vs cumulative; bar of achievement_rate |
| 3 | **Suivi financier — catégories** (`finance-category`) | Tableaux de bord financiers par catégorie de dépense | `v_financial_by_category` | `fiscal_year`→`fiscal_year` | Budget vs disbursed vs realised; taux de décaissement; taux de réalisation financière; reliquat |
| 4 | **Suivi financier — composantes** (`finance-component`) | Tableaux de bord financiers par composante | `v_financial_by_component` | `fiscal_year` | Same metrics grouped by composante; cost↔result context |
| 5 | **Passation de marchés** (`procurement`) | Suivi de la passation (PPM, étapes, durées) | `v_procurement_status`, `v_procurement_durations` | `fiscal_year` (via planned_year on questions), method/category | Planned vs realised count & amount; realisation rate; stage durations; overdue stages |
| 6 | **MGP / Plaintes** (`grievances`) | Mécanisme de Gestion des Plaintes | `v_grievance_sla` | type, level | Counts by state/type/level; % traitées dans le délai (sla_rate) |
| 7 | **Suivi d'impact** (`impact`) | Tableau 5 — indicateurs d'impact | `v_impact_change` | (indicator) | Baseline vs latest vs change (abs & %); target reference |
| 8 | **Activités** (`activities`) | Fiches (formations, visites, réunions, sous-projets…) | `v_activity_rollup` | `fiscal_year`→`period_year`, kind, geo | Activity counts & participants (women/youth) by kind, geo, period |

**Geographic drill-down.** Because `v_indicator_progress`, `v_activity_rollup` and the finance views
all carry `geo_unit_id`/`geo_rank`, add a geo filter (mapped to `geo_name` or a geo-unit field
question) on dashboards 1, 4, 8 for the wilaya→commune→village drill the manual expects.

---

## 6.5 Embedding mechanics (recap + the env contract)

The full flow is specified in `04_backend_spec.md` §4.6 (backend) and `05_frontend_spec.md`
(`MetabaseEmbed` component). Summary of the contract the three layers must agree on:

1. **Backend** signs a short-lived (10-minute) JWT with `METABASE_EMBEDDING_SECRET`, **always locking
   `project_id = request.project.id`**, and passing through only the whitelisted filters
   (`fiscal_year`, `indicator_type`, `program_node`, `status`). It returns `{ "iframe_url": "…" }`.
   *Security note:* because `project_id` is locked in the signed token, the iframe cannot be tampered
   with to reveal another project's data.
2. **Frontend** calls `GET /api/v1/metabase/embed/?dashboard=<id>&fiscal_year=<y>&…`, then renders the
   returned URL in a responsive `<iframe>` (re-fetching when a filter changes). Dashboard IDs come from
   env, never hard-coded.
3. **Metabase** parameter slugs must equal the whitelist keys, and `project_id` must be **Locked**.

### Environment variables (fill after provisioning)

Backend (`.env`, see `07_deployment.md`):

```
METABASE_SITE_URL=https://<host>/metabase
METABASE_EMBEDDING_SECRET=<secret from Admin → Embedding>
```

Frontend (`.env`, baked at build per `05_frontend_spec.md`) — the dashboard IDs from §6.4:

```
VITE_MB_DASHBOARD_RESULTS_PHYSICAL=<id1>
VITE_MB_DASHBOARD_RESULTS_FRAMEWORK=<id2>
VITE_MB_DASHBOARD_FINANCE_CATEGORY=<id3>
VITE_MB_DASHBOARD_FINANCE_COMPONENT=<id4>
VITE_MB_DASHBOARD_PROCUREMENT=<id5>
VITE_MB_DASHBOARD_GRIEVANCES=<id6>
VITE_MB_DASHBOARD_IMPACT=<id7>
VITE_MB_DASHBOARD_ACTIVITIES=<id8>
```

---

## 6.6 Acceptance criteria for this layer

- All eight `v_*` views exist (created by migration), and `metabase_ro` can `SELECT` them and nothing
  else.
- A measurement that is **not** `CONSOLIDATED` does **not** appear in any view; consolidating it makes
  it appear and updates the rate/RAG.
- `v_indicator_progress` reproduces the manual's *taux de réalisation physique* and the
  cumul/période split for a hand-checked indicator.
- `v_financial_by_category` reproduces *taux de décaissement*, *taux de réalisation financière* and
  *reliquat/dépassement* for a hand-checked category & year.
- All eight dashboards render **inside the app** via the signed-embed endpoint, scoped to the selected
  project, with the documented filters working.
