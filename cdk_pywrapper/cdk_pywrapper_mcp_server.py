from fastmcp import FastMCP
from typing import Dict, List

import importlib.resources
import pandas as pd

from cdk_pywrapper.cdk_pywrapper import Compound, gateway
from cdk_pywrapper.chemlib import ChEMBLMolecule, GTPLMolecule

# Create an MCP server instance
mcp = FastMCP("Cheminformatics Toolkit")

gtp_data_path = str(importlib.resources.files('cdk_pywrapper.data').joinpath("ligands.csv"))
print("Loading compound database from", gtp_data_path)
gtp_data = pd.read_csv(
    gtp_data_path,
    comment='#',                 # skip any lines starting with #
    skiprows=1,
    skip_blank_lines=True,
    low_memory=False,
    dtype={'PubChem SID': 'str', 'PubChem CID': 'str', 'Ligand ID': 'str'}
)

@mcp.tool()
def get_compound_identifiers(compound_string: str, identifier_type: str) -> Dict[str, str]:
    """
    Provides the SMILES, InChI, and InChIKey for a given chemical structure.

    :param compound_string: The chemical structure as a string (e.g., a SMILES or InChI).
    :param identifier_type: The type of the input chemical structure ('smiles' or 'inchi').
    :return: A dictionary containing the SMILES, InChI, and InChIKey.
    """
    try:
        compound = Compound(compound_string, identifier_type)
        return {
            "smiles": compound.get_smiles(),
            "inchi": compound.get_inchi(),
            "inchi_key": compound.get_inchi_key(),
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def calculate_molecular_descriptors(compound_string: str, identifier_type: str) -> Dict[str, str]:
    """
    Calculates a set of common molecular descriptors for a given molecule.

    :param compound_string: The chemical structure as a string (e.g., a SMILES or InChI).
    :param identifier_type: The type of the input chemical structure ('smiles' or 'inchi').
    :return: A dictionary of calculated molecular descriptors.
    """
    try:
        compound = Compound(compound_string, identifier_type)
        return {
            "molecular_weight": compound.get_mw(),
            "monoisotopic_mass": compound.get_monoisotopic_mass(),
            "tpsa": compound.get_tpsa(),
            "xlogp": compound.get_xlogp(),
            "rotatable_bond_count": compound.get_rotable_bond_count(),
            "h_bond_donor_count": compound.get_hbond_donor_count(),
            "h_bond_acceptor_count": compound.get_hbond_acceptor_count(),
            "rule_of_five_failures": compound.get_ro5_failures(),
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def generate_molecule_svg(compound_string: str, identifier_type: str) -> str:
    """
    Generates a 2D SVG image of a molecule.

    :param compound_string: The chemical structure as a string (e.g., a SMILES or InChI).
    :param identifier_type: The type of the input chemical structure ('smiles' or 'inchi').
    :return: An SVG image as a string.
    """
    try:
        compound = Compound(compound_string, identifier_type)
        return compound.get_svg()
    except Exception as e:
        return f"<svg>Error: {e}</svg>"

@mcp.tool()
def get_tautomers(compound_string: str, identifier_type: str) -> List[str]:
    """
    Finds and returns the SMILES representations of a molecule's tautomers.

    :param compound_string: The chemical structure as a string (e.g., a SMILES or InChI).
    :param identifier_type: The type of the input chemical structure ('smiles' or 'inchi').
    :return: A list of SMILES strings for the generated tautomers.
    """
    try:
        compound = Compound(compound_string, identifier_type)
        tautomers_containers = compound.get_tautomers()
        tautomer_smiles = [
            Compound(ac, "atom_container").get_smiles() for ac in tautomers_containers
        ]
        return tautomer_smiles
    except Exception as e:
        return [f"Error: {e}"]

@mcp.tool()
def perform_substructure_search(smiles: str, smarts_pattern: str) -> Dict:
    """
    Performs a substructure search on a molecule using a SMARTS pattern.

    :param smiles: The SMILES string of the molecule to be searched.
    :param smarts_pattern: The SMARTS pattern for the substructure query.
    :return: A dictionary indicating if a match was found and the number of matches.
    """
    try:
        compound = Compound(smiles, "smiles")
        querytool = gateway.jvm.org.openscience.cdk.smiles.smarts.SMARTSQueryTool(
            smarts_pattern, gateway.jvm.org.openscience.cdk.DefaultChemObjectBuilder.getInstance()
        )
        matches = querytool.matches(compound.mol_container)
        if matches:
            return {
                "match_found": True,
                "match_count": querytool.countMatches()
            }
        else:
            return {"match_found": False, "match_count": 0}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def calculate_lipinski_rule_of_5(compound_string: str, identifier_type: str) -> Dict[str, any]:
    """
    Calculates Lipinski's Rule of 5 for a given molecule.

    :param compound_string: The chemical structure as a string (e.g., a SMILES or InChI).
    :param identifier_type: The type of the input chemical structure ('smiles' or 'inchi').
    :return: A dictionary containing the number of rule of 5 failures.
    """
    try:
        compound = Compound(compound_string, identifier_type)
        return {
            "rule_of_five_failures": compound.get_ro5_failures(),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def query_chembl_by_inchi_key(inchi_key: str) -> Dict[str, any]:
    """
    Query ChEMBL using an InChIKey and return common fields.

    :param inchi_key: The InChIKey to query ChEMBL with.
    :return: A dictionary with ChEMBL id, SMILES, InChI, InChIKey and other metadata, or an error.
             Dictionary values may be integers, floats, or strings.
    """
    try:
        chem = ChEMBLMolecule(inchi_key=inchi_key)
        res =  {
            "chembl_id": chem.chembl_id,
            "smiles": chem.smiles,
            "inchi": chem.stdinchi,
            "inchi_key": chem.stdinchikey,
            "preferred_name": chem.preferred_name,
            "monoisotopic_mass": chem.monoisotopic_mass,
            "chebi": chem.chebi,
        }
        print(res)
        return res
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def search_compound_by_name(name: str) -> Dict[str, any]:
    """
    Query compound by name in compound database and return common fields and identifiers. 

    :param name: The compound name to search for.
    :return: A dictionary with ChEMBL id, SMILES, InChI, InChIKey and other metadata, or an error.
             Dictionary values may be integers, floats, or strings.
    """
    # search_results = gtp_data.loc[gtp_data['Name'].str.lower() == name.lower()]
#    gtp_data_path = str(importlib.resources.files('cdk_pywrapper.data').joinpath("ligands.csv"))
#    print("Loading compound database from", gtp_data_path)
#    gtp_data = pd.read_csv(gtp_data_path, low_memory=False, dtype={'PubChem SID': 'str', 'PubChem CID': 'str', 'Ligand ID': 'str'})

    search_results = gtp_data.loc[gtp_data['Name'].fillna('').str.contains(name, case=False), :]
    if search_results.shape[0] > 0:
        ligand_id = search_results['Ligand ID'].iloc[0]
    else:
        return {"error": "No compound found with that name"}

    try:
        chem = GTPLMolecule(gtpl_id=ligand_id)
        res =  {
            "gtpl_id": chem.gtpl_id,
            "smiles": chem.smiles,
            "inchi": chem.stdinchi,
            "inchi_key": chem.stdinchikey,
            "preferred_name": chem.preferred_name,
            "synonyms": chem.synonyms,
        }
        print(res)
        return res
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="CDK_pywrapper MCP Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        print("Debug mode enabled", file=sys.stderr)
    
    # Run in stdio mode (default for MCP)
    mcp.run()


def main():
    """Entry point for the MCP server (stdio mode by default)."""
    mcp.run()


def main_debug():
    """Entry point for debug mode."""
    import sys
    import logging
    logging.basicConfig(level=logging.DEBUG)
    print("CDK_pywrapper MCP Server - Debug mode enabled", file=sys.stderr)
    mcp.run()