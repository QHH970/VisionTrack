import os
import sys
import ctypes
site = os.path.join(sys.prefix, 'Lib', 'site-packages', 'PyQt5')
qtcore = os.path.join(site, 'Qt5', 'bin', 'Qt5Core.dll')
print('python exe:', sys.executable)
print('platform:', sys.platform)
print('bits:', sys.maxsize > 2**32)
print('Qt5Core exists:', os.path.exists(qtcore), qtcore)
try:
    ctypes.WinDLL(qtcore)
    print('Qt5Core loaded successfully via WinDLL')
except Exception as e:
    print('Qt5Core load failed:', type(e).__name__, e)
try:
    for dep in ['vcruntime140.dll', 'msvcp140.dll', 'msvcp140_1.dll']:
        path = os.path.join(site, 'Qt5', 'bin', dep)
        print(dep, 'exists', os.path.exists(path), path)
except Exception as e:
    print('dep check failed:', e)
print('PATH length:', len(os.environ.get('PATH', '')))
print('PATH contains Qt bin:', any('PyQt5\\Qt5\\bin' in p for p in os.environ.get('PATH', '').split(os.pathsep)))
