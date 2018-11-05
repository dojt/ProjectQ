import ctypes
libc = ctypes.CDLL("../C/libketita_below.so")

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
