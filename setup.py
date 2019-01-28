#! /usr/bin/env python

from setuptools import setup, find_packages
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='add_name',
    version='0.0.1',
    author='add_authoer',
    author_email='',
    description='',
    namespace_package=[''],
    long_description=read('README.rst'),
    packages=find_packages(),
    package_dir={'reegis_tools': 'reegis'},  # todo: check
    install_requires=[
        'pandas',
        'requests',
        'windpowerlib >= 0.1.0',
        'pvlib'])
