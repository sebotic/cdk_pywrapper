import cdk_pywrapper
import sys

__author__ = 'Sebastian Burgstaller-Muehlbacher'
__license__ = 'AGPLv3'
__copyright__ = 'Sebastian Burgstaller-Muehlbacher'

'''A main method with a list of InChIs. These are then used to generate SMILES and InChI keys.'''

def main():
    test_inchis = [
        'InChI=1S/C23H18ClF2N3O3S/c1-2-9-33(31,32)29-19-8-7-18(25)20(21(19)26)22(30)17-12-28-23-16(17)10-14(11-27-23)13-3-5-15(24)6-4-13/h3-8,10-12,29H,2,9H2,1H3,(H,27,28)',
        'InChI=1S/C33H42N4O6/c1-7-20-19(6)32(42)37-27(20)14-25-18(5)23(10-12-31(40)41)29(35-25)15-28-22(9-11-30(38)39)17(4)24(34-28)13-26-16(3)21(8-2)33(43)36-26/h15,26-27,35H,7-14H2,1-6H3,(H,36,43)(H,37,42)(H,38,39)(H,40,41)/b28-15-/t26-,27-/m0/s1',
        'InChI=1S/C21H25ClFN3O3/c1-2-28-20-10-19(24)18(22)9-17(20)21(27)25-11-16-13-26(7-8-29-16)12-14-3-5-15(23)6-4-14/h3-6,9-10,16H,2,7-8,11-13,24H2,1H3,(H,25,27)',
        'InChI=1S/C16H12FN3O3/c1-19-14-7-6-10(20(22)23)8-12(14)16(18-9-15(19)21)11-4-2-3-5-13(11)17/h2-8H,9H2,1H3',
        'InChI=1S/C10H17N3O6S/c11-5(10(18)19)1-2-7(14)13-6(4-20)9(17)12-3-8(15)16/h5-6,20H,1-4,11H2,(H,12,17)(H,13,14)(H,15,16)(H,18,19)/t5-,6-/m0/s1',
        'InChI=1S/C13H16N2O/c1-8-13-11(5-6-14-8)10-4-3-9(16-2)7-12(10)15-13/h3-4,7-8,14-15H,5-6H2,1-2H3',
        'InChI=1S/C27H44O2/c1-19-10-13-23(28)18-22(19)12-11-21-9-7-17-27(5)24(14-15-25(21)27)20(2)8-6-16-26(3,4)29/h11-12,20,23-25,28-29H,1,6-10,13-18H2,2-5H3/b21-11+,22-12-/t20-,23+,24-,25+,27-/m1/s1',
        'InChI=1S/C40H56/c1-31(19-13-21-33(3)25-27-37-35(5)23-15-29-39(37,7)8)17-11-12-18-32(2)20-14-22-34(4)26-28-38-36(6)24-16-30-40(38,9)10/h11-14,17-23,25-28,37H,15-16,24,29-30H2,1-10H3/b12-11+,19-13+,20-14+,27-25+,28-26+,31-17+,32-18+,33-21+,34-22+/t37-/m0/s1',
        'InChI=1S/C11H14N4O5/c1-14-3-13-9-6(10(14)19)12-4-15(9)11-8(18)7(17)5(2-16)20-11/h3-5,7-8,11,16-18H,2H2,1H3',
        'InChI=1S/C27H44O2/c1-18(2)8-6-9-19(3)24-13-14-25-21(10-7-15-27(24,25)5)11-12-22-16-23(28)17-26(29)20(22)4/h11-12,18-19,23-26,28-29H,4,6-10,13-17H2,1-3,5H3/b21-11+,22-12-/t19-,23-,24-,25+,26+,27-/m1/s1',
        'InChI=1S/C9H14N5O4P/c1-6(18-5-19(15,16)17)2-14-4-13-7-8(10)11-3-12-9(7)14/h3-4,6H,2,5H2,1H3,(H2,10,11,12)(H2,15,16,17)/t6-/m1/s1'

    ]

    for inchi in test_inchis:

        cmpnd = cdk_pywrapper.Compound(compound_string=inchi, identifier_type='inchi')
        print(cmpnd.get_smiles())
        print(cmpnd.get_inchi_key())
        print(cmpnd.get_inchi())
        print('----------------------------')

    # group of compounds with same connectivity but different configuration:
    # https://pubchem.ncbi.nlm.nih.gov/rest/rdf/inchikey/MNQDKWZEUULFPX-UHFFFAOYSA-M.html
    smiles = [
        '[Ba++].[O-][Fe]([O-])(=O)=O',
        'CCN1C2=CC=CC=C2SC1=CC=CC=CC3=[N+](C4=CC=CC=C4S3)CC.[I-]',
        'CCN\\1C2=CC=CC=C2S/C1=C\C=C\C=C\C3=[N+](C4=CC=CC=C4S3)CC.[I-]',
        'CCN\\1C2=CC=CC=C2S/C1=C/C=C/C=C/C3=[N+](C4=CC=CC=C4S3)CC.[I-]',
        'CCN\\1C2=CC=CC=C2S/C1=C\\C=C\\C=C/C3=[N+](C4=CC=CC=C4S3)CC.[I-]',
        'CCN\\1C2=CC=CC=C2S/C1=C/C=C/C=CC3=[N+](C4=CC=CC=C4S3)CC.[I-]',
        'CC1=CC=CC=C1OCC2=CC=CC=C2/C(=N\OC)/C(=O)OC'
    ]

    for smile in smiles:
        try:
            cmpnd = cdk_pywrapper.Compound(compound_string=smile, identifier_type='smiles')
            print(cmpnd.get_smiles())
            print(cmpnd.get_inchi_key())
            print(cmpnd.get_inchi())
            print('----------------------------')

        except ValueError as e:
            print(e)

if __name__ == '__main__':
    sys.exit(main())


