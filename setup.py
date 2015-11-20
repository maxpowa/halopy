# coding=utf-8
"""
Copyright 2015, Max Gurela
Licensed under the Eiffel Forum License 2
"""
from setuptools import setup

with open('requirements.txt') as requirements_file:
    requirements = [req for req in requirements_file.readlines()]

setup(
    name='halopy',
    version='0.3',
    description='Halo 5 API wrapper for python',
    url='https://github.com/maxpowa/halopy',
    author='Max Gurela',
    author_email='maxpowa@outlook.com',
    license='Eiffel Forum License 2',
    packages=['halopy'],
    install_requires=requirements
)
