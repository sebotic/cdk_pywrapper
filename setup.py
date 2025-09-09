import platform
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py
from subprocess import check_output
import subprocess
import py4j
import os
import wget
import zipfile

cdk_version = 'cdk-2.11'

class CustomBuildPy(_build_py):
    def run(self):
        host_os = platform.system()
        #cdk_version = 'cdk-2.11'
        cdk_jar_path = os.path.join('.', 'cdk_pywrapper', 'cdk')
        cdk_jar = os.path.join(cdk_jar_path, cdk_version + '.jar')


        # Download UNII_Data.zip if not present and extract
        data_dir = os.path.join('.', 'cdk_pywrapper', 'data')
        unii_zip_url = 'https://precision.fda.gov/uniisearch/archive/latest/UNII_Data.zip'
        unii_zip_path = os.path.join(data_dir, 'UNII_Data.zip')
        extracted_file = os.path.join(data_dir, 'UNII_Records_18Aug2025.txt')
        if not os.path.exists(extracted_file):
            os.makedirs(data_dir, exist_ok=True)
            if not os.path.exists(unii_zip_path):
                print('Downloading UNII_Data.zip...')
                wget.download(unii_zip_url, out=unii_zip_path)
            
            print('Extracting UNII_Data.zip...')
            with zipfile.ZipFile(unii_zip_path, 'r') as zip_ref:
                zip_ref.extractall(data_dir)
            print('Extraction complete.')

        # Download ligands.csv from Guide to Pharmacology if not present
        gtp_url =  'https://www.guidetopharmacology.org/DATA/ligands.csv'
        gtp_path = os.path.join(data_dir, 'ligands.csv')
        if not os.path.exists(gtp_path):
            print('Downloading ligands.csv from Guide to Pharmacology...')
            wget.download(gtp_url, out=gtp_path)
            print('Download complete.')


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
    package_data = {
        "cdk_pywrapper": [
            "data/*.txt", 
            "data/*.csv",
        ],
    },
    author='Sebastian Burgstaller-Muehlbacher',
    author_email='sburgs@scripps.edu',
    description='Python wrapper for the CDK (Chemistry Development Kit)',
    license='AGPLv3',
    keywords='chemistry, CDK, Chemistry Development Kit',
    url=REPO_URL,
    # packages=find_packages(),
    packages=['cdk_pywrapper'],
    include_package_data=True,
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
