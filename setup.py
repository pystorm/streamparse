#!/usr/bin/env python
"""
Copyright 2014-2020 Parsely, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import re

from setuptools import setup, find_packages

# Get version without importing, which avoids dependency issues
def get_version():
    with open("streamparse/version.py") as version_file:
        return re.search(
            r"""__version__\s+=\s+(['"])(?P<version>.+?)\1""", version_file.read()
        ).group("version")


def readme():
    """ Returns README.rst contents as str """
    with open("README.rst") as f:
        return f.read()


install_requires = [
    l.split("#")[0].strip()
    for l in open("requirements.txt").readlines()
    if not l.startswith(("#", "-"))
]

tests_require = ["graphviz", "pytest"]

setup(
    name="streamparse",
    version=get_version(),
    author="Parsely, Inc.",
    author_email="hello@parsely.com",
    url="https://github.com/Parsely/streamparse",
    description=(
        "streamparse lets you run Python code against real-time "
        "streams of data. Integrates with Apache Storm."
    ),
    long_description=readme(),
    license="Apache License 2.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "sparse = streamparse.cli.sparse:main",
            "streamparse = streamparse.cli.sparse:main",
            "streamparse_run = streamparse.run:main",
        ]
    },
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        "test": tests_require,
        "all": install_requires + tests_require,
        "docs": ["sphinx"] + tests_require,
    },
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
