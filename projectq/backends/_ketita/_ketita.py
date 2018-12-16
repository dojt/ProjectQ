from ._ketita_inter import *
import random
import json
import math
from projectq.cengines import BasicEngine
from projectq.meta import get_control_count, LogicalQubitIDTag
from projectq.ops import (NOT,
                          AROTX,
                          Y,
                          Z,
                          T,
                          Swap,
                          Tdag,
                          S,
                          Sdag,
                          H,
                          Rx,
                          Ry,
                          Rz,
                          Measure,
                          Allocate,
                          Deallocate,
                          Barrier,
                          FlushGate)



class KetitaBackend(BasicEngine):
    """
    The IBM Backend class, which stores the circuit, transforms it to JSON
    QASM, and sends the circuit through the IBM API.
    """
    def __init__(self, use_hardware=False, num_runs=1024, verbose=False,
                 user=None, password=None, device='ibmqx4',
                 retrieve_execution=None):
        """
        Initialize the Backend object.

        Args:
            use_hardware (bool): If True, the code is run on the IBM quantum
                chip (instead of using the IBM simulator)
            num_runs (int): Number of runs to collect statistics.
                (default is 1024)
            verbose (bool): If True, statistics are printed, in addition to
                the measurement result being registered (at the end of the
                circuit).
            user (string): IBM Quantum Experience user name
            password (string): IBM Quantum Experience password
            device (string): Device to use ('ibmqx4', or 'ibmqx5')
                if use_hardware is set to True. Default is ibmqx4.
            retrieve_execution (int): Job ID to retrieve instead of re-
                running the circuit (e.g., if previous run timed out).
        """
        BasicEngine.__init__(self)
        self._reset()
        if use_hardware:
            self.device = device
        else:
            self.device = 'simulator'
        self._num_runs = num_runs
        self._verbose = verbose
        self._user = user
        self._password = password
        self._probabilities = dict()
        self.blw = ""
        self._measured_ids = []
        self._allocated_qubits = set()
        self._retrieve_execution = retrieve_execution

    def is_available(self, cmd):
        """
        Return true if the command can be executed.

        The IBM quantum chip can do X, Y, Z, T, Tdag, S, Sdag,
        rotation gates, barriers, and CX / CNOT.

        Args:
            cmd (Command): Command for which to check availability
        """
        g = cmd.gate
        if g == NOT and get_control_count(cmd) <= 1:
            return True
        if get_control_count(cmd) == 0:
            if g in (T, Tdag, S, Sdag, H, Y, Z, AROTX):
                return True
            if isinstance(g, (Rx, Ry, Rz, AROTX)):
                return True
        if g in (Measure, Allocate, Deallocate, Barrier, AROTX):
            return True
        return False

    def _reset(self):
        """ Reset all temporary variables (after flush gate). """
        self._clear = True
        self._measured_ids = []

    def _store(self, cmd):
        """
        Temporarily store the command cmd.

        Translates the command and stores it in a local variable (self._cmds).

        Args:
            cmd: Command to store
        """
        if self._clear:
            self._probabilities = dict()
            self._clear = False
            self.blw = ""
            self.myid = {}
            self._allocated_qubits = set()

        gate = cmd.gate

        if gate == Allocate:
            self._allocated_qubits.add(cmd.qubits[0][0].id)
            logical_id = None
            for t in cmd.tags:
                if isinstance(t, LogicalQubitIDTag):
                    logical_id = t.logical_qubit_id
                    break
            #assert logical_id is not None
            if logical_id != None:
                self.myid[logical_id] = [cmd.qubits[0][0].id]
            return

        if gate == Deallocate:
            return

        if gate == Measure:
            assert len(cmd.qubits) == 1 and len(cmd.qubits[0]) == 1
            qb_id = cmd.qubits[0][0].id
            print("inside id" + str(qb_id))
            logical_id = None
            for t in cmd.tags:
                if isinstance(t, LogicalQubitIDTag):
                    logical_id = t.logical_qubit_id
                    break
            assert logical_id is not None
            self._measured_ids += [logical_id]
        elif gate == NOT and get_control_count(cmd) == 1:
            #print(cmd.control_qubits[0].__str__())
            #print(cmd.control_qubits)
            #print(cmd.qubits[0][0].__str__())
            #print(cmd.qubits)
            ctrl_pos = cmd.control_qubits[0].id
            qb_pos = cmd.qubits[0][0].id
            self.blw += "\ncheaptangle Q#{} Q#{}".format(ctrl_pos, qb_pos)
        elif gate == Barrier:
            qb_pos = [qb.id for qr in cmd.qubits for qb in qr]
            self.blw += "\nBarrier"
            qb_str = ""
            for pos in qb_pos:
                qb_str += "q[{}], ".format(pos)
            self.blw += qb_str[:-2] + ";"
        elif gate == Swap:
            #print(cmd.qubits[0]) 
            ctrl_pos = cmd.qubits[1][0].id
            qb_pos = cmd.qubits[0][0].id
            self.blw += "\nswap Q#{} Q#{}".format(ctrl_pos, qb_pos)
        elif gate.hasAttr("aaaa"):
            qb_pos = cmd.qubits[0][0].id
            self.blw += "\nAROT Q#{} TrAngel(1) {} {} {}".format(qb_pos, 
                            *gate.params)
        else :
            assert get_control_count(cmd) == 0
            qb_pos = cmd.qubits[0][0].id
            self.blw += "\nU1 Q#{} {} {} {}".format(qb_pos, *gate.params)

    def _logical_to_physical(self, qb_id):
        """
        Return the physical location of the qubit with the given logical id.

        Args:
            qb_id (int): ID of the logical qubit whose position should be
                returned.
        """
        assert self.main_engine.mapper is not None
        mapping = self.main_engine.mapper.current_mapping
        if qb_id not in mapping:
            raise RuntimeError("Unknown qubit id {}. Please make sure "
                               "eng.flush() was called and that the qubit "
                               "was eliminated during optimization."
                               .format(qb_id))
        return mapping[qb_id]

    def get_probabilities(self, qureg):
        """
        Return the list of basis states with corresponding probabilities.

        The measured bits are ordered according to the supplied quantum
        register, i.e., the left-most bit in the state-string corresponds to
        the first qubit in the supplied quantum register.

        Warning:
            Only call this function after the circuit has been executed!

        Args:
            qureg (list<Qubit>): Quantum register determining the order of the
                qubits.

        Returns:
            probability_dict (dict): Dictionary mapping n-bit strings to
            probabilities.

        Raises:
            RuntimeError: If no data is available (i.e., if the circuit has
                not been executed). Or if a qubit was supplied which was not
                present in the circuit (might have gotten optimized away).
        """
        if len(self._probabilities) == 0:
            raise RuntimeError("Please, run the circuit first!")

        probability_dict = dict()

        for state in self._probabilities:
            mapped_state = ['0'] * len(qureg)
            for i in range(len(qureg)):
                mapped_state[i] = state[self._logical_to_physical(qureg[i].id)]
            probability = self._probabilities[state]
            probability_dict["".join(mapped_state)] = probability

        return probability_dict

    def _run(self):
        """
        Run the circuit.

        Send the circuit via the IBM API (JSON ) using the provided user
        data / ask for username & password.
        """
        print(self.blw)
        print("idsss")
        print(self.myid)
        print("last mapping")
        print(self.main_engine.mapper.current_mapping)
        print("meas")
        print(self._measured_ids)
        #bf = blw_load("edaf")
        #blw_help_file(bf)
        #blah = blw_get_prog(bf, "f")
        #blw_help_prog(blah)


        
    def receive(self, command_list):
        """
        Receives a command list and, for each command, stores it until
        completion.

        Args:
            command_list: List of commands to execute
        """
        #print(self.main_engine.mapper.current_mapping)
        for cmd in command_list:
            if not cmd.gate == FlushGate():
                self._store(cmd)
            else:
                self._run()
                self._reset()

    """
    Mapping of gate names from our gate objects to the IBM QASM representation.
    """
    _gate_names = {str(Tdag): "tdg",
                   str(Sdag): "sdg"}





