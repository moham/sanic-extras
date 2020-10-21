import os
import setuptools
from setuptools.command.test import test as TestCommand

__version__ = None
with open("sanic_extras/__version__.py", "r") as vf:
    exec(vf.read())

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

with open("README.md", "r") as fh:
    long_description = fh.read()

kwargs_config = {
    "name": "sanic_extras",
    "version": __version__,
    "author": "Seyed Moham Mousavi",
    "author_email": "s.mohammad.msv@gmail.com",
    "description": "Extra features for Sanic web framework",
    "long_description": long_description,
    "long_description_content_type": "text/markdown",
    "url": "https://github.com/moham/sanic-extras",
    "packages": setuptools.find_packages(),
    "classifiers": [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    "python_requires": '>=3.6',
    "install_requires": [
        "sanic >= 20.6.3",
        "pydantic >= 1.6.1",
        "PyJWT >= 1.7.1",
    ]
}

setuptools.setup(**kwargs_config)
