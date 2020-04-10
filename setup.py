import re
from pathlib import Path

from setuptools import setup, find_packages

HERE = Path(__file__).resolve().parent

version_re = re.compile(r"^__version__\s*=\s*'(?P<version>.*)'$", re.M)
def version():
    match = version_re.search(Path('larc/__init__.py').read_text())
    if match:
        return match.groupdict()['version'].strip()
    return '0.0.1'

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
        'netifaces',
    ],

    version=version(),
    description=('Collection of helper functions and general utilities'
                 ' used across various LARC projects'),
    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.org/lowlandresearch/larc',

    author='Lowland Applied Research Company (LARC)',
    author_email='dogwynn@lowlandresearch.com',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],

    zip_safe=False,

    keywords=('utilities functional toolz'),

    scripts=[
    ],

    entry_points={
        'console_scripts': [
            'diffips=larc.cli.ips:diff_ips',
            'intips=larc.cli.ips:int_ips',
            'difflines=larc.cli.text:diff_lines',
            'intlines=larc.cli.text:int_lines',
            'sortips=larc.cli.ips:sort_ips',
            'getips=larc.cli.ips:get_ips',
            'getsubnets=larc.cli.ips:get_subnets',
            'zpad=larc.cli.ips:zpad_ips',
            'unzpad=larc.cli.ips:unzpad_ips',
            'larc-render=larc.cli.text:render_templates'
        ],
    },
)
