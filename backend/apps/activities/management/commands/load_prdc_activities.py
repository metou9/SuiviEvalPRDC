from django.core.management.base import BaseCommand
from django.db import transaction

from apps.activities.models import Activity
from apps.core.models import Project
from apps.program.models import ProgramNode


# ======================================================================
# REFERENTIEL DES ACTIVITES PRDC-VFS
#
# Champs chargés :
# - code
# - title
# - program_node = sous-composante
#
# La composante est déduite automatiquement via :
# activity.program_node.parent
# ======================================================================


ACTIVITIES = [

    # ==================================================================
    # COMPOSANTE 1
    # SOUS-COMPOSANTE 1A
    # ==================================================================

    ("1A01", "Const et Réhab des Infrast com de Dar Elbarka", "1A"),
    ("1A02", "Const et Réhab infrast com Dar Avia", "1A"),
    ("1A03", "Const et Réhab infrast com Boghé", "1A"),
    ("1A04", "Const et Réhab infrast com Bababé", "1A"),
    ("1A05", "Const et Réhab infrast com M bagne", "1A"),
    ("1A06", "Const et Réhab infrast com Tifon de Civé", "1A"),
    ("1A07", "Const et Réhabi infrast com de Kaédi", "1A"),
    ("1A08", "Const et Réhab infrast com de Gouraye", "1A"),
    ("1A09", "Const et Réhab infrast com de Ghabou", "1A"),
    ("1A10", "Const et Réhab infrast com de Selibaby", "1A"),
    ("1A11", "Const et Réhab infrast com de Wompou", "1A"),
    ("1A12", "Const et Réhab infrast com de Keur Macene", "1A"),
    ("1A13", "Const et Réhab infrast com de Lexeiba 2", "1A"),
    ("1A14", "Const et Réhab infrast com de Tekane", "1A"),
    ("1A15", "Const et Réhab infrast com de N diago", "1A"),
    ("1A16", "Const et Réhab infrast com de Jidr Elmohgen", "1A"),
    ("1A17", "Const et Réhab infrast com de Rosso", "1A"),
    ("1A18", "Mobilisat ONG appui Communes", "1A"),


    # ==================================================================
    # COMPOSANTE 1
    # SOUS-COMPOSANTE 1B
    # ==================================================================

    ("1B01", "Recruter quatre cabinet (...) environnemental des projets", "1B"),
    ("1B02", "Ident de Points Focaux EAS-HS (...) la promo de la femme", "1B"),
    ("1B03", "Org des réunions communaut (...) mitigation des risques VBG", "1B"),
    ("1B04", "Actual la cartogr des acteurs en matière de VBG (...) capacité", "1B"),
    ("1B05", "Mettre en place un syst de coord (...) prévent prise en charg", "1B"),
    ("1B06", "Elab Mécan de Ges Plaintes (MGP) Projet et sa déclin ttes", "1B"),
    ("1B07", "Création numéro vert et sa diffusion pour la reception des p", "1B"),
    ("1B08", "Elab des Code de Conduite (...) personnels impliqués cadre du", "1B"),
    ("1B09", "Org de quatre ateliers de com (...) Projet sur les VBG/EAS-HS", "1B"),
    ("1B10", "Org de séance de travail avec le SPM (...) spécifiques relativ", "1B"),
    ("1B11", "Org en deux visite d'échanges entre les Maire (...) Maires de", "1B"),
    ("1B12", "Org visite d'échanges entre les cadres de l'UGP MR (...) l'id", "1B"),
    ("1B13", "Faire le diagnostic des CCC (cadres de concertation communau", "1B"),
    ("1B14", "Org une session d'une journée à Nouakchott pour le cadrage d", "1B"),
    ("1B15", "Org des missions régulières de coaching du travail des ONG s", "1B"),
    ("1B16", "Org quatre mini-ateliers portant sur le renforcement de la c", "1B"),
    ("1B17", "org ateliers de capacit des commu et des comm not les fem;je", "1B"),
    ("1B18", "Organisation d'un forum pour les Jeunes de la VFS", "1B"),
    ("1B19", "Recrutement d'un opérateur spécialisé pour l'accompagnement,", "1B"),
    ("1B20", "Appui org semaine culturelle à Rosso", "1B"),
    ("1B21", "Appui org semaine culturelle à Boghé", "1B"),
    ("1B22", "Appui org semaine culturelle à Kaédi", "1B"),
    ("1B23", "Appui org semaine culturelle à Selibaby", "1B"),
    ("1B24", "Appui org semaine culturelle à Gouraye", "1B"),
    ("1B25", "Traduction des Codes de Conduite interdisant toutes formes d", "1B"),
    ("1B26", "Recrutement de 4 ONG pour la sensibilisation sur les VBG/EAS", "1B"),
    ("1B27", "Rencontre de concertation avec les maires autour des disposi", "1B"),
    ("1B28", "Partic au forum des pêcheurs sur la rive gauche de la VFS", "1B"),
    ("1B29", "Org d'activité transfrontaliere Trarza avec UGP Senegal", "1B"),
    ("1B30", "Org d'activité transfrontaliere Brakna avec UGP Senegal", "1B"),
    ("1B31", "Org d'activité transfrontaliere Gorgol avec UGP Senegal", "1B"),
    ("1B32", "Org d'activité transfrontaliere Guidimagha avec UGP Senegal", "1B"),


    # ==================================================================
    # COMPOSANTE 2
    # SOUS-COMPOSANTE 2A
    # ==================================================================

    ("2A01", "Réal initiative pilote intég en faveur (...) Sélibaby, Tifondé", "2A"),
    ("2A02", "Réal Etude pour la faisabilité d'une bretelle de 9 Km (...) re", "2A"),
    ("2A03", "Réal piste rurale de 0,5 Km au niveau du PK 10", "2A"),
    ("2A04", "Etude de réel piste de désenclavement entre N'Diago et Ghaïri", "2A"),
    ("2A05", "Etude de réel piste (...) entre l'école de sedigh zire et le v", "2A"),
    ("2A06", "Etude de réel piste rurale de désend entre FASS 1 et la ro", "2A"),
    ("2A07", "Etude réhabi d'une piste rurale en remblais à Moissaniawly p", "2A"),
    ("2A08", "Etude et trav de réel piste rurale (...) à Sekam el maradine p", "2A"),
    ("2A09", "Etuder réel digue de protec au niveau du village de Ehl Yous", "2A"),
    ("2A10", "Etude réel piste (...) Gourel Bocar Sy, Gourel Sarr et Oulou", "2A"),
    ("2A11", "Etude de réel piste de désend entre Tekane et Dar Selam lon", "2A"),
    ("2A12", "Etude de faisab digue de protec El Barka et Diatar", "2A"),
    ("2A13", "Etude de mise en place digue de protec (...) Diatar sur une ét", "2A"),
    ("2A14", "Etude de la mise en place digue (...) villages Donaye et Vethi", "2A"),
    ("2A15", "Etude pour la const piste désend (...) Mivtah Kheir, Chabour", "2A"),
    ("2A16", "Etude de la construction d'une digue de pritection à Pongel", "2A"),
    ("2A17", "Etude pour la réalouvrage rurale désend Boghé et Bakaw", "2A"),
    ("2A18", "Etude de réal piste rurale désencl axe M'Bagne, Dabé, Dabane", "2A"),
    ("2A19", "Etude pour la réhab et confot digue (...) population de 2800", "2A"),
    ("2A20", "Etude réhabi digue de protecventre Tantadji, legal Kaeidi et", "2A"),
    ("2A21", "Réal d'un pavage en pierré maçonné d'une piste d'accès et d", "2A"),
    ("2A22", "Aménag espace vert (...)commune au niveau de Kaeidi", "2A"),
    ("2A23", "Aménag place pub au bord du fleuvre ( pavage, banc publics,", "2A"),
    ("2A24", "Etude de la réal piste rurale entre Ehl Wanou, l'Islam et Go", "2A"),
    ("2A25", "Etude pour la réal confort d'une digue (...) périmètres rizico", "2A"),
    ("2A26", "Etude de réali ouvrage de franch entre wompou et Taghoutalla", "2A"),
    ("2A27", "etude pour Realisation des pistes rur pour facili connect av", "2A"),

    # 2A28 n'est pas présent dans le fichier source.

    ("2A29", "Recruter quatre cabinet (...)environmental des projets", "2A"),
    ("2A30", "Signer et mettre en oeuvre la conv de partenariat avec DECE", "2A"),
    ("2A31", "trav const ouvrage franchissent entre wompu et Taghoutallah", "2A"),
    ("2A32", "etude realis piste rurale entre Ghabou et Sabou Ciré de 7 Km", "2A"),
    ("2A33", "Etude desencl des zone Begheré et Debaye Hamedou et Ehel Sid", "2A"),
    ("2A34", "etude pour Réalis Cartogr des zones inondées à GOURAYE", "2A"),
    ("2A35", "Etude pour la protect de la ville de Djaguily", "2A"),
    ("2A36", "Trav Réha Digue de protect Diatar 1.2 KM Dar El Barka", "2A"),
    ("2A37", "Trav Réal Piste Rural entre Dabane et Winding 1.5 Km M'bagne", "2A"),
    ("2A38", "Trav de Réal de digue de Protect à Vethi 1.7 km Dar el Bark", "2A"),
    ("2A39", "Réalis Ouvrage Franchissement à Bababé et Toulel Drogo", "2A"),
    ("2A40", "etude Réal du réseau d'eau et Raccord du villag du Baghdad", "2A"),
    ("2A41", "Réalis piste Rurale Haimedath et dwalel et piste en laterite", "2A"),
    ("2A42", "Réal d'une digue de Protect entre légal Kaédi et Fleuve Séné", "2A"),
    ("2A43", "Etude de Réhab de deux ouvr de franchiss à Toufondé civé", "2A"),
    ("2A44", "Trv de réha d'une piste rurale de 3.27 km entre moisse Niawl", "2A"),
    ("2A45", "Trv de réhab et d'ext de la digue de protect de Baghdad", "2A"),


    # ==================================================================
    # COMPOSANTE 2
    # SOUS-COMPOSANTE 2B
    # ==================================================================

    ("2B01", "Sélection d'un prestataire spécialisé (...) et la proposition", "2B"),
    ("2B02", "Etude typologique des filières", "2B"),
    ("2B03", "Acquisition d'un drone DJI Matrice 350 RTK pour le suivi des", "2B"),
    ("2B04", "Initiative pilote en faveur des jeunes au Trarza & Brakna", "2B"),
    ("2B05", "Portefeuille AGR", "2B"),
    ("2B06", "Org de 4 ateliers régionaux portant sur l'améliorat des con", "2B"),
    ("2B07", "Etude d'une cartographie des vulnérabilités et des risques c", "2B"),
    ("2B08", "Recruter des cabin spec pour réaliser des instrum de sauvgar", "2B"),
    ("2B09", "org des ateliers des form sur les normes env et social de BM", "2B"),


    # ==================================================================
    # COMPOSANTE 3
    # SOUS-COMPOSANTE 3A
    # ==================================================================

    ("3A01", "Personnel UGP", "3A"),
    ("3A02", "Prép et organ d'ateliers régionaux de sensibilisation, d'inf", "3A"),
    ("3A03", "Frais Fonctionnement UGP", "3A"),
    ("3A04", "Frais de mission", "3A"),
    ("3A05", "Mission d'échange et de partage avec le PRDC-VFS-SN", "3A"),
    ("3A06", "Entretien et reparation vehicules", "3A"),
    ("3A07", "Carburant vehicules", "3A"),
    ("3A08", "Logiciels comptable", "3A"),
    ("3A09", "Mobiliers de bureau", "3A"),
    ("3A10", "Matériels informatiques", "3A"),
    ("3A11", "Matériel de froid", "3A"),
    ("3A12", "Strategie et plan de comm", "3A"),
    ("3A13", "Site web & outils de communication en ligne", "3A"),
    ("3A14", "Supports et outils de visibilité (Teeshert, cascettes, Agend", "3A"),
    ("3A15", "Supports de comm (videos, flyers, banderolles, supports numé", "3A"),
    ("3A16", "Convention avec Radio Mauritanie", "3A"),
    ("3A17", "Frais d'insertion et de publication des avis", "3A"),
    ("3A18", "Communication sociale", "3A"),
    ("3A19", "Ateliers d'habil profit du personnel de l'UGP, antennes incl", "3A"),
    ("3A20", "Atelier interne/retraite de l'équipe du projet pour faire le", "3A"),
    ("3A21", "Org des ateliers régionnaux de sensibilisation et de diffusi", "3A"),
    ("3A22", "Atelier/retraite annuel pour la capitalisation annuelle des", "3A"),
    ("3A23", "Appui à la tenue des réunions des CRD (Comites Regionaux de", "3A"),
    ("3A24", "Ateliers régionaux de partage et de validation du Manuel de", "3A"),
    ("3A25", "Etude de la situation de référence du projet PRDC_VFS", "3A"),
    ("3A26", "Formation des Assistants en suivi-évaluation et des disposi", "3A"),
    ("3A27", "Ateliers d'initiation et d'apprentissage en suivi-évaluation", "3A"),
    ("3A28", "Seminaires d'autoévaluation participative avec les communauté", "3A"),
    ("3A29", "Mise en place d'une base de données pour le S&E", "3A"),
    ("3A30", "Audit externe", "3A"),
    ("3A31", "Préparation et signature d'une convention de partenariat ave", "3A"),
    ("3A32", "Préparer et signer une convention de collaboration et de par", "3A"),
    ("3A33", "Aquisition d'un véhicule station wagon et de quatre double c", "3A"),
    ("3A34", "Appui à l'aquisition des semences et intrants pour le MASA", "3A"),
    ("3A35", "Atelier de partage et diffusion Manuel SP", "3A"),
    ("3A36", "Achat vehicule Toyota corolla", "3A"),
    ("3A37", "Achat 13 vehicules pour le compte de Projet", "3A"),
    ("3A38", "Atelier de lancement du projet", "3A"),
    ("3A39", "Atelier de partage et diffusion Manuel de passation de march", "3A"),
    ("3A40", "Brochures du PRDC avec impression", "3A"),
    ("3A41", "Impression et diffusion du manuel des sous projet dans les", "3A"),
    ("3A42", "Assistance et maintenance sur le logiciel comptable TOMPRO", "3A"),
    ("3A43", "Acquisition d'une application pour les paiements", "3A"),
    ("3A44", "Appui à l'aquisition des intrants (engrais) pour le MASA", "3A"),
    ("3A45", "Mise en œuvre d'un réseau de bornes géodésiques (120 bornes", "3A"),
    ("3A46", "Contribuer à la relais d'un progr pilote de 10 ha du MASA", "3A"),
    ("3A47", "Supports de communication annuels (Agendas, calendriers, sty", "3A"),
    ("3A48", "Diffusion de capsule vidéo présentant des success stories", "3A"),
    ("3A49", "Campagne sensibilisation scolaire : gadgets (tee-shorts, sac", "3A"),
    ("3A50", "Formation des médias locaux", "3A"),
    ("3A51", "Mise en place de relais communautaires (clubs de jeunes et f", "3A"),
    ("3A52", "Confection de panneaux de visibilité du projet", "3A"),
    ("3A53", "Conduite d'une étude sur la situation de référence", "3A"),
    ("3A54", "DRF", "3A"),


    # ==================================================================
    # COMPOSANTE 3
    # SOUS-COMPOSANTE 3B
    #
    # Les codes historiques des activités restent 1C01 à 1C19,
    # mais elles appartiennent désormais à la sous-composante 3B.
    # ==================================================================

    ("1C01", "Recrutement de 17 ADC pour appuyer techniquement les commune", "3B"),
    ("1C02", "Recrut d'un cabinet pour les besoins de format des consei", "3B"),
    ("1C03", "Orga d'un voyage d'études et de partage d'expérience entre", "3B"),
    ("1C04", "Signature d'une convention de partenariat avec l'AMM", "3B"),
    ("1C05", "Recrutement de quatre ONG pour la sensibilisant su MGP", "3B"),
    ("1C06", "Org d'ateliers de sensib à l'endroit sur MGP et code VBG/EAS", "3B"),
    ("1C07", "Organisation d'ateliers périodiques au profit des CGP", "3B"),
    ("1C08", "Reprographie du Manuel de gestion des plaintes", "3B"),
    ("1C09", "Form et accom de l'équipe du projet sur la mut des conn et", "3B"),
    ("1C10", "Appuyer le groupe parlementaire en charge du DL par le recru", "3B"),
    ("1C11", "Formation des membres du Groupe parlementaire sur les module", "3B"),
    ("1C12", "Org des mis de terrain pour le suivi des proj et pro de DL", "3B"),
    ("1C13", "Appui institutionnel aux comités villageois de veille (CVV)", "3B"),
    ("1C14", "Formation de 795 membres de CVV", "3B"),
    ("1C15", "Prise en charge du plan d'action du CRC (Comité régional de", "3B"),
    ("1C16", "Appui à la prise en charge des réunions de la commission rég", "3B"),
    ("1C17", "Appui en intrants agricoles au MASA + Appui aux inondations", "3B"),
    ("1C18", "Appui à la mise en valeur du site pilote du MASA", "3B"),
    ("1C19", "Aquisit d'un véhicule station wagon et de quatre double cabi", "3B"),


    # ==================================================================
    # COMPOSANTE 3
    # SOUS-COMPOSANTE 3C
    # ==================================================================

    ("3B01", "Signature d'une convention de partenariat et de collaboratio", "3C"),
    ("3B02", "Renforc de capacites du personnel plan de format 2025", "3C"),
    ("3B03", "Signat de conv de partenar avec les Maires AMM", "3C"),
    ("3B04", "Mise en oeuvre des Plans d'action prioritaires des PMA-GC", "3C"),
    ("3B05", "Etude et mise en oeuvre d'une action pilote de decarbonation", "3C"),
]


# ======================================================================
# COMMANDE DJANGO
# ======================================================================

class Command(BaseCommand):

    help = (
        "Charge le référentiel des activités PRDC-VFS "
        "avec code, intitulé et sous-composante."
    )

    @transaction.atomic
    def handle(self, *args, **options):

        # ==================================================================
        # 1. RECHERCHE DU PROJET
        # ==================================================================

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


        # ==================================================================
        # 2. VERIFICATION DES DOUBLONS
        # ==================================================================

        seen = set()
        duplicates = set()

        for code, title, subcomponent_code in ACTIVITIES:

            if code in seen:
                duplicates.add(code)

            seen.add(code)

        if duplicates:
            raise ValueError(
                "Codes d'activités dupliqués : "
                + ", ".join(sorted(duplicates))
            )


        # ==================================================================
        # 3. RECHERCHE DES SOUS-COMPOSANTES
        # ==================================================================

        required_subcomponents = sorted({
            subcomponent_code
            for _, _, subcomponent_code in ACTIVITIES
        })

        subcomponents = {}


        for subcomponent_code in required_subcomponents:

            program_node = (
                ProgramNode.objects
                .filter(
                    project=project,
                    code__iexact=subcomponent_code,
                    node_type=ProgramNode.NodeType.SUBCOMPONENT,
                )
                .select_related("parent")
                .first()
            )


            if program_node is None:

                self.stderr.write(
                    self.style.ERROR(
                        f"Sous-composante introuvable : "
                        f"{subcomponent_code}"
                    )
                )

                self.stderr.write(
                    self.style.ERROR(
                        "Le chargement est annulé afin de ne pas "
                        "créer des activités mal rattachées."
                    )
                )

                raise ValueError(
                    f"La sous-composante "
                    f"{subcomponent_code} "
                    f"n'existe pas dans ProgramNode."
                )


            if program_node.parent is None:

                raise ValueError(
                    f"La sous-composante "
                    f"{subcomponent_code} "
                    f"n'a pas de composante parente."
                )


            if (
                program_node.parent.node_type
                != ProgramNode.NodeType.COMPONENT
            ):

                raise ValueError(
                    f"Le parent de la sous-composante "
                    f"{subcomponent_code} "
                    f"n'est pas une composante."
                )


            subcomponents[
                subcomponent_code
            ] = program_node


            self.stdout.write(
                self.style.SUCCESS(
                    f"{subcomponent_code} : "
                    f"{program_node.name} "
                    f"→ Composante "
                    f"{program_node.parent.code} "
                    f"{program_node.parent.name}"
                )
            )


        # ==================================================================
        # 4. CREATION / MISE A JOUR DES ACTIVITES
        #
        # Important :
        #
        # Si l'activité existe déjà :
        # - title est mis à jour
        # - program_node est mis à jour
        #
        # Les autres champs NE SONT PAS TOUCHES :
        # - geo_unit
        # - responsible
        # - unit
        # - indicator
        # - objective
        # - description
        # - participants
        # etc.
        # ==================================================================

        created_count = 0
        updated_count = 0


        for (
            activity_code,
            activity_title,
            subcomponent_code,
        ) in ACTIVITIES:

            program_node = (
                subcomponents[
                    subcomponent_code
                ]
            )


            activity, created = (
                Activity.objects.update_or_create(
                    project=project,
                    code=activity_code,

                    defaults={
                        "title": activity_title,
                        "program_node": program_node,
                    },
                )
            )


            if created:

                created_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Créée : "
                        f"{activity_code} — "
                        f"{activity_title} "
                        f"[{program_node.code}]"
                    )
                )

            else:

                updated_count += 1

                self.stdout.write(
                    f"Mise à jour : "
                    f"{activity_code} — "
                    f"{activity_title} "
                    f"[{program_node.code}]"
                )


        # ==================================================================
        # 5. RESULTAT
        # ==================================================================

        total_in_db = (
            Activity.objects
            .filter(
                project=project,
                code__in=[
                    code
                    for code, _, _ in ACTIVITIES
                ],
            )
            .count()
        )


        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "=============================================="
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "CHARGEMENT DES ACTIVITES TERMINE"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "=============================================="
            )
        )

        self.stdout.write(
            f"Projet : {project.name}"
        )

        self.stdout.write(
            f"Activités du référentiel : "
            f"{len(ACTIVITIES)}"
        )

        self.stdout.write(
            f"Activités créées : "
            f"{created_count}"
        )

        self.stdout.write(
            f"Activités mises à jour : "
            f"{updated_count}"
        )

        self.stdout.write(
            f"Activités retrouvées en base : "
            f"{total_in_db}"
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Chaque activité possède maintenant :"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "- son code"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "- son intitulé"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "- sa sous-composante"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "- sa composante via la sous-composante"
            )
        )