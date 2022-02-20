# -*- coding: utf-8 -*-
from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='eazyctrl',

    version='0.4',

    description='Monitoring and controlling Easy Controls KWL (air exchanger)'\
        'devices via Modbus/TCP.',
    long_description=long_description,
    long_description_content_type='text/x-rst',

    url='https://github.com/baradi09/eazyctrl',

    author='Bálint Aradi',
    author_email='baradi09@gmail.com',

    license='BSD',

    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Topic :: Home Automation',
    ],

    keywords='easycontrols kwl air-exchanger',

    package_dir={'': 'src'},
    py_modules=['eazyctrl'],

    entry_points={
        'console_scripts': [
            'eazyctrl=eazyctrl:run_eazyctrl',
        ],
    },
)
