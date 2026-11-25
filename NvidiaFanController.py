#!/usr/bin/env python3
import ctypes as c
import signal
import sys
import time

INTERVAL = 5
HYSTERESIS = 3
STEPS = [(-100, 35), (50, 45), (60, 65), (70, 80), (75, 90)]

nv = c.CDLL('libnvidia-ml.so.1')

def bind(name, args):
    fn = getattr(nv, name)
    fn.argtypes = args
    fn.restype = c.c_int
    return fn

errstr = nv.nvmlErrorString
errstr.argtypes = [c.c_int]
errstr.restype = c.c_char_p

def check(rc, operation):
    if rc:
        raise RuntimeError(f'{operation}: {errstr(rc).decode()}')

init = bind('nvmlInit_v2', [])
shutdown = bind('nvmlShutdown', [])
get_handle = bind('nvmlDeviceGetHandleByIndex_v2', [c.c_uint, c.POINTER(c.c_void_p)])
get_num_fans = bind('nvmlDeviceGetNumFans', [c.c_void_p, c.POINTER(c.c_uint)])
get_temp = bind('nvmlDeviceGetTemperature', [c.c_void_p, c.c_uint, c.POINTER(c.c_uint)])
set_fan = bind('nvmlDeviceSetFanSpeed_v2', [c.c_void_p, c.c_uint, c.c_uint])
reset_fan = bind('nvmlDeviceSetDefaultFanSpeed_v2', [c.c_void_p, c.c_uint])
get_speed = bind('nvmlDeviceGetFanSpeed_v2', [c.c_void_p, c.c_uint, c.POINTER(c.c_uint)])

running = True

def stop(*_):
    global running
    running = False

signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

def main():
    mode = sys.argv[1] if len(sys.argv) == 2 else 'run'
    if mode not in ('run', '--test', '--auto') or len(sys.argv) > 2:
        sys.exit('Usage: rtx3090-fancurve.py [--test | --auto]')
    check(init(), 'nvmlInit')
    gpu = c.c_void_p()
    try:
        check(get_handle(0, c.byref(gpu)), 'GPU 0')
        fans = c.c_uint()
        check(get_num_fans(gpu, c.byref(fans)), 'GetNumFans')
        if not fans.value:
            raise RuntimeError('GPU reports no controllable fans')

        def apply(speed):
            for fan in range(fans.value):
                check(set_fan(gpu, fan, speed), f'SetFanSpeed fan={fan}')

        def restore():
            failed = False
            for fan in range(fans.value):
                rc = reset_fan(gpu, fan)
                if rc:
                    print(f'WARNING: auto restore fan={fan}: {errstr(rc).decode()}', flush=True)
                    failed = True
            if failed:
                raise RuntimeError('Could not restore automatic fan control')

        if mode == '--auto':
            restore()
            print('Automatic fan control restored', flush=True)
            return

        try:
            if mode == '--test':
                apply(80)
                time.sleep(5)
                for fan in range(fans.value):
                    speed = c.c_uint()
                    check(get_speed(gpu, fan, c.byref(speed)), f'GetFanSpeed fan={fan}')
                    print(f'Fan {fan}: {speed.value}% (requested 80%)', flush=True)
                    if not 60 <= speed.value <= 100:
                        raise RuntimeError('Fan did not reach expected speed; service will not be enabled')
                return

            index = None
            last_speed = None
            while running:
                temperature = c.c_uint()
                check(get_temp(gpu, 0, c.byref(temperature)), 'GetTemperature')
                t = temperature.value
                target = max(i for i, (threshold, _) in enumerate(STEPS) if t >= threshold)
                if index is None:
                    index = target
                elif target > index:
                    index = target
                elif target < index:
                    while index > target and t <= STEPS[index][0] - HYSTERESIS:
                        index -= 1
                desired = STEPS[index][1]
                if desired != last_speed:
                    apply(desired)
                    last_speed = desired
                    print(f'GPU {t}C -> fan {desired}% ({fans.value} fans)', flush=True)
                time.sleep(INTERVAL)
        finally:
            restore()
            print('Automatic fan control restored', flush=True)
    finally:
        check(shutdown(), 'nvmlShutdown')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sys.exit(str(e))
