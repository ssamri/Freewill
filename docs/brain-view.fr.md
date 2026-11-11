# La vue Cerveau

[English](brain-view.md) · **Français**

La vue représente la mémoire et l'attention de Freewill dans un volume Three.js.
Sa silhouette anatomique vient du modèle de Neural Network Prototype, utilisé
sous licence MIT. Le réseau affiché ne représente pas les neurones du modèle de
langage et les zones ne sont pas des lobes biologiques mesurés.

## Ce qui pilote la lumière

| Donnée de Freewill | Effet dans la vue |
| --- | --- |
| `stage` | Flux de la source sélectionnée vers la scène centrale ; concurrents plus discrets, saillance prise en compte |
| `recall` | Le souvenir indiqué s'allume et rejoint la scène ; sa force et son état sont actualisés |
| `remember` | Signal vers le souvenir réellement conservé, même si son chargement arrive après l'événement |
| `decision` | Réponse lumineuse centrale distincte pour accueillir ou écarter |
| `speech` | Flux de sortie vers la zone de conversation |
| `read` | Activation de la zone de lecture |
| `sleep`, `dream`, `rest` | Mode sommeil, activation des souvenirs participant au rêve et retour à l'état courant |
| `snapshot.needs` | Intensité continue de l'état des besoins ; aucun faux événement périodique |
| `/api/memory` | Nœuds, compartiments, forces et liens enregistrés entre souvenirs |

Les fibres cyan de la silhouette sont illustratives. Les liens de mémoire sont
construits exclusivement à partir des identifiants `links` enregistrés, puis
dédupliqués. Les chemins source/scène expriment les fonctions de l'application.
La vue ne crée ni souvenir, ni association persistante, ni activité cognitive.
L'historique peut être lu dans le panneau ; il ne rejoue pas une activité passée
comme si elle venait de se produire.

Le noyau central (« Noyau · soi ») est dessiné en volume : des pétales
translucides bleus, violets et roses autour d'un cœur lumineux, sur le modèle de
l'icône de Freewill. Sa forme, sa lente rotation et sa respiration sont
décoratives ; sa luminosité suit le niveau réel du soi (décisions, sommeil). Il
garde une étiquette persistante et reste sélectionnable. Les souvenirs restent visibles comme points cerclés et
contrastés ; plusieurs titres sont présentés sans survol, avec priorité aux
souvenirs récemment rappelés. Les repères évitent les recouvrements et les titres
viennent des données enregistrées. Le tissu de fond reste plus discret que ces
éléments, y compris pendant les vagues d'activité.

## Exploration

- Glisser et utiliser la molette pour tourner et zoomer.
- Sélectionner une source pour inspecter sa fonction et son poids réel.
- Cliquer sur un souvenir pour ouvrir son récit.
- Utiliser Rotation, Mouvement, Figer la vue et Recentrer pour régler le rendu.
- Au clavier : Tab pour les commandes, Espace pour figer la vue, Home ou 0 pour recentrer lorsque le canvas a le focus.

Figer la vue n'arrête pas la vie de l'être. Le statut affiché vient du serveur :
réflexion, sommeil, attente, limite horaire, nouvel essai ou pause du moteur.
Les préférences système de réduction du mouvement sont respectées.

## Architecture et distribution

`brain.js` conserve l'interface indépendante de la boucle cognitive :
`setMemories`, `stage`, `recall`, `remember`, `decision`, `speech`, `read`,
`dream`, `setNeeds`, `setAsleep`, `setSnapshot`, `setControls` et `destroy`.

Le rendu utilise des géométries groupées, des shaders d'activation, un nombre
borné de signaux et une grille spatiale pour construire les fibres. Aucun CDN
n'est utilisé. `three.bundle.js`, `brain-shape.js` et les notices sont embarqués
par setuptools et PyInstaller. En l'absence de WebGL, `brain-canvas.js` fournit
un rendu de secours. Le guide de construction est dans `tooling/brain/README.md`.

Les événements de rappel transmettent directement la force, l'état et la phase
du souvenir ; cela évite de relire toute la mémoire à chaque rappel. Les requêtes
de chargement sont sérialisées et les réponses anciennes ne remplacent pas les
forces connues plus récentes.

Les fichiers souvenirs et leurs index sont publiés par remplacement atomique afin
que l'interface ne lise pas un fichier partiel pendant un rappel ou le sommeil.

## Vérification

La suite Python vérifie notamment les états courants pendant le sommeil et les
erreurs, ainsi que les forces transmises pour les rappels conscients et nocturnes.
Les vérifications navigateur couvrent les vrais messages du moteur simulé,
les liens enregistrés, l'arrêt des signaux à l'inactivité, les contrôles, le clic
sur les souvenirs, les thèmes et le repli sans WebGL. Le moteur simulé teste la
mécanique de Freewill sans clé et sans appel à un fournisseur externe.
