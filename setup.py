import platform
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py
from subprocess import check_output
import subprocess
import py4j
import os
import wget

cdk_version = 'cdk-2.11'

class CustomBuildPy(_build_py):
    def run(self):
        host_os = platform.system()
        #cdk_version = 'cdk-2.11'
        cdk_jar_path = os.path.join('.', 'cdk_pywrapper', 'cdk')
        cdk_jar = os.path.join(cdk_jar_path, cdk_version + '.jar')

        # Download CDK jar if not present
        if not os.path.exists(cdk_jar):
            os.makedirs(cdk_jar_path, exist_ok=True)
            fn = wget.download(
                f'https://github.com/cdk/cdk/releases/download/{cdk_version}/{cdk_version}.jar',
                out=cdk_jar_path
            )
            print('Successfully downloaded', fn)

        # Compile Java bridge
        if host_os in ('Linux', 'Darwin'):
            py4j_path = os.path.join(*py4j.__path__[0].split('/')[:-4])
            py4j_jar_path = os.path.join('/', py4j_path, 'share', 'py4j', f'py4j{py4j.__version__}.jar')
            cp_sep = ':'
            javac_cmd = (
                f'javac -cp "{py4j_jar_path}{cp_sep}{cdk_jar}" '
                f'{os.path.join(".", "cdk_pywrapper", "cdk", "cdk_bridge.java")}'
            )
            subprocess.check_call(javac_cmd, shell=True)
        elif host_os == 'Windows':
            cp_sep = ';'
            drive, path = os.path.splitdrive(py4j.__path__[0])
            py4j_path = os.path.join(drive + '\\', *path.split('\\')[:-3])
            py4j_jar_path = os.path.join(py4j_path, 'share', 'py4j', f'py4j{py4j.__version__}.jar')
            javac_cmd = [
                'javac',
                '-cp',
                f'{py4j_jar_path}{cp_sep}{cdk_jar}',
                os.path.join('.', 'cdk_pywrapper', 'cdk', 'cdk_bridge.java')
            ]
            subprocess.check_call(javac_cmd, shell=True)
        super().run()

MAJOR_VERSION = 0
MINOR_VERSION = 0
MICRO_VERSION = 2

REPO_URL = 'https://github.com/sebotic/cdk_pywrapper'

setup(
    name='cdk_pywrapper',
    version="{}.{}.{}".format(MAJOR_VERSION, MINOR_VERSION, MICRO_VERSION),
    data_files=[("share/cdk", [
        f'./cdk_pywrapper/cdk/{cdk_version}.jar',
        './cdk_pywrapper/cdk/CDKBridge.class',
        './cdk_pywrapper/cdk/SearchHandler.class'
    ])],
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
        "Development Status :: 4 - Beta",
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Intended Audience :: Science/Research",
        "Topic :: Utilities",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    install_requires=[
        'py4j', 'wget'
    ],
    cmdclass={'build_py': CustomBuildPy},
)
