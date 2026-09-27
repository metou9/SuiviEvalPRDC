from django.db.models import Count, Q, Sum

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Infrastructure
from .serializers import (
    InfrastructureSerializer,
    KoboInfrastructureImportSerializer,
)
from .services.kobo_import import import_kobo_infrastructure


class InfrastructureViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InfrastructureSerializer
    permission_classes = [IsAuthenticated]

    # ==============================================================
    # QUERYSET
    # ==============================================================

    def get_queryset(self):
        project_id = self.request.query_params.get("project")

        queryset = (
            Infrastructure.objects
            .select_related(
                "project",
                "geo_unit",
            )
            .prefetch_related(
                "photos",
                "videos",
                "maintenances",
            )
            .order_by(
                "-kobo_submission_time",
                "-created_at",
            )
        )

        if project_id:
            queryset = queryset.filter(
                project_id=project_id
            )

        return queryset


    # ==============================================================
    # DASHBOARD
    # ==============================================================

    @action(
        detail=False,
        methods=["get"],
        url_path="dashboard",
    )
    def dashboard(self, request):
        """
        Dashboard Infrastructure.

        Les agrégations sont calculées directement dans PostgreSQL
        sur l'ensemble des infrastructures du projet.

        Filtres disponibles :
        - project
        - wilaya
        - moughataa
        - commune
        - infrastructure_type
        """

        project_id = request.query_params.get(
            "project"
        )

        if not project_id:
            return Response(
                {
                    "detail":
                        "Le projet est obligatoire."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = Infrastructure.objects.filter(
            project_id=project_id
        )

        # ==========================================================
        # FILTRES
        # ==========================================================

        wilaya = request.query_params.get(
            "wilaya"
        )

        moughataa = request.query_params.get(
            "moughataa"
        )

        commune = request.query_params.get(
            "commune"
        )

        infrastructure_type = (
            request.query_params.get(
                "infrastructure_type"
            )
        )

        if wilaya:
            queryset = queryset.filter(
                kobo_wilaya=wilaya
            )

        if moughataa:
            queryset = queryset.filter(
                kobo_moughataa=moughataa
            )

        if commune:
            queryset = queryset.filter(
                kobo_commune=commune
            )

        if infrastructure_type:
            queryset = queryset.filter(
                infrastructure_type=
                    infrastructure_type
            )


        # ==========================================================
        # KPI GENERAUX
        # ==========================================================

        total = queryset.count()


        # ----------------------------------------------------------
        # REHABILITATION
        # ----------------------------------------------------------

        rehabilitation_total = (
            queryset.filter(
                has_rehabilitation=True
            ).count()
        )

        works_completed = (
            queryset.filter(
                has_rehabilitation=True,
                works_completed=True,
            ).count()
        )

        works_not_completed = (
            queryset.filter(
                has_rehabilitation=True,
                works_completed=False,
            ).count()
        )


        # ----------------------------------------------------------
        # INFRASTRUCTURES FONCTIONNELLES
        #
        # Une infrastructure est considérée fonctionnelle si
        # l'un des volets renseignés indique qu'elle fonctionne.
        # ----------------------------------------------------------

        functional_queryset = (
            queryset.filter(
                Q(
                    has_rehabilitation=True,
                    rehab_functional=True,
                )
                |
                Q(
                    has_maintenance=True,
                    maintenance_functional=True,
                )
            )
            .distinct()
        )

        functional = functional_queryset.count()


        non_functional_queryset = (
            queryset.filter(
                Q(
                    has_rehabilitation=True,
                    rehab_functional=False,
                )
                |
                Q(
                    has_maintenance=True,
                    maintenance_functional=False,
                )
            )
            .exclude(
                id__in=
                    functional_queryset.values(
                        "id"
                    )
            )
            .distinct()
        )

        non_functional = (
            non_functional_queryset.count()
        )


        # ----------------------------------------------------------
        # MAINTENANCE
        # ----------------------------------------------------------

        maintenance_total = (
            queryset.filter(
                has_maintenance=True
            ).count()
        )

        maintenance_recent = (
            queryset.filter(
                has_maintenance=True,
                maintenance_last_12_months=True,
            ).count()
        )


        # ----------------------------------------------------------
        # GOUVERNANCE
        # ----------------------------------------------------------

        governance_total = (
            queryset.filter(
                has_governance=True
            ).count()
        )

        committees_functional = (
            queryset.filter(
                has_governance=True,
                committee_functional=True,
            ).count()
        )

        committees_with_women = (
            queryset.filter(
                has_governance=True,
                committee_has_women=True,
            ).count()
        )


        # ==========================================================
        # MEMBRES DES COMITES
        # ==========================================================

        members = queryset.filter(
            has_governance=True
        ).aggregate(
            total_members=Sum(
                "committee_members_total"
            ),
            total_women=Sum(
                "committee_women_total"
            ),
        )

        total_members = (
            members["total_members"]
            or 0
        )

        total_women = (
            members["total_women"]
            or 0
        )

        women_rate = (
            round(
                (
                    total_women
                    / total_members
                )
                * 100,
                1,
            )
            if total_members
            else 0
        )


        # ==========================================================
        # TAUX KPI
        # ==========================================================

        completion_rate = (
            round(
                works_completed
                / rehabilitation_total
                * 100,
                1,
            )
            if rehabilitation_total
            else 0
        )

        maintenance_rate = (
            round(
                maintenance_recent
                / maintenance_total
                * 100,
                1,
            )
            if maintenance_total
            else 0
        )

        committee_functional_rate = (
            round(
                committees_functional
                / governance_total
                * 100,
                1,
            )
            if governance_total
            else 0
        )


        # ==========================================================
        # INFRASTRUCTURES PAR TYPE
        # ==========================================================

        by_type = list(
            queryset
            .exclude(
                infrastructure_type=""
            )
            .values(
                "infrastructure_type"
            )
            .annotate(
                count=Count("id")
            )
            .order_by(
                "-count",
                "infrastructure_type",
            )
        )


        # ==========================================================
        # INFRASTRUCTURES PAR WILAYA
        # ==========================================================

        by_wilaya = list(
            queryset
            .exclude(
                kobo_wilaya=""
            )
            .values(
                "kobo_wilaya"
            )
            .annotate(
                count=Count("id")
            )
            .order_by(
                "-count",
                "kobo_wilaya",
            )
        )


        # ==========================================================
        # VOLETS
        # ==============================================================

        modules = [
            {
                "name":
                    "Réhabilitation",
                "count":
                    rehabilitation_total,
            },
            {
                "name":
                    "Maintenance",
                "count":
                    maintenance_total,
            },
            {
                "name":
                    "Gouvernance",
                "count":
                    governance_total,
            },
        ]


        # ==========================================================
        # ETAT DE FONCTIONNEMENT
        # ==============================================================

        functionality_known = (
            functional
            + non_functional
        )

        functionality_unknown = max(
            total
            - functionality_known,
            0,
        )

        functionality = [
            {
                "name":
                    "Fonctionnelles",
                "count":
                    functional,
            },
            {
                "name":
                    "Non fonctionnelles",
                "count":
                    non_functional,
            },
            {
                "name":
                    "Non renseigné",
                "count":
                    functionality_unknown,
            },
        ]


        # ==========================================================
        # VALEURS DISPONIBLES POUR LES FILTRES
        # ==============================================================

        base_queryset = (
            Infrastructure.objects
            .filter(
                project_id=project_id
            )
        )

        wilayas = list(
            base_queryset
            .exclude(
                kobo_wilaya=""
            )
            .values_list(
                "kobo_wilaya",
                flat=True,
            )
            .distinct()
            .order_by(
                "kobo_wilaya"
            )
        )

        moughataas = list(
            base_queryset
            .exclude(
                kobo_moughataa=""
            )
            .values_list(
                "kobo_moughataa",
                flat=True,
            )
            .distinct()
            .order_by(
                "kobo_moughataa"
            )
        )

        communes = list(
            base_queryset
            .exclude(
                kobo_commune=""
            )
            .values_list(
                "kobo_commune",
                flat=True,
            )
            .distinct()
            .order_by(
                "kobo_commune"
            )
        )

        infrastructure_types = list(
            base_queryset
            .exclude(
                infrastructure_type=""
            )
            .values_list(
                "infrastructure_type",
                flat=True,
            )
            .distinct()
            .order_by(
                "infrastructure_type"
            )
        )


        # ==========================================================
        # REPONSE
        # ==============================================================

        return Response(
            {
                "kpis": {
                    "total":
                        total,

                    "rehabilitation_total":
                        rehabilitation_total,

                    "works_completed":
                        works_completed,

                    "works_not_completed":
                        works_not_completed,

                    "completion_rate":
                        completion_rate,

                    "functional":
                        functional,

                    "non_functional":
                        non_functional,

                    "maintenance_total":
                        maintenance_total,

                    "maintenance_recent":
                        maintenance_recent,

                    "maintenance_rate":
                        maintenance_rate,

                    "governance_total":
                        governance_total,

                    "committees_functional":
                        committees_functional,

                    "committee_functional_rate":
                        committee_functional_rate,

                    "committees_with_women":
                        committees_with_women,

                    "committee_members_total":
                        total_members,

                    "committee_women_total":
                        total_women,

                    "women_rate":
                        women_rate,
                },

                "charts": {
                    "by_type":
                        by_type,

                    "by_wilaya":
                        by_wilaya,

                    "modules":
                        modules,

                    "functionality":
                        functionality,
                },

                "filters": {
                    "wilayas":
                        wilayas,

                    "moughataas":
                        moughataas,

                    "communes":
                        communes,

                    "infrastructure_types":
                        infrastructure_types,
                },
            }
        )


    # ==============================================================
    # IMPORT KOBO
    # ==============================================================

    @action(
        detail=False,
        methods=["post"],
        url_path="import-kobo",
        parser_classes=[
            MultiPartParser,
            FormParser,
        ],
    )
    def import_kobo(
        self,
        request,
    ):
        serializer = (
            KoboInfrastructureImportSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        project_id = (
            request.data.get(
                "project"
            )
        )

        if not project_id:
            return Response(
                {
                    "detail":
                        "Le projet est obligatoire."
                },
                status=
                    status.HTTP_400_BAD_REQUEST,
            )

        ProjectModel = (
            Infrastructure
            ._meta
            .get_field("project")
            .remote_field
            .model
        )

        try:
            project = (
                ProjectModel.objects.get(
                    pk=project_id
                )
            )

        except ProjectModel.DoesNotExist:
            return Response(
                {
                    "detail":
                        "Projet introuvable."
                },
                status=
                    status.HTTP_404_NOT_FOUND,
            )

        try:
            result = (
                import_kobo_infrastructure(
                    file_obj=
                        serializer.validated_data[
                            "file"
                        ],
                    project=project,
                    user=request.user,
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail":
                        str(exc)
                },
                status=
                    status.HTTP_400_BAD_REQUEST,
            )

        except Exception as exc:
            return Response(
                {
                    "detail":
                        "Erreur pendant l'import du fichier Kobo.",

                    "error":
                        str(exc),
                },
                status=
                    status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message":
                    "Import Kobo terminé.",
                **result,
            },
            status=
                status.HTTP_200_OK,
        )