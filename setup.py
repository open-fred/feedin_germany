#! /usr/bin/env python

from setuptools import setup
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='feedin_germany',
    version='0.0.1',
    author='oemof developing group',
    author_email='',
    description='Creating time series of renewable power plants for regions in Germany.',
    packages=['feedin_germany'],
    long_description=read('README.rst'),
    install_requires=[
        'pandas >= 0.13.1',
        'feedinlib >= 0.0.12',
	'geopandas',
        'sqlalchemy',
	'oedialect',
        'rtree']) # todo: adapt
