'''
Operation of a job.
Its duration and energy consumption depends on the machine on which it is executed.
When operation is scheduled, its schedule information is updated.

@author: Vassilissa Lehoux
'''
from typing import List


class OperationScheduleInfo(object):
    '''
    Informations known when the operation is scheduled
    '''

    def __init__(self, machine_id: int, schedule_time: int, duration: int, energy_consumption: int):
        self._machine_id = machine_id
        self._schedule_time = schedule_time
        self._duration = duration
        self._energy_consumption = energy_consumption
    @property
    def machine_id(self) -> int:
        return self._machine_id

    @property
    def schedule_time(self) -> int:
        return self._schedule_time

    @property
    def duration(self) -> int:
        return self._duration

    @property
    def energy_consumption(self) -> int:
        return self._energy_consumption

    @property
    def end_time(self) -> int:
        return self._schedule_time + self._duration

class Operation(object):
    '''
    Operation of the jobs
    '''

    def __init__(self, job_id, operation_id):
        '''
        Constructor
        '''
        self._job_id = job_id
        self._operation_id = operation_id
        self._schedule_info = None
        self._predecessors = []
        self._successors = []
        self._job = None
        self._sequence_num = -1
        self._variants = []

    def __str__(self):
        '''
        Returns a string representing the operation.
        '''
        base_str = f"O{self.operation_id}_J{self.job_id}"
        if self._schedule_info:
            return base_str + f"_M{self.assigned_to}_ci{self.processing_time}_e{self.energy}"
        else:
            return base_str + "_UNSCHEDULED"

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
    
    def add_variant(self, machine_id, processing_time, energy):
        if not hasattr(self, "_variants"):
            self._variants = []
        self._variants.append((machine_id, processing_time, energy))

    @property
    def operation_id(self) -> int:
        return self._operation_id

    @property
    def job_id(self) -> int:
        return self._job.job_id if self._job else -1

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

    @property
    def assigned_to(self) -> int:
        '''
        Returns the machine ID it is assigned to if any
        and -1 otherwise
        '''
        return self._schedule_info.machine_id if self.assigned else -1

    @property
    def processing_time(self) -> int:
        '''
        Returns the processing time if is assigned,
        -1 otherwise
        '''
        if self.assigned:
            return getattr(self, "_processing_time", self._schedule_info.duration)
        return -1

    @property
    def start_time(self) -> int:
        '''
        Returns the start time if is assigned,
        -1 otherwise
        '''
        return self._schedule_info.schedule_time if self.assigned else -1

    @property
    def end_time(self) -> int:
        '''
        Returns the end time if is assigned,
        -1 otherwise
        '''
        return self._schedule_info.end_time if self.assigned else -1

    @property
    def energy(self) -> int:
        '''
        Returns the energy consumption if is assigned,
        -1 otherwise
        '''
        return self._schedule_info.energy_consumption if self.assigned else -1

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
        if check_success and not self.is_ready(at_time):
            return False

        p_time: int
        energy: int

        if getattr(self, "_variants", []):
            variant = [v for v in self._variants if v[0] == machine_id]
            if not variant:
                return False
            p_time, energy = variant[0][1], variant[0][2]

        else:
            if (not hasattr(self, "_machine_id")) or machine_id != self._machine_id:
                return False
            p_time  = getattr(self, "_processing_time", -1)
            energy  = getattr(self, "_energy_consumption", -1)
            if p_time < 0 or energy < 0:
                return False

        self._schedule_info = OperationScheduleInfo(
            machine_id=machine_id,
            schedule_time=at_time,
            duration=p_time,
            energy_consumption=energy
        )
        self._processing_time = p_time
        self._energy_consumption = energy
        return True

    @property
    def min_start_time(self) -> int:
        '''
        Minimum start time given the precedence constraints
        '''
        if not self._predecessors:
            return 0
        return max(pred.end_time for pred in self._predecessors)

    def schedule_at_min_time(self, machine_id: int, min_time: int) -> bool:
        '''
        Try and schedule the operation af or after min_time.
        Return False if not possible
        '''
        actual_start = max(min_time, self.min_start_time)
        return self.schedule(machine_id, actual_start, check_success=True)

