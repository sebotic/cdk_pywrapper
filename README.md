## Python Wrapper for the Chemistry Development kit

### tl;dr
* A Python wrapper for the Chemistry Development Kit (CDK), which is written in Java
* Primary purpose: 
  * Generate diverse chemical compound identifiers (SMILES, InChI).
  * Inter-convert between these identifiers.
  * Integration with chem
* Fully compatible with Python 3.x.

### Motivation
Cheminformatics only has a small number of open source tools, e.g. [OpenBabel](http://openbabel.org), the 
[Chemistry Development Kit](https://github.com/cdk) and [RDKit](https://www.rdkit.org/).

Every framework has its pros and cons, e.g. OpenBabel has issues with InChI generation from SMILES.

CDK lacks the ability to be used with Python, while Python has become the indispensable programming language for data science, also in cheminformatics and computational biology.

Also, all three frameworks lack integration with databases.

### Installation

Before installing cdk_pywrapper, make sure to have a Java JDK available on your system, e.g. [OpenJDK](https://openjdk.org/).

Then, you can install from the repository directly.

```bash
# Create Python virtual environment named 'cdk_pywrapper'
python3 -m venv ./cdk_pywrapper
source ./cdk_pywrapper/bin/activate

# Clone repository from GitHub
git clone https://github.com/sebotic/cdk_pywrapper.git
cd cdk_pywrapper

# Install into created venv
pip install .

```

This will install the package on your local system. Setuptools will take care of downloading the CDK.jar and it will build the cdk_bridge.java.
So after that, cdk_pywrapper should be ready to use, like in the example below.

cdk_pywrapper was tested on Linux and MacOS, but it should also work on Windows.

### Example

```python
from cdk_pywrapper.cdk_pywrapper import Compound

smiles = 'CCN1C2=CC=CC=C2SC1=CC=CC=CC3=[N+](C4=CC=CC=C4S3)CC.[I-]'
cmpnd = Compound(compound_string=smiles, identifier_type='smiles')
ikey = cmpnd.get_inchi_key()
print(ikey)

```
Output: 'MNQDKWZEUULFPX-UHFFFAOYSA-M'


