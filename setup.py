#!/usr/bin/python3
# -*- coding: utf-8 -*

import setuptools


def main():
    with open("README.md", "r") as readme_fd:
        long_description = readme_fd.read()

    setuptools.setup(
        name="ancs",
        # Should use <ver> and replace it during deploy / commit hook
        version="0.0.1",
        author="NaeiKinDus",
        author_email="naeikindus@0x2a.ninja",
        description="Home garden climate control",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://gitlab.0x2a.ninja/iot/ancs",
        packages=setuptools.find_packages(exclude=['tests']),
        classifiers=[
            "Framework :: Flask"
            "Environment :: No Input/Output (Daemon)",
            "Development Status :: 3 - Alpha",
            "Programming Language :: Python :: 3 :: Only",
            "License :: OSI Approved :: Apache Software License"
            "Operating System :: POSIX :: Linux",
            "Intended Audience :: Other Audience",
            "Topic :: Home Automation",
        ],
        python_requires='>=3.7',
        include_package_data=True,
        zip_safe=False,
    )


if __name__ == "__main__":
    main()
