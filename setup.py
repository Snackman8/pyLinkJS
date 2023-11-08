#!/usr/bin/env python

import os
from setuptools import setup

def get_version():
    f = open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pylinkjs/__init__.py'), 'r')
    s = f.read()
    f.close()
    for line in s.split('\n'):
        if line.startswith('__version__'):
            version = line.partition('=')[2].strip()
            if version[0] == '"':
                version = version.split('"')[1]
            if version[0] == "'":
                version = version.split("'")[1]
            break
    return version

setup(name='pylinkjs',
      version=get_version(),
      description='Python Javascript Bridge',
      author='Lawrence Yu',
      author_email='lawy888@gmail.com',
      url='https://github.com/Snackman8/pyLinkJS',
      packages=['pylinkjs', 'pylinkjs.plugins', 'pylinkjs.utils'],
      package_data={'': ['*.js', 'plugins/*.html']},
      include_package_data=True,
      install_requires=["tornado", "playwright"],
      )
