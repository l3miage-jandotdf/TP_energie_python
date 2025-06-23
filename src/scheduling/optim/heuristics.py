'''
Mother class for heuristics.

@author: Vassilissa Lehoux
'''
from typing import Dict, List
from abc import ABC, abstractmethod
import random

from src.scheduling.instance.instance import Instance
from src.scheduling.solution import Solution
from src.scheduling.instance.operation import Operation
from src.scheduling.instance.machine import Machine


class Heuristic(ABC):
    '''
    Abstract base class for scheduling heuristics
    '''

    def __init__(self, params: Dict = None):
        '''
        Constructor
        @param params: The parameters of your heuristic method if any as a
               dictionary. Implementation should provide default values in the function.
        '''
        self.params = params if params is not None else {}
        self._setup_default_params()

    def _setup_default_params(self):
        '''
        Setup default parameters for the heuristic.
        Should be overridden by subclasses to define their specific parameters.
        '''
        pass

    @abstractmethod
    def run(self, instance: Instance, params: Dict = None) -> Solution:
        '''
        Computes a solution for the given instance.
        Implementation should provide default values in the function
        (the function will be evaluated with an empty dictionary).
        @param instance: the instance to solve
        @param params: the parameters for the run
        '''
        pass

    def _merge_params(self, run_params: Dict = None) -> Dict:
        '''
        Merge instance parameters with run-time parameters
        @param run_params: parameters provided at run time
        @return: merged parameters dictionary
        '''
        merged = self.params.copy()
        if run_params:
            merged.update(run_params)
        return merged


class FirstComeFirstServedHeuristic(Heuristic):
    '''
    First Come First Served heuristic - schedules operations in the order they appear
    '''

    def _setup_default_params(self):
        '''
        Setup default parameters for FCFS heuristic
        '''
        self.params.setdefault('machine_selection', 'first_available')  # 'first_available', 'fastest', 'least_energy'

    def run(self, instance: Instance, params: Dict = None) -> Solution:
        '''
        Run the FCFS heuristic
        '''
        merged_params = self._merge_params(params)
        solution = Solution(instance)
        
        # Jusqu'à ce que toutes les opérations soient faites
        while solution.available_operations:
            available_ops = solution.available_operations
            
            operation = available_ops[0]
            
            machine = self._select_machine(operation, instance, merged_params['machine_selection'])
            
            success = solution.schedule(operation, machine)
            
            if not success:
                # On essaie la prochaine machine
                for machine in instance.machines:
                    if solution.schedule(operation, machine):
                        break
        
        return solution

    def _select_machine(self, operation: Operation, instance: Instance, strategy: str) -> Machine:
        '''
        Select a machine for the operation based on the given strategy
        '''
        # Toutes les machines capables de faire l'opération
        available_machines = self._get_available_machines(operation, instance)
        
        if not available_machines:
            return instance.machines[0]  # Fallback
        
        if strategy == 'first_available':
            return available_machines[0]
        elif strategy == 'fastest':
            return min(available_machines, 
                      key=lambda m: self._get_processing_time(operation, m))
        elif strategy == 'least_energy':
            return min(available_machines, 
                      key=lambda m: self._get_energy_consumption(operation, m))
        else:
            return available_machines[0]

    def _get_available_machines(self, operation: Operation, instance: Instance) -> List[Machine]:
        '''
        Get machines that can process this operation
        '''
        machine_options = operation.get_machine_options()
        available_machines = []
        for machine_id in machine_options.keys():
            machine = instance.get_machine(machine_id)
            if machine:
                available_machines.append(machine)
        return available_machines

    def _get_processing_time(self, operation: Operation, machine: Machine) -> int:
        '''
        Get processing time for operation on machine
        '''
        machine_options = operation.get_machine_options()
        if machine.machine_id in machine_options:
            return machine_options[machine.machine_id][0]  # duration
        return float('inf')

    def _get_energy_consumption(self, operation: Operation, machine: Machine) -> int:
        '''
        Get energy consumption for operation on machine
        '''
        machine_options = operation.get_machine_options()
        if machine.machine_id in machine_options:
            return machine_options[machine.machine_id][1]  # energy
        return float('inf')


class ShortestProcessingTimeHeuristic(Heuristic):
    '''
    Shortest Processing Time heuristic - prioritizes operations with shorter processing times
    '''

    def _setup_default_params(self):
        '''
        Setup default parameters for SPT heuristic
        '''
        self.params.setdefault('machine_selection', 'fastest')

    def run(self, instance: Instance, params: Dict = None) -> Solution:
        '''
        Run the SPT heuristic
        '''
        merged_params = self._merge_params(params)
        solution = Solution(instance)
        
        while solution.available_operations:
            available_ops = solution.available_operations
            
            # On trie par les opérations qui prennent le moins de temps
            sorted_ops = sorted(available_ops, 
                              key=lambda op: self._get_min_processing_time(op, instance))
            
            # La plus courte
            operation = sorted_ops[0]
            
            machine = self._select_machine(operation, instance, merged_params['machine_selection'])
            
            success = solution.schedule(operation, machine)
            
            if not success:
                available_machines = self._get_available_machines(operation, instance)
                for machine in available_machines:
                    if solution.schedule(operation, machine):
                        break
        
        return solution

    def _get_min_processing_time(self, operation: Operation, instance: Instance) -> int:
        '''
        Get minimum processing time for operation across all machines
        '''
        machine_options = operation.get_machine_options()
        if not machine_options:
            return float('inf')
        return min(duration for duration, _ in machine_options.values())

    def _select_machine(self, operation: Operation, instance: Instance, strategy: str) -> Machine:
        '''
        Select a machine for the operation based on the given strategy
        '''
        available_machines = self._get_available_machines(operation, instance)
        
        if not available_machines:
            return instance.machines[0]  # Fallback
        
        if strategy == 'fastest':
            return min(available_machines, 
                      key=lambda m: self._get_processing_time(operation, m))
        elif strategy == 'least_energy':
            return min(available_machines, 
                      key=lambda m: self._get_energy_consumption(operation, m))
        elif strategy == 'earliest_available':
            return min(available_machines, key=lambda m: m.available_time)
        else:
            return available_machines[0]

    def _get_available_machines(self, operation: Operation, instance: Instance) -> List[Machine]:
        '''
        Get machines that can process this operation
        '''
        machine_options = operation.get_machine_options()
        available_machines = []
        for machine_id in machine_options.keys():
            machine = instance.get_machine(machine_id)
            if machine:
                available_machines.append(machine)
        return available_machines

    def _get_processing_time(self, operation: Operation, machine: Machine) -> int:
        '''
        Get processing time for operation on machine
        '''
        machine_options = operation.get_machine_options()
        if machine.machine_id in machine_options:
            return machine_options[machine.machine_id][0]  # durée
        return float('inf')

    def _get_energy_consumption(self, operation: Operation, machine: Machine) -> int:
        '''
        Get energy consumption for operation on machine
        '''
        machine_options = operation.get_machine_options()
        if machine.machine_id in machine_options:
            return machine_options[machine.machine_id][1]  # énergie
        return float('inf')


class LongestProcessingTimeHeuristic(Heuristic):
    '''
    Longest Processing Time heuristic - prioritizes operations with longer processing times
    '''

    def _setup_default_params(self):
        '''
        Setup default parameters for LPT heuristic
        '''
        self.params.setdefault('machine_selection', 'fastest')

    def run(self, instance: Instance, params: Dict = None) -> Solution:
        '''
        Run the LPT heuristic
        '''
        merged_params = self._merge_params(params)
        solution = Solution(instance)
        
        while solution.available_operations:
            available_ops = solution.available_operations
            
            # Même principe que pour l'autre fonction run, mais avec le temps le plus long
            sorted_ops = sorted(available_ops, 
                              key=lambda op: self._get_max_processing_time(op, instance),
                              reverse=True)
            
            operation = sorted_ops[0]
            
            machine = self._select_machine(operation, instance, merged_params['machine_selection'])
            
            success = solution.schedule(operation, machine)
            
            if not success:
                available_machines = self._get_available_machines(operation, instance)
                for machine in available_machines:
                    if solution.schedule(operation, machine):
                        break
        
        return solution

    def _get_max_processing_time(self, operation: Operation, instance: Instance) -> int:
        '''
        Get maximum processing time for operation across all machines
        '''
        machine_options = operation.get_machine_options()
        if not machine_options:
            return 0
        return max(duration for duration, _ in machine_options.values())

    def _select_machine(self, operation: Operation, instance: Instance, strategy: str) -> Machine:
        '''
        Select a machine for the operation based on the given strategy
        '''
        available_machines = self._get_available_machines(operation, instance)
        
        if not available_machines:
            return instance.machines[0]  # Fallback
        
        if strategy == 'fastest':
            return min(available_machines, 
                      key=lambda m: self._get_processing_time(operation, m))
        elif strategy == 'least_energy':
            return min(available_machines, 
                      key=lambda m: self._get_energy_consumption(operation, m))
        elif strategy == 'earliest_available':
            return min(available_machines, key=lambda m: m.available_time)
        else:
            return available_machines[0]

    def _get_available_machines(self, operation: Operation, instance: Instance) -> List[Machine]:
        '''
        Get machines that can process this operation
        '''
        machine_options = operation.get_machine_options()
        available_machines = []
        for machine_id in machine_options.keys():
            machine = instance.get_machine(machine_id)
            if machine:
                available_machines.append(machine)
        return available_machines

    def _get_processing_time(self, operation: Operation, machine: Machine) -> int:
        '''
        Get processing time for operation on machine
        '''
        machine_options = operation.get_machine_options()
        if machine.machine_id in machine_options:
            return machine_options[machine.machine_id][0]  # duration
        return float('inf')

    def _get_energy_consumption(self, operation: Operation, machine: Machine) -> int:
        '''
        Get energy consumption for operation on machine
        '''
        machine_options = operation.get_machine_options()
        if machine.machine_id in machine_options:
            return machine_options[machine.machine_id][1]  # energy
        return float('inf')


class RandomHeuristic(Heuristic):
    '''
    Random heuristic - makes random choices for scheduling
    '''

    def _setup_default_params(self):
        '''
        Setup default parameters for Random heuristic
        '''
        self.params.setdefault('seed', None)

    def run(self, instance: Instance, params: Dict = None) -> Solution:
        '''
        Run the Random heuristic
        '''
        merged_params = self._merge_params(params)
        solution = Solution(instance)
        
        # Aléatoire
        if merged_params['seed'] is not None:
            random.seed(merged_params['seed'])
        
        while solution.available_operations:
            available_ops = solution.available_operations
            
            operation = random.choice(available_ops)
            
            available_machines = self._get_available_machines(operation, instance)
            
            if available_machines:
                machine = random.choice(available_machines)
                
                success = solution.schedule(operation, machine)
                
                if not success:
                    machines = available_machines.copy()
                    random.shuffle(machines)
                    for machine in machines:
                        if solution.schedule(operation, machine):
                            break
        
        return solution

    def _get_available_machines(self, operation: Operation, instance: Instance) -> List[Machine]:
        '''
        Get machines that can process this operation
        '''
        machine_options = operation.get_machine_options()
        available_machines = []
        for machine_id in machine_options.keys():
            machine = instance.get_machine(machine_id)
            if machine:
                available_machines.append(machine)
        return available_machines


class EnergyAwareHeuristic(Heuristic):
    '''
    Energy-aware heuristic - prioritizes operations and machines to minimize energy consumption
    '''

    def _setup_default_params(self):
        '''
        Setup default parameters for Energy-aware heuristic
        '''
        self.params.setdefault('energy_weight', 0.7)
        self.params.setdefault('time_weight', 0.3)

    def run(self, instance: Instance, params: Dict = None) -> Solution:
        '''
        Run the Energy-aware heuristic
        '''
        merged_params = self._merge_params(params)
        solution = Solution(instance)
        
        energy_weight = merged_params['energy_weight']
        time_weight = merged_params['time_weight']
        
        while solution.available_operations:
            available_ops = solution.available_operations
            
            # Evalue les combinaisons entre machines et opérations
            best_operation = None
            best_machine = None
            best_score = float('inf')
            
            for operation in available_ops:
                available_machines = self._get_available_machines(operation, instance)
                
                for machine in available_machines:
                    # Calcule les scores (énergie + temps)
                    energy_cost = self._get_energy_consumption(operation, machine)
                    time_cost = self._get_processing_time(operation, machine)
                    
                    score = energy_weight * energy_cost + time_weight * time_cost
                    
                    if score < best_score:
                        best_score = score
                        best_operation = operation
                        best_machine = machine
            
            # Meilleure solution
            if best_operation and best_machine:
                success = solution.schedule(best_operation, best_machine)
                
                if not success:
                    available_machines = self._get_available_machines(best_operation, instance)
                    for machine in available_machines:
                        if solution.schedule(best_operation, machine):
                            break
        
        return solution

    def _get_available_machines(self, operation: Operation, instance: Instance) -> List[Machine]:
        '''
        Get machines that can process this operation
        '''
        machine_options = operation.get_machine_options()
        available_machines = []
        for machine_id in machine_options.keys():
            machine = instance.get_machine(machine_id)
            if machine:
                available_machines.append(machine)
        return available_machines

    def _get_processing_time(self, operation: Operation, machine: Machine) -> int:
        '''
        Get processing time for operation on machine
        '''
        machine_options = operation.get_machine_options()
        if machine.machine_id in machine_options:
            return machine_options[machine.machine_id][0]  # duration
        return float('inf')

    def _get_energy_consumption(self, operation: Operation, machine: Machine) -> int:
        '''
        Get energy consumption for operation on machine
        '''
        machine_options = operation.get_machine_options()
        if machine.machine_id in machine_options:
            return machine_options[machine.machine_id][1]  # energy
        return float('inf')


class EarliestDueDateHeuristic(Heuristic):
    '''
    Earliest Due Date heuristic - prioritizes jobs with earliest due dates
    Note: This assumes jobs have due dates, which may need to be added to the Job class
    '''

    def _setup_default_params(self):
        '''
        Setup default parameters for EDD heuristic
        '''
        self.params.setdefault('machine_selection', 'fastest')

    def run(self, instance: Instance, params: Dict = None) -> Solution:
        '''
        Run the EDD heuristic
        '''
        merged_params = self._merge_params(params)
        solution = Solution(instance)
        
        while solution.available_operations:
            available_ops = solution.available_operations
            
            # Trie par les priorités de job
            sorted_ops = sorted(available_ops, key=lambda op: op.job_id)
            
            operation = sorted_ops[0]
            
            machine = self._select_machine(operation, instance, merged_params['machine_selection'])
            
            success = solution.schedule(operation, machine)
            
            if not success:
                available_machines = self._get_available_machines(operation, instance)
                for machine in available_machines:
                    if solution.schedule(operation, machine):
                        break
        
        return solution

    def _select_machine(self, operation: Operation, instance: Instance, strategy: str) -> Machine:
        '''
        Select a machine for the operation based on the given strategy
        '''
        available_machines = self._get_available_machines(operation, instance)
        
        if not available_machines:
            return instance.machines[0]  # Fallback
        
        if strategy == 'fastest':
            return min(available_machines, 
                      key=lambda m: self._get_processing_time(operation, m))
        elif strategy == 'least_energy':
            return min(available_machines, 
                      key=lambda m: self._get_energy_consumption(operation, m))
        elif strategy == 'earliest_available':
            return min(available_machines, key=lambda m: m.available_time)
        else:
            return available_machines[0]

    def _get_available_machines(self, operation: Operation, instance: Instance) -> List[Machine]:
        '''
        Get machines that can process this operation
        '''
        machine_options = operation.get_machine_options()
        available_machines = []
        for machine_id in machine_options.keys():
            machine = instance.get_machine(machine_id)
            if machine:
                available_machines.append(machine)
        return available_machines

    def _get_processing_time(self, operation: Operation, machine: Machine) -> int:
        '''
        Get processing time for operation on machine
        '''
        machine_options = operation.get_machine_options()
        if machine.machine_id in machine_options:
            return machine_options[machine.machine_id][0]  # duration
        return float('inf')

    def _get_energy_consumption(self, operation: Operation, machine: Machine) -> int:
        '''
        Get energy consumption for operation on machine
        '''
        machine_options = operation.get_machine_options()
        if machine.machine_id in machine_options:
            return machine_options[machine.machine_id][1]  # energy
        return float('inf')