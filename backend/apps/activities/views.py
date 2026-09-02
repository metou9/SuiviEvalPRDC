from apps.accounts.permissions import (
    ReadOrCapability,
    WorkflowObjectPermission,
)
from apps.core.api import (
    AuthoredModelViewSet,
    ExportMixin,
)

from .models import (
    Activity,
    TechnicalExecution,
    TechnicalPlan,
    TechnicalSchedule,
    WorkPlan,
)

from .serializers import (
    ActivitySerializer,
    TechnicalExecutionSerializer,
    TechnicalPlanSerializer,
    TechnicalScheduleSerializer,
    WorkPlanSerializer,
)


# ======================================================================
# PTBA / PLAN DE TRAVAIL ANNUEL
# ======================================================================

class WorkPlanViewSet(
    ExportMixin,
    AuthoredModelViewSet,
):
    """
    Gestion des PTBA annuels.

    Exemples :
    - PTBA PRDC-VFS 2026
    - PTBA PRDC-VFS 2027
    """

    serializer_class = WorkPlanSerializer

    queryset = WorkPlan.objects.all()

    permission_classes = [
        ReadOrCapability,
    ]

    write_capability = "reference.manage"

    filterset_fields = {
        "year": ["exact"],
        "is_current": ["exact"],
        "is_active": ["exact"],
    }

    search_fields = [
        "code",
        "name",
        "version",
    ]

    ordering_fields = [
        "year",
        "code",
        "name",
        "created_at",
    ]

    ordering = [
        "-year",
        "name",
    ]


# ======================================================================
# ACTIVITES
# ======================================================================

class ActivityViewSet(
    ExportMixin,
    AuthoredModelViewSet,
):
    """
    Référentiel des activités.

    L'activité est rattachée directement à une sous-composante.

    Les informations propres au PTBA annuel sont gérées
    dans TechnicalPlan.
    """

    serializer_class = ActivitySerializer

    queryset = (
        Activity.objects.select_related(
            "geo_unit",
            "geo_unit__geo_level",
            "program_node",
            "program_node__parent",
            "indicator",
            "responsible",
            "unit",
        )
        .prefetch_related(
            "participants",
        )
        .all()
    )

    permission_classes = [
        WorkflowObjectPermission,
    ]

    workflow_area = "activity"

    geo_scope_field = "geo_unit"

    # ------------------------------------------------------------------
    # FILTRES
    # ------------------------------------------------------------------

    filterset_fields = {
        "geo_unit": ["exact"],
        "program_node": ["exact"],
        "indicator": ["exact"],
        "responsible": ["exact"],
        "unit": ["exact"],
    }

    # ------------------------------------------------------------------
    # RECHERCHE
    # ------------------------------------------------------------------

    search_fields = [
        "code",
        "title",
        "objective",
        "description",
        "program_node__code",
        "program_node__name",
        "responsible__name",
        "geo_unit__name",
        "indicator__code",
        "indicator__name",
    ]

    # ------------------------------------------------------------------
    # TRI
    # ------------------------------------------------------------------

    ordering_fields = [
        "code",
        "title",
        "created_at",
        "updated_at",
    ]

    ordering = [
        "code",
    ]


# ======================================================================
# PROGRAMMATION TECHNIQUE PTBA
# ======================================================================

class TechnicalPlanViewSet(
    ExportMixin,
    AuthoredModelViewSet,
):
    """
    Programmation annuelle d'une activité.

    Cette ressource fait le lien :

        PTBA
          +
        Activité

    Elle contient notamment :

    - quantité prévue
    - unité
    - zone
    - responsable
    - période prévue
    - modalités de mise en œuvre
    - extrant attendu
    - observations
    """

    serializer_class = TechnicalPlanSerializer

    queryset = (
        TechnicalPlan.objects.select_related(
            "workplan",
            "activity",
            "activity__program_node",
            "activity__program_node__parent",
            "unit",
            "geo_unit",
            "geo_unit__geo_level",
            "responsible",
        )
        .prefetch_related(
            "schedule",
        )
        .all()
    )

    permission_classes = [
        WorkflowObjectPermission,
    ]

    workflow_area = "activity"

    geo_scope_field = "geo_unit"

    # ------------------------------------------------------------------
    # FILTRES
    # ------------------------------------------------------------------

    filterset_fields = {
        "workplan": ["exact"],
        "activity": ["exact"],
        "unit": ["exact"],
        "geo_unit": ["exact"],
        "responsible": ["exact"],

        "planned_start_date": [
            "exact",
            "gte",
            "lte",
        ],

        "planned_end_date": [
            "exact",
            "gte",
            "lte",
        ],
    }

    # ------------------------------------------------------------------
    # RECHERCHE
    # ------------------------------------------------------------------

    search_fields = [
        "activity__code",
        "activity__title",
        "activity__program_node__code",
        "activity__program_node__name",
        "workplan__code",
        "workplan__name",
        "implementation_modality",
        "expected_output",
        "observations",
        "responsible__name",
        "geo_unit__name",
    ]

    # ------------------------------------------------------------------
    # TRI
    # ------------------------------------------------------------------

    ordering_fields = [
        "workplan__year",
        "activity__code",
        "planned_start_date",
        "planned_end_date",
        "planned_quantity",
        "created_at",
    ]

    ordering = [
        "workplan__year",
        "activity__code",
    ]

    # ------------------------------------------------------------------
    # FILTRES PRATIQUES
    #
    # Exemples :
    #
    # ?year=2026
    # ?date_after=2026-01-01
    # ?date_before=2026-12-31
    # ------------------------------------------------------------------

    def get_queryset(self):
        qs = super().get_queryset()

        year = self.request.query_params.get(
            "year"
        )

        after = self.request.query_params.get(
            "date_after"
        )

        before = self.request.query_params.get(
            "date_before"
        )

        if year:
            qs = qs.filter(
                workplan__year=year
            )

        if after:
            qs = qs.filter(
                planned_start_date__gte=after
            )

        if before:
            qs = qs.filter(
                planned_end_date__lte=before
            )

        return qs


# ======================================================================
# CHRONOGRAMME MENSUEL
# ======================================================================

class TechnicalScheduleViewSet(
    AuthoredModelViewSet,
):
    """
    Chronogramme mensuel d'une programmation technique.

    Mois :
    1  = Janvier
    2  = Février
    ...
    12 = Décembre
    """

    serializer_class = TechnicalScheduleSerializer

    queryset = (
        TechnicalSchedule.objects.select_related(
            "technical_plan",
            "technical_plan__activity",
            "technical_plan__workplan",
        )
        .all()
    )

    permission_classes = [
        WorkflowObjectPermission,
    ]

    workflow_area = "activity"

    filterset_fields = {
        "technical_plan": ["exact"],
        "month": ["exact"],
        "is_planned": ["exact"],
    }

    ordering_fields = [
        "month",
        "created_at",
    ]

    ordering = [
        "technical_plan",
        "month",
    ]


# ======================================================================
# EXECUTION / SUIVI TECHNIQUE
# ======================================================================

class TechnicalExecutionViewSet(
    ExportMixin,
    AuthoredModelViewSet,
):
    """
    Suivi de l'exécution physique des activités programmées.

    Chaque enregistrement est lié à une programmation technique
    TechnicalPlan.

    Il permet notamment de suivre :

    - l'activité concernée
    - l'exercice
    - la date de suivi
    - le trimestre
    - le mois
    - la quantité réalisée
    - le taux de réalisation physique
    - le statut d'exécution
    - les dates réelles
    - les difficultés rencontrées
    - les actions correctives
    - les observations
    """

    serializer_class = TechnicalExecutionSerializer

    queryset = (
        TechnicalExecution.objects.select_related(
            # Programmation
            "technical_plan",

            # Exercice
            "technical_plan__workplan",

            # Activité
            "technical_plan__activity",

            # Composante / Sous-composante
            "technical_plan__activity__program_node",
            "technical_plan__activity__program_node__parent",

            # Unité
            "technical_plan__unit",

            # Zone
            "technical_plan__geo_unit",
            "technical_plan__geo_unit__geo_level",

            # Responsable
            "technical_plan__responsible",
        )
        .all()
    )

    permission_classes = [
        WorkflowObjectPermission,
    ]

    # On conserve la même zone fonctionnelle que les activités.
    workflow_area = "activity"

    # ------------------------------------------------------------------
    # FILTRES
    # ------------------------------------------------------------------

    filterset_fields = {
        "technical_plan": [
            "exact",
        ],

        "period_year": [
            "exact",
        ],

        "period_quarter": [
            "exact",
        ],

        "period_month": [
            "exact",
        ],

        "execution_status": [
            "exact",
        ],

        "reporting_date": [
            "exact",
            "gte",
            "lte",
        ],

        "actual_start_date": [
            "exact",
            "gte",
            "lte",
        ],

        "actual_end_date": [
            "exact",
            "gte",
            "lte",
        ],
    }

    # ------------------------------------------------------------------
    # RECHERCHE
    # ------------------------------------------------------------------

    search_fields = [
        "technical_plan__activity__code",
        "technical_plan__activity__title",

        "technical_plan__activity__program_node__code",
        "technical_plan__activity__program_node__name",

        "technical_plan__responsible__name",

        "technical_plan__geo_unit__name",

        "difficulties",
        "corrective_actions",
        "observations",
    ]

    # ------------------------------------------------------------------
    # TRI
    # ------------------------------------------------------------------

    ordering_fields = [
        "reporting_date",
        "period_year",
        "period_quarter",
        "period_month",
        "actual_quantity",
        "physical_progress_percent",
        "execution_status",
        "actual_start_date",
        "actual_end_date",
        "created_at",
        "updated_at",
    ]

    ordering = [
        "-reporting_date",
        "-created_at",
    ]

    # ------------------------------------------------------------------
    # FILTRES PRATIQUES
    #
    # Exemples :
    #
    # ?activity=5
    # ?year=2026
    # ?workplan=2
    # ?responsible=3
    # ?geo_unit=10
    # ------------------------------------------------------------------

    def get_queryset(self):
        qs = super().get_queryset()

        activity = self.request.query_params.get(
            "activity"
        )

        year = self.request.query_params.get(
            "year"
        )

        workplan = self.request.query_params.get(
            "workplan"
        )

        responsible = self.request.query_params.get(
            "responsible"
        )

        geo_unit = self.request.query_params.get(
            "geo_unit"
        )

        if activity:
            qs = qs.filter(
                technical_plan__activity_id=activity
            )

        if year:
            qs = qs.filter(
                technical_plan__workplan__year=year
            )

        if workplan:
            qs = qs.filter(
                technical_plan__workplan_id=workplan
            )

        if responsible:
            qs = qs.filter(
                technical_plan__responsible_id=responsible
            )

        if geo_unit:
            qs = qs.filter(
                technical_plan__geo_unit_id=geo_unit
            )

        return qs