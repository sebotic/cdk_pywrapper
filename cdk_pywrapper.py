import subprocess
import psutil
from py4j.java_gateway import JavaGateway
from py4j.java_gateway import GatewayParameters
import sys
import time

__author__ = 'Sebastian Burgstaller-Muehlbacher'
__license__ = 'AGPLv3'
__copyright__ = 'Sebastian Burgstaller-Muehlbacher'

if not any([True if 'CDKBridge' in p.cmdline() else False for p in psutil.process_iter()]):
    # compile and start py4j server
    subprocess.call(["javac -cp '/usr/share/py4j/py4j0.10.2.1.jar:./cdk/cdk-1.5.13.jar' ./cdk/cdk_bridge.java"], shell=True)
    p = subprocess.Popen(["java -cp './cdk:/usr/share/py4j/py4j0.10.2.1.jar:./cdk/cdk-1.5.13.jar' CDKBridge"], shell=True)

    # wait 5 sec to start up JVM and server
    time.sleep(5)

# connect to the JVM
gateway = JavaGateway(gateway_parameters=GatewayParameters(auto_convert=True))

# shorten paths
cdk = gateway.jvm.org.openscience.cdk
java = gateway.jvm.java
javax = gateway.jvm.javax

# map exceptions
InvalidSmilesException = cdk.exception.InvalidSmilesException
CDKException = cdk.exception.CDKException
NullPointerException = java.lang.NullPointerException


class Compound(object):
    def __init__(self, compound_string, identifier_type):
        self.compound_string = compound_string
        self.identifier_type = identifier_type
        self.mol_container = None
        self.inchi_factory = cdk.inchi.InChIGeneratorFactory.getInstance()

        allowed_types = ['smiles', 'inchi']

        if self.identifier_type not in allowed_types:
            raise ValueError('Not a valid identifier type')

        if self.identifier_type == 'inchi':
            s = self.inchi_factory.getInChIToStructure(self.compound_string, cdk.DefaultChemObjectBuilder.getInstance())
            self.mol_container = s.getAtomContainer()
        elif self.identifier_type == 'smiles':
            smiles_parser = cdk.smiles.SmilesParser(cdk.DefaultChemObjectBuilder.getInstance())
            self.mol_container = smiles_parser.parseSmiles(self.compound_string)

    def get_smiles(self, smiles_type='generic'):
        smiles_generator = cdk.smiles.SmilesGenerator.isomeric()
        return smiles_generator.create(self.mol_container)

    def get_inchi_key(self):
        gen = self.inchi_factory.getInChIGenerator(self.mol_container)
        return gen.getInchiKey()

    def get_inchi(self):
        gen = self.inchi_factory.getInChIGenerator(self.mol_container)
        return gen.getInchi()


def main():
    test_inchi = 'InChI=1S/C23H18ClF2N3O3S/c1-2-9-33(31,32)29-19-8-7-18(25)20(21(19)26)22(30)17-12-28-23-16(17)10-14(11-27-23)13-3-5-15(24)6-4-13/h3-8,10-12,29H,2,9H2,1H3,(H,27,28)'
    cmpnd = Compound(compound_string=test_inchi, identifier_type='inchi')
    print(cmpnd.get_smiles())
    print(cmpnd.get_inchi_key())
    print(cmpnd.get_inchi())

    mol = 'C[BH]1H[BH](C)H1'
    mol = "CC(=O)Cl"
    cmpnd = Compound(compound_string=mol, identifier_type='smiles')
    print(cmpnd.get_smiles())
    print(cmpnd.get_inchi_key())
    print(cmpnd.get_inchi())

    print('ran through')
    time.sleep(5)

    # The py4j server process can either be killed by shutting down the gateway or killing the process directly
    # gateway.shutdown()
    # p.kill()

if __name__ == '__main__':
    sys.exit(main())
