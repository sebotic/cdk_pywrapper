import subprocess
import sys
import time
import os
import atexit

import py4j
from py4j.java_gateway import JavaGateway, GatewayParameters
from py4j.protocol import Py4JJavaError

# import cdk_pywrapper.config as config
import cdk_pywrapper
print(cdk_pywrapper.__path__)
from cdk_pywrapper.config import py4j_path, cdk_path

cdk_path = os.path.join(*cdk_pywrapper.__path__[0].split('/')[:-4])
cdk_jar_path = os.path.join('/', cdk_path, 'share', 'cdk')

py4j_path = os.path.join(*py4j.__path__[0].split('/')[:-4])
py4j_jar_path = os.path.join('/', py4j_path, 'share', 'py4j', 'py4j' + py4j.__version__ + '.jar')

# from py4j.clientserver import ClientServer, JavaParameters, PythonParameters

# set dev classpaths
if not __debug__:
    cdk_jar_path = './cdk'

__author__ = 'Sebastian Burgstaller-Muehlbacher'
__license__ = 'AGPLv3'
__copyright__ = 'Sebastian Burgstaller-Muehlbacher'


server_process_running = False
with subprocess.Popen(['ps aux | grep CDK'], shell=True, stdout=subprocess.PIPE) as proc:
    line = proc.stdout.read()
    print(line)
    if 'CDKBridge' in str(line):
        print('process running')
        server_process_running = True

# if not any([True if 'CDKBridge' in p.cmdline() else False for p in psutil.process_iter()]):
if not server_process_running:
    # compile and start py4j server
    # print(os.getcwd())
    # subprocess.call(["javac -cp '{}:.{}' ../cdk/cdk_bridge.java".format(py4j_path, cdk_path)], shell=True)
    # print('compiled sucessfully')
    p = subprocess.Popen(["java -cp '{}:{}:{}/' CDKBridge".format(py4j_jar_path,
                                                                        os.path.join(cdk_jar_path, 'cdk-2.1.1.jar'),
                                                                        cdk_jar_path)], shell=True)

    # wait 5 sec to start up JVM and server
    time.sleep(5)

# connect to the JVM
# gateway = JavaGateway(gateway_parameters=GatewayParameters(auto_convert=True))
# gateway = ClientServer(
#     java_parameters=JavaParameters(),
#     python_parameters=PythonParameters())


# shorten paths
# cdk = gateway.jvm.org.openscience.cdk
# java = gateway.jvm.java
# javax = gateway.jvm.javax

# map exceptions
# InvalidSmilesException = cdk.exception.InvalidSmilesException
# CDKException = cdk.exception.CDKException
# NullPointerException = java.lang.NullPointerException

gateway = JavaGateway(gateway_parameters=GatewayParameters(auto_convert=True))


# make sure the Java gateway server is shut down at exit of Python
@atexit.register
def cleanup_gateway():
    gateway.shutdown()


class Compound(object):
    def __init__(self, compound_string, identifier_type):
        assert(identifier_type in ['smiles', 'inchi'])

        self.cdk = gateway.jvm.org.openscience.cdk
        self.java = gateway.jvm.java
        # javax = gateway.jvm.javax

        self.compound_string = compound_string
        self.identifier_type = identifier_type
        self.mol_container = None
        self.inchi_factory = self.cdk.inchi.InChIGeneratorFactory.getInstance()

        allowed_types = ['smiles', 'inchi']

        if self.identifier_type not in allowed_types:
            raise ValueError('Not a valid identifier type')
        try:
            if self.identifier_type == 'inchi':
                s = self.inchi_factory.getInChIToStructure(self.compound_string,
                                                           self.cdk.DefaultChemObjectBuilder.getInstance())
                self.mol_container = s.getAtomContainer()
            elif self.identifier_type == 'smiles':
                smiles_parser = self.cdk.smiles.SmilesParser(self.cdk.DefaultChemObjectBuilder.getInstance())
                self.mol_container = smiles_parser.parseSmiles(self.compound_string)
        except Py4JJavaError as e:
            print(e)
            raise ValueError('Invalid {} provided!'.format(self.identifier_type))

    def get_smiles(self, smiles_type='isomeric'):
        if smiles_type == 'isomeric':
            smiles_generator = self.cdk.smiles.SmilesGenerator.isomeric()
        elif smiles_type == 'unique':
            smiles_generator = self.cdk.smiles.SmilesGenerator.unique()
        elif smiles_type == 'generic':
            smiles_generator = self.cdk.smiles.SmilesGenerator.generic()
        else:
            smiles_generator = self.cdk.smiles.SmilesGenerator.absolute()

        return smiles_generator.create(self.mol_container)

    def get_inchi_key(self):
        gen = self.inchi_factory.getInChIGenerator(self.mol_container)
        return gen.getInchiKey()

    def get_inchi(self):
        gen = self.inchi_factory.getInChIGenerator(self.mol_container)
        return gen.getInchi()

    def get_mol2(self, filename=''):
        """
        A method to convert a molecule to the mol2 format and optionally write it to a file
        :param filename: the filename, the mol2 file should be written to.
        :type filename: str
        :return: A mol2 file in string format
        """
        sdg = self.cdk.layout.StructureDiagramGenerator(self.mol_container)
        sdg.generateCoordinates()

        writer = self.java.io.StringWriter()
        mol2writer = self.cdk.io.Mol2Writer(writer)

        mol2writer.writeMolecule(self.mol_container)
        mol2writer.close()

        mol2string = writer.toString()

        if filename:
            with open(filename, "w") as text_file:
                text_file.write(mol2string)

        return mol2string

    def get_fingerprint(self):
        fingerprinter = self.cdk.fingerprint.Fingerprinter()
        fingerprint = fingerprinter.getBitFingerprint(self.mol_container)
        # raw_fingerprint = fingerprinter.getRawFingerprint(self.mol_container)
        print('Fingerprint size:', fingerprint.size())
        print(fingerprint.asBitSet())
        # print('raw fingerprint', raw_fingerprint)
        return fingerprint

    def get_bitmap_fingerprint(self):
        fingerprinter = self.cdk.fingerprint.Fingerprinter()
        fingerprint = fingerprinter.getBitFingerprint(self.mol_container)
        return fingerprint.asBitSet()

    def get_tanimoto(self, other_molecule):
        return self.cdk.similarity.Tanimoto.calculate(self.get_fingerprint(), other_molecule.get_fingerprint())

    def get_tanimoto_from_bitset(self, other_molecule):
        return self.cdk.similarity.Tanimoto.calculate(self.get_bitmap_fingerprint(), other_molecule.get_bitmap_fingerprint())


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

if __name__ == '__main__':
    sys.exit(main())
