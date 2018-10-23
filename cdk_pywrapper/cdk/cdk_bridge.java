/*
 * A py4j bridge for the CDK
 * Also has a class for substructure search and SVG xml generation
 * Copyright 2018 Sebastian Burgstaller-Muehlbacher
 * Licensed under AGPLv3
 */

import py4j.GatewayServer;
import org.openscience.cdk.*;
import org.openscience.cdk.DefaultChemObjectBuilder;
import org.openscience.cdk.interfaces.IChemObjectBuilder;
import org.openscience.cdk.interfaces.IAtomContainer;
import org.openscience.cdk.interfaces.IChemObject;

import org.openscience.cdk.smiles.SmilesParser;
import org.openscience.cdk.exception.InvalidSmilesException;
import org.openscience.cdk.exception.CDKException;
import org.openscience.cdk.smiles.smarts.SmartsPattern;
import org.openscience.cdk.isomorphism.Pattern;
import org.openscience.cdk.isomorphism.Mappings;
import org.openscience.cdk.depict.DepictionGenerator;


import java.util.*;
import java.io.IOException;
import java.awt.Color;
import java.util.concurrent.ConcurrentHashMap;

class CDKBridge {

    public static void main(String[] args) {
        CDKBridge app = new CDKBridge();
        GatewayServer server = new GatewayServer(app);
        server.start();
        System.out.println("Server process started sucessfully");
    }
}

class SearchHandler {

    ConcurrentHashMap<String, IAtomContainer> moleculeContainers;
    Pattern pattern;
    int totalCount = 0;

    public SearchHandler() {
        this.moleculeContainers = new ConcurrentHashMap();
//        this.buildSubstructureIndex(molecules);
    }

    public int buildSubstructureIndex(HashMap<String, String> mols) {
        ConcurrentHashMap<String,String> molecules = new ConcurrentHashMap<> (mols);
        IChemObjectBuilder builder = DefaultChemObjectBuilder.getInstance();
        SmilesParser parser = new SmilesParser(builder);

        molecules.forEach(
                1,

                (k, v) -> {
                    try {
                        this.moleculeContainers.put(k, parser.parseSmiles(v));

                    } catch (InvalidSmilesException e) {
                        System.err.println(e.getMessage());
                    }

                }
        );

//        moleculeContainers = new ConcurrentHashMap<String, IAtomContainer> (molecules);


//        int counter = 0;
//        for (Map.Entry<String, String> entry : molecules.entrySet()) {
//            String id = entry.getKey();
//            String smiles = entry.getValue();
//
//
//            try {
//                IAtomContainer c = parser.parseSmiles(smiles);
//                counter += 1;
//                this.moleculeContainers.put(id, c);
//
//            } catch (InvalidSmilesException e) {
//                System.err.println(e.getMessage());
//            }
//        }
//
//        System.out.println("Molecule Container size: " + this.moleculeContainers.size());
//
//        return counter;
        return molecules.size();
    }

    public String getSVG(IAtomContainer c, Iterable<IChemObject> substructures) {
        Color color = Color.orange;

        DepictionGenerator dg = new DepictionGenerator()
                .withHighlight(substructures, color)
                .withAtomColors()
                .withOuterGlowHighlight(4.0);

        try {
            return dg.depict(c).toSvgStr();

        } catch (CDKException e) {
            System.err.println(e.getMessage());
            return "";
        }
    }

    public ArrayList<ArrayList> searchPattern(String p, HashMap<String, String> mols) {

        ConcurrentHashMap<String,String> molecules = new ConcurrentHashMap<> (mols);
        IChemObjectBuilder builder = DefaultChemObjectBuilder.getInstance();
        SmilesParser parser = new SmilesParser(builder);

//        final int totalCount = 0;

        try {
            this.pattern = SmartsPattern.create(p);
        } catch (IOException e) {
            System.err.println(e.getMessage());

            return new ArrayList();
        }

        ConcurrentHashMap<String, ArrayList> ma = new ConcurrentHashMap<> ();

        molecules.forEach(
                1,

                (k, v) -> {
                    if (this.totalCount < 200) {
                        try {

                            IAtomContainer ac = parser.parseSmiles(v);

                            Mappings mappings = pattern.matchAll(ac);
                            int match_count = mappings.countUnique();

                            if (match_count > 0) {
                                Iterable<IChemObject> substructures = mappings.toChemObjects();
                                String svg = this.getSVG(ac, substructures);

                                ArrayList<String> tmp = new ArrayList(3);
                                tmp.add(0, k);
                                tmp.add(1, String.valueOf(match_count));
                                tmp.add(2, svg);
                                ma.put(k, tmp);

                                this.totalCount += 1;
                            }


                        } catch (InvalidSmilesException e) {
                            System.err.println(e.getMessage());
                        }
                    }
                }
        );


        ArrayList<ArrayList> matches = new ArrayList(500);
        for (Map.Entry<String, ArrayList> entry : ma.entrySet()) {
            matches.add(entry.getValue());

        }

//        try {
//            Pattern pattern = SmartsPattern.create(p);
//
//            int totalCount = 0;
//            for (Map.Entry<String, IAtomContainer> entry : moleculeContainers.entrySet()) {
//                String key = entry.getKey();
//                IAtomContainer ac = entry.getValue();
//                Mappings mappings = pattern.matchAll(ac);
//                int match_count = mappings.countUnique();
//
//                if (match_count > 0) {
//                    Iterable<IChemObject> substructures = mappings.toChemObjects();
//                    String svg = this.getSVG(ac, substructures);
//
//                    ArrayList<String> tmp = new ArrayList(3);
//                    tmp.add(0, key);
//                    tmp.add(1, String.valueOf(match_count));
//                    tmp.add(2, svg);
//                    matches.add(tmp);
//
//                    totalCount += 1;
//                }
//
//                if (totalCount > 200) {
//                    return matches;
//                }
//            }
//
//        } catch (IOException e) {
//            System.err.println(e.getMessage());
//        }

        return matches;
    }
}

