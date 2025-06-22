Jandot Floriane
Kone Zeinabou
Wyss Marie

# TP Ordonnancement de Tâches : Modélisation

## Modélisation

### 1) Variables de décision, contraintes et objectifs

**Variables de Décision :**

* **Affectation des opérations aux machines** : Choisir la machine sur laquelle chaque opération sera exécutée parmi les machines compatibles ("variants").
* **Temps de début des opérations** : Déterminer le moment précis du démarrage de chaque opération.
* **Gestion de l'état des machines** : Décider des instants où chaque machine est allumée (set\_up) et éteinte (tear\_down).

**Contraintes :**

* **Précédence intra-job** : Une opération ne commence qu'après la fin de son prédécesseur.
* **Capacité des machines** : Une machine n'exécute qu'une seule opération à la fois.
* **Disponibilité des machines** : Une machine doit être allumée pour exécuter une opération. Les temps de set\_up/tear\_down doivent être respectés.
* **Fenêtre de temps des machines** : Le planning ne doit pas dépasser `end_time`.
* **Toutes les opérations doivent être exécutées**.

**Objectifs :**

* **Minimiser la consommation totale d'énergie**.
* **Minimiser le makespan (Cmax)**.
* **Minimiser le temps moyen de complétion (Sum Ci)**.

### 2) Fonction objectif agrégée

Fonction objectif :

```
Objectif(S) = α × EnergieTotale(S) + β × Makespan(S) + γ × TempsMoyenCompletion(S)
```

* Poids utilisés : `ALPHA = 1.0`, `BETA = 1.0`, `GAMMA = 0.0`

### 3) Évaluation d'une solution

**Solution réalisable :**

```
Valeur(S) = α × EnergieTotale(S) + β × Makespan(S) + γ × TempsMoyenCompletion(S)
```

* Calculée via `recompute()` de la classe `Solution`.

**Solution non réalisable :**

```
Valeur(S) = NombreViolations × PENALTY
```

* `PENALTY = 10^6`

### 4) Instance non réalisable

#### Fichier `Unfeasible_Instance_op.csv`

```
job_id,op_id,machine_id,processing_time,energy_consumption
0,0,0,100,10
0,0,1,100,10
```

#### Fichier `Unfeasible_Instance_mach.csv`

```
machine_id,set_up_time,set_up_energy,tear_down_time,tear_down_energy,min_consumption,end_time
0,10,5,10,5,1,50
1,10,5,10,5,1,50
```

**Explication** :

```
Temps total requis = 10 (setup) + 100 (exec) + 10 (teardown) = 120 > 50
```

Impossible de planifier l'opération : pas de solution réalisable.

## Algorithmes

### Algorithme glouton : Earliest Finish Time First (EFTF)

**Principe :**

* Planifier l'opération avec le plus petit temps de fin possible

**Étapes :**

1. Initialiser une solution vide.
2. Maintenir la liste des opérations prêtes.
3. Tant que des opérations non planifiées :

   * Identifier les opérations prêtes
   * Pour chaque variant, calculer le plus petit temps de fin
   * Planifier l'opération avec le minimum temps de fin

**Glouton ?** Oui : fait le meilleur choix local à chaque étape sans retour arrière.

### Algorithme non-déterministe : Random Prioritized Scheduling (RPS)

**Principe :**

* Choix aléatoire parmi les opérations prêtes et les machines compatibles

**Étapes :**

1. Initialiser une solution vide.
2. Tant qu'il y a des opérations non planifiées :

   * Identifier les opérations prêtes
   * Choisir une opération et une machine au hasard
   * Tenter de la planifier

**Non-déterministe ?** Oui : choix aléatoire à chaque étape

## Complexité des algorithmes

### Glouton (EFTF)

* Boucle principale : O(N)
* Par itération : O(N \* K \* P)
* **Complexité totale** : O(N² \* M) si K=M, P constant

### Non-déterministe (RPS)

* Boucle principale : O(N)
* Par itération : O(N \* P)
* **Complexité totale** : O(N²)

## Recherche locale

### Voisinage 1 : Reassign One Operation

* Réaffecter une opération à une autre machine
* Taille : O(N \* M)
* Ne couvre pas tout l'espace de solution

### Voisinage 2 : Swap Operations on One Machine

* Échanger l'ordre de deux opérations sur une même machine
* Taille du voisinage : O(M \* L^2), L = nombre d'opérations par machine
* Permet des changements d'ordre

---

Fin du document de modélisation et d'analyse pour le TP d'ordonnancement.
