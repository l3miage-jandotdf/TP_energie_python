'''
Machine on which operation are executed.

@author: Vassilissa Lehoux
'''
from typing import List
from src.scheduling.instance.operation import Operation


class Machine(object):
    '''
    Machine class.
    When operations are scheduled on the machine, contains the relative information. 
    '''

    def __init__(self, machine_id: int, set_up_time: int, set_up_energy: int, tear_down_time: int,
                 tear_down_energy:int, min_consumption: int, end_time: int):
        '''
        Constructor
        Machine is stopped at the beginning of the planning and need to
        be started before executing any operation.
        @param end_time: End of the schedule on this machine: the machine must be
          shut down before that time.
        '''
        self._machine_id = machine_id
        self._set_up_time = set_up_time
        self._set_up_energy = set_up_energy
        self._tear_down_time = tear_down_time
        self._tear_down_energy = tear_down_energy
        self._min_consumption = min_consumption
        self._end_time = end_time
        
        # State variables
        self._scheduled_operations = []
        self._start_times = []
        self._stop_times = []
        self._current_state = 'OFF'
        self._current_energy = 0
        self._last_available_time = 0

    def reset(self):
        self._scheduled_operations = []
        self._start_times = []
        self._stop_times = []
        self._current_state = 'OFF'
        self._current_energy = 0
        self._last_available_time = 0

    @property
    def set_up_time(self) -> int:
        return self._set_up_time

    @property
    def tear_down_time(self) -> int:
        return self._tear_down_time

    @property
    def machine_id(self) -> int:
        return self._machine_id

    @property
    def scheduled_operations(self) -> List:
        '''
        Returns the list of the scheduled operations on the machine.
        '''
        return self._scheduled_operations

    @property
    def available_time(self) -> int:
        """
        Returns the next time at which the machine is available
        after processing its last operation of after its last set up.
        """
        if not self._scheduled_operations:
            if self._current_state == 'OFF':
                return self._last_available_time + self._set_up_time
            return self._last_available_time
        else:
            last_op = self._scheduled_operations[-1]
            return last_op.start_time + last_op.processing_time

    def add_operation(self, operation: Operation, start_time: int) -> int:
        '''
        Adds an operation on the machine, at the end of the schedule,
        as soon as possible after time start_time.
        Returns the actual start time.
        '''
        actual_start = max(start_time, self.available_time)
        if self._current_state == "OFF":
            actual_start = max(actual_start, self._last_available_time + self._set_up_time)

            self._start_times.append(actual_start - self._set_up_time)

            if not self._stop_times:
                self._stop_times.append(self._end_time)

            self._current_energy += self._set_up_energy
            self._current_state = "ON"

        ok = operation.schedule(
            machine_id=self._machine_id,
            at_time=actual_start,
            check_success=False
        )
        if not ok:
            raise ValueError("Operation could not be scheduled on this machine")

        self._scheduled_operations.append(operation)
        self._current_energy += operation.energy * operation.processing_time
        self._last_available_time = actual_start + operation.processing_time

        return actual_start
  
    def stop(self, at_time):
        """
        Stops the machine at time at_time.
        """
        assert(self.available_time <= at_time)
        assert at_time + self._tear_down_time <= self._end_time
        
        self._stop_times.append(at_time)
        self._current_energy += self._tear_down_energy
        self._current_state = 'OFF'
        self._last_available_time = at_time + self._tear_down_time

    @property
    def working_time(self) -> int:
        '''
        Total time during which the machine is running
        '''
        if self._start_times and not self._stop_times:
            if self.available_time >= self._end_time:
                return self._end_time
            else:
                return self._end_time - self._start_times[0]

        total = 0
        for i, start in enumerate(self._start_times):
            stop = self._stop_times[i]
            total += stop - start
        return total

    @property
    def start_times(self) -> List[int]:
        """
        Returns the list of the times at which the machine is started
        in increasing order
        """
        return self._start_times

    @property
    def stop_times(self) -> List[int]:
        """
        Returns the list of the times at which the machine is stopped
        in increasing order
        """
        return self._stop_times

    @property
    def total_energy_consumption(self) -> int:
        """
        Total energy consumption of the machine during planning exectution.
        """
        total_time = self._end_time
        busy_time = sum(op.processing_time for op in self._scheduled_operations)
        idle_time = max(0, total_time - busy_time - sum(self._start_times) - sum(self._stop_times))
        
        return (self._current_energy + 
                idle_time * self._min_consumption +
                len(self._start_times) * self._set_up_energy +
                len(self._stop_times) * self._tear_down_energy)

    def __str__(self):
        return f"M{self.machine_id}"

    def __repr__(self):
        return str(self)

