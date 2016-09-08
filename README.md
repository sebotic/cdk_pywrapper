## Python Wrapper for the Chemistry Development kit

### tl;dr
* A Python wrapper for the CDK (which is written in Java)
* Primary purpose: 
  * Generate diverse chemical compound identifiers (SMILES, InChI)
  * Inter-convert between these identifiers
* Fully compatible to Python 3

### Motivation
The chemistry world only has a small number of open tools, e.g. [OpenBabel](http://openbabel.org) and the 
[Chemistry Development Kit](cdk.sourceforge.net) ([github](https://github.com/cdk)). 

I have been using OpenBabel for some time now, and it is a great tool offering many options,
I found several issues which make it hard to use:
* Generating InChI (keys) from SMILES often either does not work or struggles with stereochemistry.
* InChI cannot be used as input format.


