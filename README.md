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


## MCP server
I also added a MCP server now which makes use of the functions of cdk_pywrapper and also integrates with UNII, Chembl and Guide to Pharmacology data.

It requires a LLM capable of tool use.

Key features:
* Allows a LLM to search for a compound by name.
* Allows a LLM to get the corresponding SMILES string.
* Allows a LLM to get the name associated with a structure (SMILES or InChI, will lookup Chembl).
* Allows for convertions between SMILES and InChI and also InChI key.
* Allows for calculation of basic compound properties (e.g. molecular mass).
* Allows for creation of an SVG of the compound structure.

### Installation of the MCP
Most conveniently, one would install it locally as a tool, using the [uv package manager](https://docs.astral.sh/uv/).
Install uv first, according to it's instructions, then run from the repo root:

```bash
uv tool install . --force-reinstall
```

For using the MCP server, add this configuration to your respective LLM MCP configuration.
```json
  "cdk_pywrapper-mcp-server": {
    "command": "uv",
    "args": [
      "tool",
      "run",
      "--from",
      "cdk-pywrapper",
      "cdk_pywrapper-mcp-server"
    ],
    "env": {}
  }
```

### Example prompts for using the MCP tools:
```
Search for structure of compound vemurafenib.
```
Will return SMILES, InchI and Inchi key for vemurafenib.


```
Get details for compound vemurafenib.
```
Will return synonyms and compound structure.

```
Get inchi for CCOH
```
Will return the InChI for Ethanol, which is InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3

This conversion works for any valid SMILES string and can also return the InChI key.

```
Get the compound names for this smiles CC1=CN=C(C(=C1OC)C)CS(=O)C2=NC3=C(N2)C=C(C=C3)OC
```
That should return [Omeprazole](https://www.wikidata.org/wiki/Q422210). Use a modern thinking model like Google Gemini 2.5. Gemini will figure out on its own that it first needs to convert the SMILES to an InChI key and then use the Chembl tool to get the name. 
