import os
import sys
site = os.path.join(sys.prefix, 'Lib', 'site-packages', 'PyQt5')
qt_bin = os.path.join(site, 'Qt5', 'bin')
print('qt_bin=', qt_bin)
os.environ['PATH'] = qt_bin + os.pathsep + os.environ.get('PATH', '')
print('PATH starts with qt_bin:', os.environ['PATH'].startswith(qt_bin))
try:
    from PyQt5 import QtCore
    print('import QtCore OK', QtCore)
except Exception as e:
    print('import failed', type(e).__name__, e)
