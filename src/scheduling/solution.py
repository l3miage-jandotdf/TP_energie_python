'''
Object containing the solution to the optimization problem.

@author: Vassilissa Lehoux
'''
from __future__ import annotations
from typing import List, Tuple, Optional
import csv
import copy
from matplotlib import pyplot as plt
from src.scheduling.instance.instance import Instance
from src.scheduling.instance.operation import Operation

from matplotlib import colormaps
from src.scheduling.instance.machine import Machine

# weight of total energy
ALPHA   = 1.0
# weight of makespan
BETA    = 1.0
# weight of average job completion time
GAMMA   = 0.0
# penalty added if a solution is infeasible
PENALTY = 10 ** 6

class Solution(object):
    '''
    Solution class
    '''

    def __init__(self, instance: Instance):
        '''
        Constructor
        '''
        self._instance: Instance = instance

        # Cached metrics
        self._total_energy:  Optional[int]   = None
        self._makespan:      Optional[int]   = None
        self._avg_job_c:     Optional[float] = None
        self._feasible:      Optional[bool]  = None
        self._objective_val: Optional[float] = None

        self.recompute()


    @property
    def inst(self):
        '''
        Returns the associated instance
        '''
        return self._instance

    def recompute(self) -> None:
        self._total_energy = sum(m.total_energy_consumption
                             for m in self.inst.machines)

        comp_times = [job.completion_time for job in self.inst.jobs]
        self._makespan  = max(comp_times) if comp_times else 0
        self._avg_job_c = (sum(comp_times) / len(comp_times)
                        if comp_times else 0)

        feasible = True
        for op in self.inst.operations:
            if not op.assigned:
                feasible = False
                break
            for pred in op.predecessors:
                if pred.end_time > op.start_time:
                    feasible = False
                    break
            if not feasible:
                break
        self._feasible = feasible

        if not feasible:
            viol = sum(1 for op in self.inst.operations if not op.assigned)
            self._objective_val = viol * PENALTY
            return

        self._objective_val = (ALPHA * self._total_energy
                            + BETA  * self._makespan
                            + GAMMA * self._avg_job_c)
        
    def reset(self):
        '''
        Resets the solution: everything needs to be replanned
        '''
        for mach in self.inst.machines:
            mach.reset()
        for job in self.inst.jobs:
            job.reset()
        self.recompute()

    @property
    def is_feasible(self) -> bool:
        '''
        Returns True if the solution respects the constraints.
        To call this function, all the operations must be planned.
        '''
        return bool(self._feasible)

    @property
    def evaluate(self) -> int:
        '''
        Computes the value of the solution
        '''
        return self._objective_val

    @property
    def objective(self) -> int:
        '''
        Returns the value of the objective function
        '''
        return self._objective_val

    @property
    def cmax(self) -> int:
        '''
        Returns the maximum completion time of a job
        '''
        return self._makespan

    @property
    def sum_ci(self) -> int:
        '''
        Returns the sum of completion times of all the jobs
        '''
        return self._avg_job_c * len(self.inst.jobs)

    @property
    def total_energy_consumption(self) -> int:
        '''
        Returns the total energy consumption for processing
        all the jobs (including energy for machine switched on but doing nothing).
        '''
        return self._total_energ

    def deepcopy(self) -> "Solution":
        new_inst = copy.deepcopy(self.inst)
        return Solution(new_inst)
    
    def __str__(self) -> str:
        '''
        String representation of the solution
        '''
        return (f"Solution[obj={self._objective_val:.2f}, "
                f"energy={self._total_energy}, "
                f"Cmax={self._makespan}, "
                f"avgC={self._avg_job_c:.1f}, "
                f"feasible={self._feasible}]")

    def to_csv(self):
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
        with open(operation_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["operation_id", "machine_id", "start_time"])
            for op in self.all_operations:
                writer.writerow([op.operation_id, op.assigned_to, op.start_time])

        with open(machine_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["machine_id", "start_time", "stop_time"])
            for mach in self.inst.machines:
                for s, e in zip(mach.start_times, mach.stop_times):
                    writer.writerow([mach.machine_id, s, e])

    def from_csv(self, inst_folder, operation_file, machine_file):
        '''
        Reads a solution from the instance folder
        '''
        self.reset()

        with open(operation_file, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                op = self.inst.get_operation(int(row["operation_id"]))
                m  = self.inst.get_machine(int(row["machine_id"]))
                st = int(row["start_time"])
                m.add_operation(op, st)

        if machine_file:
            for mach in self.inst.machines:
                mach.start_times.clear()
                mach.stop_times.clear()

            with open(machine_file, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    mach = self.inst.get_machine(int(row["machine_id"]))
                    start = int(row["start_time"])
                    stop  = int(row["stop_time"])
                    mach.start_times.append(start)
                    mach.stop_times.append(stop)

        self.recompute()

    @property
    def available_operations(self)-> List[Operation]:
        '''
        Returns the available operations for scheduling:
        all constraints have been met for those operations to start
        '''
        return [op for op in self.all_operations if not op.assigned and op.is_ready(0)]

    @property
    def all_operations(self) -> List[Operation]:
        '''
        Returns all the operations in the instance
        '''
        return self.inst.operations

    def schedule(self, operation: Operation, machine: Machine):
        '''
        Schedules the operation at the end of the planning of the machine.
        Starts the machine if stopped.
        @param operation: an operation that is available for scheduling
        '''
        assert not operation.assigned, "Operation already scheduled"
        start_time = max(machine.available_time, operation.min_start_time)
        machine.add_operation(operation, start_time)
        self.recompute()

    def gantt(self, colormapname):
        """
        Generate a plot of the planning.
        Standard colormaps can be found at https://matplotlib.org/stable/users/explain/colors/colormaps.html
        """
        fig, ax = plt.subplots()
        colormap = colormaps[colormapname]
        for machine in self.inst.machines:
            machine_operations = sorted(machine.scheduled_operations, key=lambda op: op.start_time)
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
        ax.set_yticklabels([f'M{machine_id+1}' for machine_id in range(self.inst.nb_machines)])
        ax.set_xlabel('Time')
        ax.set_ylabel('Machine')
        ax.set_title('Gantt Chart')
        ax.grid(True)
    
        return plt

