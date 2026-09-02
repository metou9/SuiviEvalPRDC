from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.models import Project
from apps.geo.models import GeoLevel, GeoUnit


# ======================================================================
# DONNEES GEOGRAPHIQUES PRDC-VFS
#
# Source :
# LISTE DES COMMUNES D’INTERVENTION DU PRDC-VFS EN MAURITANIE
# ======================================================================

GEOGRAPHY = {

    "Gorgol": {

        "Kaédi": [
            "Kaédi",
            "Toufoundé Civé",
            "Néré Walo",
            "Djéol",
            "Tokomadji",
        ],

        "Maghama": [
            "Maghama",
            "Dolol",
            "Daw",
            "Waly",
            "Toulel",
            "Sagué",
        ],
    },


    "Trarza": {

        "Rosso": [
            "Rosso",
            "Jidr Mohgen",
        ],

        "Tekane": [
            "Tekane",
            "Lexeiba",
            "Chemama",
        ],

        "Keurmacène": [
            "Keurmacène",
            "N’Diago",
            "M’Balal",
        ],
    },


    "Brakna": {

        "Boghé": [
            "Boghé",
            "Ould Birome",
        ],

        "Bababé": [
            "Bababé",
            "Aéré M’Bare",
        ],

        "M’Bagne": [
            "M’Bagne",
            "Niabina",
            "Bagodine",
        ],
    },


    "Guidimakha": {

        "Sélibaby": [
            "Sélibaby",
        ],

        "Ghabou": [
            "Ghabou",
            "Gouraye",
            "Diougountourou",
        ],

        "Wompou": [
            "Wompou",
            "Sagué Diéri",
        ],
    },
}


# ======================================================================
# CODES
# ======================================================================

WILAYA_CODES = {
    "Gorgol": "GOR",
    "Trarza": "TRA",
    "Brakna": "BRA",
    "Guidimakha": "GUI",
}


MOUGHATAA_CODES = {
    ("Gorgol", "Kaédi"): "GOR-KAE",
    ("Gorgol", "Maghama"): "GOR-MAG",

    ("Trarza", "Rosso"): "TRA-ROS",
    ("Trarza", "Tekane"): "TRA-TEK",
    ("Trarza", "Keurmacène"): "TRA-KEU",

    ("Brakna", "Boghé"): "BRA-BOG",
    ("Brakna", "Bababé"): "BRA-BAB",
    ("Brakna", "M’Bagne"): "BRA-MBA",

    ("Guidimakha", "Sélibaby"): "GUI-SEL",
    ("Guidimakha", "Ghabou"): "GUI-GHA",
    ("Guidimakha", "Wompou"): "GUI-WOM",
}


# ======================================================================
# COMMANDE
# ======================================================================

class Command(BaseCommand):

    help = (
        "Remplace les unités géographiques du projet PRDC-VFS "
        "par les Wilaya, Moughataa et Communes du document officiel."
    )


    @transaction.atomic
    def handle(self, *args, **options):

        # ==============================================================
        # PROJET
        # ==============================================================

        project = (
            Project.objects
            .filter(code__iexact="prdc-vfs")
            .first()
        )


        if project is None:

            project = (
                Project.objects
                .filter(name__icontains="PRDC-VFS")
                .first()
            )


        if project is None:

            self.stderr.write(
                self.style.ERROR(
                    "Projet PRDC-VFS introuvable."
                )
            )

            return


        self.stdout.write(
            self.style.SUCCESS(
                f"Projet trouvé : {project.name}"
            )
        )


        # ==============================================================
        # NIVEAUX GEOGRAPHIQUES
        # ==============================================================

        wilaya_level, _ = (
            GeoLevel.objects.update_or_create(
                project=project,
                code="WIL",
                defaults={
                    "name": "Wilaya",
                    "name_plural": "Wilayas",
                    "rank": 0,
                },
            )
        )


        moughataa_level, _ = (
            GeoLevel.objects.update_or_create(
                project=project,
                code="MOU",
                defaults={
                    "name": "Moughataa",
                    "name_plural": "Moughataas",
                    "rank": 1,
                },
            )
        )


        commune_level, _ = (
            GeoLevel.objects.update_or_create(
                project=project,
                code="COM",
                defaults={
                    "name": "Commune",
                    "name_plural": "Communes",
                    "rank": 2,
                },
            )
        )


        # ==============================================================
        # SUPPRESSION DES ANCIENNES UNITES
        #
        # On supprime UNIQUEMENT les GeoUnit du projet PRDC-VFS.
        # Les GeoLevel sont conservés et normalisés ci-dessus.
        # ==============================================================

        old_count = (
            GeoUnit.objects
            .filter(project=project)
            .count()
        )


        GeoUnit.objects.filter(
            project=project
        ).delete()


        self.stdout.write(
            f"Anciennes unités supprimées : {old_count}"
        )


        # ==============================================================
        # CREATION
        # ==============================================================

        wilaya_count = 0
        moughataa_count = 0
        commune_count = 0


        for wilaya_name, moughataas in GEOGRAPHY.items():

            # ----------------------------------------------------------
            # WILAYA
            # ----------------------------------------------------------

            wilaya_code = (
                WILAYA_CODES[wilaya_name]
            )


            wilaya = (
                GeoUnit.objects.create(
                    project=project,
                    geo_level=wilaya_level,
                    parent=None,
                    name=wilaya_name,
                    code=wilaya_code,
                    is_active=True,
                )
            )


            wilaya_count += 1


            self.stdout.write(
                f"WILAYA : {wilaya_name}"
            )


            for moughataa_name, communes in moughataas.items():

                # ------------------------------------------------------
                # MOUGHATAA
                # ------------------------------------------------------

                moughataa_code = (
                    MOUGHATAA_CODES[
                        (
                            wilaya_name,
                            moughataa_name,
                        )
                    ]
                )


                moughataa = (
                    GeoUnit.objects.create(
                        project=project,
                        geo_level=moughataa_level,
                        parent=wilaya,
                        name=moughataa_name,
                        code=moughataa_code,
                        is_active=True,
                    )
                )


                moughataa_count += 1


                self.stdout.write(
                    f"  MOUGHATAA : {moughataa_name}"
                )


                for index, commune_name in enumerate(
                    communes,
                    start=1,
                ):

                    # --------------------------------------------------
                    # COMMUNE
                    # --------------------------------------------------

                    commune_code = (
                        f"{moughataa_code}-"
                        f"{index:02d}"
                    )


                    GeoUnit.objects.create(
                        project=project,
                        geo_level=commune_level,
                        parent=moughataa,
                        name=commune_name,
                        code=commune_code,
                        is_active=True,
                    )


                    commune_count += 1


                    self.stdout.write(
                        f"    COMMUNE : {commune_name}"
                    )


        # ==============================================================
        # RESULTAT
        # ==============================================================

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Chargement géographique terminé."
            )
        )


        self.stdout.write(
            self.style.SUCCESS(
                f"Wilayas : {wilaya_count}"
            )
        )


        self.stdout.write(
            self.style.SUCCESS(
                f"Moughataas : {moughataa_count}"
            )
        )


        self.stdout.write(
            self.style.SUCCESS(
                f"Communes : {commune_count}"
            )
        )


        total = (
            wilaya_count +
            moughataa_count +
            commune_count
        )


        self.stdout.write(
            self.style.SUCCESS(
                f"Total GeoUnit : {total}"
            )
        )