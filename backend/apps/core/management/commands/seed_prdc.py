"""Idempotent seed of the PRDC-VFS reference project.

This is the ONLY place PRDC-specific values live (02_domain_and_data_model.md §2.5).
Re-running changes nothing (keyed on stable codes).
"""
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import ProjectMembership, Role, RoleAssignment, User
from apps.core.models import Milestone, Project
from apps.finance.models import ExpenseCategory, FundingSource
from apps.geo.models import GeoLevel, GeoUnit
from apps.grievances.models import GrievanceType
from apps.indicators.models import (
    Dimension,
    DimensionCategory,
    Indicator,
    IndicatorTarget,
    IndicatorType,
)
from apps.procurement.models import ProcurementMethod, ProcurementStage
from apps.program.models import ProgramNode
from apps.reporting.models import ReportTemplate

ROLES = [
    ("ADMIN", "Administrateur système"),
    ("COORDINATOR", "Coordonnateur"),
    ("ME_SPECIALIST", "Spécialiste / Expert S&E"),
    ("ME_REGIONAL", "S&E régional / Chef d'antenne"),
    ("FIELD_AGENT", "Agent de terrain"),
    ("VALIDATOR", "Superviseur / Validateur"),
    ("AUDITOR", "Auditeur / Contrôle qualité"),
    ("RAF", "Responsable Administratif & Financier"),
    ("PROCUREMENT_OFFICER", "Responsable passation (APM)"),
    ("GENDER_OFFICER", "Responsable Genre"),
    ("INFRA_ENGINEER", "Ingénieur infrastructure"),
    ("GRIEVANCE_OFFICER", "Responsable MGP"),
    ("LOCAL_DEV_OFFICER", "Responsable développement local"),
    ("COMPONENT_MANAGER", "Responsable de composante"),
    ("EXTERNAL_CONSULTANT", "Consultant externe"),
    ("VALIDATION_COMMITTEE", "Comité de validation"),
    ("VIEWER", "Lecteur (consultation)"),
]

# Wilaya, Moughataa, Commune, population
GEO = [
    ("Trarza", "Tekane", "Tekane", 8603),
    ("Trarza", "Tekane", "Lexeiba 2", 12973),
    ("Trarza", "Keurmacène", "Keurmacène", 4898),
    ("Trarza", "Keurmacène", "N'Diago", 6215),
    ("Trarza", "Rosso", "Rosso", 51026),
    ("Trarza", "Rosso", "Jidr Mohgen", 6700),
    ("Brakna", "Bababé", "Bababé", 12883),
    ("Brakna", "Boghé", "Boghé", 42759),
    ("Brakna", "Boghé", "Dar El Barka", 12667),
    ("Brakna", "Boghé", "Dar El Avia", 4329),
    ("Brakna", "M'Bagne", "M'Bagne", 11859),
    ("Guidimagha", "Woumpou", "Woumpou", 6527),
    ("Guidimagha", "Ghabou", "Ghabou", 10877),
    ("Guidimagha", "Ghabou", "Gouraye", 26142),
    ("Guidimagha", "Sélibaby", "Sélibaby", 29786),
    ("Gorgol", "Kaédi", "Kaédi", 8097),
    ("Gorgol", "Kaédi", "Toufoundé-Civé", 57249),
]

PROGRAM = [
    ("1", "Investissement dans la résilience et l'inclusion communautaire pour la cohésion sociale", None),
    ("1a", "Investissements dans les infrastructures communautaires pour la résilience", "1"),
    ("1b", "Activités d'autonomisation des jeunes et de cohésion sociale", "1"),
    ("2", "Investissements territoriaux intégrés pour la connectivité et le DEL", None),
    ("2a", "Infrastructure prioritaire pour le développement territorial intégré", "2"),
    ("2b", "Moyens de subsistance et opportunités économiques pour le DEL", "2"),
    ("3", "Gestion de projet, renforcement institutionnel et plateforme régionale", None),
    ("3a", "Gestion de projet", "3"),
    ("3b", "Renforcement institutionnel", "3"),
    ("3c", "Plateforme régionale de gestion des connaissances et de dialogue", "3"),
    ("4", "Intervention d'urgence en cas d'urgence (CERC)", None),
]

INDICATOR_TYPES = [
    ("PDO", "Indicateurs de l'ODP", 0),
    ("INTERMEDIATE", "Indicateurs intermédiaires", 1),
    ("EXECUTION", "Indicateurs d'exécution", 2),
    ("IMPACT", "Indicateurs d'impact", 3),
]

# code, name, type, component, unit, base, mid, close, is_cri
PDO = [
    ("ODP-1", "Personnes bénéficiant d'infrastructures et de services intégrés au niveau régional, résilients au climat et inclusifs grâce au projet", "PDO", None, "NUMBER", 0, 300000, 1100000, False),
    ("ODP-2", "Niveau d'achèvement du plan d'action conjoint pour la coopération et la collaboration régionales", "PDO", None, "PERCENTAGE", 0, 50, 95, False),
    ("ODP-3", "Plans locaux et régionaux avec processus de planification intégrés, résilients au climat et inclusifs", "PDO", None, "NUMBER", 0, 15, 21, False),
]

INTERMEDIATE = [
    ("INT-1", "Infrastructures socio-économiques communautaires transfrontalières réhabilitées/mises à niveau", "1", "NUMBER", 0, 200, 400, False),
    ("INT-2", "Exploitation & maintenance des sous-projets conformes aux plans 12 mois après achèvement", "1", "PERCENTAGE", 0, 70, 85, False),
    ("INT-3", "Femmes occupant des rôles décisionnels dans la conception/mise en œuvre des sous-projets", "1", "NUMBER", 0, 150, 250, False),
    ("INT-4", "Activités de cohésion sociale réalisées", "1", "NUMBER", 0, 100, 175, False),
    ("INT-5", "Fonctionnaires UGL utilisant leurs nouvelles compétences", "1", "NUMBER", 0, 75, 150, False),
    ("INT-6", "Membres de communautés estimant les conflits mieux gérés", "1", "PERCENTAGE", 0, 10, 25, False),
    ("INT-7", "Infrastructures réhabilitées pour l'interconnexion transfrontalière", "2", "NUMBER", 0, 10, 20, False),
    ("INT-8", "Marchés frontaliers réhabilités/améliorés", "2", "NUMBER", 0, 15, 30, False),
    ("INT-9", "Personnes bénéficiant de meilleures conditions de vie en milieu urbain (CRI)", "2", "NUMBER", 0, 200000, 400000, True),
    ("INT-10", "Exploitation & maintenance des investissements infra conformes aux plans 12 mois après achèvement", "2", "PERCENTAGE", 0, 70, 85, False),
    ("INT-11", "Mise en œuvre de trois plans régionaux d'amélioration de la résilience/inclusion de la chaîne de valeur", "2", "PERCENTAGE", 0, 50, 95, False),
    ("INT-12", "Agriculteurs ayant bénéficié d'actifs/services agricoles (CRI)", "2", "NUMBER", 0, 30000, 60000, True),
    ("INT-13", "Bénéficiaires orientés ayant utilisé emploi/services financiers/plateformes d'info agricole", "2", "NUMBER", 0, 1000, 2000, False),
    ("INT-14", "Femmes bénéficiant d'AGR", "2", "NUMBER", 0, 1000, 1500, False),
    ("INT-15", "Bénéficiaires ayant augmenté leurs revenus grâce aux AGR", "2", "PERCENTAGE", 0, 50, 90, False),
    ("INT-16", "Plaintes relayées par le système MGP et traitées dans les délais", "3", "PERCENTAGE", 0, 80, 95, False),
    ("INT-17", "Études achevées sur FCV/fragilité climatique approuvées par le CRC", "3", "NUMBER", 0, 12, 20, False),
]

IMPACT = [
    ("IMP-1", "Nombre total de personnes à accès facilité aux infrastructures sanitaires/éducatives", "1"),
    ("IMP-2", "Personnes bénéficiant de services de connectivité", "2"),
    ("IMP-3", "Personnes à nouveaux revenus (dont femmes)", "2"),
    ("IMP-4", "Thèmes de cohésion sociale développés & participation", "1"),
    ("IMP-5", "Taux de satisfaction des bénéficiaires", "3"),
]

EXECUTION = [
    ("EXE-1", "Nombre de séances de sensibilisation"),
    ("EXE-2", "Plans d'action communaux élaborés/mis en œuvre"),
    ("EXE-3", "Plans d'investissement annuels négociés"),
    ("EXE-4", "Thèmes de formation par an"),
    ("EXE-5", "Organisations rurales renforcées"),
    ("EXE-6", "PTBA élaborés dans les délais"),
    ("EXE-7", "Demandes de décaissement envoyées"),
]

EXPENSE_CATEGORIES = [
    ("01", "Travaux"), ("02", "Fourniture"), ("03", "Services consultants et Audit"),
    ("04", "Formation et ateliers"), ("05", "Dons"), ("06", "Charges d'exploitation"),
]

FUNDING_SOURCES = [("WB", "Banque Mondiale"), ("GOV", "Gouvernement (État mauritanien)")]

PROCUREMENT_METHODS = [
    ("AOI", "Appel d'Offres International", None),
    ("AON", "Appel d'Offres National ouvert", None),
    ("CR", "Consultations restreintes", None),
    ("AD", "Achat direct", None),
    ("AD-AFF", "Achat direct par affichage", "AD"),
    ("AD-DEV", "Achat direct par devis concurrentiel", "AD"),
]

PROCUREMENT_STAGES = [
    ("1", "Préparation documents d'AO", 1),
    ("2", "Préparation des offres", 2),
    ("3", "Évaluation des offres", 3),
    ("4", "Signature de contrat", 4),
    ("5", "Paiement", 5),
]

GRIEVANCE_TYPES = [
    ("FONCIER", "Foncier"), ("EMPLOI", "Recrutement/Emploi"), ("INDEMN", "Indemnisation"),
    ("ENVIR", "Environnemental/Social"), ("AUTRE", "Autre"),
]

# username, role, password
DEMO_USERS = [
    ("prdc_admin", "ADMIN", "demo12345"),
    ("prdc_me", "ME_SPECIALIST", "demo12345"),
    ("prdc_validator", "VALIDATOR", "demo12345"),
    ("prdc_auditor", "AUDITOR", "demo12345"),
    ("prdc_field", "FIELD_AGENT", "demo12345"),
    ("prdc_raf", "RAF", "demo12345"),
    ("prdc_proc", "PROCUREMENT_OFFICER", "demo12345"),
]


class Command(BaseCommand):
    help = "Seed (idempotently) the PRDC-VFS reference project."

    @transaction.atomic
    def handle(self, *args, **options):
        roles = self.seed_roles()
        project = self.seed_project()
        milestones = self.seed_milestones(project)
        self.seed_geo(project)
        program = self.seed_program(project)
        types = self.seed_indicator_types(project)
        self.seed_dimensions(project)
        self.seed_indicators(project, types, program, milestones)
        self.seed_finance(project)
        self.seed_procurement(project)
        self.seed_grievance_types(project)
        self.seed_report_templates(project)
        self.seed_users(project, roles)
        self.stdout.write(self.style.SUCCESS("PRDC-VFS seed complete."))

    # ------------------------------------------------------------------ roles
    def seed_roles(self):
        roles = {}
        for code, name in ROLES:
            role, _ = Role.objects.update_or_create(
                code=code, defaults={"name": name, "is_system": True}
            )
            roles[code] = role
        return roles

    # --------------------------------------------------------------- project
    def seed_project(self):
        project, _ = Project.objects.update_or_create(
            code="prdc-vfs",
            defaults=dict(
                name="PRDC-VFS",
                full_name=(
                    "Projet de Résilience et de Développement Communautaire de la Vallée "
                    "du Fleuve Sénégal"
                ),
                currency_code="MRU",
                currency_symbol="UM",
                funder="Banque Mondiale P179449",
                country="Mauritanie",
                fiscal_year_start_month=1,
                grievance_sla_days=30,
            ),
        )
        return project

    def seed_milestones(self, project):
        data = [
            ("BASELINE", "Base de référence", date(2024, 2, 1), 0),
            ("MIDTERM", "Mi-parcours", date(2026, 8, 1), 1),
            ("CLOSING", "Clôture", date(2029, 2, 1), 2),
        ]
        out = {}
        for code, name, target_date, order in data:
            ms, _ = Milestone.objects.update_or_create(
                project=project, code=code,
                defaults={"name": name, "target_date": target_date, "order": order},
            )
            out[code] = ms
        return out

    # -------------------------------------------------------------------- geo
    def seed_geo(self, project):
        levels = {}
        for rank, (name, code) in enumerate(
            [("Wilaya", "WIL"), ("Moughataa", "MOU"), ("Commune", "COM"), ("Village", "VIL")]
        ):
            lvl, _ = GeoLevel.objects.update_or_create(
                project=project, rank=rank, defaults={"name": name, "code": code}
            )
            levels[rank] = lvl
        wil_cache, mou_cache = {}, {}
        for wilaya, moughataa, commune, pop in GEO:
            w = wil_cache.get(wilaya)
            if not w:
                w, _ = GeoUnit.objects.update_or_create(
                    project=project, code=f"WIL-{_slug(wilaya)}",
                    defaults={"geo_level": levels[0], "parent": None, "name": wilaya},
                )
                wil_cache[wilaya] = w
            mkey = (wilaya, moughataa)
            m = mou_cache.get(mkey)
            if not m:
                m, _ = GeoUnit.objects.update_or_create(
                    project=project, code=f"MOU-{_slug(moughataa)}",
                    defaults={"geo_level": levels[1], "parent": w, "name": moughataa},
                )
                mou_cache[mkey] = m
            GeoUnit.objects.update_or_create(
                project=project, code=f"COM-{_slug(commune)}",
                defaults={"geo_level": levels[2], "parent": m, "name": commune, "population": pop},
            )

    # --------------------------------------------------------------- program
    def seed_program(self, project):
        nodes = {}
        for order, (code, name, parent_code) in enumerate(PROGRAM):
            parent = nodes.get(parent_code) if parent_code else None
            node_type = (
                ProgramNode.NodeType.COMPONENT if parent_code is None
                else ProgramNode.NodeType.SUBCOMPONENT
            )
            node, _ = ProgramNode.objects.update_or_create(
                project=project, code=code,
                defaults={"name": name, "parent": parent, "order": order, "node_type": node_type},
            )
            nodes[code] = node
        return nodes

    # ------------------------------------------------------------- indicators
    def seed_indicator_types(self, project):
        out = {}
        for code, name, order in INDICATOR_TYPES:
            it, _ = IndicatorType.objects.update_or_create(
                project=project, code=code, defaults={"name": name, "order": order}
            )
            out[code] = it
        return out

    def seed_dimensions(self, project):
        sex, _ = Dimension.objects.update_or_create(
            project=project, code="SEX", defaults={"name": "Sexe", "order": 0}
        )
        for code, name, order in [("M", "Hommes", 0), ("F", "Femmes", 1)]:
            DimensionCategory.objects.update_or_create(
                dimension=sex, code=code, defaults={"name": name, "order": order}
            )
        age, _ = Dimension.objects.update_or_create(
            project=project, code="AGE", defaults={"name": "Tranche d'âge", "order": 1}
        )
        for code, name, order in [("YOUTH", "Jeunes", 0), ("ADULT", "Adultes", 1)]:
            DimensionCategory.objects.update_or_create(
                dimension=age, code=code, defaults={"name": name, "order": order}
            )

    def _targets(self, indicator, milestones, base, mid, close):
        for ms_code, value in [("BASELINE", base), ("MIDTERM", mid), ("CLOSING", close)]:
            IndicatorTarget.objects.update_or_create(
                indicator=indicator, milestone=milestones[ms_code], geo_unit=None,
                defaults={"value": value},
            )

    def seed_indicators(self, project, types, program, milestones):
        order = 0
        for code, name, _type, _comp, unit, base, mid, close, is_cri in PDO:
            ind, _ = Indicator.objects.update_or_create(
                project=project, code=code,
                defaults=dict(
                    name=name, indicator_type=types["PDO"], program_node=None, unit=unit,
                    aggregation_method=("LAST" if unit == "PERCENTAGE" else "SUM"),
                    is_cri=is_cri, order=order,
                ),
            )
            self._targets(ind, milestones, base, mid, close)
            order += 1
        for code, name, comp, unit, base, mid, close, is_cri in INTERMEDIATE:
            ind, _ = Indicator.objects.update_or_create(
                project=project, code=code,
                defaults=dict(
                    name=name, indicator_type=types["INTERMEDIATE"],
                    program_node=program.get(comp), unit=unit,
                    aggregation_method=("LAST" if unit == "PERCENTAGE" else "SUM"),
                    is_cri=is_cri, order=order,
                ),
            )
            self._targets(ind, milestones, base, mid, close)
            order += 1
        for code, name, comp in IMPACT:
            Indicator.objects.update_or_create(
                project=project, code=code,
                defaults=dict(
                    name=name, indicator_type=types["IMPACT"], program_node=program.get(comp),
                    unit="NUMBER", aggregation_method="LAST", order=order,
                    data_source="Enquêtes Kobo auprès des bénéficiaires",
                ),
            )
            order += 1
        for code, name in EXECUTION:
            Indicator.objects.update_or_create(
                project=project, code=code,
                defaults=dict(
                    name=name, indicator_type=types["EXECUTION"], unit="NUMBER",
                    aggregation_method="SUM", reporting_frequency="QUARTERLY", order=order,
                ),
            )
            order += 1

    # ----------------------------------------------------------------- finance
    def seed_finance(self, project):
        for order, (code, name) in enumerate(EXPENSE_CATEGORIES):
            ExpenseCategory.objects.update_or_create(
                project=project, code=code, defaults={"name": name, "order": order}
            )
        for code, name in FUNDING_SOURCES:
            FundingSource.objects.update_or_create(
                project=project, code=code, defaults={"name": name}
            )

    # ------------------------------------------------------------- procurement
    def seed_procurement(self, project):
        cache = {}
        for order, (code, name, parent_code) in enumerate(PROCUREMENT_METHODS):
            parent = cache.get(parent_code) if parent_code else None
            m, _ = ProcurementMethod.objects.update_or_create(
                project=project, code=code,
                defaults={"name": name, "parent": parent, "order": order},
            )
            cache[code] = m
        for code, name, order in PROCUREMENT_STAGES:
            ProcurementStage.objects.update_or_create(
                project=project, code=code, defaults={"name": name, "order": order}
            )

    def seed_grievance_types(self, project):
        for code, name in GRIEVANCE_TYPES:
            GrievanceType.objects.update_or_create(
                project=project, code=code, defaults={"name": name}
            )

    def seed_report_templates(self, project):
        ReportTemplate.objects.update_or_create(
            project=project, code="QUARTERLY",
            defaults={
                "name": "Rapport trimestriel",
                "structure": {"sections": ["physical", "financial", "procurement", "difficulties"]},
            },
        )
        ReportTemplate.objects.update_or_create(
            project=project, code="ANNUAL",
            defaults={"name": "Rapport annuel", "structure": {"sections": ["physical", "financial", "procurement", "impact"]}},
        )

    # ------------------------------------------------------------------- users
    def seed_users(self, project, roles):
        for username, role_code, password in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"display_name": username, "default_locale": "fr"},
            )
            if created:
                user.set_password(password)
                if role_code == "ADMIN":
                    user.is_staff = True
                    user.is_superuser = True
                user.save()
            ProjectMembership.objects.update_or_create(
                project=project, user=user, defaults={"is_default": True}
            )
            RoleAssignment.objects.update_or_create(
                user=user, role=roles[role_code], project=project,
                scope_geo=None, scope_program=None, defaults={"is_active": True},
            )


def _slug(value):
    import re

    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
