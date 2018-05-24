## Python Wrapper for the Chemistry Development kit

### tl;dr
* A Python wrapper for the CDK (which is written in Java)
* Primary purpose: 
  * Generate diverse chemical compound identifiers (SMILES, InChI)
  * Inter-convert between these identifiers
* Fully compatible to Python 3.x

### Motivation
The chemistry world only has a small number of open tools, e.g. [OpenBabel](http://openbabel.org) and the 
[Chemistry Development Kit](cdk.sourceforge.net) ([github](https://github.com/cdk)). 

I have been using OpenBabel for some time now, and it is a great tool offering many options,
I found several issues which make it hard to use:
* Generating InChI (keys) from SMILES often either does not work or struggles with stereochemistry.
* InChI cannot be used as input format.

### Installation

```bash
git clone https://github.com/sebotic/cdk_pywrapper.git
cd cdk_pywrapper

pip install .

```

This will install the package on your local system, it will download the CDK and it will build the cdk_bridge.java.
So after that, cdk_pywrapper should be ready to use, like in the example below.

Don't forget to use e.g. sudo for global installation or pip3 for Python 3.

### Example

```python
from cdk_pywrapper.cdk_pywrapper import Compound

smiles = 'CCN1C2=CC=CC=C2SC1=CC=CC=CC3=[N+](C4=CC=CC=C4S3)CC.[I-]'
cmpnd = Compound(compound_string=smiles, identifier_type='smiles')
ikey = cmpnd.get_inchi_key()
print(ikey)

```
Output: 'MNQDKWZEUULFPX-UHFFFAOYSA-M'


