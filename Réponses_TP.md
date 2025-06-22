<h1 style="text-align: center;">
TP Ordonnancement de Tâches : Modélisation
</h1>

<h3>
Modélisation
</h3>
<h5>
1)Variables de décision, contraintes et objectifs
</h5>
Variables de Décision :
Affectation des opérations aux machines : Pour chaque opération, nous devons choisir la machine sur laquelle elle sera exécutée, parmi l'ensemble des machines compatibles (appelées "variants" dans le code).
Temps de début des opérations : Pour chaque opération affectée, nous devons déterminer son instant de début précis sur la machine choisie.
Gestion de l'état des machines (marche/arrêt) : Pour chaque machine, il faut décider des instants où elle est allumée (set_up) et éteinte (tear_down). Une machine peut être allumée et éteinte plusieurs fois, créant ainsi des plages de fonctionnement continues ou discontinues.
Contraintes :
Contraintes de Précédence des Opérations (intra-job) : Une opération ne peut commencer que lorsque son prédécesseur direct (l'opération précédente du même job) est terminée. Ces contraintes sont essentielles pour assurer le bon déroulement des tâches.
Contraintes de Capacité des Machines : Une machine ne peut exécuter qu'une seule opération à la fois. Il est donc impossible que deux opérations se chevauchent sur la même machine.
Disponibilité des Machines : Une opération ne peut être exécutée sur une machine que si celle-ci est allumée et disponible. Les temps de démarrage (set_up_time) et d'arrêt (tear_down_time) des machines doivent être impérativement pris en compte dans le planning.
Fenêtre de Temps des Machines : Le planning de chaque machine, incluant les temps de démarrage et d'arrêt, ne doit pas dépasser une durée maximale fixée (end_time).
Toutes les Opérations Doivent Être Exécutées : Chaque opération de chaque tâche doit impérativement être planifiée et achevée dans le planning final.
Objectifs :
Minimiser la Consommation Totale d'Énergie : L'entreprise souhaite réduire au maximum la somme de l'énergie consommée par toutes les machines. Cela inclut l'énergie de démarrage, d'arrêt, l'énergie consommée en inactivité (min_consumption) et celle consommée lors de l'exécution des opérations.
Minimiser le Makespan (Cmax) : Cet objectif vise à réduire le temps total nécessaire pour compléter toutes les tâches, c'est-à-dire l'instant de fin de la dernière opération de toutes les tâches.
Minimiser le Temps Moyen de Complétion des Tâches (Sum Ci) : L'entreprise cherche également à réduire la moyenne des temps de complétion de chaque tâche, ce qui correspond à la somme des temps de complétion de chaque job divisée par le nombre de jobs.



2) Fonction objectif agrégée
La fonction objectif proposée pour agréger les différents objectifs de l'entreprise est une combinaison linéaire pondérée. Cette approche permet de refléter l'importance relative de chaque objectif :

Objectif(S)=α× 
EnergieTotale(S)+β×Makespan(S)+γ×TempsMoyenCompletion(S)

Où :

S représente une solution de planning.
EnergieTotale(S) est la consommation totale d'énergie de toutes les machines pour la solution S.
textMakespan(S) est le temps de complétion maximal parmi tous les jobs pour la solution S.
textTempsMoyenCompletion(S) est le temps moyen de complétion de tous les jobs pour la solution S.
alpha,
beta,
gamma sont des poids positifs (définis comme ALPHA, BETA, GAMMA dans le code solution.py) qui déterminent l'influence de chaque critère sur la valeur finale de l'objectif.
Dans le code fourni, les poids sont configurés ainsi : ALPHA = 1.0, BETA = 1.0, et GAMMA = 0.0. Cela signifie que la fonction objectif cherche actuellement à minimiser la somme de l'énergie totale et du makespan, tandis que le temps moyen de complétion n'est pas directement pris en compte.



3) Évaluation d'une solution réalisable et non réalisable
Évaluation d'une solution réalisable :
Une solution est dite réalisable si elle respecte l'ensemble des contraintes définies (toutes les opérations sont planifiées, les précédences sont respectées, les machines ne sont pas surchargées et respectent leurs fenêtres de temps maximales).

Pour une solution réalisable, sa valeur est calculée directement par la fonction objectif agrégée précédemment définie :

Valeur(S)=α× 
EnergieTotale(S)+β×Makespan(S)+γ×TempsMoyenCompletion(S)

Cette évaluation est mise en œuvre dans la méthode recompute() de la classe Solution et est accessible via les propriétés evaluate ou objective.

Évaluation d'une solution non réalisable :
Une solution est considérée comme non réalisable si au moins une contrainte est violée (par exemple, une opération n'est pas planifiée, une précédence est ignorée, ou une machine dépasse son end_time).

Pour une solution non réalisable, une pénalité élevée est appliquée à la fonction objectif. Cette pénalité rend la solution non réalisable intrinsèquement moins "bonne" que n'importe quelle solution réalisable, même de mauvaise qualité. La formule utilisée dans le code est la suivante :

Valeur(S)=NombreViolations×PENALTY

Où :

NombreViolations représente le nombre d'opérations qui n'ont pas pu être affectées.
PENALTY est une constante de grande valeur (10 ** 6 dans le code).
Cette approche garantit que les algorithmes d'optimisation chercheront toujours à trouver une solution réalisable avant d'optimiser les métriques de performance.



4) Instance non réalisable
Voici une instance d'exemple où aucune solution réalisable n'existe :

Nom de l'instance : Unfeasible_Instance

Fichier Unfeasible_Instance_op.csv :


job_id,op_id,machine_id,processing_time,energy_consumption
0,0,0,100,10
0,0,1,100,10
Cela définit une seule opération (Job 0, Op 0).
Cette opération peut être effectuée sur la machine 0 ou la machine 1.
Le temps de traitement (processing_time) pour cette opération est de 100 unités de temps, avec une consommation d'énergie de 10.
Fichier Unfeasible_Instance_mach.csv :


machine_id,set_up_time,set_up_energy,tear_down_time,tear_down_energy,min_consumption,end_time
0,10,5,10,5,1,50
1,10,5,10,5,1,50
Cela définit deux machines, Machine 0 et Machine 1, qui ont des caractéristiques identiques.
Chaque machine a un temps de démarrage (set_up_time) de 10 unités de temps et un temps d'arrêt (tear_down_time) de 10 unités de temps.
Le temps de fin maximum (end_time) alloué pour le planning sur chaque machine est de 50 unités de temps.
Explication de l'irréalisabilité :
Pour qu'une opération soit planifiée sur une machine, la machine doit être allumée, exécuter l'opération, puis être éteinte (ou rester allumée pour d'autres opérations, mais dans ce cas simple, elle ne ferait que cette opération).

Calculons le temps minimum requis pour exécuter la seule opération (Job 0, Op 0) sur n'importe laquelle des machines :

Temps total minimum requis=set_up_time+processing_time+tear_down_time

En utilisant les valeurs de l'instance :

Temps total minimum requis=10 (démarrage)+100 (exécution)+10 (arrêt)=120 unités de temps

Cependant, la contrainte end_time pour chaque machine est fixée à 50 unités de temps.

Puisque le temps minimum requis pour exécuter l'opération (120) est largement supérieur au temps maximum autorisé sur n'importe quelle machine (50), il est impossible de planifier cette opération. Par conséquent, aucune solution réalisable n'existe pour cette instance.


Proposition d'algorithme glouton déterministe : "Earliest Finish Time First (EFTF)"
Cet algorithme glouton privilégie la rapidité d'exécution des opérations en cherchant à minimiser leur temps de fin.

Principe de l'algorithme :
L'algorithme parcourt les opérations disponibles et non encore planifiées, et pour chacune d'elles, il évalue l'option de planification qui la fera se terminer le plus tôt possible. L'opération et l'affectation qui offrent le meilleur temps de fin sont choisies et l'opération est planifiée. Ce processus est répété jusqu'à ce que toutes les opérations soient planifiées ou qu'aucune opération ne puisse être planifiée.

Étapes de l'algorithme :
Initialisation :

Créer une nouvelle solution vide à partir de l'instance.
Initialiser une liste des opérations prêtes (celles dont tous les prédécesseurs sont terminés, ou qui n'ont pas de prédécesseurs). Au début, ce sont les premières opérations de chaque job.
Conserver la liste de toutes les opérations à planifier.
Boucle de Planification :

Tant qu'il reste des opérations non planifiées :
Identification des opérations candidates : Mettre à jour la liste des opérations prêtes. Une opération est "prête" si elle n'est pas encore planifiée et que tous ses prédécesseurs sont terminés.
Choix glouton : Parmi toutes les opérations prêtes, et pour chaque variante possible (machine, temps de traitement, énergie) de ces opérations :
Calculer le temps de fin le plus tôt possible pour cette opération sur cette machine. Pour ce faire, nous devons considérer :
Le temps de fin de son prédécesseur direct (s'il y en a un).
Le temps de disponibilité de la machine choisie.
Les temps de set_up et tear_down de la machine si elle doit être allumée ou arrêtée.
La "meilleure" affectation est celle qui minimise ce temps de fin.
Sélection : Choisir l'opération et la machine qui permettent le plus petit temps de fin global. S'il y a des égalités, on peut briser les égalités arbitrairement (par exemple, par le plus petit job_id, puis op_id, puis machine_id).
Planification : Affecter l'opération choisie à la machine choisie à son temps de début calculé. Mettre à jour l'état de la machine et de l'opération.
Mise à jour : L'opération planifiée est retirée des opérations non planifiées. Ses successeurs peuvent potentiellement devenir "prêts".
En quoi cet algorithme est glouton :
Cet algorithme est glouton car à chaque étape, il prend la décision qui semble la meilleure localement, sans considérer l'impact de cette décision sur les étapes futures ou sur l'objectif global. Plus précisément :

Il choisit toujours l'opération et l'affectation qui permettent de terminer une opération le plus tôt possible. C'est une stratégie de minimisation locale du temps.
Il ne réévalue pas les décisions passées et ne tente pas de les annuler ou de les modifier pour obtenir un meilleur résultat global.
L'objectif ici est de produire un planning rapidement, quitte à ce qu'il ne soit pas optimal globalement.


Première heuristique

2) Algorithme non-déterministe
Proposition d'algorithme non-déterministe : "Random Prioritized Scheduling (RPS)"
Cet algorithme introduit de l'aléatoire dans le processus de décision pour générer différentes solutions à chaque exécution.

Principe de l'algorithme :
Au lieu de choisir la "meilleure" option de manière déterministe, cet algorithme choisit aléatoirement parmi les opérations prêtes et leurs affectations possibles. Pour ajouter un peu d'intelligence tout en restant non-déterministe, on peut introduire une notion de "priorité aléatoire" ou de "sélection pondérée" si souhaité, mais la forme la plus simple est une sélection purement aléatoire.

Étapes de l'algorithme :
Initialisation :

Créer une nouvelle solution vide à partir de l'instance.
Initialiser la liste des opérations non planifiées.
(Optionnel) Initialiser le générateur de nombres aléatoires avec une graine si la reproductibilité est parfois souhaitée pour des tests.
Boucle de Planification :

Tant qu'il reste des opérations non planifiées :
Identification des opérations candidates : Filtrer les opérations non planifiées pour obtenir la liste des opérations prêtes (celles dont tous les prédécesseurs sont terminés).
Gestion des blocages : Si aucune opération n'est prête (mais il en reste des non planifiées), cela signifie qu'il y a un blocage (deadlock) ou qu'une opération n'a pas pu être satisfaite par le planning précédent. Dans ce cas, l'heuristique s'arrête, laissant une solution potentiellement non réalisable.
Sélection aléatoire d'une opération : Choisir une opération au hasard parmi les opérations prêtes.
Sélection aléatoire d'une machine : Pour l'opération choisie, sélectionner au hasard l'une de ses machines variantes possibles.
Tentative de Planification : Tenter de planifier l'opération choisie sur la machine choisie au plus tôt. Si la planification est réussie (respect des contraintes internes à operation.schedule et machine.add_operation), l'opération est marquée comme planifiée et retirée de la liste des opérations non planifiées.
Mise à jour : L'opération planifiée est retirée des opérations non planifiées. Ses successeurs peuvent potentiellement devenir "prêts".
En quoi cet algorithme est non-déterministe :
Cet algorithme est non-déterministe car à chaque itération, la sélection de la prochaine opération à planifier et de la machine sur laquelle l'affecter est basée sur un choix aléatoire parmi les options disponibles. Deux exécutions de l'algorithme sur la même instance (sans fixer la graine aléatoire) auront de fortes chances de produire des plannings différents.

3) Complexité des algorithmes
Pour analyser la complexité, nous allons utiliser les notations suivantes :

N: nombre total d'opérations dans l'instance (instance.nb_operations).
J: nombre total de jobs (instance.nb_jobs).
M: nombre total de machines (instance.nb_machines).
K: nombre maximum de variantes (associations machine/temps/énergie) pour une opération. Dans le pire des cas, K peut être égal à M.
P: nombre maximum de prédécesseurs pour une opération (souvent 1 pour les prédécesseurs intra-job).
Complexité de l'algorithme Glouton "Earliest Finish Time First (EFTF)" (Greedy):
L'algorithme glouton itère jusqu'à ce que toutes les opérations soient planifiées. Dans le pire des cas, il planifie une opération par itération.

Boucle principale : S'exécute N fois (une fois pour chaque opération à planifier).

ready_operations : À chaque itération, pour trouver les opérations prêtes, il faut parcourir les unassigned_operations. Cette liste peut contenir jusqu'à N opérations. Pour chaque opération, vérifier op.is_ready(0) implique de parcourir ses prédécesseurs. Dans le pire des cas, O(N
timesP).

Choix glouton (recherche de la meilleure affectation) :

Parcourt toutes les ready_operations (max N).
Pour chaque ready_operation, parcourt toutes ses _variants (max K).
Pour chaque variante, il récupère la machine (instance.get_machine) qui est O(1) en moyenne avec un dictionnaire.
Le calcul de potential_start_time implique op.min_start_time qui est O(P) et machine.available_time qui est O(1).
Donc, cette étape est O(N timesK timesP).
solution.schedule : Cette opération implique d'ajouter l'opération à la liste de la machine (machine.add_operation) et de recalculer potentiellement la disponibilité de la machine. Si la liste est simple, l'ajout est O(1). La mise à jour de l'état de la machine est O(1).

En combinant ces étapes, la complexité dominante par itération est la recherche du meilleur choix glouton, qui est O(N timesK timesP). Puisqu'il y a N itérations dans le pire des cas (où une seule opération est planifiée par itération), la complexité totale est :

Complexité : O(N² timesK timesP)

Dans le cas où K est au maximum M (chaque opération peut aller sur toutes les machines) et P est petit et constant (précédence linéaire dans les jobs), cela se simplifie souvent à O(N² timesM).

Complexité de l'algorithme Non-Déterministe "Random Prioritized Scheduling (RPS)" (NonDeterminist):
Cet algorithme fonctionne également en itérant jusqu'à ce que toutes les opérations soient planifiées.

Boucle principale : S'exécute N fois dans le pire des cas.
ready_operations : Similaire à l'algorithme glouton, cette étape est O(N
timesP).
Sélection aléatoire :
random.choice(ready_operations) : O(1) après la construction de la liste.
random.choice(possible_machines_data) : O(1) après l'accès aux variants.
solution.schedule : Similaire à l'algorithme glouton, O(1).
La différence majeure est que l'algorithme non-déterministe ne parcourt pas toutes les options pour trouver la "meilleure" à chaque étape, mais effectue des choix aléatoires. Donc, l'étape de sélection est beaucoup plus rapide.

En combinant ces étapes, la complexité dominante par itération est la recherche des opérations prêtes, soit O(N
timesP). Puisqu'il y a N itérations, la complexité totale est :

Complexité : O(N² timesP)

Si P est constant (précédences intra-job simples), la complexité est O(N²).

Recherche locale


1) Proposition de deux voisinages de solutions
La recherche locale explore l'espace des solutions en effectuant de petits changements sur une solution courante pour en trouver une meilleure dans un voisinage défini.

Pour la modélisation de nos voisinages, nous allons manipuler les deux principales variables de décision : l'affectation des opérations aux machines et l'ordre des opérations sur une machine donnée.

Notations :

N : Nombre total d'opérations.
M : Nombre total de machines.
K_i : Nombre de machines sur lesquelles l'opération i peut être exécutée (nombre de variants).
Voisinage 1 : "Reassign One Operation" (Réaffecter une opération)
Description : Ce voisinage génère de nouvelles solutions en prenant une seule opération déjà planifiée et en la réaffectant à une autre machine compatible disponible dans ses _variants, tout en essayant de la replanifier au plus tôt sur cette nouvelle machine.

Justification :

Taille du voisinage : Pour chaque opération i (il y en a N), elle peut être réaffectée à K_i−1 autres machines (si K_i1). La taille totale du voisinage est donc
sum_i=1 N (K_i−1). Dans le pire des cas où chaque opération peut aller sur toutes les machines, K_i=M, la taille est N
times(M−1).
Taille : O(N timesM)
Taille polynomiale : Oui, la taille du voisinage est polynomiale par rapport à la taille de l'instance (N et M).
Accessibilité de l'espace de solution : Non, ce voisinage ne permet pas d'atteindre toutes les solutions de l'espace. Par exemple, il ne peut pas modifier l'ordre des opérations sur une machine ou échanger des opérations entre des machines si cela implique des réordonnancements complexes qui ne peuvent pas être résolus par une simple réaffectation et replanification "au plus tôt". Il ne peut pas non plus modifier les temps de démarrage/arrêt des machines indépendamment de la planification des opérations.
Voisinage 2 : "Swap Operations on One Machine" (Échanger des opérations sur une machine)
Description : Ce voisinage génère de nouvelles solutions en sélectionnant une machine, puis en échangeant l'ordre de deux opérations adjacentes (ou non, pour une version plus complexe) qui sont planifiées sur cette machine. Après l'échange, les opérations sont replanifiées au plus tôt sur cette machine.

Justification :

Taille du voisinage :
Nous devons choisir une machine ( M choix).
Pour chaque machine, s'il y a L_m opérations planifiées dessus, nous pouvons choisir 2 opérations parmi L_m pour les échanger. Le nombre de paires est
binomL_m2=
fracL_m(L_m−1)2.
Le nombre total d'opérations planifiées sur toutes les machines est N, donc
sumL_m=N.
Dans le pire des cas, si toutes les opérations sont sur une seule machine, L_m=N, la taille est O(N²). Si les opérations sont réparties uniformément, L_m=N/M, alors la taille est M
timesO((N/M)²)=O(N²/M).
Taille : O(N²) (dans le pire des cas, si une machine a beaucoup d'opérations).
Taille polynomiale : Oui, la taille du voisinage est polynomiale par rapport à la taille de l'instance (N).
Accessibilité de l'espace de solution : Non, ce voisinage ne permet pas non plus d'atteindre toutes les solutions. Il ne peut pas changer l'affectation d'une opération à une machine différente. Il ne peut modifier que l'ordre sur une machine spécifique. Pour explorer pleinement l'espace, il faudrait combiner des mouvements de réaffectation et de réordonnancement, et potentiellement de modification des arrêts/démarrages.

4) Script tests/script_comparaison_algos.py créé !

Attention, il faut installer le module tabulate pour l'exécuter :
```
python3   -m pip install tabulate
```

```
python3 -m src.scheduling.tests.script_comparer_algos
```