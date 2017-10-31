# from distutils.core import setup
from setuptools import setup
import platform

setup(
    name='mountwizzard',
    version='2.5.17.2',
    packages=[
        'mountwizzard',
        'mountwizzard.analyse',
        'mountwizzard.astrometry',
        'mountwizzard.automation',
        'mountwizzard.baseclasses',
        'mountwizzard.camera',
        'mountwizzard.dome',
        'mountwizzard.environment',
        'mountwizzard.gui',
        'mountwizzard.indi',
        'mountwizzard.modeling',
        'mountwizzard.mount',
        'mountwizzard.relays',
        'mountwizzard.remote',
        'mountwizzard.widgets'
    ],
    python_requires='~=3.5',
    install_requires=[
        # 'PyQt5>=5.6',                   # problem on ubuntu, can't be installed via pip, should be done with apt-get install
        'matplotlib>=1.5.3',            # sudo apt-get install libfreetype6-dev might be needed
        # 'pypiwin32>=219',             # not useful for linux
        'pyfits>=3.4',
        'wakeonlan>=0.2.2',
        'requests'
    ]
    + (['PyQt5>=5.6'] if "Darwin" == platform.system() else [])
    + (['PyQt5>=5.6'] if "Windows" == platform.system() else [])
    + (['pypiwin32>=219'] if "Windows" == platform.system() else [])
    ,
    url='https://pypi.python.org/pypi/mountwizzard',
    license='APL 2.0',
    author='mw',
    author_email='michael@wuertenberger.org',
    description='tooling for a 10micron mount',
)

if platform.system() == 'Linux':
    print('#############################################')
    print('### Important hint:                       ###')
    print('### you have to install PYQT5 manually    ###')
    print('### sudo apt-get install pyqt5            ###')
    print('### There might be the need to install    ###')
    print('### libfreetype6-dev manually as well     ###')
    print('### sudo apt-get install libfreetype6-dev ###')
    print('#############################################')

