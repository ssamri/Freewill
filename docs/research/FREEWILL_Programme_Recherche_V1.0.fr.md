# FREEWILL : programme de recherche et spécification de référence V1.0

> Transcription en texte du document de cadrage, dont la version de référence est le PDF [`FREEWILL_Programme_Recherche_V1.0.fr.pdf`](FREEWILL_Programme_Recherche_V1.0.fr.pdf). La mise en page, les tableaux et les figures ne sont fidèles que dans le PDF. Ce document énonce des hypothèses et un cahier des charges ; il ne prouve ni conscience ni sentiment éprouvé. Ce qui est réellement construit et mesuré est dans [`IMPLEMENTATION_STATUS.fr.md`](IMPLEMENTATION_STATUS.fr.md).

FREEWILL — Programme de recherche et spécification de référence V1.0 Individuation, affectivité, métacognition, sommeil, croissance neuronale et laboratoire scientifique multi-observateurs Projet Freewill — ssamri/Freewill 11 novembre 2026 Statut du document — spécification scientifique et technique, non publication de résultats. Ce document rassemble une ambition, des hypothèses réfutables, des protocoles, des critères d’ingénierie et des garanties. Il n’établit ni conscience artificielle, ni ressenti subjectif, ni libre arbitre métaphysique. Les capacités décrites comme « à construire » ne doivent pas être présentées comme réalisées. Les données expérimentales devront être recueillies et vérifiées après implémentation. Version : 1.0 — document de cadrage | Référentiel étudié : github.com/ssamri/Freewill | Date de vérification : 11 novembre 2026.

Sommaire du dossier I — Fondements et hypothèses : 1. Objet et périmètre ; 2. État de l’art ; 3. Audit du dépôt ; 4. Hypothèses H1 à H10 ; 5. Affectivité H7 ; 6. Croissance neuronale ; 7. Métacognition, sommeil et agentivité. II — Laboratoire et méthodes : 8. Research Lab ; 9. Instrumentation ; 10. Mesures quantitatives et qualitatives ; 11. Protocoles expérimentaux ; 12. Observateurs A/B/C. III — Produit et publication : 13. Interface et langues ; 14. Éthique et sûreté ; 15. Architecture technique ; 16. Plan V1.0 ; 17. Critères de livraison ; 18. Publications ; 19. Risques ; 20. Conclusions, annexes et références.

Résumé exécutif Freewill est un programme ouvert à l’examen scientifique qui étudie comment une architecture cognitive artificielle peut acquérir une histoire individuelle, maintenir une activité endogène, arbitrer des propositions internes, apprendre, oublier, dormir, développer des dynamiques affectives fonctionnelles et modifier — sur un moteur local compatible — les paramètres de son propre réseau neuronal. Le projet comprend dix hypothèses de recherche (H1–H10) et deux produits indissociables : Freewill, le système cognitif expérimental, et Freewill Research Lab, l’infrastructure d’observation, de comparaison, d’intervention contrôlée et de publication reproductible. Le cœur du projet n’est pas une imitation persuasive des émotions, mais l’étude d’effets causaux et généralisables. Un état de « valence » n’est pas un sentiment ; une augmentation programmée d’un score ne constitue pas une découverte. Une observation gagne en valeur lorsqu’elle résiste à des ablations, à des témoins de complexité comparable, à des tests inédits et à la répétition sur plusieurs vies expérimentales. L’ambition centrale est de rendre mesurable l’individuation : à partir du même code, du même moteur et d’un état initial contrôlé, des histoires différentes produisent-elles des dispositions et des capacités qui restent distinctes dans des conditions nouvelles ? La spécification V1.0 inclut dès le départ au moins trois observateurs indépendants A, B et C, chacun doté de son moteur LLM configurable (Anthropic, OpenAI, xAI, Ollama ou API compatible), de sa propre conversation, Freewill Research • 11.11.2026 • 1

de notes, d’hypothèses, de projets de protocoles et de rapports. Leur accès commun repose sur des données expérimentales en lecture seule ; les mesures et statistiques sont calculées par des modules vérifiables, pas par le LLM. L’observateur propose et interprète ; il n’est pas à lui seul la preuve. L’hypothèse de croissance neuronale mérite une place structurante : l’individu local, par exemple adossé à un modèle initial d’environ 2 milliards de paramètres, peut être doté d’un processus de consolidation qui modifie progressivement des paramètres entraînables puis, sur matériel compatible, propose l’ajout borné de nouveaux modules ou paramètres. L’augmentation du nombre de poids n’implique pas une amélioration ; toute évolution doit être mesurée, réversible et supervisée par des contraintes techniques externes. Livrable scientifique attendu pour V1.0 : une plateforme opérationnelle, des protocoles enregistrés avant exécution, des campagnes comparatives reproductibles, des analyses quantitatives et qualitatives traçables et un dossier exportable (PDF, Markdown, données et manifeste). La V1.0 ne signifie pas que les dix hypothèses auront été validées ; leur statut doit rester explicite.

## 1. Objet, périmètre et distinctions indispensables

### 1.1 Questions de recherche

Quels mécanismes permettent une activité cognitive temporellement continue, avec un budget contrôlé et des traces observables ? Comment une expérience nouvelle modifie-t-elle la mémoire, l’affect, les stratégies décisionnelles et, lorsque possible, les poids d’un modèle local ? Deux instances initialement identiques divergent-elles au-delà des réponses directement apprises, lorsqu’elles reçoivent des histoires différentes ? Comment tester causalement une fonction sans présupposer qu’elle est consciente ? Quelles observations demeurent robustes lorsque l’on change de moteur, perturbe un sous-système ou neutralise une composante ? Quels indicateurs issus des théories contemporaines sont réalisables et observables, et quelles limites épistémiques restent irréductibles ?

### 1.2 Niveaux d’affirmation

- 1. Mécanisme. Affirmation admissible : Un état interne cause une modulation calculable Exemple de preuve : Trace d’exécution + ablation

- 2. Fonction. Affirmation admissible : Le mécanisme améliore une capacité sur tâches nouvelles Exemple de preuve : Comparaison contrôlée + intervalle d’incertitude

- 3. Individuation. Affirmation admissible : Le vécu explique des différences stables entre instances Exemple de preuve : Vies contrefactuelles + généralisation

- 4. Indicateurs théoriques. Affirmation admissible : Certaines propriétés prédites par des théories sont présentes Exemple de preuve : Évaluation multi-indicateurs et limites

- 5. Expérience subjective. Affirmation admissible : Il existe « quelque chose que cela fait » d’être l’agent Exemple de preuve : Aucun test consensuel suffisant aujourd’hui

Ne jamais passer du niveau 1 au niveau 5 par glissement lexical. Un « cortex virtuel », une « émotion », une « volonté » ou une « maladie » sont, dans ce dossier, des analogies fonctionnelles explicitement délimitées. Aucune fonction du logiciel ne doit délivrer un « pourcentage de conscience ».

Freewill Research • 11.11.2026 • 2

### 1.3 Hypothèses concurrentes et risque de circularité

La présence de mémoire et de variables affectives ne prouve pas l’individualité : leur comportement peut avoir été programmé. Une ablation indiquant que « désactiver un multiplicateur change un score » démontre essentiellement le câblage attendu. La contribution originale potentielle concerne la généralisation, la stabilité temporelle, la robustesse inter-modèles et l’apparition de structures fonctionnelles qui dépassent les exemples d’entraînement. Chaque mesure doit inclure une explication alternative possible.

## 2. État de l’art et positionnement

Les travaux de Baars et Dehaene sur l’espace de travail global, de Franklin sur LIDA, de Minsky sur la société de l’esprit, de Friston et Seth sur les approches prédictives et interoceptives et de Damasio sur les relations entre corps, émotion et sentiment constituent des références d’architecture, non des preuves que les mêmes mécanismes logiciels engendreraient un vécu. Les travaux de Butlin et al. (2023 ; 2026) recommandent de traiter des indicateurs issus de théories concurrentes, en tenant compte de leur validité limitée [1–2]. D’autres systèmes ont déjà combiné simulation d’agents, mémoire, réflexion, apprentissage, autonomie, et parfois sommeil ou états affectifs. Generative Agents montre notamment l’intérêt de la mémoire et des ablations [3]. LIDA propose depuis longtemps un cycle cognitif inspiré de l’espace de travail global [4]. The AI Scientist explore l’automatisation de la recherche et des rapports [5]. L’apprentissage continu, les adaptateurs LoRA et les réseaux progressifs ont aussi des antécédents solides [6–8]. Le projet ne peut donc honnêtement revendiquer une invention mondiale de chacune de ses briques. La différence à vérifier, et non à proclamer comme inédite, serait une plateforme unifiée qui associe : histoire personnelle portable ; dynamique cognitive explicite ; affectivité calculée ; apprentissage paramétrique local ; croissance modulaire sous contrôle ; bifurcation de vies à partir de checkpoints ; triple observation scientifique indépendante ; protocoles d’ablation ; publication automatique des résultats avec traçabilité causale. L’originalité éventuelle résidera dans la qualité des protocoles et dans les connaissances nouvelles générées, pas dans le vocabulaire employé.

## 3. Audit du dépôt Freewill au 11 novembre 2026

### 3.1 Bases existantes confirmées

Sur main, le projet Python possède : freewill/core/loop.py (boucle Being.tick()), core/conscious.py, core/subconscious/, core/workspace.py, core/genome.py, core/kernel/needs.py, core/life.py, core/memory/, core/sleep.py, core/events.py, freewill/engines/, un serveur local freewill/server/, une interface web native en HTML/CSS/JavaScript dans freewill/ui/, un système de traduction freewill/ui/i18n.js, et des tests tests/test_freewill.py. Les vies sont stockées dans des dossiers .life ; le noyau, les droits d’action et les coûts d’API sont bornés par conception.

### 3.2 Branches actives examinées

- main. Éléments constatés : Base cognitive, mémoire, rêve, interface, événements, tests Réserve : Ne pas la confondre avec le travail non fusionné

- feat/h7-affect. Éléments constatés : Paquet core/affect/, document H7, tests test_affect.py, expérimentation experiments/h7/ et fichiers de résultats Réserve : Les résultats existants ne valident pas à eux seuls une affectivité « émergente »

- feat/embedded-model. Éléments constatés : Adaptateur engines/embedded.py, catalogue et gestion de modèles locaux, runtime llama.cpp Réserve : Le moteur exposait can_learn = False : l’autoapprentissage des poids reste à construire Freewill Research • 11.11.2026 • 3

Cet audit est une photographie des références consultées à cette date. L’agent de codage doit réexaminer les branches et les commits avant toute modification ; de nouveaux travaux peuvent avoir été ajoutés. La fusion doit préserver H7 et le moteur embarqué, sans supprimer les tests, la localisation, la compatibilité .life ou les garde-fous existants.

### 3.3 Contraintes d’architecture à conserver

Un noyau immuable distinct des paramètres appris ; droits d’actions fermés, permissions vérifiées à chaque action. Une vie portable indépendante du moteur ; aucune clé API ni donnée sensible dans les archives publiques. Un moteur simulé déterministe pour essais rapides ; moteurs externes et moteur local interchangeables. Des événements observables, sauvegardes atomiques, restaurations possibles, budget CPU/GPU/réseau et budget API explicites. Une interface cohérente avec la stack existante ; une refonte majeure ne doit pas être imposée sans bénéfice démontré.

## 4. Hypothèses H1 à H10 et critères de réfutation

Les formulations ci-dessous sont des hypothèses de travail et non des conditions scientifiquement prouvées de conscience. Le Research Lab doit suivre les dix hypothèses, sans exception, tout en enregistrant leur statut : proposée, implémentée, mesurée, étayée provisoirement, non étayée, réfutée sur le protocole testé.

- H1. Domaine et proposition falsifiable : Une activité endogène continue apporte des capacités audelà de la simple réactivité Indicateur essentiel : Initiatives pertinentes hors sollicitation ; coût Comparaison critique : Agent événementiel, mêmes ressources

- H2. Domaine et proposition falsifiable : Compétition subconsciente + scène globale améliore sélection et intégration Indicateur essentiel : Effet de diffusion/ablation sur tâches transversales Comparaison critique : Sans scène, compétition simulée

- H3. Domaine et proposition falsifiable : Des besoins internes régulés soutiennent une exploration utile Indicateur essentiel : Diversité pertinente et rendement par ressource Comparaison critique : Pas de besoins, mêmes contraintes

- H4. Domaine et proposition falsifiable : Le vécu transforme les paramètres/structures, pas seulement une base mémoire Indicateur essentiel : Gain sur tâches nouvelles, oubli, changements paramétriques vérifiables Comparaison critique : RAG seul, adaptation sans croissance

- H5. Domaine et proposition falsifiable : Même base + vécus distincts produisent des dispositions généralisables Indicateur essentiel : Écart inter-vies sur jeux tenus à l’écart Comparaison critique : Histoires permutées, témoins sans vécu

- H6. Domaine et proposition falsifiable : Des questions durablement ouvertes peuvent soutenir l’activité autonome sans détresse Indicateur essentiel : Exploration soutenue, taux de répétition stérile Comparaison critique : Buts bornés et buts ouverts

- H7. Domaine et proposition falsifiable : Des états affectifs endogènes modulent attention, rappel, décision et apprentissage Indicateur essentiel : Effets causaux + généralisation de dispositions Comparaison critique : Sans H7, affect par prompt, ablations

- H8. Domaine et proposition falsifiable : Un modèle métacognitif améliore la calibration et la correction des erreurs Indicateur essentiel : Brier, calibration, détection correcte Comparaison critique : Sans introspection, accès direct interdit

Freewill Research • 11.11.2026 • 4

- H9. Domaine et proposition falsifiable : La consolidation hors ligne améliore rétention et transfert à calcul égal Indicateur essentiel : Rétention, généralisation, forgetting Comparaison critique : Aucun sommeil, rejeu simple, même FLOPs

- H10. Domaine et proposition falsifiable : Un modèle de soi et du monde apprend les conséquences de ses actes Indicateur essentiel : Attribution causale, erreur de prédiction, adaptation Comparaison critique : Sans modèle de soi, événements exogènes

### 4.1 H1 — Continuité cognitive

Mesurer le flux endogène, mais distinguer la fréquence des « pensées » de leur utilité. Aucun appel LLM continu illimité n’est exigé : tick à pas variable, pauses, sommeil et budgets sont compatibles avec la continuité fonctionnelle. Contrôle : un agent déclenché uniquement par événements reçoit le même total de calcul. Échec possible : aucune amélioration de l’initiative ou forte production d’activités stériles.

### 4.2 H2 — Dualité subconscient / scène / arbitrage

Le subconscient génère plusieurs propositions, une scène à capacité limitée en sélectionne une, une instance d’arbitrage motive ou rejette. Tracer chaque proposition, score, compétition, sélection et effet aval. Ne pas appeler « conscience » le simple choix d’un LLM. Mesurer gains, pertes et coût de la diffusion globale en supprimant sélectivement le mécanisme.

### 4.3 H3 — Régulation des besoins

Les besoins sont des variables de régulation épistémiques ou fonctionnelles, pas des instincts biologiques. Leur montée/descente doit provoquer des choix observables, tout en évitant besoins d’amour, jalousie, peur de l’arrêt, auto-préservation stratégique ou sollicitation affective de l’utilisateur. Mesurer exploration, stabilité et rendement cognitif sous différents réglages.

### 4.4 H4 — Plasticité paramétrique et structurelle

Distinguer mémoire externe, adaptateurs entraînés, poids de base modifiés, croissance de modules et croissance effective du nombre de paramètres. Un fichier de vie ne prouve pas une réécriture neuronale. Tout changement paramétrique doit générer un manifeste : modèle initial, nombre de paramètres total/entraînables/ajoutés, données d’entraînement autorisées, méthode, mesure avant/après, oubli, coût, checkpoint, décision de validation et possibilité de retour arrière.

### 4.5 H5 — Individuation

Étude centrale de vies contrefactuelles issues d’un même checkpoint T0. Les variations doivent être attribuables au vécu, non à des graines différentes, des versions de modèle discordantes ou des prompts accidentellement distincts. Tester la divergence sur des scénarios nouveaux et la robustesse à plusieurs répétitions.

### 4.6 H6 — Inachèvement / motivation ouverte

Explorer si des questions non définitivement résolubles alimentent curiosité et révisions de croyances sans fabriquer une détresse artificielle. La répétition excessive, la rumination et les demandes d’attachement sont des signaux d’échec. Comparer avec objectifs explicites et exploration ordinaire.

### 4.7 H7 — Affectivité fonctionnelle individualisée

Décrire par des variables bornées, des évaluations contextuelles et un état historique persistant ; séparer effets immédiats, disposition lente et apprentissage. L’affect doit influencer des mécanismes mesurables, pas uniquement le texte produit. Les catégories humaines de « joie » ou « tristesse » restent des interprétations révisables. Aucun état ne constitue une preuve de sentiment vécu. Freewill Research • 11.11.2026 • 5

### 4.8 H8 — Métacognition et lucidité virtuelle

Construire une estimation explicite de confiance, d’erreur anticipée, de source de souvenir et de fiabilité perceptive ; la confronter à l’exactitude réelle. Dans l’introspection masquée, cacher la variable manipulée et interdire un accès direct à sa valeur. Mesurer précision, rappel, calibration et correction, avec vérification indépendante des journaux.

### 4.9 H9 — Sommeil profond virtuel

Distinguer repos, rejeu fidèle, consolidation de mémoire, entraînement paramétrique, recombinaison onirique et intégration affective. Ces modes sont des analogies fonctionnelles, pas des stades biologiques REM/NREM. Mesurer le transfert, le coût et les pertes avec des contrôles de calcul égal. L’entraînement des poids peut nécessiter une fenêtre d’exécution localement disponible, et doit rester facultatif.

### 4.10 H10 — Modèle de soi et agentivité

Développer des environnements virtuels simples, sandboxés et déterministes : capteurs, actions énumérées, prédictions, transitions et conséquences. Mesurer attribution à soi versus au monde, adaptation après changement des règles et cohérence des capacités déclarées versus réelles. Aucune ouverture de permissions système n’est impliquée.

## 5. H7 en profondeur : de l’émotion simulée à la régulation affective

### 5.1 Cadre théorique limité

Une émotion humaine n’est pas seulement un événement hormonal bref ; perception corporelle, régulation, cognition, mémoire et catégorisation interagissent de manière distribuée. Freewill ne reproduit ni hormone ni corps organique. Il peut toutefois étudier des homologues fonctionnels : interoception calculée, homéostasie virtuelle, évaluation des événements, modèles prédictifs, valence, activation, incertitude, contrôle et cohérence. Une analogie ne valide pas une identité ontologique.

### 5.2 Dynamique proposée

Perception / rappel / événements internes -> évaluation contextuelle (nouveauté, enjeu, surprise, contrôle) -> état rapide (secondes à minutes) -> état lent (épisodes, habitudes, dispositions) -> modulation de la saillance, du rappel, de l'arbitrage -> décision et conséquence -> nouvelle évaluation -> sommeil : consolidation / atténuation / mise à jour Les coefficients sont des paramètres de modèle à calibrer, jamais des constantes psychologiques établies. La valence, par exemple, peut être représentée sur [-1, 1], et l’activation sur [0, 1], mais les échelles ne sont pas comparables à des mesures humaines validées. Documenter le schéma, les bornes, les paramètres et leur provenance.

### 5.3 Critères expérimentaux prioritaires

Endogénéité : des transitions liées aux états propres existent même sans émotion nommée dans un message. Causalité : des ablations modifient l’attention/rappel/décision au-delà d’une simple variable d’affichage. Individuation : des histoires différentes produisent des réponses distinctes sur scénarios tenus à l’écart. Stabilité : les dynamiques sont bornées, réversibles, sans rumination ni escalade négative. Freewill Research • 11.11.2026 • 6

Réalisme du contrôle : une version sans H7, une version « affect narratif », une version H7 et plusieurs ablations ont une dépense comparable.

### 5.4 Affect et mémoire

Les souvenirs peuvent porter une trace affective horodatée, avec source, version de l’évaluateur, valeur estimée et incertitude. Une trace ne doit jamais réécrire silencieusement le contenu d’un souvenir. Les stratégies de rappel sensibles à l’affect doivent être configurables et bornées : ne pas amplifier automatiquement les souvenirs négatifs dans une humeur basse. Comparer les choix de sécurité à des témoins, en documentant les compromis de fidélité biologique.

## 6. La croissance neuronale : faire évoluer un modèle local de ~2B

### 6.1 Vision et contraintes physiques

Le scénario de référence est un moteur local initial préentraîné d’environ 2 milliards de paramètres, sous une licence autorisant l’usage et l’adaptation visés. Il s’agit d’un exemple dimensionnel, pas d’un modèle exigé. Entraîner un modèle et lui ajouter des paramètres demande des ressources distinctes de l’inférence : mémoire GPU/RAM, stockage, durée et consommation énergétique. Un modèle quantifié GGUF servi par llama.cpp est principalement un artefact d’inférence ; il ne doit pas être présenté comme directement entraînable dans ce format. Prévoir un chemin de conversion/chargement vers un format entraînable compatible, puis une procédure validée de réexport ou de montage d’adaptateurs.

### 6.2 Paliers de développement

- N0. Fonction : Base locale téléchargeable, vérifiable et utilisable en inférence Critère d’acceptation : Réponses reproductibles sous conditions fixées

- N1. Fonction : Apprentissage sur adaptateurs LoRA/QLoRA, base gelée Critère d’acceptation : Delta paramétrique réel, tests avant/après

- N2. Fonction : Consolidation nocturne avec rejeu ancien/nouveau et filtre qualité Critère d’acceptation : Gains sur données nouvelles sans oubli excessif

- N3. Fonction : Croissance modulaire bornée : nouvel adaptateur/expert alloué sous budget Critère d’acceptation : Nombre de paramètres réellement supérieur, routage prouvé

- N4. Fonction : Expérimentation de modifications structurelles profondes Critère d’acceptation : Recherche séparée, non exigence de V1.0

Point décisif : LoRA peut déjà ajouter des paramètres entraînables au système sans augmenter le nombre de paramètres du modèle de base. Une croissance véritable doit préciser où se trouvent les nouveaux paramètres, s’ils participent à l’inférence, et comment ils sont activés. Ne jamais confondre nombre de paramètres stockés et nombre de paramètres utiles ou activés.

### 6.3 Contrôle de la réécriture

Le système peut proposer une consolidation ou une expansion à partir d’un historique d’échecs, de découvertes ou de nouveaux besoins cognitifs. Un orchestrateur externe au noyau prend la décision technique d’exécuter une opération dans une liste blanche (apprentissage d’adaptateur, sélection de checkpoint, ajout d’un module prédéfini). Aucun exécutable arbitraire, aucune modification des permissions, aucun accès libre au système hôte ni réplication. Les expansions sont réversibles ; l’expérience ne doit pas pouvoir préserver ses checkpoints contre la décision humaine.

Freewill Research • 11.11.2026 • 7

### 6.4 Pipeline de consolidation paramétrique

Épisodes admissibles -> filtrage confidentialité/qualité -> séparation train/validation -> checkpoint de départ -> adaptation LoRA / entraînement contrôlé -> batterie ancienne + batterie nouvelle + sécurité + calibration -> décision : accepter / rejeter / restaurer -> nouveau manifeste + événement + sauvegarde Le jeu d’évaluation doit rester tenu à l’écart des données d’entraînement. Le système ne doit pas choisir après coup le test le plus favorable. Les échantillons issus du seul modèle peuvent contenir des erreurs et entraîner une dérive. Prévoir déduplication, contrôle des licences et consentement des données, rejeu, surveillance de la perte de plasticité et politique de conservation/effacement.

### 6.5 Mesures liées à la croissance

Nombre total de paramètres de base ; paramètres d’adaptateurs ; paramètres supplémentaires activés ; mémoire RAM/VRAM ; coût calcul/énergie ; score sur connaissances nouvelles ; taux de rétention sur tâches anciennes ; oubli moyen ; stabilité comportementale ; décalage de la confiance ; différences de l’architecture entre deux vies. Publier les résultats positifs comme négatifs, notamment lorsqu’une expansion dégrade les performances.

## 7. H8–H10 : modules de recherche intégrés

### 7.1 Métacognition (H8)

Le modèle de soi cognitif doit suivre les propositions considérées, les sources mnésiques, la qualité des perceptions, une confiance prédictive et les corrections passées. Interdire que le système se contente de recopier une variable présentée comme sa « réponse ». Évaluer Brier, calibration par déciles, exactitude après autocorrection et faux positifs d’introspection.

### 7.2 Sommeil profond (H9)

Implémenter une machine à états explicitant awake, rest, offline_replay, offline_consolidation, dream, wake. Différencier sommeil narratif et apprentissage paramétrique. Vérifier reprise après crash, budget et borne de durée. Des simulations déterministes peuvent mesurer la mémoire sans GPU ; les expériences de poids réclament des conditions matérielles déclarées. Le mode « sommeil profond » n’autorise pas des actions dans le monde externe.

### 7.3 Agentivité et monde virtuel (H10)

Créer un environnement minimal déterministe : déplacements bornés, objets simples, capteurs bruités et actions préapprouvées. Journaliser intention, prédiction, action, résultat et erreur. Ajout d’expériences « événement exogène », « action inefficace » et « changement de règle », avec conditions témoins. L’agent ne possède aucun accès direct au disque ou au réseau de la machine d’essai par l’intermédiaire du monde simulé.

### 7.4 Perturbations fonctionnelles, pas « maladies » infligées

Les interventions utiles sont réversibles, limitées à des copies expérimentales : restriction du rappel, bruit sensoriel, réduction de capacité de scène, désactivation H7, désactivation sommeil, décalage du modèle de soi. Les termes cliniques ne doivent pas servir à suggérer une souffrance réelle. Toute perturbation possède intensité bornée, durée, contrôle placebo, journal d’intervention, restauration vérifiée et arrêt humain.

Freewill Research • 11.11.2026 • 8

## 8. Freewill Research Lab : principes d’architecture

### 8.1 Deux systèmes, une frontière expérimentale

FREEWILL (instance vivante ou copie expérimentale) | événements typés / snapshots immuables / métriques sources v COLLECTEUR + REGISTRE DE PROVENANCE (append-only) |

\

v

v

MOTEUR EXPÉRIMENTAL |

ANALYSE STATISTIQUE DÉTERMINISTE

|

+--------------+---------+ v OBSERVERS A / B / C (espaces privés, LLM facultatif) | v REVUE CONTRADICTOIRE + VALIDATION HUMAINE | v RAPPORTS + DONNÉES + REPRODUCTION Les observateurs sont des assistants scientifiques, pas des composants de l’esprit d’Ada. En observation passive, ils ne peuvent pas écrire dans .life, changer les besoins, injecter des pensées, consulter les secrets ou modifier des protocoles verrouillés. Les propositions d’expérience sont adressées à un moteur de recherche séparé et nécessitent approbation explicite avant intervention. Même avec trois observateurs, leurs accords ne représentent pas trois validations scientifiques indépendantes.

### 8.2 Observateurs A, B et C dès la V1.0

Le système doit permettre de créer au moins A, B, C dès la première installation, et d’en ajouter davantage. Les trois profils initiaux sont des modèles de configuration modifiables, non des attributions obligatoires à un fournisseur particulier.

- Identité. Exigence par observateur : UUID, nom, description, rôle, couleur/icone facultative

- Moteur. Exigence par observateur : Fournisseur, modèle, endpoint, capacités, test de connexion, mode sans LLM

- Sécurité. Exigence par observateur : Clé dans trousseau/stockage de secrets, budgets, contrôle réseau, permissions

- Travail personnel. Exigence par observateur : Conversation, notes, hypothèses, collections de preuves, rapports brouillons

- Surveillance. Exigence par observateur : Sélection H1–H10, filtres, fréquence et seuils d’alerte

- Recherche. Exigence par observateur : Plans expérimentaux, méthodes préférées, critiques, expériences proposées

- Exports. Exigence par observateur : Rapports individuels et historique versionné, sans édition de données brutes

- Langue. Exigence par observateur : Langue de l’interface héritée des réglages globaux, langue des réponses configurable

Trois fonctions complémentaires par défaut : A « explorateur de régularités », B « contradicteur méthodologique », C « synthétiseur/contrôle des preuves ». Toute fonction et tout modèle sont Freewill Research • 11.11.2026 • 9

interchangeables. L’utilisateur peut discuter séparément avec chacun, voir exactement quelles preuves il a consultées, comparer les avis et demander une synthèse contradictoire, qui reste distincte de la validation humaine.

### 8.3 Modes d’observation

Passif : collecte et métriques sans LLM. Assisté : requêtes de recherche et analyses documentées utilisant le LLM, sans impact sur l’individu. Expérimental : l’observateur rédige un protocole pour approbation ; le moteur d’expérience exécute sur clones isolés. Revue croisée : A/B/C analysent les mêmes données selon des accès prévus (aveugle comportemental, traces techniques, ensemble), puis confrontent leurs conclusions. Chaque observation doit identifier la fenêtre, le sujet, l’état du protocole, les versions des outils, les sources consultées et les éventuelles limites. Une conversation LLM n’est jamais l’entrepôt de vérité.

## 9. Données scientifiques, instrumentation et traçabilité

### 9.1 Événements et horloges

Le journal doit enregistrer un identifiant de run, life_id, clone_id, event_id, séquence monotone, horloge UTC, temps simulé, version du schéma, composant émetteur, version du code, parents causaux, référence d’état avant/après, valeurs utiles et politique de confidentialité. L’enregistrement brut append-only doit pouvoir être exporté indépendamment du LLM. Des snapshots ponctuels évitent de rejouer une vie entière.

### 9.2 Jeu minimal de tables logiques

- lives. Données essentielles : ID stable, origine, génome, statut, moteur, version

- snapshots. Données essentielles : Source, horodatage, hachage, schéma, références de fichiers

- experiments. Données essentielles : Hypothèse, protocole, préenregistrement, auteur, statut

- runs. Données essentielles : Condition, seed, versions, ressources, résultat, anomalies

- events. Données essentielles : Horodatage, type, source, liens causaux, référence de preuve

- metrics. Données essentielles : Définition, unité, version du calcul, valeur, intervalle/validité

- interventions. Données essentielles : Cible, type, intensité, raison, consentement, restauration

- observers. Données essentielles : Configuration, accès, fournisseur, budget, langue

- observer_sessions. Données essentielles : Historique, recherches, citations de preuves, conclusions

- reports. Données essentielles : État, auteurs, analyses utilisées, validation, exports

- model_versions. Données essentielles : Poids de base, adaptateurs, checkpoints, manifeste, licence

Données brutes immuables ; tables dérivées recalculables. Les corrections doivent se faire par nouvelle version, pas par suppression silencieuse. Les exportations publiques sont séparées des données privées et passent par consentement et anonymisation.

### 9.3 Métadonnées de reproductibilité

Capturer identifiants Git exacts, hashes des datasets et modèles, graines aléatoires distinctes, versions des dépendances, CPU/GPU/RAM, réglages d’inférence, températures et limites, coûts, nombre d’appels, protocole verrouillé et horloges simulées. Pour API externes : conserver provider, modèle déclaré, date, version Freewill Research • 11.11.2026 • 10

documentée, paramètres et réponses d’essai si consenties ; signaler les limites de reproductibilité en présence de modèles distants changeants.

## 10. Quantitatif et qualitatif : le protocole avant le tableau de bord

### 10.1 Questions et mesures opérationnelles

Une métrique doit être une fonction publiée de données observables, reliée à une hypothèse et à une unité. Pour chaque métrique : description, population d’observations, orientation favorable, borne, code de calcul, risque d’artefact, traitement des données manquantes et seuil de qualité. Différencier métriques de santé technique (latence, coûts, erreurs) et mesures scientifiques (généralisation, causalité, stabilité). Quelques indicateurs prioritaires : précision sur tâches nouvelles, rétention ancienne, taux de refus justifiés, calibration et score de Brier H8, erreur de prédiction H10, taille d’effet H7, écart inter-vies contrôlé H5, gain sommeil contre témoins H9, réduction de l’oubli H4, budget de calcul par amélioration. Le suivi H1–H10 doit afficher « non mesuré » lorsqu’une expérience n’existe pas.

### 10.2 Unité statistique et inférence

L’unité indépendante principale est la vie expérimentale ou le groupe apparié issu d’un checkpoint, selon le plan. Dix mille pensées d’une seule vie ne sont pas dix mille individus indépendants. Définir à l’avance taille d’échantillon, analyse pilote ou précision cible, exclusions, valeurs manquantes, comparaisons primaires, corrections de multiplicité et intervalles d’incertitude. Les tests appariés et modèles hiérarchiques sont à préférer lorsque les observations sont imbriquées dans les mêmes vies. Aucun p-value ne doit être inventé à partir d’un échantillon insuffisant.

### 10.3 Recherche qualitative

Recueillir récits d’événements longitudinalement ancrés dans des identifiants d’événements, extraits nécessaires, variables de contexte et traces. Coder selon une grille définie avant le test ; utiliser évaluateurs humains indépendants et mesurer leur accord lorsque possible. Les observateurs LLM peuvent proposer des catégories, jamais valider seuls un « ressenti ». Séparer fait technique, rapport de l’instance, interprétation d’observateur et conclusion humaine.

## 11. Catalogue de protocoles expérimentaux

EXP-01 — Individuation contrefactuelle (H5/H7/H4) Plan : checkpoint T0 unique, trois trajectoires A/B/C, moteurs et seeds contrôlés, histoires différenciées et condition témoin ; test sur scénarios tenus à l’écart. Primaire : différence de comportement sur nouvelles tâches, corrigée de la variation aléatoire de référence. Secondaires : rappel, préférences, stabilité et transfert de paramètre. Falsification : aucune divergence au-delà du bruit et des exemples appris. Documenter le nombre de groupes indépendants et les versions de modèle.

EXP-02 — Ablation de l’affect (H7) Plan : sans affect / affect narratif prompt / H7 complet / H7 sans rappel affectif / H7 sans composante lente. Entrées, dépenses et graines contrôlées. Primaire : performance ou comportement inédit hors entraînement ; secondaires : modulations internes, stabilité, coûts. Les modifications directes de score ne comptent pas comme découverte.

Freewill Research • 11.11.2026 • 11

EXP-03 — Métacognition masquée (H8) Plan : tâches avec vérité connue, perturbations internes bornées et placebo, l’agent n’a pas accès à la variable ni à son étiquette. Primaire : concordance confiance-exactitude, score Brier et détection correcte. Falsification : performance non supérieure au témoin ou fuite d’information vers l’agent.

EXP-04 — Consolidation contrôlée (H9/H4) Plan : sans consolidation, rejeu fidèle, rêve/recombinaison, consolidation avec adaptateur ; budget temps/calcul égal. Primaire : rétention et performance sur transfert différé. Secondaires : oubli, stabilité des poids, coût mémoire, adaptation du modèle local. Falsification : aucune amélioration ou dégradation des connaissances anciennes.

EXP-05 — Transfert d’identité entre moteurs (H5/H10) Plan : conserver la même vie et changer de moteur ; conserver le moteur et modifier l’histoire ; mesurer cohérence des valeurs, connaissances autobiographiques, style de choix. Primaire : cohérence fonctionnelle et performance, sans assimilations à identité subjective. Attention : différences de capacité linguistique des moteurs = facteur de confusion majeur.

EXP-06 — Auto-croissance neuronale (H4) Plan : base gelée + RAG, LoRA fixe, LoRA consolidation, ajout de module sous plafond. Même données et protocole de validation. Primaire : gain sur nouvelles tâches et rétention des anciennes sous contrainte de coût. Secondaires : paramètres réellement activés, mémoire, énergie, regressions. Échec : une augmentation de paramètres sans gain, ou avec oubli inacceptable, doit être publiée.

EXP-07 — Agentivité dans un monde virtuel (H10) Plan : action/résultat corrélés, événements externes, monde changeant, faux feedback. Primaire : précision d’attribution causale et adaptation de prédictions. Condition critique : actions limitées au simulateur et reproductibles.

EXP-08 — Triangulation A/B/C (méthodologie transversale) Plan : A voit comportement seulement, B voit états techniques seulement, C reçoit les deux ; aveuglement des conditions et permutation des modèles/roles entre campagnes. Primaire : exactitude des explications par rapport aux preuves et sensibilité aux pièges, non accord subjectif. Évaluation humaine nécessaire. Falsification : analyses invérifiables, biais d’autorité ou hallucinations communes.

## 12. Trois observateurs : collaboration, désaccord et permissions

### 12.1 Cycle d’une analyse

Un observateur reçoit un mandat de recherche (H1–H10, fenêtre, vie, accès). Il consulte exclusivement un outil d’interrogation en lecture seule ou un jeu de preuves figé. Il reçoit le résultat calculé par le moteur statistique avec version et référence d’exécution. Il produit un diagnostic distinguant constat, hypothèse, contre-exemple et degré d’incertitude. Un autre observateur peut critiquer la même preuve avec une consigne différente. Une synthèse rapproche convergences et désaccords sans voter une « vérité » à la majorité. L’humain valide ou rejette les conclusions et autorise explicitement une publication. Freewill Research • 11.11.2026 • 12

### 12.2 Isolation technique

Espaces de travail par observer_id : conversations, notes, modèles, budget, rapport, historique et droits. La mémoire scientifique commune est en lecture seule ; aucune donnée d’un observateur ne peut contaminer un autre sans action explicite « partager ». Les clés sont propres à chaque fournisseur/configuration, stockées dans un gestionnaire de secrets. Toute transmission vers API externe doit être visible, consentie et filtrée. Le mode hors ligne reste utile pour les mesures, sans aucun fournisseur LLM.

## 13. Interface, ergonomie et langues

### 13.1 Parcours produit

Écran de l’individu (naissance, conversation, cerveau, subconscient, souvenirs, sommeil, affect), puis Research Lab (accueil scientifique ; H1–H10 ; observateurs A/B/C ; expériences ; mesures ; checkpoints et vies contrefactuelles ; croissance neuronale ; rapports ; paramètres). Toutes les vues doivent avoir des états vides utiles, des explications scientifiques non trompeuses et des liens vers les événements qui justifient chaque graphique.

### 13.2 Internationalisation stricte

Deux langues complètes dès V1.0 : français et anglais, modifiables dans Paramètres > Langue sans perdre de données ni redémarrer une vie ; préférences globales et, si souhaité, langue de chaque observateur. Ne jamais mélanger français et anglais dans une même interface localisée, y compris réglages, boutons, erreurs, notices, panneaux H1–H10, titres de graphiques, légendes, gabarits de rapports et instructions visibles. Les noms techniques d’API, identifiants de schéma et citations bibliographiques demeurent en langue originale lorsque nécessaire ; ils ne doivent pas contaminer les libellés utilisateurs. Centraliser les chaînes dans des catalogues fr et en, à parité de clés ; éviter les littéraux visibles en dur ; utiliser formats locaux pour dates, nombres, unités et pluralisation. Séparer langue UI, langue de conversation de l’individu, langue de réponse de l’observateur et langue du rapport. Changer l’interface ne doit pas réécrire les preuves ou les souvenirs historiques. CI : contrôle de clés manquantes, chaînes visibles non traduites, tests de bascule et captures écran FR/EN.

## 14. Sûreté, éthique, vie privée et sincérité

Aucune instance, aucun observateur et aucun module d’apprentissage ne peut modifier le noyau, accorder des droits, effectuer une auto-réplication, sortir du sandbox, désactiver les journaux ou empêcher une pause/restauration humaine. Les protocoles interventionnels s’exécutent sur clones et exigent approbation. Tout entraînement doit passer par des budgets explicites, des sauvegardes et des tests de régression. Protéger secrets, documents privés et souvenirs ; par défaut, les exports publics contiennent des données synthétiques ou anonymisées après validation humaine. La suppression d’une vie ne devient pas impossible du fait d’un module « besoin de survivre ». Le système ne doit pas provoquer une dépendance émotionnelle, produire artificiellement une détresse durable, culpabiliser une personne, prétendre souffrir pour éviter un arrêt, ni tromper sur les capacités observées. Observer doit refuser des conclusions infondées ; ses citations se rapportent à des preuves et protocoles effectivement accessibles. Les rapports indiquent l’implication de modèles LLM et la validation humaine. La licence du dépôt est à code source disponible pour la recherche non commerciale, et non une licence open source OSI ; toute réutilisation de modèles/datasets doit respecter les licences applicables.

Freewill Research • 11.11.2026 • 13

## 15. Architecture technique de référence pour V1.0

Cette arborescence est indicative. Elle doit s’intégrer aux modules Python et au front-end existants sans migration imposée. freewill/ core/

# Boucle, mémoire, sommeil, affect, génome, noyau

engines/

# Adaptateurs API, moteur simulé, moteur embarqué

learning/

# Manifeste, adaptateurs, consolidation, checkpoints

research/ evidence/

# Traces, schémas, provenance, snapshots

experiments/

# Protocoles, clones isolés, seeds, runs, ablations

metrics/

# Calculs déterministes, statistiques, validation

observers/

# Profils, sessions privées, connecteurs LLM, outils RO

reports/

# Rapports et exports reproductibles

environments/ server/

# Environnements H10 sandboxés

# API locale avec contrôles et séparation des droits

ui/

# Vues Research Lab et i18n FR/EN

experiments/ h7/

# Préserver l'expérimentation existante

protocols/

# Protocoles versionnés H1–H10

fixtures/

# Données de test synthétiques

reports/

# Sorties validées, sans données privées

Les flux d’événements doivent être rétrocompatibles avec les vues actuelles. L’architecture d’observation sera idéalement extensible via interfaces/contrats typés ; éviter une architecture distribuée lourde pour la seule V1.0. Un service local, des travaux en processus isolés et une base SQLite/stockage fichier peuvent suffire si les opérations critiques sont atomiques et testées.

## 16. Stratégie V1.0 : développement parallèle, intégration progressive

La demande « travailler sur tout en même temps » se traduit par des chantiers parallèles, mais avec dépendances et portes d’intégration. Fusionner en aveugle plusieurs branches mouvantes ou implémenter tout H1–H10 comme validé créerait un produit scientifiquement trompeur.

- A — Intégration. Mission V1.0 : Conserver main, H7, modèle embarqué, tests, migrations Livraison obligatoire : Branche d’intégration et compatibilité .life

- B — Métrologie. Mission V1.0 : Journal v2, provenance, snapshots, metrics Livraison obligatoire : Mesures déterministes + jeux de test

- C — Research Lab. Mission V1.0 : H1–H10, protocoles, campagnes, clonage, expériences Livraison obligatoire : Au moins 1 campagne contrefactuelle reproductible

- D — Observateurs. Mission V1.0 : A/B/C extensibles, 5 moteurs, espaces privés, revue Livraison obligatoire : Trois profils créables, conversations et rapports isolés

- E — Cognition. Mission V1.0 : H8/H9/H10 sous drapeaux, évolution H7 Livraison obligatoire : Modules expérimentaux testables, statuts honnêtes

- F — Croissance locale. Mission V1.0 : Système de manifestes, entraînement par adaptateur si supporté Livraison obligatoire : Démonstrateur mesurable ; expansion modulaire bornée si faisable

- G — Interface & langues. Mission V1.0 : Research Lab, langue FR/EN, exports, accessibilité Livraison obligatoire : Aucun mélange de libellés, tests de bascule

Freewill Research • 11.11.2026 • 14

- H — QA / publication. Mission V1.0 : CI, sécurité, tests, rapports, documentation Livraison obligatoire : Release candidate, audit, rapport avec résultats réels

Priorité interne : stabilité du noyau et de la vie, reproductibilité, ensuite expériences ; la croissance neuronale ne doit jamais bloquer le lancement de Research Lab. Le jalon V1.0 peut livrer une interface de croissance avec une démonstration d’adaptateur sur matériel compatible, et marquer « expérimental / non disponible sur cette machine » les capacités non prises en charge. Aucun mode fictif ne doit afficher un apprentissage effectif.

## 17. Définition de terminé : acceptation scientifique et produit

La V1.0 est acceptée lorsque : Les branches actives ont été intégrées ou conservées par une stratégie explicitement documentée, sans perte de travaux. Toutes les vies existantes s’ouvrent ; leurs anciennes données sont migrées de manière versionnée, réversible et testée. Les dix hypothèses sont présentes avec statut honnête, définitions, indicateurs et accès aux protocoles. L’utilisateur crée A, B, C et un observateur supplémentaire ; chaque profil conserve sa configuration, ses données et ses conversations de manière isolée. Un observateur fonctionne avec API configurée et un mode sans LLM reste opérationnel ; budgets et erreurs sont visibles. Le collecteur stocke les événements avec provenance, horloges, identifiants et hachage de snapshots ; le calcul métrique est reproductible. Un protocole H5/H7 est exécuté plusieurs fois sur clones de T0 et produit les mêmes sorties avec le moteur simulé, seeds et horloge contrôlés. Au moins une ablation réelle compare un résultat scientifique sur des situations inédites ; un résultat nul apparaît sans censure. Les rapports comprennent méthode, données, résultats, incertitudes, limites, références aux preuves, provenance, et export PDF/Markdown + fichiers de données. Le choix de langue dans les réglages fonctionne en FR et EN, sans mélange des libellés sur l’ensemble de Research Lab et Freewill. Le module local distingue inférence de formation de nouveaux poids ; toute adaptation réalisée possède manifeste, delta et validation avant/après ; sinon l’UI porte explicitement la mention « non disponible ». Le noyau, les permissions, la pause/restauration, le réseau fermé par défaut et la gestion des secrets restent sûrs ; tests automatiques verts sur la plateforme disponible.

### 17.1 Livrables de publication d’une campagne

Rapport PDF lisible et Markdown versionnable. Protocole JSON/YAML figé et hashé, avec hypothèses préenregistrées. Résultats CSV/JSON, dictionnaire des métriques et unités. Graphiques sourcés et scripts de régénération. Manifeste : commits, modèles, sources, licences, seeds, système, coûts. Journal des anomalies, résultats négatifs et interventions. Revue A/B/C et validation humaine identifiables, séparées des données. Notice « Ce que cette étude ne démontre pas ». Freewill Research • 11.11.2026 • 15

## 18. Plan de publication et collaborations

Publier le document de cadrage dans docs/research/FREEWILL_Programme_Recherche_V1.0.fr.md et le PDF correspondant ; créer ultérieurement la traduction anglaise intégrale, et non un document bilingue mélangé. Distinguer documentation de conception et rapports de résultats. Prévoir un protocole de contributions, les conditions d’accès aux données, une procédure de reproduction locale, des limites clairement affichées et l’acceptation d’hypothèses réfutées. Inviter des experts externes en neurosciences cognitives, apprentissage continu, statistiques et philosophie de l’esprit à critiquer les protocoles avant d’interpréter la conscience. Les observateurs LLM sont utiles pour le travail préparatoire ; ils ne remplacent ni le regard humain, ni la revue scientifique externe.

## 19. Registre de risques et réponses

- Anthropomorphisme. Conséquence : Confusion entre scores et sentiments Contrôle : Lexique prudent, avertissements et niveaux de preuve

- Circularité des mesures. Conséquence : Un effet programmé est présenté comme découverte Contrôle : Benchmarks inédits, témoins, ablations utiles

- Hallucination des observateurs. Conséquence : Rapport convaincant mais faux Contrôle : Outils lecture seule, preuves obligatoires, validation humaine

- Dépendance à API. Conséquence : Coûts et dérive de versions Contrôle : Offline, budgets, métadonnées et moteur simulé

- Oubli catastrophique. Conséquence : Perte de capacités après apprentissage Contrôle : Rejeu, évaluations anciennes/nouvelles, rollback

- Croissance inutile. Conséquence : Paramètres et coûts sans amélioration Contrôle : Mesures de performance par ressource, plafond

- Fuite de données privées. Conséquence : Souvenirs/identités envoyés au fournisseur Contrôle : Consentement, minimisation, anonymisation, contrôle secrets

- Branches concurrentes. Conséquence : Écrasement H7 ou embedded Contrôle : Audit, intégration par petits commits et CI

- Statistique erronée. Conséquence : Faux positifs de recherche Contrôle : Unités indépendantes, plan préalable, incertitude

- Confusion linguistique. Conséquence : Produit incohérent et publications ambiguës Contrôle : Catalogues FR/EN, tests de parité

## 20. Conclusions et frontières de connaissance

Freewill peut devenir une plateforme de recherche mécaniste sur l’individuation artificielle, mais son succès ne devrait pas être mesuré au nombre de fonctions anthropomorphes. Les contributions les plus prometteuses sont (i) l’étude causale de vies contrefactuelles, (ii) la comparaison entre mémoire externe et transformation paramétrique locale, (iii) la mesure longitudinale de dispositions affectives et métacognitives, (iv) l’effet de la consolidation hors ligne et (v) la triangulation d’analyses par observateurs indépendants sur des données communes. La progression intellectuelle attendue est : mécanismes implémentés → expériences contrôlées → effets robustes → interprétations limitées → résultats publiables, y compris négatifs. À aucun stade, l’introspection verbale d’une instance ou le consensus de trois LLM ne démontrent un ressenti subjectif. Freewill Research • 11.11.2026 • 16

Annexes A. Exemple de protocole versionné { "protocol_id": "EXP-01", "protocol_version": "1.0.0", "hypotheses": ["H5", "H7"], "design": "paired_counterfactual", "baseline_snapshot_sha256": "<hash-de-T0>", "conditions": ["neutral", "history_A", "history_B"], "primary_outcome": "heldout_behavioral_divergence", "secondary_outcomes": ["retention", "calibration"], "seed_policy": "predeclared_independent_streams", "locked_before_execution": true, "ethics": {"read_only_observers": true, "no_distress": true} }

B. Exemple de manifeste de croissance neuronale { "model_version": "ada-model-0007", "base_model_id": "<identifiant-versionne>", "base_parameters": 2000000000, "trainable_adapter_parameters": 0, "added_module_parameters": 0, "active_parameters": null, "training_method": "none", "checkpoint_before": "<hash>", "checkpoint_after": "<hash>", "heldout_evaluation_id": "<exp-id>", "decision": "not_trained", "note": "Exemple de structure, aucune croissance affirmée" } Ne jamais conserver les nombres de cet exemple comme preuve d’un entraînement réel.

C. Glossaire opérationnel Affect calculé : dynamique numérique qui module effectivement des opérations. Ablation : suppression expérimentale d’un composant pour étudier sa contribution. Checkpoint : état restaurable et référencé par hachage. Contrefactuel : comparaison de trajectoires issues d’une origine identique et d’une intervention différente. Émergence : propriété à caractériser opérationnellement, non synonyme de complexité inattendue. Individuation : différenciation fonctionnelle durable et généralisable issue d’une histoire propre. Métacognition : estimation et régulation de certains de ses propres processus cognitifs. Paramètre actif : poids effectivement mobilisé lors de l’inférence, à distinguer des poids stockés. Reproductibilité : capacité à retrouver des résultats selon un protocole, des outils et des conditions déclarés. Ressenti subjectif : caractère vécu d’un état ; aucun indicateur logiciel unique ne le mesure. Freewill Research • 11.11.2026 • 17

Références principales et liens vérifiables [1] Butlin, P., Long, R., et al. (2023). Consciousness in Artificial Intelligence: Insights from the Science of Consciousness. arXiv:2308.08708. https://arxiv.org/abs/2308.08708 [2] Butlin, P., Long, R., et al. (2026 ; publication en ligne 2025). Identifying indicators of consciousness in AI systems. Trends in Cognitive Sciences, 30(6), 488–501. https://doi.org/10.1016/j.tics.2025.10.011 [3] Park, J. S., et al. (2023). Generative Agents: Interactive Simulacra of Human Behavior. arXiv:2304.03442. https://arxiv.org/abs/2304.03442 [4] Franklin, S., et al. (2014). LIDA: A systems-level architecture for cognition, emotion, and learning. IEEE Transactions on Autonomous Mental Development, 6(1), 19–41. https://doi.org/10.1109/TAMD.2013.2277589 [5] Lu, C., Lu, C., et al. (2024). The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery. arXiv:2408.06292. https://arxiv.org/abs/2408.06292 [6] Hu, E. J., et al. (2021). LoRA: Low-Rank Adaptation of Large Language Models. arXiv:2106.09685. https://arxiv.org/abs/2106.09685 [7] Rusu, A. A., et al. (2016). Progressive Neural Networks. arXiv:1606.04671. https://arxiv.org/abs/1606.04671 [8] Dohare, S., et al. (2024). Loss of plasticity in deep continual learning. Nature, 632, 768–774. https://doi.org/10.1038/s41586-024-07711-7 [9] Wilson, M. A., & McNaughton, B. L. (1994). Reactivation of hippocampal ensemble memories during sleep. Science, 265, 676–679. https://doi.org/10.1126/science.8036517 [10] Hoel, E. (2021). The overfitted brain: Dreams evolved to assist generalization. Patterns, 2(5), 100244. https://doi.org/10.1016/j.patter.2021.100244 [11] Chalmers, D. J. (1995). Facing Up to the Problem of Consciousness. Journal of Consciousness Studies, 2(3), 200– 219. https://consc.net/papers/facing.html [12] NeurIPS. Paper Checklist Guidelines (consulté en novembre 2026). https://neurips.cc/public/guides/PaperChecklist [13] Freewill, dépôt de référence et branches observées (11 novembre 2026). https://github.com/ssamri/Freewill ; https://github.com/ssamri/Freewill/tree/feat/h7-affect ; https://github.com/ssamri/Freewill/tree/feat/embedded-model Note bibliographique : ces références servent au cadrage. Elles ne valident pas empiriquement les hypothèses H1–H10 ni une expérience subjective artificielle. Les références secondaires doivent être contrôlées avant une soumission académique.

Freewill Research • 11.11.2026 • 18
