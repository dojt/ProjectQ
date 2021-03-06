import ctypes as ct
libc = ct.CDLL("/home/bahman/Documents/usb/below.jl/C/libketita_below.so")

class fl(ct.Structure):
	pass

class prg(ct.Structure):
	pass

err_string = {}
err_string[ -1 ] = "Other error"
err_string[  0 ] = "OK"
err_string[  1 ] = "One of the angel vectors has not been set"
err_string[  2 ] = "One of the freturn callbacks has not been set"
err_string[  3 ] = "Compile error"

fl._fields_ = [("fn", ct.c_char_p), ("bp", prg * 7)]

prg._fields_ = [("n_angels", ct.c_uint ), 
		("n_freturns", ct.c_uint), 
		("angel_sz", ct.c_uint * 8), 
		("angel", ct.c_double * 8), 
		("freturn_sz", ct.c_uint * 8), 
		("freturn_nm", ct.c_char_p * 8), 
 		("callback", ct.CFUNCTYPE(ct.c_double, 
					ct.c_double) * 8 ), 
		("data", ct.c_void_p * 8)]

def init_angels(angels, all = False):
        n = len(angels)
        if all:
                myarr = ct.c_double * n
                return myarr(*angels)
        else:
                l = []
                for i in range(n):
                        m = len(angels[i])
                        myarr = ct.c_double * m
                        l.append(myarr(*angels[i]))
                return l

 
def wrap_function(lib, funcname, restype, argtypes):
	func = lib.__getattr__(funcname)
	func.restype = restype
	func.argtypes = argtypes
	return func

__load = wrap_function(libc, "ketita_below__load", ct.POINTER(fl), [ct.c_char_p])


__get = wrap_function(libc, "ketita_below__get_prog", ct.POINTER(prg), 
                        [ct.POINTER(fl), ct.c_char_p])

__help_file = wrap_function(libc, "ketita_below__help_file",
                                None, [ct.POINTER(fl)])

__help_prog = wrap_function(libc, "ketita_below__help_prog",
                                None, [ct.POINTER(prg)])

__free = wrap_function(libc, "ketita_below__free",
                                None, [ct.POINTER(fl)])

__free_prog = wrap_function(libc, "ketita_below__free_prog",
                                None, [ct.POINTER(prg)])

__set_angel_vec = wrap_function(libc, "ketita_below__set_angel_vec",
                                ct.c_int,[ct.POINTER(prg),
                                ct.c_uint, ct.POINTER(ct.c_double)])

__set_freturn = wrap_function(libc, "ketita_below__set_freturn_callback",
                                        ct.c_int, [ct.POINTER(prg),
                                        ct.c_uint, 
                                        ct.CFUNCTYPE(ct.c_double,
                                        ct.POINTER(ct.c_void_p), 
                                        ct.c_ulonglong,
                                        ct.c_ulong), 
                                        ct.c_void_p])

__run_prog = wrap_function(libc, "ketita_below__run_prog",
                                ct.c_int, [ct.POINTER(prg),
                                        ct.c_ulong,
                                        ct.POINTER(ct.c_double)])

__get_num_angels = wrap_function(libc, "ketita_below__get_num_angels",
                                ct.c_uint, [ct.POINTER(prg)])

__get_num_freturns = wrap_function(libc, "ketita_below__get_num_freturns",
                                ct.c_uint, [ct.POINTER(prg)])

__get_angel_size = wrap_function(libc, "ketita_below__get_angel_size",
                                ct.c_uint, [ct.POINTER(prg), 
                                                ct.c_uint])

__set_all_angels = wrap_function(libc, "ketita_below__set_all_angels",
                                ct.c_int, [ct.POINTER(prg),
                                                ct.POINTER(ct.c_double)])

def blw_free(bf):
        __free(bf)

def blw_load(filename = "dummy"):
        c_name = ct.c_char_p(str.encode(filename))
        bf = __load(c_name)
        assert (bool(bf) == True ), "Loading of Below file "+filename+" failed."
        return bf

def blw_help_file(bf):
        __help_file(bf)

def blw_get_prog(bf, prog_name = "blah"):
        prg_name = ct.c_char_p(str.encode(prog_name))
        this_prg = __get(bf, prg_name)
        error = "Retrieving the Below program "+prog_name+" failed."
        assert (bool(this_prg) == True), error
        return this_prg

def blw_free_prog(prg):
        __free_prog(prg)

def blw_help_prog(tmp_prg):
        __help_prog(tmp_prg)

def blw_setup_prog(p, angels, freturns):
        n_angels = len(angels)
        n_freturns = len(freturns)
        c_n_angels = __get_num_angels(p)
        _sum_lgth_angels = 0
        for i in range(c_n_angels):
                lgth = __get_angel_size(p, i)
                error = "Angel vector {} has invalid length -- weird".format(i)
                assert (lgth != 0), error
                _sum_lgth_angels += lgth
        
        error = "The given angels vector has wrong length"        
        assert (n_angels == c_n_angels or n_angels == _sum_lgth_angels), error

        error = "The given freturns vector has wrong length"
        assert (n_freturns == __get_num_freturns(p)), error
        
        if n_angels == c_n_angels:
                for i in range(n_angels):
                        ok = __set_angel_vec(p, i, angels[i])
                        error = "There has been a weird problem with the angels"                        
                        assert (ok != 0), error
        else: 
                ok = __set_all_angels(p, angels)
                error = "There has been a weird problem with the angels"
                assert ( ok != 0 ), error
        cb_args = [ct.POINTER(ct.c_void_p), ct.c_ulonglong, ct.c_ulong]
        ccb = ct.CFUNCTYPE(ct.c_double, *cb_args)

        for i in range(n_freturns):
                ok = __set_freturn(p, i , ccb(freturns[i]), None)
                assert (ok != 0), "There has been a weird problem with the freturns"

def create_exp(n):
        myarr = ct.c_double * n
        return myarr(0.0)

def blw_run_prog(p, iter, expvals):
        ok = __run_prog(p, iter, expvals)
        assert ( ok == 0 ), err_string[ok]

#bf = load_file("edaf")
#help_file(bf)
#blah = get_prog(bf, "f")
#help_prog(blah)
