'''
Information for the instance of the optimization problem.

@author: Vassilissa Lehoux
'''
from typing import List
import os
import csv

from src.scheduling.instance.job import Job
from src.scheduling.instance.operation import Operation
from src.scheduling.instance.machine import Machine


class Instance(object):
    '''
    classdocs
    '''

    def __init__(self, instance_name):
        '''
        Constructor
        '''
        self._instance_name = instance_name
        self._machines = []
        self._jobs = []
        self._operations = []
        self._machine_dict = {}  # Pour accès rapide par ID
        self._job_dict = {}      # Pour accès rapide par ID
        self._operation_dict = {} # Pour accès rapide par ID

    def __str__(self):
        """
        Return a string representation of the instance in the format: name_M{nb_machines}_J{nb_jobs}_O{nb_operations}
        """
        return f"{self._instance_name}_M{self.nb_machines}_J{self.nb_jobs}_O{self.nb_operations}"

    @classmethod
    def from_file(cls, folderpath):
        inst = cls(os.path.basename(folderpath))
        
        # Reading machine info first
        with open(folderpath + os.path.sep + inst._instance_name + '_mach.csv', 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            header = next(csv_reader)
            for row in csv_reader:
                machine_id = int(row[0])
                set_up_time = float(row[1])
                set_up_energy = float(row[2])
                tear_down_time = float(row[3])
                tear_down_energy = float(row[4])
                min_consumption = float(row[5])
                end_time = float(row[6])
                
                # Créer la machine
                machine = Machine(machine_id, end_time, set_up_time, set_up_energy, 
                                tear_down_time, tear_down_energy, min_consumption)
                inst._machines.append(machine)
                inst._machine_dict[machine_id] = machine
        
        # Créer les jobs d'abord
        # Reading operation info pour déterminer les jobs uniques
        job_ids = set()
        with open(folderpath + os.path.sep + inst._instance_name + '_op.csv', 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            header = next(csv_reader)
            for row in csv_reader:
                job_id = int(row[0])
                job_ids.add(job_id)
        
        # Créer les jobs
        for job_id in sorted(job_ids):
            job = Job(job_id)
            inst._jobs.append(job)
            inst._job_dict[job_id] = job
        
        # Créer un dictionnaire pour stocker les opérations de chaque job
        job_operations = {job_id: {} for job_id in job_ids}
        
        # Lire à nouveau le fichier pour créer les opérations
        with open(folderpath + os.path.sep + inst._instance_name + '_op.csv', 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            header = next(csv_reader)
            for row in csv_reader:
                job_id = int(row[0])
                op_id = int(row[1])
                machine_id = int(row[2])
                processing_time = float(row[3])
                energy_consumption = float(row[4])
                
                # Créer l'opération si elle n'existe pas déjà
                if op_id not in job_operations[job_id]:
                    job = inst._job_dict[job_id]
                    operation = Operation(op_id, job)
                    job_operations[job_id][op_id] = operation
                    inst._operations.append(operation)
                    inst._operation_dict[(job_id, op_id)] = operation
                
                # Ajouter l'option machine à l'opération
                operation = job_operations[job_id][op_id]
                machine = inst._machine_dict[machine_id]
                operation.add_machine_option(machine, processing_time, energy_consumption)
        
        # Ajouter les opérations aux jobs dans l'ordre
        for job_id, operations in job_operations.items():
            job = inst._job_dict[job_id]
            for op_id in sorted(operations.keys()):
                operation = operations[op_id]
                job.add_operation(operation)
        
        return inst

    @property
    def name(self):
        return self._instance_name

    @property
    def machines(self) -> List[Machine]:
        return self._machines

    @property
    def jobs(self) -> List[Job]:
        return self._jobs

    @property
    def operations(self) -> List[Operation]:
        return self._operations

    @property
    def nb_jobs(self):
        return len(self._jobs)

    @property
    def nb_machines(self):
        return len(self._machines)

    @property
    def nb_operations(self):
        return len(self._operations)

    def get_machine(self, machine_id) -> Machine:
        return self._machine_dict.get(machine_id)

    def get_job(self, job_id) -> Job:
        return self._job_dict.get(job_id)

    def get_operation(self, operation_id) -> Operation:
        return self._operation_dict.get(operation_id)