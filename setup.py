import os
from setuptools import setup, find_packages
from subprocess import check_output
import subprocess
import py4j
import os

py4j_path = os.path.join(*py4j.__path__[0].split('/')[:-4])
py4j_jar_path = os.path.join('/', py4j_path, 'share', 'py4j', 'py4j' + py4j.__version__ + '.jar')

cdk_version = 'cdk-2.1.1'
cdk_jar_path = './cdk_pywrapper/cdk/'
cdk_jar = cdk_jar_path + cdk_version + '.jar'

MAJOR_VERSION = 0
MINOR_VERSION = 0
MICRO_VERSION = 1

REPO_URL = 'https://github.com/sebotic/cdk_pywrapper'

subprocess.check_call(["wget https://github.com/cdk/cdk/releases/download/{0}/{0}.jar "
                 "--directory-prefix={1}".format(cdk_version, cdk_jar_path)], shell=True)

subprocess.check_call(["javac -cp '{}:{}' ./cdk_pywrapper/cdk/cdk_bridge.java".format(py4j_jar_path,
                                                                                      cdk_jar)], shell=True)

setup(
    name='cdk_pywrapper',
    version="{}.{}.{}".format(MAJOR_VERSION, MINOR_VERSION, MICRO_VERSION),
    data_files=[("share/cdk", [cdk_jar, './cdk_pywrapper/cdk/CDKBridge.class'])],
    author='Sebastian Burgstaller-Muehlbacher',
    author_email='sburgs@scripps.edu',
    description='Python wrapper for the CDK (Chemistry Development Kit)',
    license='MIT',
    keywords='chemistry, CDK, Chemistry Development Kit',
    url=REPO_URL,
    # packages=find_packages(),
    packages=['cdk_pywrapper'],
    # include_package_data=True,
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
