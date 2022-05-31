#!/usr/bin/env python3
import subprocess

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
import os
import urllib
import shutil


ENHSP_dst = './up_fmap/FMAP'
ENHSP_PUBLIC = 'fmap'
#COMPILE_CMD = './compile'
ENHSP_TAG = 'master'
ENHSP_REPO = 'https://bitbucket.org/altorler/fmap'

long_description = \
    """============================================================
    UP_FMAP
 ============================================================
"""


def install_ENHSP():
    subprocess.run(['git', 'clone', '-b', ENHSP_TAG, ENHSP_REPO])
    shutil.move(ENHSP_PUBLIC, ENHSP_dst)
    curr_dir = os.getcwd()
    os.chdir(ENHSP_dst)
    #subprocess.run(COMPILE_CMD)
    os.system('mkdir fmap-dist')
    #os.system('cp -r libs/ enhsp-dist/')
    os.system('cp FMAP.jar fmap-dist/')
    os.chdir(curr_dir)


class InstallENHSP(build_py):
    """Custom install command."""

    def run(self):
        install_ENHSP()
        build_py.run(self)


class InstallENHSPdevelop(develop):
    """Custom install command."""

    def run(self):
        install_ENHSP()
        develop.run(self)


setup(name='up_fmap',
      version='0.0.1',
      description='up_fmap',
      author='Alejandro Torreño, Eva Onaindia and Oscar Sapena',
      author_email='onaindia@dsic.upv.es',
      packages=['up_fmap'],
      package_data={
          "": ["FMAP/FMAP.jar"],
      },
      cmdclass={
          'build_py': InstallENHSP,
          'develop': InstallENHSPdevelop,
      },
      license='APACHE')
