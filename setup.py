#! /usr/bin/env python


import os

from setuptools import find_packages, setup


ETC = os.path.join("etc", "libmorse")
RESOURCE = os.path.join("res", "libmorse")


def read(fpath):
    with open(os.path.join(os.path.dirname(__file__), fpath)) as stream:
        return stream.read()


def get_requirements(path="requirements.txt"):
    data = read(path)
    lines = []
    for line in data.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("-r"):
            new_path = line[2:].strip()
            lines.extend(get_requirements(path=new_path))
            continue
        lines.append(line)
    return lines


setup(
    name="libmorse",
    version="0.2.0",
    description="Convert timed signals into alphabet.",
    long_description=read("README.md"),
    url="https://github.com/cmin764/libmorse",
    license="MIT",
    author="Cosmin Poieana",
    author_email="cmin764@gmail.com",
    packages=find_packages(),
    scripts=[os.path.join("bin", "libmorse")],
    include_package_data=True,
    install_requires=get_requirements(),
    test_suite="tests",
    data_files = [
        (
            ETC,
            map(
                lambda name: os.path.join(ETC, name),
                [
                    "libmorse.conf",
                ]
            )
        ),
        (
            RESOURCE,
            map(
                lambda name: os.path.join(RESOURCE, name),
                [
                    "basic.mor",
                ]
            )
        ),
    ],
)
