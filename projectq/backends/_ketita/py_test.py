#test for python

import py_ketita_inter as ket
import ctypes
angels = []
myarr = ctypes.c_double * 2
myarr2 = ctypes.c_double * 3
angels.append(myarr(2.3, 5.77))
angels.append(myarr2(1.1, 3.3, 8.8))
 
def cb(data, meas):
    print(meas)
    return meas * 1.0

ccb = ctypes.CFUNCTYPE(ctypes.c_double, ctypes.POINTER(ctypes.c_void_p), ctypes.c_ulonglong)
callback = ccb(cb)


bf = ket.blw_load("dummy")
f = ket.blw_get_prog(bf, "f")

ket.blw_setup_prog(f, angels, [callback])

expvals = (ctypes.POINTER(ctypes.c_double) * 2)
ret1 = ctypes.c_double(1.1)
ret2 = ctypes.c_double(2.2)
myexp = expvals(ctypes.pointer(ret1), ctypes.pointer(ret2))
for i in range(1):
        ket.blw_run_prog(f, ctypes.c_ulong(8), myexp)
        print(ret1)

