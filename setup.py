#!/usr/bin/env python3
import subprocess

from setuptools import setup  # type: ignore
from setuptools.command.build_py import build_py  # type: ignore
from setuptools.command.develop import develop  # type: ignore
import os
import urllib
import shutil


FMAP_dst = "./up_fmap/FMAP"
FMAP_PUBLIC = "fmap"
# COMPILE_CMD = './compile'
FMAP_TAG = "master"
FMAP_REPO = "https://bitbucket.org/altorler/fmap"

long_description = """============================================================
    UP_FMAP
 ============================================================
"""
isExist = os.path.exists("up_fmap")
if not isExist:
    os.system("mkdir up_fmap")


def install_FMAP():
    subprocess.run(["git", "clone", "-b", FMAP_TAG, FMAP_REPO])
    shutil.move(FMAP_PUBLIC, FMAP_dst)
    curr_dir = os.getcwd()
    os.chdir(FMAP_dst)
    # subprocess.run(COMPILE_CMD)
    os.system("rm -r out 2> /dev/null")
    os.system("rm -r fmap-dist 2> /dev/null")
    os.system("mkdir fmap-dist")
    # os.system('cp -r libs/ enhsp-dist/')
    os.system("cp FMAP.jar fmap-dist/")
    os.chdir(curr_dir)


class InstallFMAP(build_py):
    """Custom install command."""

    def run(self):
        install_FMAP()
        build_py.run(self)


class InstallFMAPdevelop(develop):
    """Custom install command."""

    def run(self):
        install_FMAP()
        develop.run(self)


setup(
    name="up_fmap",
    version="0.0.6",
    description="up_fmap",
    author="Alejandro Torreño, Eva Onaindia and Oscar Sapena",
    author_email="onaindia@dsic.upv.es",
    packages=["up_fmap"],
    package_data={"": ["FMAP/FMAP.jar"]},
    cmdclass={"build_py": InstallFMAP, "develop": InstallFMAPdevelop},
    license="APACHE",
)
