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
        super().__init__() # We override this.

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
        max_iterations = params.get("max_iterations", 100) # Default stop criterion

        # Step 1: Initialize a solution
        initial_heuristic = InitClass(params)
        current_solution = initial_heuristic.run(instance, params)

        print(f"Initial solution objective: {current_solution.objective:.2f}")

        # Step 2: Local Search Loop
        iteration = 0
        while iteration < max_iterations:
            found_better = False
            
            # Instantiate the neighborhood for the current solution
            neighborhood = NeighborClass(instance) 
            
            # Get the first better neighbor
            next_solution = neighborhood.first_better_neighbor(current_solution)

            if next_solution.objective < current_solution.objective:
                current_solution = next_solution
                found_better = True
                print(f"  Iteration {iteration+1}: Found better solution with objective {current_solution.objective:.2f}")
            
            if not found_better:
                # No better neighbor found in the entire neighborhood, stop.
                print(f"  Iteration {iteration+1}: No better neighbor found. Local optimum reached.")
                break 

            iteration += 1

        print(f"Final solution objective: {current_solution.objective:.2f}")
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
        super().__init__() # We override this.

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
        # Additional stop criterion: no improvement for 'x' consecutive iterations
        no_improvement_limit = params.get("no_improvement_limit", 10) 
        consecutive_no_improvement = 0

        # Step 1: Initialize a solution
        initial_heuristic = InitClass(params)
        current_solution = initial_heuristic.run(instance, params)

        print(f"Initial solution objective: {current_solution.objective:.2f}")

        # Step 2: Local Search Loop
        iteration = 0
        while iteration < max_iterations:
            best_neighbor_overall = current_solution.deepcopy() # Start with current as the best candidate
            found_better_in_step = False

            # Iterate through all provided neighborhoods
            for NeighborClass in NeighborClasses:
                neighborhood = NeighborClass(instance)
                
                # Get the best neighbor from this specific neighborhood
                best_neighbor_in_this_neighborhood = neighborhood.best_neighbor(current_solution)
                
                # Compare with the best overall neighbor found so far in this iteration
                if best_neighbor_in_this_neighborhood.objective < best_neighbor_overall.objective:
                    best_neighbor_overall = best_neighbor_in_this_neighborhood
                    found_better_in_step = True
            
            if best_neighbor_overall.objective < current_solution.objective:
                current_solution = best_neighbor_overall
                consecutive_no_improvement = 0 # Reset counter
                print(f"  Iteration {iteration+1}: Found better solution with objective {current_solution.objective:.2f}")
            else:
                consecutive_no_improvement += 1
                print(f"  Iteration {iteration+1}: No improvement. Consecutive no improvement: {consecutive_no_improvement}")

            if consecutive_no_improvement >= no_improvement_limit:
                print(f"  Stopping: No improvement for {no_improvement_limit} consecutive iterations.")
                break

            iteration += 1

        print(f"Final solution objective: {current_solution.objective:.2f}")
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
    # Using ReassignOneOperation as MyNeighborhood1
    sol_first = first_neighbor_ls.run(inst, NonDeterminist, ReassignOneOperation, {"max_iterations": 50})
    plt_first = sol_first.gantt("tab20")
    plt_first.savefig("gantt_first_neighbor_ls.png")
    print(f"Gantt chart for FirstNeighborLocalSearch saved to gantt_first_neighbor_ls.png")

    print("\n--- Running BestNeighborLocalSearch ---")
    best_neighbor_ls = BestNeighborLocalSearch()
    # Using both neighborhoods: ReassignOneOperation and SwapOperationsOnOneMachine
    sol_best = best_neighbor_ls.run(inst, NonDeterminist, [ReassignOneOperation, SwapOperationsOnOneMachine], 
                                    {"max_iterations": 100, "no_improvement_limit": 20})
    plt_best = sol_best.gantt("tab20")
    plt_best.savefig("gantt_best_neighbor_ls.png")
    print(f"Gantt chart for BestNeighborLocalSearch saved to gantt_best_neighbor_ls.png")

    # Important: plt.show() might be needed to display the plots if not saving
    # plt.show()