import subprocess
import sys
import time
import os
import atexit
import platform
import copy

import py4j
from py4j.java_gateway import JavaGateway, GatewayParameters
from py4j.java_collections import SetConverter, MapConverter, ListConverter
from py4j.protocol import Py4JJavaError

# import cdk_pywrapper.config as config
import cdk_pywrapper
print(cdk_pywrapper.__path__)
from cdk_pywrapper.config import py4j_path, cdk_path

cdk_path = os.path.join(*cdk_pywrapper.__path__[0].split('/')[:-4])
cdk_jar_path = os.path.join('/', cdk_path, 'share', 'cdk')

py4j_path = os.path.join(*py4j.__path__[0].split('/')[:-4])
py4j_jar_path = os.path.join('/', py4j_path, 'share', 'py4j', 'py4j' + py4j.__version__ + '.jar')

# make sure host paths are set correctly,
# TODO: test if this can reasonably be replace by finding full path using 'which' shell command
host_os = platform.system()
ps_path = 'ps'
java_path = 'java'
grep_path = 'grep'

if host_os == 'Darwin':
    ps_path = '/bin/ps'
    java_path = '/usr/bin/java'
    grep_path = '/usr/bin/grep'
elif host_os == 'Linux':
    ps_path = '/usr/bin/ps'
    java_path = '/usr/bin/java'
    grep_path = '/usr/bin/grep'

# from py4j.clientserver import ClientServer, JavaParameters, PythonParameters

# set dev classpaths
if not __debug__:
    cdk_jar_path = './cdk'

__author__ = 'Sebastian Burgstaller-Muehlbacher'
__license__ = 'AGPLv3'
__copyright__ = 'Sebastian Burgstaller-Muehlbacher'


server_process_running = False
with subprocess.Popen(['{} aux | {} CDK'.format(ps_path, grep_path)], shell=True, stdout=subprocess.PIPE) as proc:
    line = proc.stdout.read()
    print(line)
    if 'CDKBridge' in str(line):
        print('process running')
        server_process_running = True

# if not any([True if 'CDKBridge' in p.cmdline() else False for p in psutil.process_iter()]):
if not server_process_running:
    # compile and start py4j server
    # print(os.getcwd())
    # subprocess.check_call(["javac -cp '{}:.{}' ../cdk/cdk_bridge.java".format(py4j_path, cdk_path)], shell=True)

    # subprocess.check_call(["javac -cp '{}:{}' ../cdk_pywrapper/cdk/cdk_bridge.java".format(py4j_jar_path,
    #                                                              '../cdk_pywrapper/cdk/cdk-2.1.1.jar')], shell=True)
    # # print('compiled sucessfully')
    p = subprocess.Popen(["{} -cp '{}:{}:{}/' CDKBridge".format(java_path, py4j_jar_path,
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


# make sure the Java gateway server is shut down at exit of Python, but don't shut down if it has already been running
@atexit.register
def cleanup_gateway():
    if not server_process_running:
        gateway.shutdown()


def search_substructure(pattern, molecules):
    g = JavaGateway.launch_gateway(classpath="{}:{}:{}/".format(py4j_jar_path,
                                                                os.path.join(cdk_jar_path, 'cdk-2.1.1.jar'),
                                                                cdk_jar_path), java_path=java_path)

    # search_handler = g.jvm.SearchHandler(MapConverter().convert(molecules, g._gateway_client))
    search_handler = g.jvm.SearchHandler()

    matches = search_handler.searchPattern(pattern, MapConverter().convert(molecules, g._gateway_client))

    results = copy.deepcopy([{'id': copy.deepcopy(str(compound_id)), 'match_count': copy.deepcopy(int(match_count)),
                              'svg': copy.deepcopy(str(svg))}
                             for compound_id, match_count, svg in matches])
    g.shutdown()
    return results


class Compound(object):
    def __init__(self, compound_string, identifier_type, suppress_hydrogens=False, add_explicit_hydrogens=False):
        allowed_types = ['smiles', 'inchi', 'atom_container']
        assert(identifier_type in allowed_types)

        self.cdk = gateway.jvm.org.openscience.cdk
        self.java = gateway.jvm.java

        self.identifier_type = identifier_type
        self.mol_container = None
        self.inchi_factory = self.cdk.inchi.InChIGeneratorFactory.getInstance()

        if self.identifier_type not in allowed_types:
            raise ValueError('Not a valid identifier type')
        try:
            if identifier_type == 'atom_container':
                self.compound_string = compound_string
                self.mol_container = self.compound_string
            else:
                self.compound_string = compound_string.strip()
                builder = self.cdk.DefaultChemObjectBuilder.getInstance()
                if self.identifier_type == 'inchi':
                    s = self.inchi_factory.getInChIToStructure(self.compound_string, builder)
                    self.mol_container = s.getAtomContainer()
                elif self.identifier_type == 'smiles':

                    smiles_parser = self.cdk.smiles.SmilesParser(builder)
                    self.mol_container = smiles_parser.parseSmiles(self.compound_string)

                if suppress_hydrogens:
                    self.mol_container = self.cdk.tools.manipulator.AtomContainerManipulator.copyAndSuppressedHydrogens(
                        self.mol_container)

                if add_explicit_hydrogens:
                    self.cdk.tools.manipulator.AtomContainerManipulator\
                        .percieveAtomTypesAndConfigureAtoms(self.mol_container)
                    self.cdk.tools.CDKHydrogenAdder.getInstance(builder).addImplicitHydrogens(self.mol_container)
                    self.cdk.tools.manipulator.AtomContainerManipulator\
                        .convertImplicitToExplicitHydrogens(self.mol_container)

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

    def get_tautomers(self):
        tautomer_generator = self.cdk.tautomers.InChITautomerGenerator()
        tautomers = tautomer_generator.getTautomers(self.mol_container)
        # py4j.java_collections.JavaList('o16', gateway)
        # mol1 = tautomers[0]
        t_obj = [Compound(compound_string=x, identifier_type='atom_container') for x in tautomers]
        print([t.get_inchi_key() for t in t_obj])
        print(*[t.get_inchi() for t in t_obj], sep='\n')
        print(*[t.get_smiles() for t in t_obj], sep='\n')
        return list(tautomers)

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

    def get_molfile(self, filename=''):
        """
        A method to convert a molecule to molfile V2000 (MDLV2000) format and optionally write it to a file
        :param filename: the filename, the molfile V2000 (MDLV2000) file should be written to.
        :type filename: str
        :return: A molfile V2000 (MDLV2000) file in string format
        """
        sdg = self.cdk.layout.StructureDiagramGenerator(self.mol_container)
        sdg.generateCoordinates()

        writer = self.java.io.StringWriter()
        molfile_writer = self.cdk.io.MDLV2000Writer(writer)

        molfile_writer.writeMolecule(self.mol_container)
        molfile_writer.close()

        molfile2string = writer.toString()

        if filename:
            with open(filename, "w") as text_file:
                text_file.write(molfile2string)

        return molfile2string

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

    def get_molecule_signature(self):
        molecule_signature = self.cdk.signature.MoleculeSignature(self.mol_container)
        return molecule_signature.toCanonicalString()

    def substructure_search(self, smarts='O=CO'):
        querytool = self.cdk.smiles.smarts.SMARTSQueryTool(smarts, self.cdk.DefaultChemObjectBuilder.getInstance())
        status = querytool.matches(self.mol_container)

        if status:
            nmatch = querytool.countMatches()
            mappings = querytool.getMatchingAtoms()
            for i in range(nmatch):
                print(mappings.get(i))

        return ''

    def get_svg(self, file_name=None, substructures=None):
        if substructures:
            color = self.java.awt.Color.orange
            dg = self.cdk.depict.DepictionGenerator()\
                .withHighlight(substructures, color)\
                .withAtomColors()\
                .withOuterGlowHighlight(4.0)
        else:
            dg = self.cdk.depict.DepictionGenerator().withAtomColors()

        if file_name:
            if not file_name.split('.')[-1].lower() == 'svg':
                file_name += '.svg'

            dg.depict(self.mol_container).writeTo(file_name)
            return ''

        else:
            return dg.depict(self.mol_container).toSvgStr()

    def get_molecular_weight(self):
        weight_descriptor = self.cdk.qsar.descriptors.molecular.WeightDescriptor()
        return weight_descriptor.calculate(self.mol_container).getValue().toString()

    @staticmethod
    def search_substructure(search_string, molecules, svg_return_count=10):
        """A slow version of a substructure search going back and forth btwn Java and Python"""

        cdk = gateway.jvm.org.openscience.cdk
        pattern = cdk.smiles.smarts.SmartsPattern.create(search_string)
        results = []

        for count, (compound_id, smiles) in enumerate(molecules):
            try:
                mol = Compound(compound_string=smiles, identifier_type='smiles')
            except ValueError as e:
                continue

            mappings = pattern.matchAll(mol.mol_container)
            match_count = mappings.countUnique()
            if match_count > 0:
                substructures = mappings.toChemObjects()
                svg = ''
                if len(results) <= svg_return_count:
                    svg = mol.get_svg(substructures=substructures)

                results.append({
                    'compound_id': compound_id,
                    'smiles': smiles,
                    'svg': svg
                })
                # print(svg)

        return results


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
