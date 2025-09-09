import requests
import sys
import json
import time
import re
import importlib.resources
# import wikidataintegrator.wdi_core as wdi_core
# import wikidataintegrator.wdi_login as wdi_login
import pprint
import pandas as pd
import numpy as np
import os

import chemspipy
# sys.path.append('/home/sebastian/PycharmProjects/cdk_pywrapper/')
from cdk_pywrapper.cdk_pywrapper import Compound

"""
A Python library for PubChem RDF
"""

__author__ = 'Sebastian Burgstaller-Muehlbacher'
__license__ = 'AGPLv3'
__copyright__ = 'Sebastian Burgstaller-Muehlbacher'


class UNIIMolecule(object):
    # with importlib.resources.open_text("cdk_pywrapper.data", "UNII_Records_18Aug2025.txt") as f:
    # data = f.read()

    # load UNII data. Can be downloaded from https://precision.fda.gov/uniisearch/archive/latest/UNII_Data.zip
    # TODO: update regularly/dynamically.
    data = str(importlib.resources.files('cdk_pywrapper.data').joinpath("UNII_Records_18Aug2025.txt"))
    unii_data = pd.read_csv(data, low_memory=False, index_col=0, sep='\t',
                               dtype={
                                   'UNII': 'str',
                                   'RXCUI': 'str',
                                   'INN_ID': 'str',
                                   'ITIS': 'str',
                                   'NCBI': 'str',
                                   'RxNorm_CUI': 'str',  # same as RXCUI, but from NDF-RT
                               })

    for count, row in unii_data.iterrows():
        smiles = row['SMILES']
        ikey = row['INCHIKEY']
        if pd.notnull(smiles) and pd.isnull(ikey):
            cmpnd = Compound(compound_string=smiles, identifier_type='smiles')
            unii_data.loc[count, 'INCHIKEY'] = cmpnd.get_inchi_key()

            if count % 10000 == 0:
                print('processed to UNII ID', count)

    # base_path = str(importlib.resources.files('cdk_pywrapper.data'))    
    # unii_data.to_csv(os.path.join(base_path, 'unii_data_ndfrt.csv'))

    def __init__(self, unii=None, inchi_key=None):

        print('unii inchi key', inchi_key)
        if unii:
            ind = UNIIMolecule.unii_data['UNII'].values == unii
        else:
            ind = UNIIMolecule.unii_data['INCHIKEY'].values == inchi_key


        self.data = UNIIMolecule.unii_data.loc[ind, :]

        if len(self.data.index) != 1:
            raise ValueError('Provided ID did not return a unique UNII')

        self.data_index = self.data.index[0]



    @property
    def stdinchikey(self):
        ikey = self.data.loc[self.data_index, 'INCHIKEY']
        if pd.isnull(ikey) and pd.isnull(self.smiles):
            return None
        elif pd.notnull(self.smiles):
            cmpnd = Compound(compound_string=self.smiles, identifier_type='smiles')
            ikey = cmpnd.get_inchi_key()

        return ikey

    @property
    def stdinchi(self):
        if pd.isnull(self.smiles):
            return None
        elif pd.notnull(self.smiles):
            cmpnd = Compound(compound_string=self.smiles, identifier_type='smiles')
            return cmpnd.get_inchi()

    @property
    def preferred_name(self):
        name = self.data.loc[self.data_index, 'PT']
        return UNIIMolecule.label_converter(name) if pd.notnull(name) else None

    @property
    def smiles(self):
        smiles = self.data.loc[self.data_index, 'SMILES']
        return smiles if pd.notnull(smiles) else None

    @property
    def molecule_type(self):
        molecule_type = self.data.loc[self.data_index, 'UNII_TYPE']
        return molecule_type if pd.notnull(molecule_type) else None

    @property
    def unii(self):
        return self.data.loc[self.data_index, 'UNII']

    @property
    def cas(self):
        cas = self.data.loc[self.data_index, 'RN']
        return cas if pd.notnull(cas) else None

    @property
    def einecs(self):
        einecs = self.data.loc[self.data_index, 'EC']
        return einecs if pd.notnull(einecs) else None

    @property
    def rxnorm(self):
        rxnorm = self.data.loc[self.data_index, 'RXCUI']
        return rxnorm if pd.notnull(rxnorm) else None

    @property
    def ndfrt(self):
        ndfrt = self.data.loc[self.data_index, 'NUI']
        return ndfrt if pd.notnull(ndfrt) else None

    @property
    def umls(self):
        umls_cui = self.data.loc[self.data_index, 'UMLS_CUI']
        return umls_cui if pd.notnull(umls_cui) else None


    def to_wikidata(self):
        item_label = self.preferred_name if self.preferred_name else self.unii

        refs = [[
            wdi_core.WDItemID(value='Q6593799', prop_nr='P248', is_reference=True),  # stated in
            wdi_core.WDExternalID(value=self.unii, prop_nr='P652', is_reference=True),  # source element
            wdi_core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),  # language of work
            wdi_core.WDMonolingualText(value=item_label[0:400], language='en', prop_nr='P1476', is_reference=True),
            wdi_core.WDTime(time=time.strftime('+%Y-%m-%dT00:00:00Z'), prop_nr='P813', is_reference=True)  # retrieved
        ]]
        print('UNII Main label is', item_label)

        cmpnd = Compound(compound_string=self.smiles, identifier_type='smiles')
        isomeric_smiles = cmpnd.get_smiles(smiles_type='isomeric')
        canonical_smiles = cmpnd.get_smiles(smiles_type='generic')

        elements = {
            'P652': self.unii,
            'P233': canonical_smiles,
            'P2017': isomeric_smiles,
            'P235': self.stdinchikey,
            'P234': self.stdinchi[6:],
            'P231': self.cas,
            'P232': self.einecs,
            'P2892': self.umls,
            'P2115': self.ndfrt,
            'P3345': self.rxnorm
        }

        dtypes = {
            'P652': wdi_core.WDExternalID,
            'P683': wdi_core.WDExternalID,
            'P661': wdi_core.WDExternalID,
            'P2153': wdi_core.WDExternalID,
            'P233': wdi_core.WDString,
            'P2017': wdi_core.WDString,
            'P235': wdi_core.WDExternalID,
            'P234': wdi_core.WDExternalID,
            'P274': wdi_core.WDString,
            'P231': wdi_core.WDExternalID,
            'P232': wdi_core.WDExternalID,
            'P2892': wdi_core.WDExternalID,
            'P2115': wdi_core.WDExternalID,
            'P3345': wdi_core.WDExternalID
        }

        # do not add isomeric smiles if no isomeric info is available
        if canonical_smiles == isomeric_smiles or len(self.smiles) > 400:
            del elements['P2017']

        # do not try to add InChI longer than 400 chars
        if len(self.stdinchi[6:]) > 400:
            del elements['P234']

        if len(self.smiles) > 400:
            del elements['P233']

        data = []

        for k, v in elements.items():
            if not v:
                continue

            print('{}:'.format(k), v)
            if isinstance(v, list) or isinstance(v, set):
                for x in v:
                    data.append(dtypes[k](prop_nr=k, value=x, references=refs))
            else:
                data.append(dtypes[k](prop_nr=k, value=v, references=refs))

        return data

    @staticmethod
    def label_converter(label):
        label = label.lower()

        greek_codes = {
            '.alpha.': '\u03B1',
            '.beta.': '\u03B2',
            '.gamma.': '\u03B3',
            '.delta.': '\u03B4',
            '.epsilon.': '\u03B5',
            '.zeta.': '\u03B6 ',
            '.eta.': '\u03B7',
            '.theta.': '\u03B8',
            '.iota.': '\u03B9',
            '.kappa.': '\u03BA',
            '.lambda.': '\u03BB',
            '.mu.': '\u03BC',
            '.nu.': '\u03BD',
            '.xi.': '\u03BE',
            '.omicron.': '\u03BF',
            '.pi.': '\u03C0',
            '.rho.': '\u03C1',
            '.sigma.': '\u03C3',
            '.tau.': '\u03C4',
            '.upsilon.': '\u03C5',
            '.phi.': '\u03C6',
            '.chi.': '\u03C7',
            '.psi.': '\u03C8',
            '.omega.': '\u03C9',

        }

        for greek_letter, unicode in greek_codes.items():
            if greek_letter in label:
                label = label.replace(greek_letter, unicode)

        match = re.compile('(^|[^a-z])([ezdlnhros]{1}|dl{1})[^a-z]{1}')

        while True:
            if re.search(match, label):
                replacement = label[re.search(match, label).start(): re.search(match, label).end()].upper()
                label = re.sub(match, repl=replacement, string=label, count=1)
            else:
                break

        splits = label.split(', ')
        splits.reverse()
        return ''.join(splits)


# class DrugBankMolecule(object):
#     """DrugBank ID, Accession Numbers, Common name, CAS, UNII, Synonyms, Standard InChI Key"""

#     drugbank_data = pd.read_csv('drugbank vocabulary.csv', low_memory=False)
#     drugbank_data = pd.concat([drugbank_data.drop_duplicates(subset=['Standard InChI Key'], keep='first'),
#                                drugbank_data.loc[drugbank_data['Standard InChI Key'].isnull(), :]])


#     def __init__(self, db=None, inchi_key=None):

#         print('unii inchi key', inchi_key)
#         if db:
#             ind = DrugBankMolecule.drugbank_data['DrugBank ID'].values == db
#         else:
#             ind = DrugBankMolecule.drugbank_data['Standard InChI Key'].values == inchi_key


#         self.data = DrugBankMolecule.drugbank_data.loc[ind, :]

#         if len(self.data.index) != 1:
#             raise ValueError('Provided ID did not return a unique DrugBank ID')

#         self.data_index = self.data.index[0]

#     @property
#     def stdinchikey(self):
#         ikey = self.data.loc[self.data_index, 'Standard InChI Key']
#         if pd.isnull(ikey):
#             return None

#         return ikey

#     @property
#     def stdinchi(self):
#         # CC0 data does not provide InChI, instead could create a PubChemMolecule using the InChI key provided and use that
#         return None

#     @property
#     def preferred_name(self):
#         name = self.data.loc[self.data_index, 'Common name']
#         return name if pd.notnull(name) else None

#     @property
#     def synonyms(self):
#         synonyms = self.data.loc[self.data_index, 'Synonyms']
#         return synonyms.split(' | ') if pd.notnull(synonyms) else []

#     @property
#     def smiles(self):
#         # same applies as for InChIs
#         return None

#     @property
#     def molecule_type(self):
#         # return either 'approved', 'experimental', 'retracted', 'biotech', 'antibody'. Based on what the accession numbers say
#         return None

#     @property
#     def accession_numbers(self):
#         acc_nrs = self.data.loc[self.data_index, 'Accession Numbers'].split('|')
#         return acc_nrs

#     @property
#     def unii(self):
#         unii = self.data.loc[self.data_index, 'UNII']
#         return unii if pd.notnull(unii) else None

#     @property
#     def cas(self):
#         cas = self.data.loc[self.data_index, 'CAS']
#         return cas if pd.notnull(cas) else None

#     @property
#     def drugbank(self):
#         return self.data.loc[self.data_index, 'DrugBank ID'][2:]

#     def to_wikidata(self):
#         item_label = self.preferred_name if self.preferred_name else 'DB' + self.drugbank

#         refs = [[
#             wdi_core.WDItemID(value='Q1122544', prop_nr='P248', is_reference=True),  # stated in
#             wdi_core.WDExternalID(value=self.drugbank, prop_nr='P715', is_reference=True),  # source element
#             wdi_core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),  # language of work
#             wdi_core.WDMonolingualText(value=item_label[0:400], language='en', prop_nr='P1476', is_reference=True),
#             wdi_core.WDTime(time=time.strftime('+%Y-%m-%dT00:00:00Z'), prop_nr='P813', is_reference=True)  # retrieved
#         ]]
#         print('DrugBank Main label is', item_label)

#         # cmpnd = Compound(compound_string=self.smiles, identifier_type='smiles')
#         # isomeric_smiles = cmpnd.get_smiles(smiles_type='isomeric')
#         # canonical_smiles = cmpnd.get_smiles(smiles_type='generic')

#         elements = {
#             'P652': self.unii,
#             'P715': self.drugbank,
#             #'P233': canonical_smiles,
#             #'P2017': isomeric_smiles,
#             #'P235': self.stdinchikey,
#             #'P234': self.stdinchi[6:],
#             'P231': self.cas,
#         }

#         dtypes = {
#             'P652': wdi_core.WDExternalID,
#             'P715': wdi_core.WDExternalID,
#             'P683': wdi_core.WDExternalID,
#             'P661': wdi_core.WDExternalID,
#             'P2153': wdi_core.WDExternalID,
#             'P233': wdi_core.WDString,
#             'P2017': wdi_core.WDString,
#             'P235': wdi_core.WDExternalID,
#             'P234': wdi_core.WDExternalID,
#             'P274': wdi_core.WDString,
#             'P231': wdi_core.WDExternalID,
#             'P232': wdi_core.WDExternalID
#         }

#         # # do not add isomeric smiles if no isomeric info is available
#         # if canonical_smiles == isomeric_smiles or len(self.smiles) > 400:
#         #     del elements['P2017']
#         #
#         # # do not try to add InChI longer than 400 chars
#         # if len(self.stdinchi[6:]) > 400:
#         #     del elements['P234']
#         #
#         # if len(self.smiles) > 400:
#         #     del elements['P233']

#         data = []

#         for k, v in elements.items():
#             if not v:
#                 continue

#             print('{}:'.format(k), v)
#             if isinstance(v, list) or isinstance(v, set):
#                 for x in v:
#                     data.append(dtypes[k](prop_nr=k, value=x, references=refs))
#             else:
#                 data.append(dtypes[k](prop_nr=k, value=v, references=refs))

#         return data


# class ChEBIMolecule(object):
#     chebi_data_path = './chebi_data/'
#     chebi_data = pd.read_csv(os.path.join(chebi_data_path, 'chebiId_inchi.tsv'), low_memory=False, index_col=0, sep='\t')

#     'ID	COMPOUND_ID	TYPE	SOURCE	NAME	ADAPTED	LANGUAGE'
#     chebi_names = pd.read_csv(os.path.join(chebi_data_path, 'names.tsv'), low_memory=False, index_col=None, sep='\t',
#                              dtype={'ID': 'str', 'COMPOUND_ID': 'str'}, na_filter=False)

#     zwitterion_id_list = set()
#     for zz in chebi_names.iterrows():
#         data = zz[1]
#         if 'zwitterion' in data['NAME']:
#             zwitterion_id_list.add(np.int64(data['COMPOUND_ID']))

#     compounds = pd.read_csv(os.path.join(chebi_data_path, 'compounds.tsv'), low_memory=False, index_col=0, sep='\t')

#     for c, zz in compounds.iterrows():
#         # pd.NaN is handled as a float datatype so it needs extra treatment, what a nonsense.
#         if pd.isnull(zz['NAME']):
#             zwitterion_id_list.add(c)
#             continue
#         if 'zwitterion' in zz['NAME']:
#             zwitterion_id_list.add(c)

#     chebi_data = chebi_data.drop(list(zwitterion_id_list))

#     if 'InChI key' not in chebi_data:
#         print('Generating InChI keys ...')
#         for row in chebi_data.iterrows():
#             index = row[0]
#             data = row[1]

#             inchi = data['InChI']
#             cmpnd = Compound(compound_string=inchi, identifier_type='inchi')
#             chebi_data.loc[index, 'InChI key'] = cmpnd.get_inchi_key()

#             if index % 1000 == 0:
#                 print('processed to ChEBI ID', index)

#         chebi_data.to_csv(os.path.join(chebi_data_path, 'chebiId_inchi.tsv'), sep='\t')


#     'ID	COMPOUND_ID	SOURCE	TYPE	ACCESSION_NUMBER'
#     db_accessions = pd.read_csv(os.path.join(chebi_data_path, 'database_accession.tsv'), low_memory=False, index_col=None, sep='\t',
#                                 dtype={'ID': 'str', 'COMPOUND_ID': 'str'}, na_filter=False)

#     # remove CAS numbers provided by KEGG, as they are frequently incorrect
#     db_accessions = db_accessions.loc[~(db_accessions['SOURCE'].isin(['KEGG COMPOUND']) &
#                                       db_accessions['TYPE'].isin(['CAS Registry Number'])), :]

#     def __init__(self, chebi_id=None, inchi_key=None):

#         if chebi_id:
#             ind = ChEBIMolecule.chebi_data.index == np.int64(chebi_id)
#         else:
#             ind = ChEBIMolecule.chebi_data['InChI key'].values == inchi_key

#         self._canonical_smiles = None
#         self._isomeric_smiles = None

#         self.data = ChEBIMolecule.chebi_data.loc[ind, :]

#         if len(self.data.index) != 1:
#             raise ValueError('No unique found for ChEBI ID')

#         self.data_index = self.data.index[0]

#         self.all_names = ChEBIMolecule.chebi_names.loc[ChEBIMolecule.chebi_names['COMPOUND_ID'] == self.chebi, :]
#         self.accessions = ChEBIMolecule.db_accessions.loc[ChEBIMolecule.db_accessions['COMPOUND_ID'] == self.chebi, :]
#         self.chebi_base_data = ChEBIMolecule.compounds.loc[ChEBIMolecule.compounds.index == np.int64(self.chebi), :]

#     @property
#     def stdinchikey(self):
#         return self.data.loc[self.data_index, 'InChI key']

#     @property
#     def stdinchi(self):
#         return self.data.loc[self.data_index, 'InChI']

#     @property
#     def preferred_name(self):
#         pref_names = [x[1]['NAME'] for x in self.chebi_base_data
#                                                 .loc[self.chebi_base_data.index == np.int64(self.chebi), :].iterrows()]
#         return pref_names[0] if len(pref_names) > 0 else None

#     @property
#     def synonyms(self):
#         return [x[1]['NAME'] for x in self.all_names.loc[self.all_names['TYPE'] == 'SYNONYM', :]
#             .iterrows() if x[1]['LANGUAGE'] == 'en']

#     @property
#     def canonical_smiles(self):
#         if not self._canonical_smiles:
#             cmpnd = Compound(compound_string=self.stdinchi, identifier_type='inchi')
#             self._canonical_smiles = cmpnd.get_smiles(smiles_type='generic')
#             self._isomeric_smiles = cmpnd.get_smiles(smiles_type='isomeric')
#         return self._canonical_smiles

#     @canonical_smiles.setter
#     def canonical_smiles(self, value):
#         self._canonical_smiles = value

#     @property
#     def isomeric_smiles(self):
#         if not self._isomeric_smiles:
#             csmiles = self.canonical_smiles
#         return self._isomeric_smiles

#     @isomeric_smiles.setter
#     def isomeric_smiles(self, value):
#         self._isomeric_smiles = value

#     @property
#     def chebi(self):
#         return str(self.data_index)

#     @property
#     def cas(self):
#         return set([x[1]['ACCESSION_NUMBER'] for x in self.accessions.loc[self.accessions['TYPE']
#             .isin(['CAS Registry Number']), :].iterrows()])

#     @property
#     def hmdb(self):
#         return set([x[1]['ACCESSION_NUMBER'] for x in self.accessions.loc[self.accessions['TYPE']
#             .isin(['HMDB accession']), :].iterrows()])

#     @property
#     def beilstein(self):
#         return set([x[1]['ACCESSION_NUMBER'] for x in self.accessions.loc[self.accessions['TYPE']
#             .isin(['Beilstein Registry Number', 'Reaxys Registry Number']), :].iterrows()])

#     @property
#     def kegg(self):
#         return set([x[1]['ACCESSION_NUMBER'] for x in self.accessions.loc[self.accessions['TYPE']
#             .isin(['KEGG COMPOUND accession', 'KEGG DRUG accession']), :].iterrows()])

#     @property
#     def knapsack(self):
#         return set([x[1]['ACCESSION_NUMBER'] for x in self.accessions.loc[self.accessions['TYPE']
#                    .isin(['KNApSAcK accession']), :].iterrows()])

#     @property
#     def who_inn(self):
#         return [x[1]['NAME'] for x in self.all_names.loc[self.all_names['TYPE'] == 'INN', :]
#             .iterrows() if x[1]['LANGUAGE'] == 'en']

#     def to_wikidata(self):
#         item_label = self.preferred_name if self.preferred_name else 'ChEBI:' + self.chebi

#         refs = [[
#             wdi_core.WDItemID(value='Q902623', prop_nr='P248', is_reference=True),  # stated in
#             wdi_core.WDExternalID(value=self.chebi, prop_nr='P683', is_reference=True),  # source element
#             wdi_core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),  # language of work
#             wdi_core.WDMonolingualText(value=item_label[0:400], language='en', prop_nr='P1476', is_reference=True),
#             wdi_core.WDTime(time=time.strftime('+%Y-%m-%dT00:00:00Z'), prop_nr='P813', is_reference=True)  # retrieved
#         ]]
#         print('ChEBI Main label is', item_label)

#         elements = {
#             'P683': self.chebi,
#             'P233': self.canonical_smiles,
#             'P2017': self.isomeric_smiles,
#             'P235': self.stdinchikey,
#             'P234': self.stdinchi[6:],
#             'P231': self.cas,
#             'P665': self.kegg,
#             'P2057': self.hmdb,
#             'P1579': self.beilstein,
#             'P2064': self.knapsack,
#             'P2275': self.who_inn
#         }

#         dtypes = {
#             'P652': wdi_core.WDExternalID,
#             'P683': wdi_core.WDExternalID,
#             'P661': wdi_core.WDExternalID,
#             'P2153': wdi_core.WDExternalID,
#             'P233': wdi_core.WDString,
#             'P2017': wdi_core.WDString,
#             'P235': wdi_core.WDExternalID,
#             'P234': wdi_core.WDExternalID,
#             'P274': wdi_core.WDString,
#             'P231': wdi_core.WDExternalID,
#             'P232': wdi_core.WDExternalID,
#             'P665': wdi_core.WDExternalID,
#             'P2057': wdi_core.WDExternalID,
#             'P1579': wdi_core.WDExternalID,
#             'P2064': wdi_core.WDExternalID,
#             'P2275': wdi_core.WDMonolingualText
#         }

#         # do not add isomeric smiles if no isomeric info is available
#         if self.canonical_smiles == self.isomeric_smiles or len(self.isomeric_smiles) > 400:
#             del elements['P2017']

#         # do not try to add InChI longer than 400 chars
#         if len(self.stdinchi[6:]) > 400:
#             del elements['P234']

#         if len(self.canonical_smiles) > 400:
#             del elements['P233']

#         data = []

#         for k, v in elements.items():
#             if not v:
#                 continue

#             print('{}:'.format(k), v)
#             if isinstance(v, list) or isinstance(v, set):
#                 for x in v:
#                     data.append(dtypes[k](prop_nr=k, value=x, references=refs))
#             else:
#                 data.append(dtypes[k](prop_nr=k, value=v, references=refs))

#         return data


class GTPLMolecule(object):
    def __init__(self, gtpl_id=None, cid=None, sid=None, inchi_key=None, name=None):
        gtp_data_path = str(importlib.resources.files('cdk_pywrapper.data').joinpath("ligands.csv"))
        
        gtp_data = pd.read_csv(
            gtp_data_path,
            comment='#',                 # skip any lines starting with #
            skip_blank_lines=True,
            skiprows=1,
            low_memory=False,
            dtype={'PubChem SID': 'str', 'PubChem CID': 'str', 'Ligand ID': 'str'}
        )
        # remove all labelled or radioactive compounds as they have the same inchi key as unlabelled compounds
        gtp_data = gtp_data.loc[pd.isnull(gtp_data['Labelled'].values), :]

        print('gtpl inchi', inchi_key)
        if gtpl_id:
            ind = gtp_data['Ligand ID'].values == gtpl_id
        elif cid:
            ind = gtp_data['PubChem CID'].values == cid
        elif sid:
            ind = gtp_data['PubChem SID'].values == sid
        elif inchi_key:
            ind = gtp_data['InChIKey'].values == inchi_key
        else:
            ind = gtp_data['Name'].values == name

        self.data = gtp_data.loc[ind, :]

        if len(self.data.index) != 1:
            raise ValueError('Provided ID did not return a unique GTPL ID')

        self.data_index = self.data.index[0]


    @property
    def stdinchikey(self):
        return self.data.loc[self.data_index, 'InChIKey']

    @property
    def stdinchi(self):
        return self.data.loc[self.data_index, 'InChI']

    @property
    def preferred_name(self):
        return GTPLMolecule.label_converter(self.data.loc[self.data_index, 'Name'])

    @property
    def synonyms(self):
        synonyms = self.data.loc[self.data_index, 'Synonyms']
        synonyms = synonyms.split('|') if pd.notnull(synonyms) else []
        return [GTPLMolecule.label_converter(x) for x in synonyms]

    @property
    def smiles(self):
        return self.data.loc[self.data_index, 'SMILES']

    @property
    def molecule_type(self):
        return self.data.loc[self.data_index, 'Type']

    @property
    def gtpl_id(self):
        return self.data.loc[self.data_index, 'Ligand ID']

    def to_wikidata(self):
        item_label = self.preferred_name if self.preferred_name else 'GTPL' + self.gtpl_id

        refs = [[
            wdi_core.WDItemID(value='Q17091219', prop_nr='P248', is_reference=True),  # stated in
            wdi_core.WDExternalID(value=self.gtpl_id, prop_nr='P595', is_reference=True),  # source element
            wdi_core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),  # language of work
            wdi_core.WDMonolingualText(value=item_label[0:400], language='en', prop_nr='P1476', is_reference=True),
            wdi_core.WDTime(time=time.strftime('+%Y-%m-%dT00:00:00Z'), prop_nr='P813', is_reference=True)  # retrieved
        ]]
        print('GTPL Main label is', item_label)

        cmpnd = Compound(compound_string=self.smiles, identifier_type='smiles')
        isomeric_smiles = cmpnd.get_smiles(smiles_type='isomeric')
        canonical_smiles = cmpnd.get_smiles(smiles_type='generic')

        elements = {
            'P595': self.gtpl_id,
            'P233': canonical_smiles,
            'P2017': isomeric_smiles,
            'P235': self.stdinchikey,
            'P234': self.stdinchi[6:],
        }

        dtypes = {
            'P595': wdi_core.WDExternalID,
            'P683': wdi_core.WDExternalID,
            'P661': wdi_core.WDExternalID,
            'P2153': wdi_core.WDExternalID,
            'P233': wdi_core.WDString,
            'P2017': wdi_core.WDString,
            'P235': wdi_core.WDExternalID,
            'P234': wdi_core.WDExternalID,
            'P274': wdi_core.WDString
        }

        # do not add isomeric smiles if no isomeric info is available
        if canonical_smiles == isomeric_smiles or len(self.smiles) > 400:
            del elements['P2017']

        # do not try to add InChI longer than 400 chars
        if len(self.stdinchi[6:]) > 400:
            del elements['P234']

        if len(self.smiles) > 400:
            del elements['P233']

        data = []

        for k, v in elements.items():
            if not v:
                continue

            print('{}:'.format(k), v)
            if isinstance(v, list) or isinstance(v, set):
                for x in v:
                    data.append(dtypes[k](prop_nr=k, value=x, references=refs))
            else:
                data.append(dtypes[k](prop_nr=k, value=v, references=refs))

        return data

    @staticmethod
    def label_converter(label):
        greek_codes = {
            '&alpha;': '\u03B1',
            '&beta;': '\u03B2',
            '&gamma;': '\u03B3',
            '&delta;': '\u03B4',
            '&epsilon;': '\u03B5',
            '&zeta;': '\u03B6 ',
            '&eta;': '\u03B7',
            '&theta;': '\u03B8',
            '&iota;': '\u03B9',
            '&kappa;': '\u03BA',
            '&lambda;': '\u03BB',
            '&mu;': '\u03BC',
            '&nu;': '\u03BD',
            '&xi;': '\u03BE',
            '&omicron;': '\u03BF',
            '&pi;': '\u03C0',
            '&rho;': '\u03C1',
            '&sigma;': '\u03C3',
            '&tau;': '\u03C4',
            '&upsilon;': '\u03C5',
            '&phi;': '\u03C6',
            '&chi;': '\u03C7',
            '&psi;': '\u03C8',
            '&omega;': '\u03C9',

            '&Alpha;': '\u0391',
            '&‌Beta;': '\u0392',
            '&G‌amma;': '\u0393',
            '&Delta;': '\u0394',
            '&E‌psilon;': '\u0395',
            '&Zeta;': '\u0396',
            '&E‌ta;': '\u0397',
            '&T‌heta;': '\u0398',
            '&Iota;': '\u0399',
            '&K‌appa;': '\u039A',
            '&L‌ambda;': '\u039B',
            '&‌Mu;': '\u039C',
            '&‌Nu;': '\u039D',
            '&Xi;': '\u039E',
            '&Omicron;': '\u039F',
            '&Pi;': '\u03A0',
            '&Rho;': '\u03A1',
            '&Sigma;': '\u03A3',
            '&Tau;': '\u03A4',
            '&Upsilon;': '\u03A5',
            '&Phi;': '\u03A6',
            '&Chi;': '\u03A7',
            '&Psi;': '\u03A8',
            '&Omega;': '\u03A9',

            '&reg;': '\u00AE',
            '&plusmn;': '\u00B1'
        }

        for greek_letter, unicode in greek_codes.items():
            if greek_letter in label:
                label = label.replace(greek_letter, unicode)

        remove_tags = ['<i>', '</i>', '<sub>', '</sub>', '<sup>', '</sup>']
        for x in remove_tags:
            label = label.replace(x, '')

        return label



class ChEMBLMolecule(object):
    def __init__(self, chembl_id=None, inchi_key=None):
        ci = chembl_id if chembl_id is not None else inchi_key

        url = 'https://www.ebi.ac.uk/chembl/api/data/molecule/{}'.format(ci.upper())

        params = {'format': 'json'}

        r = requests.get(url, params=params)
        if r.status_code == 404:
            raise ValueError('ChEMBL ID {} not found in ChEMBL'.format(chembl_id))
        self.compound = r.json()

    @property
    def stdinchikey(self):
        return self.compound['molecule_structures']['standard_inchi_key']

    @property
    def stdinchi(self):
        return self.compound['molecule_structures']['standard_inchi']

    @property
    def preferred_name(self):
        return self.compound['pref_name']

    @property
    def smiles(self):
        return self.compound['molecule_structures']['canonical_smiles']

    @property
    def chembl_id(self):
        return self.compound['molecule_chembl_id']

    @property
    def monoisotopic_mass(self):
        return self.compound['molecule_properties']['mw_monoisotopic']

    @property
    def chebi(self):
        return self.compound['chebi_par_id'] if 'chebi_par_id' in self.compound else None

    # def to_wikidata(self):
    #     item_label = self.preferred_name if self.preferred_name else self.chembl_id

    #     refs = [[
    #         wdi_core.WDItemID(value='Q6120337', prop_nr='P248', is_reference=True),  # stated in
    #         wdi_core.WDExternalID(value=self.chembl_id, prop_nr='P592', is_reference=True),  # source element
    #         wdi_core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),  # language of work
    #         wdi_core.WDMonolingualText(value=item_label[0:400], language='en', prop_nr='P1476', is_reference=True),
    #         wdi_core.WDTime(time=time.strftime('+%Y-%m-%dT00:00:00Z'), prop_nr='P813', is_reference=True)  # retrieved
    #     ]]
    #     print('ChEMBL Main label is', item_label)

    #     cmpnd = Compound(compound_string=self.smiles, identifier_type='smiles')
    #     isomeric_smiles = cmpnd.get_smiles(smiles_type='isomeric')
    #     canonical_smiles = cmpnd.get_smiles(smiles_type='generic')

    #     elements = {
    #         'P592': self.chembl_id,
    #         'P233': canonical_smiles,
    #         'P2017': isomeric_smiles,
    #         'P235': self.stdinchikey,
    #         'P234': self.stdinchi[6:],
    #         'P683': str(self.chebi) if self.chebi else None
    #     }

    #     dtypes = {
    #         'P592': wdi_core.WDExternalID,
    #         'P683': wdi_core.WDExternalID,
    #         'P661': wdi_core.WDExternalID,
    #         'P2153': wdi_core.WDExternalID,
    #         'P233': wdi_core.WDString,
    #         'P2017': wdi_core.WDString,
    #         'P235': wdi_core.WDExternalID,
    #         'P234': wdi_core.WDExternalID,
    #         'P274': wdi_core.WDString
    #     }

    #     # do not add isomeric smiles if no isomeric info is available
    #     if canonical_smiles == isomeric_smiles or len(self.smiles) > 400:
    #         del elements['P2017']

    #     # do not try to add InChI longer than 400 chars
    #     if len(self.stdinchi[6:]) > 400:
    #         del elements['P234']

    #     if len(self.smiles) > 400:
    #         del elements['P233']

    #     data = [
    #         wdi_core.WDQuantity(value=self.monoisotopic_mass, prop_nr='P2067', upper_bound=self.monoisotopic_mass,
    #                             lower_bound=self.monoisotopic_mass, unit='http://www.wikidata.org/entity/Q483261',
    #                             references=refs)
    #     ]

    #     for k, v in elements.items():
    #         if not v:
    #             continue

    #         print('{}:'.format(k), v)
    #         if isinstance(v, list) or isinstance(v, set):
    #             for x in v:
    #                 data.append(dtypes[k](prop_nr=k, value=x, references=refs))
    #         else:
    #             data.append(dtypes[k](prop_nr=k, value=v, references=refs))

    #     return data

# class ChemSpiderMolecule(object):
#     token = ''

#     def __init__(self, csid=None, mol=None):
#         if csid:
#             cs = chemspipy.ChemSpider(ChemSpiderMolecule.token)
#             self.compound = cs.get_compound(csid)
#         else:
#             self.compound = mol

#         # self._inchikey = self.compound.inchikey
#         # self._inchi = self.compound.inchi
#         # self._common_name = self.compound.common_name
#         # self._smiles = self.compound.smiles


#         # ikey = 'HGCGQDMQKGRJNO-UHFFFAOYSA-N'
#         # ikey = 'MTNISTQLDNOGTM-UHFFFAOYSA-N'
#         # ikey = 'ZWAWYSBJNBVQHP-UHFFFAOYSA-N'


#     @property
#     def stdinchikey(self):
#         return self.compound.stdinchikey

#     @property
#     def stdinchi(self):
#         return self.compound.stdinchi

#     @property
#     def common_name(self):
#         try:
#             return self.compound.common_name
#         except KeyError:
#             return None

#     @property
#     def smiles(self):
#         return self.compound.smiles

#     @property
#     def csid(self):
#         return str(self.compound.csid)

#     @property
#     def monoisotopic_mass(self):
#         return self.compound.monoisotopic_mass


#     def to_wikidata(self):
#         item_label = self.common_name if self.common_name else self.csid

#         pubchem_ref = [[
#             wdi_core.WDItemID(value='Q2311683', prop_nr='P248', is_reference=True),  # stated in
#             wdi_core.WDExternalID(value=self.csid, prop_nr='P661', is_reference=True),  # source element
#             wdi_core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),  # language of work
#             wdi_core.WDMonolingualText(value=item_label[0:200], language='en', prop_nr='P1476', is_reference=True),
#             wdi_core.WDTime(time=time.strftime('+%Y-%m-%dT00:00:00Z'), prop_nr='P813', is_reference=True)  # retrieved
#         ]]
#         print('Main label is', item_label)

#         try:
#             cmpnd = Compound(compound_string=self.smiles, identifier_type='smiles')
#             isomeric_smiles = cmpnd.get_smiles(smiles_type='isomeric')
#             canonical_smiles = cmpnd.get_smiles(smiles_type='generic')
#         except ValueError as e:
#             print(e)
#             print('Error when trying to convert ChemSpider SMILES')
#             canonical_smiles = None
#             isomeric_smiles = None

#         elements = {
#             'P661': self.csid,
#             'P233': canonical_smiles,
#             'P2017': isomeric_smiles,
#             'P235': self.stdinchikey,
#             'P234': self.stdinchi[6:],
#         }

#         dtypes = {
#             'P661': wdi_core.WDExternalID,
#             'P2153': wdi_core.WDExternalID,
#             'P233': wdi_core.WDString,
#             'P2017': wdi_core.WDString,
#             'P235': wdi_core.WDExternalID,
#             'P234': wdi_core.WDExternalID,
#             'P274': wdi_core.WDString
#         }

#         # do not add isomeric smiles if no isomeric info is available
#         if canonical_smiles == isomeric_smiles or len(self.smiles) > 400:
#             del elements['P2017']

#         # do not try to add InChI longer than 400 chars
#         if len(self.stdinchi[6:]) > 400:
#             del elements['P234']

#         if len(self.smiles) > 400:
#             del elements['P233']

#         data = []
#         if float(self.monoisotopic_mass) != 0:
#             data = [
#                 wdi_core.WDQuantity(value=self.monoisotopic_mass, prop_nr='P2067', upper_bound=self.monoisotopic_mass,
#                                     lower_bound=self.monoisotopic_mass, unit='http://www.wikidata.org/entity/Q483261',
#                                     references=pubchem_ref)
#             ]

#         for k, v in elements.items():
#             if not v:
#                 continue

#             print('{}:'.format(k), v)
#             if isinstance(v, list) or isinstance(v, set):
#                 for x in v:
#                     data.append(dtypes[k](prop_nr=k, value=x, references=pubchem_ref))
#             else:
#                 data.append(dtypes[k](prop_nr=k, value=v, references=pubchem_ref))

#         return data

#     @staticmethod
#     def search(search_string):
#         molecules = []

#         cs = chemspipy.ChemSpider(ChemSpiderMolecule.token)

#         for x in cs.search(search_string):
#             molecules.append(ChemSpiderMolecule(mol=x))
#             # print(x.common_name)
#             # print(x.stdinchikey)
#             # print(x.stdinchi)
#             # print(x.csid)
#         return molecules


class PubChemMolecule(object):

    # s = requests.Session()
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'charset': 'utf-8'
    }

    base_url = 'http://pubchem.ncbi.nlm.nih.gov/rest/rdf/{}'

    def __init__(self, cid=None, inchi_key=None, inchi=None, sid=None, mol_type='canonical'):
        self.dtxsid = None
        self.einecs = None
        self.cas = None
        self.zinc = None
        self.chembl = None
        self.kegg = None
        self.chebi = None
        self.unii = None

        self._cid = None
        self._sids = None
        self._inchi_key = None
        self._inchi = None
        self._canonical_smiles = None
        self._isomeric_smiles = None
        self._exact_mass = None
        self._molecular_formula = None
        self._aids = None

        # self.s = requests.Session()
        # PubChemMolecule.s.close()
        # PubChemMolecule.s = self.s
        print('cid parameter value', cid)
        if cid:
            self.cid = cid
        if sid:
            self.sids = sid
        if inchi_key:
            self.stdinchikey = inchi_key
        if inchi:
            self.inchi = inchi

        assert(mol_type == 'canonical' or mol_type == 'zwitterion')
        self.mol_type = mol_type

        if cid:
            pass
        elif inchi_key:
            cids = self._retrieve_pubchem_cids(self.stdinchikey)
            if len(cids) == 0:
                raise InChIKeyMissingError('InChI key not found in PubChem!')
            if len(cids) == 1:
                self.cid = cids[0]
            else:
                self.cid = self._determine_mol_type(cids)

        self.synonyms = PubChemMolecule._get_synonyms(self.cid)
        self.main_label = '' if len(self.synonyms) == 0 else self.synonyms[0]

    @property
    def canonical_smiles(self):
        if not self._canonical_smiles:
            self._canonical_smiles = PubChemMolecule._get_descriptors(self.cid, 'Canonical_SMILES')
        return self._canonical_smiles

    @canonical_smiles.setter
    def canonical_smiles(self, value):
        self._canonical_smiles = value

    @property
    def isomeric_smiles(self):
        if not self._isomeric_smiles:
            self._isomeric_smiles = PubChemMolecule._get_descriptors(self.cid, 'Isomeric_SMILES')
        return self._isomeric_smiles

    @isomeric_smiles.setter
    def isomeric_smiles(self, value):
        self._isomeric_smiles = value

    @property
    def exact_mass(self):
        """Get exact mass of a PubChem compound."""
        if not self._exact_mass:
            self._exact_mass = PubChemMolecule._get_descriptors(self.cid, 'Exact_Mass')
        return self._exact_mass

    @exact_mass.setter
    def exact_mass(self, value):
        """Set exact mass of a PubChem compound."""
        self._exact_mass = value

    @property
    def molecular_formula(self):
        if not self._molecular_formula:
            self._molecular_formula = PubChemMolecule._get_descriptors(self.cid, 'Molecular_Formula')
        return self._molecular_formula

    @molecular_formula.setter
    def molecular_formula(self, value):
        self._molecular_formula = value

    @property
    def cid(self):
        return self._cid

    @cid.setter
    def cid(self, value):

        if value and not value.lower().startswith('cid'):
            # make sure that the provided cid is an integer, will raise a ValueError if not
            int(value)

            self._cid = 'CID{}'.format(value)
        else:
            self._cid = value

        if self._cid:
            base_data = PubChemMolecule._retrieve_basic_compound_info(self.cid)

            # object triples
            has_parts = set()
            active_ingredient_of = set()
            has_roles = set()
            has_parent = set()

            # deal with item as subject
            subj_data = base_data['compound/' + self._cid]
            del base_data['compound/' + self._cid]

            subj_mapping = {
                'vocabulary#FDAApprovedDrugs': has_roles,
                'vocabulary#is_active_ingredient_of': active_ingredient_of,
                'http://purl.obolibrary.org/obo/has-role': has_roles,
                'vocabulary#has_parent': has_parent
            }

            for k, v in subj_data.items():
                if k not in subj_mapping:
                    continue

                value =  v[0]['value']
                if value.startswith('compound/CID'):
                    value = value.split('/')[-1]
                subj_mapping[k].add(value)

            # subject properties
            isotopologues = set()
            stereoisomers = set()
            same_connectivity = set()
            sids = set()
            parent_of = set()
            part_of = set()

            obj_mapping = {
                'vocabulary#has_parent': parent_of,
                'http://semanticscience.org/resource/CHEMINF_000455': isotopologues,
                'http://semanticscience.org/resource/CHEMINF_000461': stereoisomers,
                'http://semanticscience.org/resource/CHEMINF_000462': same_connectivity,
                'http://semanticscience.org/resource/CHEMINF_000477': sids,
                'http://semanticscience.org/resource/CHEMINF_000478': part_of,
                'http://semanticscience.org/resource/has-attribute': set(),
                'http://semanticscience.org/resource/CHEMINF_000446': 'cas',
                'http://semanticscience.org/resource/CHEMINF_000447': 'einecs',
                'http://semanticscience.org/resource/CHEMINF_000412': 'chembl',
                'http://semanticscience.org/resource/CHEMINF_000409': 'kegg',
                'http://semanticscience.org/resource/CHEMINF_000407': 'chebi',
                'http://semanticscience.org/resource/CHEMINF_000563': 'unii',

            }

            prefix_mapping = {
                ('DTXSID', 'dtxsid'),
                ('ZINC', 'zinc')
            }

            # deal with item as object
            for k, v in base_data.items():
                if k.startswith('inchikey'):
                    self.stdinchikey = k.split('/')[-1]
                    continue

                if k.startswith('synonym/MD5_'):
                    # print(k)

                    res = requests.get(url=self.base_url.format(k + '.json'), headers=self.headers).json()

                    identifier = [x['value'] for x in res[k]['http://semanticscience.org/resource/has-value']]

                    types = [x['value'] for x in res[k]['http://www.w3.org/1999/02/22-rdf-syntax-ns#type']]

                    # retrieve database identifiers
                    if len(types) == 1 and types[0] == 'http://semanticscience.org/resource/CHEMINF_000467':
                        for pref, prop in prefix_mapping:
                            if identifier[0].startswith(pref):
                                #print(prop, identifier[0])
                                setattr(self, prop, identifier[0])

                    for x in types:
                        if x in obj_mapping:

                            # process identifier strings from PubChem, if needed
                            #EINECS
                            if x == 'http://semanticscience.org/resource/CHEMINF_000447':
                                identifier = [x.split(' ').pop() for x in identifier]
                            #ChEBI
                            if x == 'http://semanticscience.org/resource/CHEMINF_000407':
                                identifier = list(set([x.split(':').pop() for x in identifier]))
                            #UNII
                            if x == 'http://semanticscience.org/resource/CHEMINF_000563':
                                identifier = list(set([x.upper() for x in identifier]))

                            #print(obj_mapping[x], x, identifier)
                            setattr(self, obj_mapping[x], identifier)

                for kk, vv in v.items():
                    if kk not in obj_mapping:
                        continue

                    obj_mapping[kk].add(k.split('/')[-1])

            self.sids = list(sids)

    @property
    def sids(self):
        return self._sid

    @sids.setter
    def sids(self, value):
        self._sid = value

    @property
    def aids(self):
        return self._aids

    @aids.setter
    def aids(self, value):
        self._aids = value

    @property
    def stdinchikey(self):
        return self._inchi_key

    @stdinchikey.setter
    def stdinchikey(self, value):
        self._inchi_key = value

    @property
    def inchi(self):
        if not self._inchi:
            self._inchi = PubChemMolecule._get_descriptors(self.cid, 'IUPAC_InChI')
        return self._inchi

    @inchi.setter
    def inchi(self, value):
        self._inchi = value

    @property
    def assay_ids(self):
        return PubChemMolecule._get_assay_ids(self.sids)

    def _determine_mol_type(self, cids):
        print(cids)
        zwitterion_charge_count = []
        for count, cid in enumerate(cids):
            ismiles = PubChemMolecule._get_descriptors(cid, 'Isomeric_SMILES')
            plus_count = ismiles.count('+')
            minus_count = ismiles.count('-')
            zwitterion_charge_count.append(plus_count + minus_count)

        if self.mol_type == 'canonical':
            charge = min(zwitterion_charge_count)
        else:
            charge = max(zwitterion_charge_count)

        if zwitterion_charge_count.count(charge) > 1:
            x = [len(json.dumps(PubChemMolecule._retrieve_basic_compound_info(cids[c])))
                 if z == charge else 0 for c, z in enumerate(zwitterion_charge_count)]
            return cids[x.index(max(x))]
        else:
            return cids[zwitterion_charge_count.index(charge)]

    @staticmethod
    def _get_synonyms(cid):
        url = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{}/synonyms/json'.format(cid[3:])
        # reply = PubChemMolecule.s.get(url, headers=PubChemMolecule.headers)
        # reply = PubChemMolecule.s.get(url, headers=PubChemMolecule.headers)
        reply = requests.get(url, headers=PubChemMolecule.headers)
        if 'Fault' in reply.json():
            return []
        return reply.json()['InformationList']['Information'][0]['Synonym']

    @staticmethod
    def _retrieve_basic_compound_info(cid):
        cmpnd_url = 'https://pubchem.ncbi.nlm.nih.gov/rest/rdf/compound/{}.json'.format(cid)
        print(cmpnd_url)

        # r = PubChemMolecule.s.get(cmpnd_url, headers=PubChemMolecule.headers).json()
        r = requests.get(cmpnd_url, headers=PubChemMolecule.headers).json()

        return r

    @staticmethod
    def _get_descriptors(cid, descr_type):
        url = 'https://pubchem.ncbi.nlm.nih.gov/rest/rdf/descriptor/{}_{}.json'.format(cid, descr_type)

        # descr_json = PubChemMolecule.s.get(url, headers=PubChemMolecule.headers).json()
        descr_json = requests.get(url, headers=PubChemMolecule.headers).json()
        return descr_json['descriptor/{}_{}'
            .format(cid, descr_type)]['http://semanticscience.org/resource/has-value'][0]['value']

    @staticmethod
    def _get_assay_ids(sids):
        url = 'http://pubchem.ncbi.nlm.nih.gov/rest/rdf/query'
        assay_ids = dict()

        for sid_block in [sids[c : c + 20] for c in range(0, len(sids), 20)]:
            r = dict()

            params = {
                'graph': 'substance',
                'pred': 'obo:BFO_0000056',
                'subj': ','.join(['substance:{}'.format(x) for x in sid_block]),
                'format': 'json'
            }

            try:
                response = requests.get(url, params=params, headers=PubChemMolecule.headers)
                print(response.url)
                r = response.json()['results']['bindings']
                print('length response items', len(r))

            except json.JSONDecodeError as e:
                print(e)
                print('Error retrieving PubChem Assay Ids')

            for x in r:
                if 'subject' not in x:
                    continue

                assay_id = x['object']['value'].split('/')[-1].split('_')[0]
                sid = x['subject']['value'].split('/')[-1]

                if sid in assay_ids:

                    assay_ids[sid].add(assay_id)
                else:
                    assay_ids.update({sid: {assay_id}})
        print(assay_ids)
        return assay_ids

    @staticmethod
    def _retrieve_pubchem_cids(ikey):
        url = 'http://pubchem.ncbi.nlm.nih.gov/rest/rdf/inchikey/{}.json'.format(ikey)

        try:
            # r = PubChemMolecule.s.get(url, headers=PubChemMolecule.headers).json()
            r = requests.get(url, headers=PubChemMolecule.headers).json()
        except json.JSONDecodeError as e:
            # print(e.__str__())
            print('PubChem does not have this InChI key', ikey)
            return []

        cids = list()
        if 'http://semanticscience.org/resource/is-attribute-of' in r['inchikey/{}'.format(ikey)]:
            for x in r['inchikey/{}'.format(ikey)]['http://semanticscience.org/resource/is-attribute-of']:
                cids.append(x['value'].split('/')[-1])

        return cids

    # def __del__(self):
    #     self.s.close()

    def to_wikidata(self):
        item_label = self.cid if self.main_label == '' else self.main_label

        pubchem_ref = [[
            wdi_core.WDItemID(value='Q278487', prop_nr='P248', is_reference=True),  # stated in
            wdi_core.WDExternalID(value=self.cid[3:], prop_nr='P662', is_reference=True),  # source element
            wdi_core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),  # language of work
            wdi_core.WDMonolingualText(value=item_label[0:400], language='en', prop_nr='P1476', is_reference=True),
            wdi_core.WDTime(time=time.strftime('+%Y-%m-%dT00:00:00Z'), prop_nr='P813', is_reference=True)  # publication date
        ]]
        print('Main label is', self.main_label)

        elements = {
            'P662': self.cid[3:],
            #'P2153': self.sid[3:],
            'P233': self.canonical_smiles,
            'P2017': self.isomeric_smiles,
            'P235': self.stdinchikey,
            'P234': self.inchi[6:],
            'P274': PubChemMolecule.convert_to_index_numbers(self.molecular_formula),
            'P3117': self.dtxsid,
            'P231': self.cas,
            'P232': self.einecs,
            'P2084': self.zinc,
            'P592': self.chembl,
            'P665': self.kegg,
            'P683': self.chebi,
            'P652': self.unii,

        }

        dtypes = {
            'P662': wdi_core.WDExternalID,
            'P2153': wdi_core.WDExternalID,
            'P233': wdi_core.WDString,
            'P2017': wdi_core.WDString,
            'P235': wdi_core.WDExternalID,
            'P234': wdi_core.WDExternalID,
            'P274': wdi_core.WDString,
            'P232': wdi_core.WDExternalID,
            'P231': wdi_core.WDExternalID,
            'P3117': wdi_core.WDExternalID,
            'P2084': wdi_core.WDExternalID,
            'P592': wdi_core.WDExternalID,
            'P665': wdi_core.WDExternalID,
            'P683': wdi_core.WDExternalID,
            'P652': wdi_core.WDExternalID,


        }

        # do not add isomeric smiles if canonical smiles is the same
        if self.canonical_smiles == self.isomeric_smiles or len(self.isomeric_smiles) > 400:
            del elements['P2017']

        # do not try to add InChI longer than 400 chars
        if len(self.inchi[6:]) > 400:
            del elements['P234']

        if len(self.canonical_smiles) > 400:
            del elements['P233']

        data = [
            wdi_core.WDQuantity(value=self.exact_mass, prop_nr='P2067', upper_bound=self.exact_mass,
                                lower_bound=self.exact_mass, unit='http://www.wikidata.org/entity/Q483261',
                                references=pubchem_ref)
        ]

        for k, v in elements.items():
            if not v:
                continue

            print('{}:'.format(k), v)
            if isinstance(v, list) or isinstance(v, set):
                for x in v:
                    data.append(dtypes[k](prop_nr=k, value=x, references=pubchem_ref))
            else:
                data.append(dtypes[k](prop_nr=k, value=v, references=pubchem_ref))

        return data

    @staticmethod
    def convert_to_index_numbers(formula_string):
        """
        Converts the numbers in a normal string into unicode index numbers (as used in chemical formulas)
        :param formula_string: a string containing numbers which should be converted to index numbers
        :type formula_string: str
        :return: returns a unicode string with numbers converted to index numbers
        """
        index_numbers = ['₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉']
        conventional_numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

        conversion_map = dict(zip(conventional_numbers, index_numbers))

        for i in set(formula_string):
            if i in conversion_map:
                formula_string = formula_string.replace(i, conversion_map[i])

        return formula_string


class InChIKeyMissingError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def main():
    # a = PubChemMolecule(inchi_key='ADPBHYYCECQFTN-UHFFFAOYSA-K')
    # print(a.cid)
    # print(a.main_label)
    #
    # b = PubChemMolecule(inchi_key='PIOZZBNFRIZETM-UHFFFAOYSA-L')
    # print(b.cid)
    # print(b.main_label)
    #
    #
    # c = PubChemMolecule(inchi_key='RNAICSBVACLLGM-GNAZCLTHSA-N')
    # print(c.cid)
    # print(c.main_label)

    login_obj = wdi_login.WDLogin(user='', pwd='')


    query = '''
    SELECT * WHERE {
      ?cmpnd wdt:P235 ?pc .
      FILTER NOT EXISTS{
            #{?cmpnd wdt:P279 wd:Q11173 .} UNION
            #{?cmpnd wdt:P31 wd:Q11173 .} UNION
            {?cmpnd wdt:P662 ?x .}
      }
    }
    '''

    results = wdi_core.WDItemEngine.execute_sparql_query(query=query)

    cid_not_found_count = 0
    for count, item in enumerate(results['results']['bindings']):
        start = time.time()
        ikey = item['pc']['value']
        try:
            print('--' * 10)
            print(ikey)
            cmpnd = PubChemMolecule(inchi_key=ikey)
            print(cmpnd.cid)
            print(cmpnd.canonical_smiles)
            print(cmpnd.isomeric_smiles)
            print(cmpnd.inchi)
            print(cmpnd.exact_mass)
            print(cmpnd.molecular_formula)
            print(cmpnd.main_label)
            print(cmpnd.sids)
            cmpnd.s.close()

            wd_item = wdi_core.WDItemEngine(item_name='ddk', domain='drugs', data=cmpnd.to_wikidata(),
                                            append_value=['P31'])
            print(wd_item.wd_item_id)
            pprint.pprint(wd_item.entity_metadata)
            # pprint.pprint(wd_item.get_wd_json_representation())
            wd_item.write(login_obj)

            # if count > 120:
            #     break
        except InChIKeyMissingError as e:
            print(ikey, e)
            cid_not_found_count += 1
            continue
        except Exception as e:
            print(e)

            wdi_core.WDItemEngine.log(
                'ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'
                    .format(
                        main_data_id='{}'.format(ikey),
                        exception_type=type(e),
                        message=e.__str__(),
                        wd_id='',
                        duration=time.time() - start
                    ))



    print('not found count', cid_not_found_count)




if __name__ == '__main__':
    sys.exit(main())
