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
    TechnicalPlan,
    TechnicalSchedule,
    WorkPlan,
)
from .serializers import (
    ActivitySerializer,
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
# ACTIVITÉS
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
    # Filtres
    # ------------------------------------------------------------------

    filterset_fields = {
        "geo_unit": ["exact"],
        "program_node": ["exact"],
        "indicator": ["exact"],
        "responsible": ["exact"],
        "unit": ["exact"],
    }

    # ------------------------------------------------------------------
    # Recherche
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
    # Tri
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
    # Filtres
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
    # Recherche
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
    # Tri
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
    # Filtres pratiques
    #
    # Exemple :
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