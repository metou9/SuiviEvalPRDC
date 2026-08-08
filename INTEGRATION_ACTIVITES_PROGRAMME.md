# Première intégration métier : Activités → Programme → Indicateurs

Cette version ajoute la première liaison fonctionnelle demandée entre les activités et la structure du programme.

## Changements réalisés

- Le formulaire d'activité affiche désormais un champ obligatoire **Composante / sous-composante**.
- Le formulaire permet d'associer un **indicateur** à l'activité.
- La liste des activités affiche la composante/sous-composante et l'indicateur associés.
- Un filtre par composante/sous-composante a été ajouté à la liste.
- L'API retourne désormais les codes et libellés de la zone, du nœud de programme et de l'indicateur.
- Le backend empêche d'associer un indicateur appartenant à une autre branche du programme.

## Déploiement

Depuis la racine du projet :

```bash
docker compose down
docker compose build --no-cache backend frontend
docker compose up -d
```

Puis vider le cache du navigateur ou ouvrir une fenêtre privée.

## Remarque

Le modèle `Activity` possédait déjà les champs `program_node` et `indicator`. Cette intégration les rend réellement utilisables dans l'interface et renforce leur cohérence côté API. Aucune nouvelle migration de base de données n'est nécessaire pour cette première étape.
