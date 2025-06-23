'''
Heuristics that compute an initial solution and 
then improve it.

@author: Vassilissa Lehoux
'''
from typing import Dict

from src.scheduling.optim.heuristics import Heuristic
from src.scheduling.instance.instance import Instance
from src.scheduling.solution import Solution
from src.scheduling.optim.constructive import NonDeterminist
# Import the neighborhoods
from src.scheduling.optim.neighborhoods import ReassignOneOperation, SwapOperationsOnOneMachine


class FirstNeighborLocalSearch(Heuristic):
    '''
    Vanilla local search will first create a solution,
    then at each step try and improve it by looking at
    solutions in its neighborhood.
    The first solution found that improves over the current solution
    replaces it.
    The algorithm stops when no solution is better than the current solution
    in its neighborhood.
    '''

    def __init__(self, params: Dict = dict()):
        '''
        Constructor
        @param params: The parameters of your heuristic method if any as a
                       dictionary. Implementation should provide default values in the function.
        '''
        super().__init__()

    def run(self, instance: Instance, InitClass, NeighborClass, params: Dict = dict()) -> Solution:
        '''
        Compute a solution for the given instance.
        Implementation should provide default values in the function
        (the function will be evaluated with an empty dictionary).

        @param instance: the instance to solve
        @param InitClass: the class for the heuristic computing the initialization (e.g., NonDeterminist)
        @param NeighborClass: the class of neighborhood used in the vanilla local search (e.g., ReassignOneOperation)
        @param params: the parameters for the run (e.g., {"max_iterations": 100})
        '''
        max_iterations = params.get("max_iterations", 100) # Critère d'arrêt par défaut

        initial_heuristic = InitClass(params)
        current_solution = initial_heuristic.run(instance, params)

        print(f"Initial solution objective: {current_solution.objective:.2f}")

        iteration = 0
        while iteration < max_iterations:
            found_better = False
            
            # On "instancie" le voisinage pour la solution actuelle
            neighborhood = NeighborClass(instance) 
            
            next_solution = neighborhood.first_better_neighbor(current_solution)

            if next_solution.objective < current_solution.objective:
                current_solution = next_solution
                found_better = True
                print(f"  Itération {iteration+1}: Meilleure solution trouvée avec {current_solution.objective:.2f}")
            
            if not found_better:
                print(f"  Itération {iteration+1}: Pas de meilleur voisin trouvé ! On ne peut pas faire mieux.")
                break 

            iteration += 1

        print(f"Solution finale: {current_solution.objective:.2f}")
        return current_solution


class BestNeighborLocalSearch(Heuristic):
    '''
    Vanilla local search will first create a solution,
    then at each step try and improve it by looking at
    solutions in its neighborhood.
    The best solution found that improves over the current solution
    replaces it.
    The algorithm stops when no solution is better than the current solution
    in its neighborhood.
    '''

    def __init__(self, params: Dict = dict()):
        '''
        Constructor
        @param params: The parameters of your heuristic method if any as a
                       dictionary. Implementation should provide default values in the function.
        '''
        super().__init__() 

    def run(self, instance: Instance, InitClass, NeighborClasses, params: Dict = dict()) -> Solution:
        '''
        Computes a solution for the given instance.
        Implementation should provide default values in the function
        (the function will be evaluated with an empty dictionary).

        @param instance: the instance to solve
        @param InitClass: the class for the heuristic computing the initialization (e.g., NonDeterminist)
        @param NeighborClasses: A list of neighborhood classes to use (e.g., [ReassignOneOperation, SwapOperationsOnOneMachine])
        @param params: the parameters for the run (e.g., {"max_iterations": 100})
        '''
        max_iterations = params.get("max_iterations", 100)
        
        no_improvement_limit = params.get("no_improvement_limit", 10) 
        consecutive_no_improvement = 0

        initial_heuristic = InitClass(params)
        current_solution = initial_heuristic.run(instance, params)

        print(f"Objectif de la solution initiale: {current_solution.objective:.2f}")

        iteration = 0
        while iteration < max_iterations:
            best_neighbor_overall = current_solution.deepcopy() # On commence avec la solution courante
            found_better_in_step = False

            # Parcourir tous les voisins fournis
            for NeighborClass in NeighborClasses:
                neighborhood = NeighborClass(instance)
                
                # Trouver le meilleur voisin de ce voisinnage 
                best_neighbor_in_this_neighborhood = neighborhood.best_neighbor(current_solution)
                
                # Comparer avec le meilleur voisin global trouvé jusqu'à présent dans cette itération
                if best_neighbor_in_this_neighborhood.objective < best_neighbor_overall.objective:
                    best_neighbor_overall = best_neighbor_in_this_neighborhood
                    found_better_in_step = True
            
            if best_neighbor_overall.objective < current_solution.objective:
                current_solution = best_neighbor_overall
                consecutive_no_improvement = 0 # Reset
                print(f"  Iteration {iteration+1}: Meilleure solution trouvée avec {current_solution.objective:.2f}")
            else:
                consecutive_no_improvement += 1
                print(f"  Iteration {iteration+1}: Pas d'amélioration ! : {consecutive_no_improvement}")

            if consecutive_no_improvement >= no_improvement_limit:
                print(f"  Stopping: Pas d'amélioration sur {no_improvement_limit} itérations consécutives.")
                break

            iteration += 1

        print(f"Objectif de la fonction finale: {current_solution.objective:.2f}")
        return current_solution


if __name__ == "__main__":
    # To play with the heuristics
    from src.scheduling.tests.test_utils import TEST_FOLDER_DATA
    import os
    import matplotlib.pyplot as plt

    inst_path = TEST_FOLDER_DATA + os.path.sep + "jsp10"
    print(f"Loading instance from: {inst_path}")
    inst = Instance.from_file(inst_path)
    
    print("\n--- Running FirstNeighborLocalSearch ---")
    first_neighbor_ls = FirstNeighborLocalSearch()

    sol_first = first_neighbor_ls.run(inst, NonDeterminist, ReassignOneOperation, {"max_iterations": 50})
    plt_first = sol_first.gantt("tab20")
    plt_first.savefig("gantt_first_neighbor_ls.png")
    print(f"Gantt chart for FirstNeighborLocalSearch saved to gantt_first_neighbor_ls.png")

    print("\n--- Running BestNeighborLocalSearch ---")
    best_neighbor_ls = BestNeighborLocalSearch()
    sol_best = best_neighbor_ls.run(inst, NonDeterminist, [ReassignOneOperation, SwapOperationsOnOneMachine], 
                                    {"max_iterations": 100, "no_improvement_limit": 20})
    plt_best = sol_best.gantt("tab20")
    plt_best.savefig("gantt_best_neighbor_ls.png")
    print(f"Gantt chart for BestNeighborLocalSearch saved to gantt_best_neighbor_ls.png")
