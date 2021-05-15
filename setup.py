#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shlex

from glob import glob

from setuptools import setup
from setuptools.command.test import test as TestCommand


with open('README.md', 'r') as f:
    readme = f.read()

name = 'texel-assignment'

try:
    tag = subprocess.check_output([
        'git',
        'describe',
        '--abbrev=0',
        '--tags',
    ]).strip().decode()
except subprocess.CalledProcessError as e:
    print(e.output)
    tag = 'v0.0.0'

version = tag[1:]


class PyTest(TestCommand):

    user_options = [('pytest-args=', 'a', "Arguments to pass into py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest

        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


class Pep8(TestCommand):

    def run_tests(self):
        from pycodestyle import StyleGuide

        package_dir = os.path.dirname(os.path.abspath(__file__))
        sources = glob(os.path.join(package_dir, 'texel_assignment', '*.py'))
        style_guide = StyleGuide(paths=sources)
        options = style_guide.options

        report = style_guide.check_files()
        report.print_statistics()

        if report.total_errors:
            if options.count:
                sys.stderr.write(str(report.total_errors) + '\n')
            sys.exit(1)


setup(
    name=name,
    version=version,
    description='Detect frozen frames in video using ffmpeg',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='olegsivokon@gmail.com',
    url='https://github.com/wvxvw/texel-assignment',
    license='MIT',
    packages=['texel_assignment'],
    cmdclass={
        'test': PyTest,
        'lint': Pep8,
    },
    tests_require=['pytest', 'pycodestyle'],
    install_requires=[
        'pandas',
        'numpy',
    ],
    scripts=[
        'bin/texel-detect-frozen',
    ],
)
