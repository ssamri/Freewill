# Journal des modifications

[English](CHANGELOG.md) · **Français**

## 1.0.0

Le laboratoire de recherche, et les premières choses qu'une vie peut entraîner. Rien dans cette version n'affirme qu'un système est conscient ou ressent quoi que ce soit.

**Ajouté**

- Des réglages de recherche pour chaque vie : 26 interrupteurs et 7 nombres bornés, chacun retirant ou rétablissant un mécanisme de la boucle de vie. Chaque valeur par défaut reproduit la boucle d'avant ; chaque changement est écrit au journal d'événements ; aucun n'atteint le noyau.
- Le laboratoire de recherche : contrats versionnés, journal de preuves en ajout seul, empreintes d'état, statistiques déterministes qui refusent les petits échantillons, registre de métriques pour H1 à H10, protocoles verrouillés et hachés avant exécution, campagnes sur des copies isolées d'une vie sous horloge virtuelle, observateurs A, B et C qui lisent et n'agissent jamais, rapports en Markdown et en PDF avec un pack de reproduction, validés seulement par une personne.
- H8, métacognition : l'être prédit ses propres décisions, compare, et lève une alerte quand sa manière de décider a changé, sans accès à la cause.
- H9, sommeil en phases : repos, relecture, rêve, consolidation, réveil. Chacune peut être retirée. Un sommeil coupé reprend à la phase qu'il avait atteinte.
- H10, agentivité : un acte par instant dans un monde clos en grille, prédit, observé et attribué à soi ou au monde. Aucune action nouvelle dans le noyau.
- H4, plasticité : un petit module entraînable (Python pur) ; le réseau de neurones propre à Freewill, entraîné pendant le sommeil sur le texte qu'un être a vécu, gardé seulement quand il prédit mieux du texte jamais vu, capable d'ajouter des couches sous un plafond, avec retour possible aux poids précédents (demande PyTorch) ; des adaptateurs à côté d'un modèle de base figé (LoRA), vérifiés sur un modèle jouet seulement.
- Six protocoles exécutables (EXP-01, 02, 03, 04, 06, 07) et leurs résultats réels dans `experiments/v1.0/`.
- Dans l'application : le laboratoire, une page « Apprentissage », les réglages de recherche, des jauges dans la barre du haut, l'export des traces.
- L'anglais est la langue par défaut de l'interface ; le français se choisit dans les réglages. Un test échoue si les deux catalogues n'ont pas les mêmes clés, partagent une phrase non traduite ou contiennent des mots de l'autre langue.
- `docs/research/IMPLEMENTATION_STATUS.fr.md` : ce qui existe, ce qui a été testé, ce qui manque.

**Modifié**

- Les souvenirs sont datés par l'horloge propre de l'être, pour que le temps d'une expérience soit celui de l'expérience.
- Le fichier qui liste la bibliothèque d'une vie est écrit de façon atomique.
- `QUICKSTART.md` est désormais en anglais seulement ; le texte français est dans `QUICKSTART.fr.md`.

**Limites connues**

- Le moteur qui pense pour un être n'est jamais entraîné par sa vie.
- Le réseau propre de Freewill ne participe pas à la pensée et ne grandit qu'en profondeur.
- Les campagnes ont tourné sur le moteur simulé seulement. Aucun modèle distant n'a été appelé et aucune carte graphique n'a été utilisée pour construire ou tester cette version.
- EXP-05 et EXP-08 ne sont que des spécifications.

## 0.3.0

H7 : un état affectif calculé, désactivé par défaut, avec son protocole et ses résultats.

## 0.2.0

Bibliothèque (documents, images, images fixes de vidéos), sommeil et rêves, application de bureau.
