import os
import sys
import glob
site = os.path.join(sys.prefix, 'Lib', 'site-packages', 'PyQt5')
print('site=' + site)
print('exists=' + str(os.path.isdir(site)))
print('DLLS:')
for f in glob.glob(os.path.join(site, '**', '*.dll'), recursive=True):
    print(f)
print('PYDs:')
for f in glob.glob(os.path.join(site, '**', '*.pyd'), recursive=True):
    print(f)
print('PATH=' + os.environ.get('PATH', ''))
