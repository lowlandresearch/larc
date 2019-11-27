from pathlib import Path

from setuptools import setup, find_packages

HERE = Path(__file__).resolve().parent

def version():
    return Path(HERE, 'VERSION').read_text()

long_description = Path(HERE, 'README.md').resolve().read_text()

setup(
    name='larc',
    packages=find_packages(
        exclude=['tests'],
    ),
    package_dir={
        'larc': 'larc',
    },

    install_requires=[
        'toolz',
        'multipledispatch',
        'pyrsistent',
        'networkx',
        'coloredlogs',
        'gevent',
        'pyyaml',
        'ruamel.yaml',
        'ipython',
        'click',
        'pyperclip',
        'python-nmap',
        'tcping',
        'ipparser',
        'dnspython',
        'paramiko',
        'xmljson',
        'python-dateutil',
        'jmespath',
    ],

    version=version(),
    description=('Collection of helper functions and general utilities'
                 ' used across various LARC projects'),
    long_description=long_description,

    url='https://github.org/lowlandresearch/larc',

    author='Lowland Applied Research Company (LARC)',
    author_email='dogwynn@lowlandresearch.com',

    license='GPLv3',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPLv3 License',
        'Programming Language :: Python :: 3.7',
    ],

    zip_safe=False,

    keywords=('utilities functional toolz'),

    scripts=[
    ],

    entry_points={
        'console_scripts': [
        ],
    },
)
