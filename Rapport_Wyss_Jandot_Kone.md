Jandot Floriane</br>
Kone Zeinabou</br>
Wyss Marie

# TP d’Ordonnancement de Tâches – Modélisation

## Partie I Modélisation

### 1) Variables de décision, contraintes et objectifs

Nous commençons par identifier les **variables de décision** :

- Il s’agit d’abord de décider sur quelle machine chaque opération doit être effectuée, en choisissant parmi les machines compatibles (appelées "variants").
- Ensuite, il faut déterminer le **moment de début** de chaque opération.
- Enfin, il est nécessaire de gérer l’**état des machines**, c’est-à-dire décider à quels moments elles doivent être allumées (*set-up*) ou éteintes (*tear-down*).

Les **contraintes** à respecter sont les suivantes :

- Il faut respecter l’ordre des opérations à l’intérieur d’un même job : une opération ne peut commencer que lorsque celle qui la précède est terminée.
- Une machine ne peut exécuter **qu’une seule opération à la fois**.
- Une machine ne peut fonctionner que si elle est allumée ; les temps de set-up et tear-down doivent donc être pris en compte dans le planning.
- Le planning global ne doit pas dépasser une durée maximale appelée `end_time`.
- Enfin, toutes les opérations doivent impérativement être planifiées.

Concernant les **objectifs**, plusieurs critères doivent être optimisés :

- Minimiser la **consommation totale d’énergie**.
- Minimiser le **makespan**, c’est-à-dire la durée totale du planning.
- Minimiser le **temps moyen de complétion**, c’est-à-dire la moyenne des temps d’achèvement des opérations.

### 2) Fonction objectif agrégée

La fonction objectif permet d’agréger ces trois critères en une seule valeur à minimiser. Elle s’écrit comme suit :

```
Objectif(S) = α × EnergieTotale(S) + β × Makespan(S) + γ × TempsMoyenCompletion(S)
```

Dans notre cas, les poids utilisés sont :
- `ALPHA = 1.0`
- `BETA = 1.0`
- `GAMMA = 0.0`

Cela signifie que nous accordons autant d’importance à l’énergie consommée qu’au makespan, tandis que le temps moyen de complétion n’est pas pris en compte ici.

### 3) Évaluation d’une solution

Pour évaluer une **solution réalisable**, on utilise la même fonction que ci-dessus, calculée grâce à la méthode `recompute()` de la classe `Solution` :

```
Valeur(S) = α × EnergieTotale(S) + β × Makespan(S) + γ × TempsMoyenCompletion(S)
```

Si la solution est **non réalisable**, on la pénalise fortement :

```
Valeur(S) = NombreViolations × PENALTY
```

où `PENALTY` vaut `10^6`.

### 4) Exemple d’instance non réalisable

Voici un exemple concret :

#### Fichier `Unfeasible_Instance_op.csv`

```csv
job_id,op_id,machine_id,processing_time,energy_consumption
0,0,0,100,10
0,0,1,100,10
```

#### Fichier `Unfeasible_Instance_mach.csv`

```csv
machine_id,set_up_time,set_up_energy,tear_down_time,tear_down_energy,min_consumption,end_time
0,10,5,10,5,1,50
1,10,5,10,5,1,50
```

Dans cet exemple, pour chaque machine, le temps total nécessaire est :

```
setup (10) + exécution (100) + teardown (10) = 120
```

Or, le `end_time` est de 50, ce qui rend impossible l’exécution de l’opération dans les temps. Cette instance est donc non réalisable.

---

## Partie II Algorithmes

### 1) Algorithme glouton : **Earliest Finish Time First (EFTF)**

Cet algorithme cherche à planifier en priorité l’opération qui peut se terminer le plus tôt possible.

**Déroulement :**
1. On initialise une solution vide.
2. On maintient une liste des opérations prêtes à être planifiées.
3. Tant qu’il reste des opérations à planifier :
   - On identifie les opérations prêtes.
   - Pour chaque opération et chaque machine compatible, on calcule le temps de fin.
   - On planifie l’opération avec le **plus petit temps de fin**.

Il s’agit bien d’un algorithme **glouton**, car à chaque étape, il choisit localement la meilleure option possible, sans revenir sur ses choix précédents.

### 2) Algorithme non-déterministe : **Random Prioritized Scheduling (RPS)**

Cet algorithme repose sur une stratégie aléatoire.

**Déroulement :**
1. On commence avec une solution vide.
2. Tant que toutes les opérations ne sont pas planifiées :
   - On identifie les opérations prêtes.
   - On en choisit une au hasard, ainsi qu’une machine compatible.
   - On tente de la planifier.

Cet algorithme est **non-déterministe**, car les choix sont effectués de manière aléatoire à chaque itération.

### 3) Complexité des algorithmes

### Glouton (EFTF)

- La boucle principale s’exécute `N` fois (une par opération).
- À chaque itération, on explore `N × K × P` possibilités (N = nb opérations, K = machines compatibles, P = variants).
- On peut donc estimer la complexité à **O(N² × M)** si K ≈ M et P est constant.

### RPS (aléatoire)

- Même boucle principale en `O(N)`.
- À chaque étape, on a environ `N × P` choix.
- La complexité est donc **O(N²)**, légèrement plus faible mais moins efficace en pratique, car aléatoire.

---

## Partie III Recherche locale

### 1) Proposition de deux voisinages de solutions

La recherche locale vise à améliorer une solution existante en explorant les solutions voisines, c’est-à-dire celles qui peuvent être obtenues par de légères modifications de la solution actuelle. Dans notre cas, ces modifications portent sur deux types de décisions : l'affectation des opérations aux machines, et l'ordre des opérations sur une même machine.

Notations

N : Nombre total d'opérations.

M : Nombre total de machines.

Kᵢ : Nombre de machines compatibles avec l’opération i (appelées "variants").

#
#### Voisinage 1 : Réaffecter une opération à une autre machine ("Reassign One Operation")

Description :Dans ce voisinage, on modifie une solution existante en prenant une opération déjà planifiée et en la réaffectant à une autre machine parmi ses machines compatibles. L’opération est ensuite replanifiée au plus tôt sur cette nouvelle machine.

Justification :

Taille du voisinage :Pour chaque opération (au total N), on peut envisager de la déplacer sur l’une de ses autres machines compatibles (au nombre de Kᵢ − 1 pour chaque opération). La taille totale du voisinage est donc :


Dans le pire des cas, si chaque opération peut être affectée à n’importe quelle machine (donc Kᵢ = M), alors la taille du voisinage devient :

Complexité : O(N × M)

Taille polynomiale : Oui

Accessibilité de l’espace de solutions : Non. Ce voisinage ne permet pas d’explorer toutes les solutions possibles, car il ne modifie pas l’ordre des opérations ni les temps de démarrage/arrêt indépendamment des affectations.


#
####  Voisinage 2 : Échanger deux opérations sur une même machine ("Swap Operations on One Machine")

Description :Ce voisinage consiste à sélectionner une machine donnée et à échanger l’ordre de deux opérations planifiées sur cette machine. Après l’échange, on replanifie ces opérations au plus tôt dans leur nouvel ordre.

Justification :

Taille du voisinage :Pour chaque machine (M au total), si elle contient Lₘ opérations, on peut échanger deux opérations parmi elles. Le nombre de combinaisons possibles sur une machine est :



Comme la somme des Lₘ sur toutes les machines est N, la taille du voisinage total dépend de la répartition des opérations :

Si toutes les opérations sont sur une seule machine : O(N²)

Si les opérations sont réparties uniformément : O(N² / M)

Complexité : O(N²) dans le pire des cas

Taille polynomiale : Oui

Accessibilité de l’espace de solutions : Non. Ce voisinage ne permet pas de changer l’affectation d’une opération. Il faut le combiner à d'autres pour couvrir l’espace complet des solutions.

---
