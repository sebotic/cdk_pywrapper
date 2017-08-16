import os
from setuptools import setup, find_packages
from subprocess import check_output

MAJOR_VERSION = 0
MINOR_VERSION = 0
MICRO_VERSION = 1

REPO_URL = 'https://github.com/sebotic/cdk_pywrapper'

setup(
    name='cdk_pywrapper',
    version="{}.{}.{}".format(MAJOR_VERSION, MINOR_VERSION, MICRO_VERSION),
    author='Sebastian Burgstaller-Muehlbacher',
    author_email='sburgs@scripps.edu',
    description='Python wrapper for the CDK (Chemistry Development Kit)',
    license='MIT',
    keywords='chemistry, CDK, Chemistry Development Kit',
    url=REPO_URL,
    # packages=find_packages(),
    packages=['cdk_pywrapper'],
    include_package_data=True,
    # long_description=read('README.md'),
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2.7",
        "Development Status :: 4 - Beta",
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Intended Audience :: Science/Research",
        "Topic :: Utilities",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    install_requires=[
        'py4j'
    ],
)
