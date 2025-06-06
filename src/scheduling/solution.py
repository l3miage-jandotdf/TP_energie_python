'''
Object containing the solution to the optimization problem.

@author: Vassilissa Lehoux
'''
from typing import List
from matplotlib import pyplot as plt
from src.scheduling.instance.instance import Instance
from src.scheduling.instance.operation import Operation
import csv
import os

from matplotlib import colormaps
from src.scheduling.instance.machine import Machine


class Solution(object):
    '''
    Solution class
    '''

    def __init__(self, instance: Instance):
        '''
        Constructor
        '''
        self._instance = instance
        # Coefficients pour la fonction objectif multi-critères
        # Ces valeurs peuvent être ajustées selon les priorités de l'entreprise
        self._energy_weight = 1.0  # Poids pour la consommation d'énergie
        self._time_weight = 1.0    # Poids pour le temps de complétion
        self._penalty_weight = 1000  # Pénalité pour les contraintes violées

    @property
    def inst(self):
        '''
        Returns the associated instance
        '''
        return self._instance

    def reset(self):
        '''
        Resets the solution: everything needs to be replanned
        '''
        # Reset toutes les machines
        for machine in self._instance.machines:
            machine.reset()
        
        # Reset tous les jobs
        for job in self._instance.jobs:
            job.reset()
        
        # Reset toutes les opérations
        for operation in self._instance.operations:
            operation.reset()

    @property
    def is_feasible(self) -> bool:
        '''
        Returns True if the solution respects the constraints.
        To call this function, all the operations must be planned.
        '''
        # Vérifier que toutes les opérations sont planifiées
        for operation in self._instance.operations:
            if not operation.assigned:
                return False
        
        # Vérifier les contraintes de précédence
        for operation in self._instance.operations:
            if not self._check_precedence_constraints(operation):
                return False
        
        # Vérifier les contraintes de capacité des machines
        for machine in self._instance.machines:
            if not self._check_machine_capacity_constraints(machine):
                return False
        
        return True

    def _check_precedence_constraints(self, operation: Operation) -> bool:
        '''
        Vérifie les contraintes de précédence pour une opération
        '''
        for predecessor in operation.predecessors:
            if not predecessor.assigned:
                return False
            if predecessor.end_time > operation.start_time:
                return False
        return True

    def _check_machine_capacity_constraints(self, machine: Machine) -> bool:
        '''
        Vérifie les contraintes de capacité pour une machine
        '''
        # Vérifier qu'aucune opération ne se chevauche
        operations = [(op, start_time) for op, start_time in machine.scheduled_operations]
        operations.sort(key=lambda x: x[1])  # Trier par temps de début
        
        for i in range(len(operations) - 1):
            current_op, current_start = operations[i]
            next_op, next_start = operations[i + 1]
            current_end = current_start + current_op.processing_time
            
            if current_end > next_start:
                return False  # Chevauchement détecté
        
        # Vérifier que toutes les opérations finissent avant la limite de temps
        for op, start_time in operations:
            end_time = start_time + op.processing_time
            if end_time > machine._end_time:
                return False
        
        return True

    @property
    def evaluate(self) -> int:
        '''
        Computes the value of the solution
        '''
        return self.objective

    @property
    def objective(self) -> int:
        '''
        Returns the value of the objective function
        '''
        # Fonction objectif multi-critères combinant énergie et temps
        energy_cost = self.total_energy_consumption * self._energy_weight
        time_cost = self.cmax * self._time_weight
        
        # Ajouter des pénalités si la solution n'est pas réalisable
        penalty = 0
        if not self.is_feasible:
            penalty = self._penalty_weight * self._count_violated_constraints()
        
        return int(energy_cost + time_cost + penalty)

    def _count_violated_constraints(self) -> int:
        '''
        Compte le nombre de contraintes violées
        '''
        violations = 0
        
        # Compter les opérations non planifiées
        for operation in self._instance.operations:
            if not operation.assigned:
                violations += 1
        
        # Compter les violations de précédence
        for operation in self._instance.operations:
            if operation.assigned and not self._check_precedence_constraints(operation):
                violations += 1
        
        # Compter les violations de capacité des machines
        for machine in self._instance.machines:
            if not self._check_machine_capacity_constraints(machine):
                violations += 1
        
        return violations

    @property
    def cmax(self) -> int:
        '''
        Returns the maximum completion time of a job
        '''
        max_completion = 0
        for job in self._instance.jobs:
            completion_time = job.completion_time
            max_completion = max(max_completion, completion_time)
        return max_completion

    @property
    def sum_ci(self) -> int:
        '''
        Returns the sum of completion times of all the jobs
        '''
        total_completion = 0
        for job in self._instance.jobs:
            total_completion += job.completion_time
        return total_completion

    @property
    def total_energy_consumption(self) -> int:
        '''
        Returns the total energy consumption for processing
        all the jobs (including energy for machine switched on but doing nothing).
        '''
        total_energy = 0
        for machine in self._instance.machines:
            total_energy += machine.total_energy_consumption
        return total_energy

    def __str__(self) -> str:
        '''
        String representation of the solution
        '''
        if not self.is_feasible:
            feasible_str = "INFEASIBLE"
        else:
            feasible_str = "FEASIBLE"
        
        return f"Solution for {self._instance.name}: {feasible_str}, " \
               f"Objective={self.objective}, Cmax={self.cmax}, " \
               f"Sum_Ci={self.sum_ci}, Energy={self.total_energy_consumption}"

    def to_csv(self, output_folder):
        '''
        Save the solution to a csv files with the following formats:
        Operation file:
          One line per operation
          operation id - machine to which it is assigned - start time
          header: "operation_id,machine_id,start_time"
        Machine file:
          One line per pair of (start time, stop time) for the machine
          header: "machine_id, start_time, stop_time"
        '''
        # Sauvegarder les opérations
        operation_file = os.path.join(output_folder, f"{self._instance.name}_operations.csv")
        with open(operation_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["operation_id", "machine_id", "start_time"])
            
            for operation in self._instance.operations:
                if operation.assigned:
                    writer.writerow([operation.operation_id, operation.assigned_to, operation.start_time])
        
        # Sauvegarder les machines
        machine_file = os.path.join(output_folder, f"{self._instance.name}_machines.csv")
        with open(machine_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["machine_id", "start_time", "stop_time"])
            
            for machine in self._instance.machines:
                for start_time, stop_time in zip(machine.start_times, machine.stop_times):
                    writer.writerow([machine.machine_id, start_time, stop_time])

    def from_csv(self, inst_folder, operation_file, machine_file):
        '''
        Reads a solution from the instance folder
        '''
        # Reset la solution actuelle
        self.reset()
        
        # Lire les opérations
        operation_path = os.path.join(inst_folder, operation_file)
        with open(operation_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                operation_id = int(row['operation_id'])
                machine_id = int(row['machine_id'])
                start_time = int(row['start_time'])
                
                # Trouver l'opération correspondante
                operation = None
                for op in self._instance.operations:
                    if op.operation_id == operation_id:
                        operation = op
                        break
                
                if operation:
                    operation.schedule(machine_id, start_time, check_success=False)
        
        # Lire les informations des machines (si nécessaire pour la reconstruction)
        machine_path = os.path.join(inst_folder, machine_file)
        with open(machine_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                machine_id = int(row['machine_id'])
                start_time = int(row['start_time'])
                stop_time = int(row['stop_time'])
                
                machine = self._instance.get_machine(machine_id)
                if machine:
                    # Reconstruire l'état de la machine
                    machine._start_times.append(start_time)
                    machine._stop_times.append(stop_time)

    @property
    def available_operations(self) -> List[Operation]:
        '''
        Returns the available operations for scheduling:
        all constraints have been met for those operations to start
        '''
        available = []
        
        for job in self._instance.jobs:
            next_op = job.next_operation
            if next_op is not None and not next_op.assigned:
                # Vérifier que tous les prédécesseurs sont terminés
                can_start = True
                for pred in next_op.predecessors:
                    if not pred.assigned:
                        can_start = False
                        break
                
                if can_start:
                    available.append(next_op)
        
        return available

    @property
    def all_operations(self) -> List[Operation]:
        '''
        Returns all the operations in the instance
        '''
        return self._instance.operations

    def schedule(self, operation: Operation, machine: Machine):
        '''
        Schedules the operation at the end of the planning of the machine.
        Starts the machine if stopped.
        @param operation: an operation that is available for scheduling
        '''
        assert(operation in self.available_operations)
        

        success = machine.add_operation(operation, machine._end_time)
        
        if success:
            for job in self._instance.jobs:
                if operation in job.operations and job.next_operation == operation:
                    job.schedule_operation()
                    break
            
            return True
        
        return False

    def gantt(self, colormapname):
        """
        Generate a plot of the planning.
        Standard colormaps can be found at https://matplotlib.org/stable/users/explain/colors/colormaps.html
        """
        fig, ax = plt.subplots()
        colormap = colormaps[colormapname]
        
        for machine in self.inst.machines:
            # Récupérer les opérations planifiées sur cette machine
            machine_operations = []
            for op, start_time in machine.scheduled_operations:
                machine_operations.append(op)
            
            machine_operations = sorted(machine_operations, key=lambda op: op.start_time)
            
            for operation in machine_operations:
                operation_start = operation.start_time
                operation_end = operation.end_time
                operation_duration = operation_end - operation_start
                operation_label = f"O{operation.operation_id}_J{operation.job_id}"
    
                # Set color based on job ID
                color_index = operation.job_id + 2
                if color_index >= colormap.N:
                    color_index = color_index % colormap.N
                color = colormap(color_index)
    
                ax.broken_barh(
                    [(operation_start, operation_duration)],
                    (machine.machine_id - 0.4, 0.8),
                    facecolors=color,
                    edgecolor='black'
                )

                middle_of_operation = operation_start + operation_duration / 2
                ax.text(
                    middle_of_operation,
                    machine.machine_id,
                    operation_label,
                    rotation=90,
                    ha='center',
                    va='center',
                    fontsize=8
                )
            
            set_up_time = machine.set_up_time
            tear_down_time = machine.tear_down_time
            for (start, stop) in zip(machine.start_times, machine.stop_times):
                start_label = "set up"
                stop_label = "tear down"
                ax.broken_barh(
                    [(start, set_up_time)],
                    (machine.machine_id - 0.4, 0.8),
                    facecolors=colormap(0),
                    edgecolor='black'
                )
                ax.broken_barh(
                    [(stop, tear_down_time)],
                    (machine.machine_id - 0.4, 0.8),
                    facecolors=colormap(1),
                    edgecolor='black'
                )
                ax.text(
                    start + set_up_time / 2.0,
                    machine.machine_id,
                    start_label,
                    rotation=90,
                    ha='center',
                    va='center',
                    fontsize=8
                )
                ax.text(
                    stop + tear_down_time / 2.0,
                    machine.machine_id,
                    stop_label,
                    rotation=90,
                    ha='center',
                    va='center',
                    fontsize=8
                )          

        fig = ax.figure
        fig.set_size_inches(12, 6)
    
        ax.set_yticks(range(self._instance.nb_machines))
        ax.set_yticklabels([f'M{machine_id}' for machine_id in range(self.inst.nb_machines)])
        ax.set_xlabel('Time')
        ax.set_ylabel('Machine')
        ax.set_title('Gantt Chart')
        ax.grid(True)
    
        return plt