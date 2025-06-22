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
        solution.reset() # Ensure a clean slate for scheduling

        unassigned_operations = list(instance.operations)
        
        while unassigned_operations:
            best_operation = None
            best_machine = None
            earliest_finish_time = float('inf')
            
            # Find all currently ready operations
            ready_operations = [op for op in unassigned_operations if op.is_ready(0)]

            if not ready_operations:
                # If no operations are ready but unassigned_operations is not empty,
                # it means there's a deadlock or unresolvable precedence.
                # In a greedy context, we might stop or force assign if this were allowed.
                # For this TP, we assume valid instances. If we reach here, it implies no further
                # operations can be scheduled respecting current precedences.
                # The solution will be infeasible due to unassigned operations.
                break 

            # Iterate through all ready operations and their possible machine assignments
            for op in ready_operations:
                # Iterate through all variants (machine, processing_time, energy) for the operation
                for machine_id, processing_time, energy in op._variants:
                    machine = instance.get_machine(machine_id)
                    
                    # Calculate potential start time on this machine, considering machine availability
                    # and operation's precedence constraints
                    
                    # Minimum start time based on operation predecessors
                    min_start_time_predecessors = op.min_start_time
                    
                    # Machine's current availability time
                    machine_available_time = machine.available_time
                    
                    # If machine is OFF, consider set-up time from its last available time
                    # This logic for machine.available_time already takes set_up into account
                    # for the *first* operation if the machine is OFF.
                    # For subsequent operations, machine.available_time is simply the end of the last op.
                    
                    # Determine the actual earliest start time for this operation on this machine
                    potential_start_time = max(min_start_time_predecessors, machine_available_time)
                    
                    potential_finish_time = potential_start_time + processing_time
                    
                    # Check if this potential assignment leads to an earlier finish time
                    if potential_finish_time < earliest_finish_time:
                        earliest_finish_time = potential_finish_time
                        best_operation = op
                        best_machine = machine

            if best_operation and best_machine:
                # Schedule the chosen operation
                solution.schedule(best_operation, best_machine)
                unassigned_operations.remove(best_operation)
            else:
                # Should not happen if ready_operations is not empty and instance is valid,
                # but a safeguard for potential issues (e.g., no valid variant fits).
                break 

        solution.recompute() # Recalculate metrics and feasibility
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
        super().__init__() # Call parent constructor, though Heuristic's raises error. We override this.
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
        solution.reset() # Ensure a clean slate for scheduling

        unassigned_operations = list(instance.operations)
        
        while unassigned_operations:
            ready_operations = [op for op in unassigned_operations if op.is_ready(0)]

            if not ready_operations:
                # No operations can be scheduled, break the loop. Solution will be infeasible if operations remain.
                break 

            # Randomly pick one ready operation
            chosen_op: Operation = random.choice(ready_operations)
            
            # Get available machines for this operation
            # _variants is a list of (machine_id, processing_time, energy) tuples
            possible_machines_data = chosen_op._variants
            
            if not possible_machines_data:
                # This operation has no valid machine variants, skip it (or signal error)
                unassigned_operations.remove(chosen_op) # Remove to avoid infinite loop
                continue 

            # Randomly pick a machine variant
            chosen_machine_data = random.choice(possible_machines_data)
            chosen_machine_id = chosen_machine_data[0]
            chosen_machine = instance.get_machine(chosen_machine_id)
            
            # Schedule the chosen operation on the chosen machine at the earliest possible time
            # The .schedule method of solution takes care of max(machine_available_time, op.min_start_time)
            # and updates machine state.
            try:
                solution.schedule(chosen_op, chosen_machine)
                unassigned_operations.remove(chosen_op)
            except ValueError:
                # If scheduling fails (e.g., machine.add_operation raises error), 
                # this specific assignment isn't possible.
                # In a simple non-deterministic, we might just try another loop iteration.
                # For robustness, we could mark this op/machine pair as invalid for this step,
                # or remove it from possible choices for this operation, but for a basic heuristic,
                # letting the loop continue and potentially picking another op/machine is fine.
                # However, if it loops infinitely on an unassignable op, we need a mechanism.
                # For this problem, `solution.schedule` will handle the actual scheduling details
                # and internal consistency checks. The main goal here is random selection.
                # If an operation truly can't be scheduled after many tries, it might indicate
                # an issue with the instance or the operation itself (e.g., no valid variant leads to a feasible schedule).
                pass # Try another random choice in the next iteration

        solution.recompute() # Recalculate metrics and feasibility
        return solution


if __name__ == "__main__":
    # Example of playing with the heuristics
    from src.scheduling.tests.test_utils import TEST_FOLDER_DATA
    import os
    inst = Instance.from_file(TEST_FOLDER_DATA + os.path.sep + "jsp1")
    heur = NonDeterminist()
    sol = heur.run(inst)
    plt = sol.gantt("tab20")
    plt.savefig("gantt.png")
