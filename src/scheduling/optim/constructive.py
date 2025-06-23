'''
Constructive heuristics that returns preferably **feasible** solutions.

@author: Vassilissa Lehoux
'''
from typing import Dict
import random

from src.scheduling.instance.instance import Instance
from src.scheduling.solution import Solution
from src.scheduling.optim.heuristics import Heuristic
from src.scheduling.instance.operation import Operation


class Greedy(Heuristic):
    '''
    A deterministic greedy method to return a solution.
    '''

    def __init__(self, params: Dict = dict()):
        '''
        Constructor
        @param params: The parameters of your heuristic method if any as a
                       dictionary. Implementation should provide default values in the function.
        '''
        super().__init__() # Call parent constructor, though Heuristic's raises error. We override this.

    def run(self, instance: Instance, params: Dict = dict()) -> Solution:
        '''
        Computes a solution for the given instance.
        Implementation should provide default values in the function
        (the function will be evaluated with an empty dictionary).

        @param instance: the instance to solve
        @param params: the parameters for the run
        '''
        solution = Solution(instance)
        solution.reset() # On part "proprement"

        unassigned_operations = list(instance.operations)
        
        while unassigned_operations:
            best_operation = None
            best_machine = None
            earliest_finish_time = float('inf')
            
            ready_operations = [op for op in unassigned_operations if op.is_ready(0)]

            if not ready_operations:
                # Si aucune opération n'est prête, mais que unassigned_operations n'est pas vide, cela signifie qu'il y a un blocage .
                break 

            for op in ready_operations:
                # On parcourts toutes les variantes (machine, temps de traitement, énergie) pour l'opération
                for machine_id, processing_time, energy in op._variants:
                    machine = instance.get_machine(machine_id)

                    min_start_time_predecessors = op.min_start_time
                    machine_available_time = machine.available_time
                    
                    # Détermine l'heure de débtu réelle la plus ancienne pour cette opération sur cette machine
                    potential_start_time = max(min_start_time_predecessors, machine_available_time)
                    
                    potential_finish_time = potential_start_time + processing_time
                    
                    # On vérifie si cette opération amène à une heure de fin plus tôt
                    if potential_finish_time < earliest_finish_time:
                        earliest_finish_time = potential_finish_time
                        best_operation = op
                        best_machine = machine

            if best_operation and best_machine:
                solution.schedule(best_operation, best_machine)
                unassigned_operations.remove(best_operation)
            else:
                # Normalement, on ne devrait pas rentrer là dedans
                break 

        solution.recompute() # Recalcule
        return solution


class NonDeterminist(Heuristic):
    '''
    Heuristic that returns different values for different runs with the same parameters
    (or different values for different seeds and otherwise same parameters)
    '''

    def __init__(self, params: Dict = dict()):
        '''
        Constructor
        @param params: The parameters of your heuristic method if any as a
                       dictionary. Implementation should provide default values in the function.
        '''
        super().__init__() 
        self.seed = params.get("seed", None)
        if self.seed is not None:
            random.seed(self.seed)

    def run(self, instance: Instance, params: Dict = dict()) -> Solution:
        '''
        Computes a solution for the given instance.
        Implementation should provide default values in the function
        (the function will be evaluated with an empty dictionary).

        @param instance: the instance to solve
        @param params: the parameters for the run
        '''
        solution = Solution(instance)
        solution.reset()

        unassigned_operations = list(instance.operations)
        
        while unassigned_operations:
            ready_operations = [op for op in unassigned_operations if op.is_ready(0)]

            if not ready_operations:
                # S'il n'y a pas d'opération, on sort de la boucle
                break 

            # choix aléatoire de l'opération
            chosen_op: Operation = random.choice(ready_operations)
            
            possible_machines_data = chosen_op._variants
            
            if not possible_machines_data:
                unassigned_operations.remove(chosen_op) # Evite les boucles infinies
                continue 

            # Choisit aléatoirement une machine
            chosen_machine_data = random.choice(possible_machines_data)
            chosen_machine_id = chosen_machine_data[0]
            chosen_machine = instance.get_machine(chosen_machine_id)
            
            # On lance l'opération sur la machine au temps le plus tôt possible
            try:
                solution.schedule(chosen_op, chosen_machine)
                unassigned_operations.remove(chosen_op)
            except ValueError:
                pass

        solution.recompute() 
        return solution


if __name__ == "__main__":
    # Exemple
    from src.scheduling.tests.test_utils import TEST_FOLDER_DATA
    import os
    inst = Instance.from_file(TEST_FOLDER_DATA + os.path.sep + "jsp1")
    heur = NonDeterminist()
    sol = heur.run(inst)
    plt = sol.gantt("tab20")
    plt.savefig("gantt.png")
