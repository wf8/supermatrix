#! /usr/bin/python
"""
SUMAC: supermatrix constructor

Copyright 2014 Will Freyman - freyman@berkeley.edu
License: GNU GPLv3 http://www.gnu.org/licenses/gpl.html
"""

import os
import sys
import argparse

from util import Color
from genbank import GenBankSetup
from genbank import GenBankSearch
from distancematrix import DistanceMatrixBuilder
from clusters import DistanceMatrixClusterBuilder
from clusters import GuidedClusterBuilder
import alignments


def main():
    # parse the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--download_gb", "-d", help="Name of the GenBank division to download (e.g. PLN or MAM).")
    parser.add_argument("--path", "-p", help="Absolute path to download GenBank files to. Defaults to ./genbank/")
    parser.add_argument("--ingroup", "-i", help="Ingroup clade to build supermatrix.")
    parser.add_argument("--outgroup", "-o", help="Outgroup clade to build supermatrix.")
    parser.add_argument("--max_outgroup", "-m", help="Maximum number of taxa to include in outgroup. Defaults to 10.")
    parser.add_argument("--evalue", "-e", help="BLAST E-value threshold to cluster taxa. Defaults to 0.1")
    parser.add_argument("--length", "-l", help="Threshold of sequence length percent similarity to cluster taxa. Defaults to 0.5")
    parser.add_argument("--guide", "-g", help="""FASTA file containing sequences to guide cluster construction. If this option is 
                                                 selected then all-by-all BLAST comparisons are not performed.""")
    args = parser.parse_args()
 
    color = Color()

    print("")
    print(color.blue + "SUMAC: supermatrix constructor" + color.done)
    print("")

    # download and set up sqllite db
    if args.path:
        gb_dir = args.path
    else:
        gb_dir = os.path.abspath("genbank/")
    if args.download_gb:
        GenBankSetup.download(args.download_gb, gb_dir)
        print(color.yellow + "Setting up SQLite database..." + color.done)
        gb = GenBankSetup.sqlite(gb_dir)
    elif not os.path.exists(gb_dir + "/gb.idx"):
        print(color.red + "GenBank database not downloaded. Re-run with the -d option. See --help for more details." + color.done)
        sys.exit(0)
    else:
        print(color.purple + "Genbank database already downloaded. Indexing sequences..." + color.done)
        gb = GenBankSetup.sqlite(gb_dir)
    print(color.purple + "%i sequences indexed!" % len(gb) + color.done)

    # check for ingroup and outgroup
    if args.ingroup and args.outgroup:
        ingroup = args.ingroup
        outgroup = args.outgroup
    else:
        print(color.red + "Please specify ingroup and outgroup. See --help for details." + color.done)
        sys.exit(0)
    
    # search db for ingroup and outgroup sequences
    print(color.blue + "Outgroup = " + outgroup)
    print("Ingroup = " + ingroup + color.done)
    print(color.blue + "Searching for ingroup and outgroup sequences..." + color.done)
    search_results = GenBankSearch(gb, ingroup, outgroup)
    ingroup_keys = search_results.ingroup_keys
    outgroup_keys = search_results.outgroup_keys
    all_seq_keys = ingroup_keys + outgroup_keys

    # determine sequence length similarity threshold
    length_threshold = 0.5
    if args.length:
        length_threshold = args.length
    print(color.blue + "Using sequence length similarity threshold " + color.red + str(length_threshold) + color.done)

    # determine e-value threshold
    evalue_threshold = (1.0/10**10)
    if args.evalue:
        evalue_threshold = float(args.evalue)
    print(color.blue + "Using BLAST e-value threshold " + color.red + str(evalue_threshold) + color.done)

    # now build clusters, first checking whether we are using FASTA file of guide sequences
    # or doing all-by-all comparisons
    if args.guide:
        # use FASTA file of guide sequences
        print(color.blue + "Building clusters using the guide sequences..." + color.done)
        cluster_builder = GuidedClusterBuilder(args.guide, all_seq_keys, length_threshold, evalue_threshold, gb_dir)
    else:
        # make distance matrix
        print(color.blue + "Making distance matrix for all sequences..." + color.done)
        distance_matrix = DistanceMatrixBuilder(gb, all_seq_keys, length_threshold, gb_dir).distance_matrix

        # cluster sequences
        print(color.purple + "Clustering sequences..." + color.done)
        cluster_builder = DistanceMatrixClusterBuilder(all_seq_keys, distance_matrix, evalue_threshold)

    print(color.purple + "Found " + color.red + str(len(cluster_builder.clusters)) + color.purple + " clusters." + color.done)
    if len(cluster_builder.clusters) == 0:
        print(color.red + "No clusters found." + color.done)
        sys.exit(0)

    # filter clusters, make FASTA files
    print(color.yellow + "Building sequence matrices for each cluster." + color.done)
    cluster_builder.assemble_fasta(gb)
    print(color.purple + "Kept " + color.red + str(len(cluster_builder.clusters)) + color.purple + " clusters, discarded those with < 4 taxa." + color.done)
    if len(cluster_builder.clusters) == 0:
        print(color.red + "No clusters left to align." + color.done)
        sys.exit(0)

    # now align each cluster with MUSCLE
    print(color.blue + "Aligning clusters with MUSCLE..." + color.done)
    alignments = Alignments(cluster_builder.cluster_files)
    alignments.print_region_data()

    # concatenate alignments
    print(color.purple + "Concatenating alignments..." + color.done)
    alignments.concatenate()
    print(color.yellow + "Final alignment: " + color.red + "alignments/combined.fasta" + color.done)

    # TODO:
    # reduce the number of outgroup taxa, make graphs, etc



if __name__ == "__main__":
    main()
