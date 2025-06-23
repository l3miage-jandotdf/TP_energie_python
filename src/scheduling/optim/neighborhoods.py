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
            if not op.assigned: # On ne prend que les opérations pas déjà assignées
                continue

            current_assigned_machine_id = op.assigned_to
            
            # Parcourir toutes les machines variantes possibles pour cette opération
            # Une variante, c'est une combinaison de (machine_id, processing_time, energy)
            for new_machine_id, _, _ in op._variants: 
                if new_machine_id == current_assigned_machine_id:
                    continue 

                new_sol = sol.deepcopy()
                
                # Récupère les objets d'opération et de machine dans la nouvelle copie de solution
                op_in_new_sol = new_sol.inst.get_operation(op.operation_id)
                current_machine_in_new_sol = new_sol.inst.get_machine(current_assigned_machine_id)
                new_machine_in_new_sol = new_sol.inst.get_machine(new_machine_id)

                op_in_new_sol.reset() # Reset le _schedule_info

                # Maintenant, on essaie de programmer sur la nouvelle machine
                try:
                    new_sol.schedule(op_in_new_sol, new_machine_in_new_sol)

                    # Après avoir tenté de planifier, on recalcule les métriques de la nouvelle solution
                    new_sol.recompute()
                    yield new_sol 
                except ValueError:
                    pass

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
            # On obtient les opérations actuellement planifiées sur cette machine, triées par heure de début
            scheduled_ops_on_machine = sorted(
                [op for op in sol.all_operations if op.assigned and op.assigned_to == machine.machine_id], 
                key=lambda op: op.start_time
            )

            num_ops = len(scheduled_ops_on_machine)
            if num_ops < 2:
                continue 

            # On parcourt toutes les paires uniques d'opérations sur cette machine
            for i in range(num_ops):
                for j in range(i + 1, num_ops):
                    op1_original = scheduled_ops_on_machine[i]
                    op2_original = scheduled_ops_on_machine[j]

                    new_sol = sol.deepcopy()
                    
                    # On obtietn les opérations et la machine correspondantes dans la nouvelle copie de solution
                    machine_in_new_sol = new_sol.inst.get_machine(machine.machine_id)
                    op1_in_new_sol = new_sol.inst.get_operation(op1_original.operation_id)
                    op2_in_new_sol = new_sol.inst.get_operation(op2_original.operation_id)
                    
                    # Réinitialise le calendrier de la machine et les opérations pertinentes dans la nouvelle copie de la solution
                    machine_in_new_sol.reset() 
                    for op_on_mach in scheduled_ops_on_machine:
                         new_sol.inst.get_operation(op_on_mach.operation_id).reset()

                    # On crée la nouvelle séquence d'opérations pour cette machine
                    new_sequence = list(scheduled_ops_on_machine) 
                    new_sequence[i], new_sequence[j] = new_sequence[j], new_sequence[i]

                    # Reprogramme les opérations sur cette machine dans le nouvel ordre
                    replan_success = True
                    for op_to_replan_original in new_sequence:
                        op_to_replan_in_new_sol = new_sol.inst.get_operation(op_to_replan_original.operation_id)
                        try:
                            new_sol.schedule(op_to_replan_in_new_sol, machine_in_new_sol)
                        except ValueError:
                            replan_success = False
                            break
                    
                    if replan_success:
                        new_sol.recompute()
                        yield new_sol
                        
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