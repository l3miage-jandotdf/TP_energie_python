'''
Operation of a job.
Its duration and energy consumption depends on the machine on which it is executed.
When operation is scheduled, its schedule information is updated.

@author: Vassilissa Lehoux
'''
from typing import List, Dict, Tuple


class OperationScheduleInfo(object):
    '''
    Informations known when the operation is scheduled
    '''

    def __init__(self, machine_id: int, schedule_time: int, duration: int, energy_consumption: int):
        self.machine_id = machine_id
        self.schedule_time = schedule_time
        self.duration = duration
        self.energy_consumption = energy_consumption


class Operation(object):
    '''
    Operation of the jobs
    '''

    def __init__(self, operation_id, job):
        '''
        Constructor
        '''
        self._operation_id = operation_id
        self._job = job
        self._job_id = job.job_id
        self._predecessors = []
        self._successors = []
        self._schedule_info = None
        # Machine options: dict avec machine_id comme clé et (duration, energy) comme valeur
        self._machine_options = {}

    def __str__(self):
        '''
        Returns a string representing the operation.
        '''
        base_str = f"O{self.operation_id}_J{self.job_id}"
        if self._schedule_info:
            return base_str + f"_M{self.assigned_to}_ci{self.processing_time}_e{self.energy}"
        else:
            return base_str

    def __repr__(self):
        return str(self)

    def reset(self):
        '''
        Removes scheduling informations
        '''
        self._schedule_info = None

    def add_predecessor(self, operation):
        '''
        Adds a predecessor to the operation
        '''
        if operation not in self._predecessors:
            self._predecessors.append(operation)
            operation.add_successor(self)

    def add_successor(self, operation):
        '''
        Adds a successor operation
        '''
        if operation not in self._successors:
            self._successors.append(operation)
            operation.add_predecessor(self)

    def set_predecessor(self, operation):
        '''
        Sets an operation as predecessor (for Job class)
        '''
        self.add_predecessor(operation)

    def add_machine_option(self, machine, duration, energy_consumption):
        '''
        Adds a machine option with its associated duration and energy consumption
        '''
        self._machine_options[machine.machine_id] = (duration, energy_consumption, machine)

    @property
    def operation_id(self) -> int:
        return self._operation_id

    @property
    def job_id(self) -> int:
        return self._job_id

    @property
    def predecessors(self) -> List:
        """
        Returns a list of the predecessor operations
        """
        return self._predecessors

    @property
    def successors(self) -> List:
        '''
        Returns a list of the successor operations
        '''
        return self._successors

    @property
    def assigned(self) -> bool:
        '''
        Returns True if the operation is assigned
        and False otherwise
        '''
        return self._schedule_info is not None

    def is_scheduled(self) -> bool:
        '''
        Alias for assigned (pour compatibilité avec Job.completion_time)
        '''
        return self.assigned

    @property
    def assigned_to(self) -> int:
        '''
        Returns the machine ID it is assigned to if any
        and -1 otherwise
        '''
        if self._schedule_info:
            return self._schedule_info.machine_id
        return -1

    @property
    def processing_time(self) -> int:
        '''
        Returns the processing time if is assigned,
        -1 otherwise
        '''
        if self._schedule_info:
            return self._schedule_info.duration
        return -1

    @property
    def start_time(self) -> int:
        '''
        Returns the start time if is assigned,
        -1 otherwise
        '''
        if self._schedule_info:
            return self._schedule_info.schedule_time
        return -1

    @property
    def end_time(self) -> int:
        '''
        Returns the end time if is assigned,
        -1 otherwise
        '''
        if self._schedule_info:
            return self._schedule_info.schedule_time + self._schedule_info.duration
        return -1

    @property
    def energy(self) -> int:
        '''
        Returns the energy consumption if is assigned,
        -1 otherwise
        '''
        if self._schedule_info:
            return self._schedule_info.energy_consumption
        return -1

    def is_ready(self, at_time) -> bool:
        '''
        Returns True if all the predecessors are assigned
        and processed before at_time.
        False otherwise
        '''
        for pred in self._predecessors:
            if not pred.assigned or pred.end_time > at_time:
                return False
        return True

    def schedule(self, machine_id: int, at_time: int, check_success=True) -> bool:
        '''
        Schedules an operation. Updates the schedule information of the operation
        @param check_success: if True, check if all the preceeding operations have
          been scheduled and if the schedule time is compatible
        '''
        # Vérifier si la machine est disponible pour cette opération
        if machine_id not in self._machine_options:
            return False
        
        # Vérifier que les prédécesseurs sont bien terminés
        if check_success and not self.is_ready(at_time):
            return False
        
        # Récupérer les informations de durée et d'énergie pour cette machine
        duration, energy, _ = self._machine_options[machine_id]
        
        # Créer les informations d'ordonnancement
        self._schedule_info = OperationScheduleInfo(machine_id, at_time, duration, energy)
        
        return True

    @property
    def min_start_time(self) -> int:
        '''
        Minimum start time given the precedence constraints
        '''
        max_end_time = 0
        for pred in self._predecessors:
            if pred.assigned:
                max_end_time = max(max_end_time, pred.end_time)
            else:
                # Si un prédécesseur n'est pas assigné, on ne peut pas déterminer
                # le temps minimum de départ
                return -1
        return max_end_time

    def schedule_at_min_time(self, machine_id: int, min_time: int = 0) -> bool:
        '''
        Try and schedule the operation at or after min_time.
        Return False if not possible
        '''
        if machine_id not in self._machine_options:
            return False
        
        # Déterminer le temps de départ le plus tôt en tenant compte des contraintes
        # de précédence et du temps minimum demandé
        earliest_start = max(min_time, self.min_start_time)
        
        if earliest_start < 0:
            return False  # Un prédécesseur n'est pas assigné
        
        # Planifier l'opération
        return self.schedule(machine_id, earliest_start)

    def get_machine_options(self) -> Dict[int, Tuple[int, int]]:
        '''
        Returns a dictionary of machine options with machine_id as key
        and (duration, energy) as value
        '''
        return {mid: (d, e) for mid, (d, e, _) in self._machine_options.items()}