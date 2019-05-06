import platform
from setuptools import setup, find_packages
from subprocess import check_output
import subprocess
import py4j
import os
import wget

host_os = platform.system()

cdk_version = 'cdk-2.2'
cdk_jar_path = os.path.join('.', 'cdk_pywrapper', 'cdk')
cdk_jar = os.path.join(cdk_jar_path, cdk_version + '.jar')

fn = wget.download('https://github.com/cdk/cdk/releases/download/{0}/{0}.jar'.format(cdk_version), out=cdk_jar_path)
print('successfully downloaded', fn)

if host_os == 'Linux' or host_os == 'Darwin':
    py4j_path = os.path.join(*py4j.__path__[0].split('/')[:-4])
    py4j_jar_path = os.path.join('/', py4j_path, 'share', 'py4j', 'py4j' + py4j.__version__ + '.jar')
    cp_sep = ':'

    subprocess.check_call([
        'javac ' +
        ' -cp ' +
        ' {}{}{} '.format(py4j_jar_path,
                          cp_sep,
                          cdk_jar) +
        os.path.join('.', 'cdk_pywrapper', 'cdk', 'cdk_bridge.java')
    ],
        shell=True)

if host_os == 'Windows':
    cp_sep = ';'
    drive, path = os.path.splitdrive(py4j.__path__[0])
    py4j_path = os.path.join(drive + '\\', *path.split('\\')[:-3])
    py4j_jar_path = os.path.join(py4j_path, 'share', 'py4j', 'py4j' + py4j.__version__ + '.jar')

    subprocess.check_call([
        'javac',
        '-cp',
        '{}{}{}'.format(py4j_jar_path,
                        cp_sep,
                        cdk_jar),
        os.path.join('.', 'cdk_pywrapper', 'cdk', 'cdk_bridge.java')
    ],
        shell=True)

MAJOR_VERSION = 0
MINOR_VERSION = 0
MICRO_VERSION = 1

REPO_URL = 'https://github.com/sebotic/cdk_pywrapper'

setup(
    name='cdk_pywrapper',
    version="{}.{}.{}".format(MAJOR_VERSION, MINOR_VERSION, MICRO_VERSION),
    data_files=[("share/cdk", [cdk_jar, './cdk_pywrapper/cdk/CDKBridge.class',
                               './cdk_pywrapper/cdk/SearchHandler.class'])],
    author='Sebastian Burgstaller-Muehlbacher',
    author_email='sburgs@scripps.edu',
    description='Python wrapper for the CDK (Chemistry Development Kit)',
    license='AGPLv3',
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
