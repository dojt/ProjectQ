import ctypes
libc = ctypes.CDLL("/home/bahman/Documents/below.jl/C/libketita_below.so")

class fl(ctypes.Structure):
	pass

class prg(ctypes.Structure):
	pass

fl._fields_ = [("fn", ctypes.c_char_p), ("bp", prg * 7)]

prg._fields_ = [("n_angels", ctypes.c_uint ), 
		("n_freturns", ctypes.c_uint), 
		("angel_sz", ctypes.c_uint * 8), 
		("angel", ctypes.c_double * 8), 
		("freturn_sz", ctypes.c_uint * 8), 
		("freturn_nm", ctypes.c_char_p * 8), 
 		("callback", ctypes.CFUNCTYPE(ctypes.c_double, 
					ctypes.c_double) * 8 ), 
		("data", ctypes.c_void_p * 8)]
 
def wrap_function(lib, funcname, restype, argtypes):
	func = lib.__getattr__(funcname)
	func.restype = restype
	func.argtypes = argtypes
	return func

__load = wrap_function(libc, "ketita_below__load", 
                        ctypes.POINTER(fl), [ctypes.c_char_p])


__get = wrap_function(libc, "ketita_below__get_prog", 
			ctypes.POINTER(prg), [ctypes.POINTER(fl), ctypes.c_char_p])

__help_file = wrap_function(libc, "ketita_below__help_file",
                                None, [ctypes.POINTER(fl)])

__help_prog = wrap_function(libc, "ketita_below__help_prog",
                                None, [ctypes.POINTER(prg)])

__free = wrap_function(libc, "ketita_below__free",
                                None, [ctypes.POINTER(fl)])

__free_prog = wrap_function(libc, "ketita_below__free_prog",
                                None, [ctypes.POINTER(prg)])

__set_angel_vec = wrap_function(libc, "ketita_below__set_angel_vec",
                                ctypes.c_int,[ctypes.POINTER(prg),
                                ctypes.c_uint, ctypes.POINTER(ctypes.c_double)])

__set_freturn = wrap_function(libc, "ketita_below__set_freturn_callback",
                                        ctypes.c_int, [ctypes.POINTER(prg),
                                        ctypes.c_uint, 
                                        ctypes.CFUNCTYPE(ctypes.c_double,
                                        ctypes.POINTER(ctypes.c_void_p), 
                                        ctypes.c_ulonglong), 
                                        ctypes.c_void_p])

__run_prog = wrap_function(libc, "ketita_below__run_prog",
                                None, [ctypes.POINTER(prg),
                                        ctypes.c_ulong,
                                        ctypes.POINTER(
                                                ctypes.POINTER(ctypes.c_double))])

def blw_free(bf):
        __free(bf)

def blw_load(filename = "dummy"):
        c_name = ctypes.c_char_p(str.encode(filename))
        bf = __load(c_name)
        return bf

def blw_help_file(bf):
        __help_file(bf)

def blw_get_prog(bf, prog_name = "blah"):
        prg_name = ctypes.c_char_p(str.encode(prog_name))
        this_prg = __get(bf, prg_name)
        return this_prg

def blw_free_prog(prg):
        __free_prog(prg)

def blw_help_prog(tmp_prg):
        __help_prog(tmp_prg)

def blw_setup_prog(p, angels, freturns):
        n_angels = len(angels)
        n_freturns = len(freturns)
        for i in range(n_angels):
                __set_angel_vec(p, i, angels[i])
        for i in range(n_freturns):
                __set_freturn(p, i , freturns[i], None)

def blw_run_prog(p, iter, expvals):
        __run_prog(p, iter, expvals)

#bf = load_file("edaf")
#help_file(bf)
#blah = get_prog(bf, "f")
#help_prog(blah)


from projectq.cengines import BasicEngine
from projectq.meta import get_control_count, LogicalQubitIDTag
from projectq.ops import (NOT,
                          Y,
                          Z,
                          T,
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
        self.qasm = ""
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
            if g in (T, Tdag, S, Sdag, H, Y, Z):
                return True
            if isinstance(g, (Rx, Ry, Rz)):
                return True
        if g in (Measure, Allocate, Deallocate, Barrier):
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
            self.qasm = ""
            self._allocated_qubits = set()

        gate = cmd.gate

        

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

        Send the circuit via the IBM API (JSON QASM) using the provided user
        data / ask for username & password.
        """
        bf = blw_load("edaf")
        blw_help_file(bf)
        blah = blw_get_prog(bf, "f")
        blw_help_prog(blah)


        
    def receive(self, command_list):
        """
        Receives a command list and, for each command, stores it until
        completion.

        Args:
            command_list: List of commands to execute
        """
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





