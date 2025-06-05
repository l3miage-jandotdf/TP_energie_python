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

    def __init__(self, machine_id: int, end_time: int, set_up_time: int, set_up_energy: int, 
                 tear_down_time: int, tear_down_energy: int, min_consumption: int):
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
        
        # Informations pour le planning
        self._scheduled_operations = []  # Liste des opérations planifiées
        self._start_times = []  # Liste des temps de démarrage de la machine
        self._stop_times = []   # Liste des temps d'arrêt de la machine
        self._is_running = False  # La machine est-elle en fonctionnement?
        self._available_time = 0  # Temps à partir duquel la machine est disponible

    def reset(self):
        '''
        Reset machine scheduling information
        '''
        self._scheduled_operations = []
        self._start_times = []
        self._stop_times = []
        self._is_running = False
        self._available_time = 0

    @property
    def set_up_time(self) -> int:
        '''
        Returns the set up time of the machine
        '''
        return self._set_up_time

    @property
    def tear_down_time(self) -> int:
        '''
        Returns the tear down time of the machine
        '''
        return self._tear_down_time

    @property
    def machine_id(self) -> int:
        '''
        Returns the ID of the machine
        '''
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
        return self._available_time

    def add_operation(self, operation: Operation, start_time: int) -> int:
        '''
        Adds an operation on the machine, at the end of the schedule,
        as soon as possible after time start_time.
        Returns the actual start time.
        '''
        # Vérifier si on peut ajouter l'opération à ce moment
        actual_start_time = max(start_time, self._available_time)
        
        # Si la machine n'est pas en marche, il faut la démarrer
        if not self._is_running:
            # Démarrer la machine
            self._start_times.append(actual_start_time)
            self._is_running = True
            # Mise à jour du temps disponible après démarrage
            actual_start_time += self._set_up_time
            self._available_time = actual_start_time
        
        # Vérifier si l'opération peut être planifiée avant la fin du temps imparti
        if actual_start_time + operation.processing_time + self._tear_down_time > self._end_time:
            # L'opération ne peut pas être planifiée car elle dépasserait le temps imparti
            return -1
        
        # Ajout de l'opération au planning
        self._scheduled_operations.append((operation, actual_start_time))
        
        # Mise à jour du temps disponible
        self._available_time = actual_start_time + operation.processing_time
        
        return actual_start_time
  
    def stop(self, at_time):
        """
        Stops the machine at time at_time.
        """
        assert(self.available_time <= at_time)
        
        if self._is_running:
            self._stop_times.append(at_time)
            self._is_running = False
            self._available_time = at_time + self._tear_down_time

    @property
    def working_time(self) -> int:
        '''
        Total time during which the machine is running
        '''
        if not self._start_times:
            return 0
        
        total_time = 0
        for i in range(len(self._start_times)):
            start = self._start_times[i]
            stop = self._stop_times[i] if i < len(self._stop_times) else self._available_time
            total_time += (stop - start)
        
        return total_time

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
        Total energy consumption of the machine during planning execution.
        """
        if not self._start_times:
            return 0
        
        total_energy = 0
        
        # Énergie de démarrage
        for _ in self._start_times:
            total_energy += self._set_up_energy
        
        # Énergie d'arrêt
        for _ in self._stop_times:
            total_energy += self._tear_down_energy
        
        # Énergie des opérations
        for operation, _ in self._scheduled_operations:
            total_energy += operation.energy
        
        # Énergie de veille (idle energy)
        # Calculer le temps total pendant lequel la machine est allumée mais n'exécute pas d'opérations
        idle_time = 0
        
        for i in range(len(self._start_times)):
            start = self._start_times[i] + self._set_up_time  # Après le démarrage
            stop = self._stop_times[i] if i < len(self._stop_times) else self._available_time
            
            # Calculer le temps total pendant lequel la machine est allumée
            total_on_time = stop - start
            
            # Calculer le temps pendant lequel la machine exécute des opérations dans cette période
            operation_time = 0
            for op, op_start in self._scheduled_operations:
                op_end = op_start + op.processing_time
                
                # Si l'opération est exécutée pendant cette période de fonctionnement
                if op_start >= start and op_end <= stop:
                    operation_time += op.processing_time
            
            # Le temps d'inactivité est la différence
            idle_time += (total_on_time - operation_time)
        
        # Ajouter l'énergie de veille
        total_energy += idle_time * self._min_consumption
        
        return total_energy

    def __str__(self):
        return f"M{self.machine_id}"

    def __repr__(self):
        return str(self)