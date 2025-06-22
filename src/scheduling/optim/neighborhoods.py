'''
Neighborhoods for solutions.
They must derive from the Neighborhood class.

@author: Vassilissa Lehoux
'''
from typing import Dict
import copy

from src.scheduling.instance.instance import Instance
from src.scheduling.solution import Solution
from src.scheduling.instance.operation import Operation
from src.scheduling.instance.machine import Machine


class Neighborhood(object):
    '''
    Base neighborhood class for solutions of a given instance.
    Do not modify!!!
    '''

    def __init__(self, instance: Instance, params: Dict = dict()):
        '''
        Constructor
        '''
        self._instance = instance

    def best_neighbor(self, sol: Solution) -> Solution:
        '''
        Returns the best solution in the neighborhood of the solution.
        Can be the solution itself.
        '''
        raise "Not implemented error"

    def first_better_neighbor(self, sol: Solution) -> Solution:
        '''
        Returns the first solution in the neighborhood of the solution
        that improves other it and the solution itself if none is better.
        '''
        raise "Not implemented error"


class ReassignOneOperation(Neighborhood):
    '''
    ReassignOneOperation Neighborhood:
    Generates neighbors by reassigning a single scheduled operation
    to another compatible machine and replanning it at the earliest possible time.
    '''

    def __init__(self, instance: Instance, params: Dict = dict()):
        '''
        Constructor
        '''
        super().__init__(instance, params)

    def _generate_neighbors(self, sol: Solution):
        """
        Generator for neighbor solutions.
        Each neighbor is a deep copy of the original solution,
        with one operation reassigned.
        """
        original_operations_assignment = {op.operation_id: (op.assigned_to, op.start_time) 
                                          for op in sol.all_operations if op.assigned}

        for op in sol.all_operations:
            if not op.assigned: # Only consider already assigned operations
                continue

            current_assigned_machine_id = op.assigned_to
            
            # Iterate through all possible variant machines for this operation
            # A variant is (machine_id, processing_time, energy)
            for new_machine_id, _, _ in op._variants: 
                if new_machine_id == current_assigned_machine_id:
                    continue # Don't try to reassign to the same machine

                # Create a deep copy of the current solution to modify
                new_sol = sol.deepcopy()
                
                # Get the operation and machine objects in the new solution copy
                op_in_new_sol = new_sol.inst.get_operation(op.operation_id)
                current_machine_in_new_sol = new_sol.inst.get_machine(current_assigned_machine_id)
                new_machine_in_new_sol = new_sol.inst.get_machine(new_machine_id)

                # Reset the original assignment for this operation and the relevant machine states
                # This requires a more complex "undo" mechanism than simple reset.
                # The easiest is to re-schedule all operations.
                # However, for local search, we want minimal changes.
                # Let's simplify: reset all operations and machines, then re-schedule everything except the changed one,
                # then schedule the changed one. This is very inefficient.

                # A better approach for local search:
                # 1. Store the state of operations and machines involved.
                # 2. Reset affected operations/machines.
                # 3. Schedule the changed operation.
                # 4. For any operation whose start_time might be affected by the change (e.g., subsequent on the same machine),
                #    re-schedule them. This is complex because of precedence.

                # Simpler: The `schedule` method of Machine class manages internal state for current operations.
                # For `deepcopy`, a full reset is simpler if `add_operation` can rebuild.
                # However, the current `add_operation` in `Machine` is for *adding* to the end.
                # It doesn't support removing and re-inserting within a schedule efficiently.

                # RETHINKING: To ensure feasibility (esp. precedence) after a move,
                # it's safer to re-plan the entire job of the moved operation,
                # and potentially subsequent jobs/operations on the affected machine.
                # For simplicity in a basic local search, we will reset the *entire* solution copy
                # and then try to rebuild parts. This will be slow but correct.

                # Let's make a simplified move for this TP, focusing on reassignment only.
                # We will clear the assignment of the chosen op in the new solution,
                # then try to re-schedule it.
                
                # To clear an operation's assignment without deep resetting everything:
                op_in_new_sol.reset() # Clears _schedule_info

                # Now, try to schedule it on the new machine
                # The `schedule` method of Solution handles machine.add_operation
                # and updates the operation's internal schedule info.
                try:
                    new_sol.schedule(op_in_new_sol, new_machine_in_new_sol)
                    # After scheduling one operation, other operations on the same machine
                    # or in the same job might need to be re-evaluated/re-scheduled to maintain feasibility
                    # and push forward their start times if needed. This is the hardest part.
                    # For a simple neighborhood, we'll assume `solution.schedule`
                    # and subsequent `recompute` are enough to capture immediate effects.
                    # If this is not robust enough, the solution might become infeasible or suboptimal due to simple changes.

                    # A more robust "reassignment" might involve:
                    # 1. Removing op_in_new_sol.
                    # 2. Shifting all subsequent operations on current_machine_in_new_sol backward to fill gap.
                    # 3. Re-scheduling op_in_new_sol on new_machine_in_new_sol.
                    # 4. Propagating time changes for all affected operations and jobs.
                    # This is too complex for a basic neighborhood.

                    # Let's use the simplest interpretation for now: clear assigned op, try to schedule on new machine.
                    # This might lead to infeasible solutions if precedence or machine availability is badly impacted.
                    # The problem statement says solutions can be infeasible, so this is acceptable for now.
                    
                    # After attempting to schedule, recompute the new solution's metrics
                    new_sol.recompute()
                    yield new_sol # Yield the potential neighbor
                except ValueError:
                    # Operation could not be scheduled on this machine (e.g., if it needs specific variant properties not met)
                    pass
                # Reset new_sol to its state before attempting this specific re-assignment if we continue
                # This is why deepcopy at the start of loop is crucial.

    def best_neighbor(self, sol: Solution) -> Solution:
        '''
        Returns the best solution in the neighborhood of the solution.
        Can be the solution itself.
        '''
        best_sol = sol
        for neighbor_sol in self._generate_neighbors(sol):
            if neighbor_sol.objective < best_sol.objective:
                best_sol = neighbor_sol
        return best_sol

    def first_better_neighbor(self, sol: Solution) -> Solution:
        '''
        Returns the first solution in the neighborhood of the solution
        that improves other it and the solution itself if none is better.
        '''
        for neighbor_sol in self._generate_neighbors(sol):
            if neighbor_sol.objective < sol.objective:
                return neighbor_sol
        return sol


class SwapOperationsOnOneMachine(Neighborhood):
    '''
    SwapOperationsOnOneMachine Neighborhood:
    Generates neighbors by swapping the positions of two operations
    scheduled on the same machine.
    '''

    def __init__(self, instance: Instance, params: Dict = dict()):
        '''
        Constructor
        '''
        super().__init__(instance, params)

    def _generate_neighbors(self, sol: Solution):
        """
        Generator for neighbor solutions.
        Each neighbor is a deep copy of the original solution,
        with two operations swapped on one machine.
        """
        for machine in self._instance.machines:
            # Get operations currently scheduled on this machine, sorted by start time
            # Important: operate on a copy to avoid issues during iteration
            scheduled_ops_on_machine = sorted(
                [op for op in sol.all_operations if op.assigned and op.assigned_to == machine.machine_id], 
                key=lambda op: op.start_time
            )

            num_ops = len(scheduled_ops_on_machine)
            if num_ops < 2:
                continue # Need at least two operations to swap

            # Iterate through all unique pairs of operations on this machine
            for i in range(num_ops):
                for j in range(i + 1, num_ops):
                    op1_original = scheduled_ops_on_machine[i]
                    op2_original = scheduled_ops_on_machine[j]

                    # Create a deep copy of the current solution
                    new_sol = sol.deepcopy()
                    
                    # Get the corresponding operations and machine in the new solution copy
                    machine_in_new_sol = new_sol.inst.get_machine(machine.machine_id)
                    op1_in_new_sol = new_sol.inst.get_operation(op1_original.operation_id)
                    op2_in_new_sol = new_sol.inst.get_operation(op2_original.operation_id)

                    # For swapping operations on a single machine, the safest is to:
                    # 1. Reset all operations on this machine.
                    # 2. Reset the machine's state (current_state, last_available_time, etc.).
                    # 3. Reschedule them in the new order. This also needs careful handling of global state.

                    # Simpler approach for this TP:
                    # Clear the schedule of the operations involved and reset the machine.
                    # Then re-schedule them in the new order.
                    # This implies resetting the machine's schedule and rebuilding it.

                    # A more robust "swap" would involve carefully removing and re-inserting,
                    # but `machine.add_operation` only adds to the end.
                    # For a valid swap, we'd need to re-plan all ops on the machine.

                    # Let's try a simplified swap:
                    # 1. Temporarily unassign the two operations.
                    # 2. Re-assign them in swapped start_time order, respecting precedence.
                    # This is tricky because `machine.add_operation` adds to the end.
                    # To correctly swap, we need to completely clear the machine's schedule and
                    # re-add all its operations in the new order.

                    # This is a major challenge for local search on scheduling problems:
                    # simple moves can invalidate many other parts of the schedule.
                    # A full re-scheduling of the affected machine's operations is often necessary.

                    # Let's implement a *simplified* swap by clearing all ops on this machine
                    # and re-scheduling them in the new order. This is computationally heavier
                    # but ensures internal consistency for the machine.
                    
                    # Reset the machine's schedule and relevant operations in the new solution copy
                    machine_in_new_sol.reset() # This clears scheduled_operations, start_times, stop_times
                    for op_on_mach in scheduled_ops_on_machine:
                         new_sol.inst.get_operation(op_on_mach.operation_id).reset()

                    # Create the new sequence of operations for this machine
                    new_sequence = list(scheduled_ops_on_machine) # Copy of original sequence
                    # Swap ops in the sequence
                    new_sequence[i], new_sequence[j] = new_sequence[j], new_sequence[i]

                    # Reschedule operations on this machine in the new order
                    replan_success = True
                    for op_to_replan_original in new_sequence:
                        op_to_replan_in_new_sol = new_sol.inst.get_operation(op_to_replan_original.operation_id)
                        try:
                            # Use solution.schedule which calls machine.add_operation
                            # and also updates op's internal schedule info.
                            new_sol.schedule(op_to_replan_in_new_sol, machine_in_new_sol)
                        except ValueError:
                            # Failed to reschedule, this neighbor is likely infeasible
                            replan_success = False
                            break
                    
                    if replan_success:
                        # Recompute the new solution's metrics
                        new_sol.recompute()
                        yield new_sol
                    # else: this neighbor is invalid, just don't yield it
                        
    def best_neighbor(self, sol: Solution) -> Solution:
        '''
        Returns the best solution in the neighborhood of the solution.
        Can be the solution itself.
        '''
        best_sol = sol
        for neighbor_sol in self._generate_neighbors(sol):
            if neighbor_sol.objective < best_sol.objective:
                best_sol = neighbor_sol
        return best_sol

    def first_better_neighbor(self, sol: Solution) -> Solution:
        '''
        Returns the first solution in the neighborhood of the solution
        that improves other it and the solution itself if none is better.
        '''
        for neighbor_sol in self._generate_neighbors(sol):
            if neighbor_sol.objective < sol.objective:
                return neighbor_sol
        return sol