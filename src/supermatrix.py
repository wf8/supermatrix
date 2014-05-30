"""
SUMAC: supermatrix constructor

Copyright 2014 Will Freyman - freyman@berkeley.edu
License: GNU GPLv3 http://www.gnu.org/licenses/gpl.html
"""


import os
import sys
from Bio import Entrez
from Bio import SeqIO
from util import Color



class Supermatrix(object):
    """
    Class responsible for managing the final supermatrix
    """


    file = ""   # FASTA file of final supermatrix
    otus = {}   # dictionary of Otu objects



    def __init__(self, alignments):
        """
        Builds a supermatrix from a set of alignments.
        """
        otus = {}
        for alignment in alignments.files:
            records = SeqIO.parse(alignment, "fasta")
            for record in records:
                # sample record.description:
                # AF495760.1 Lythrum salicaria chloroplast ribulose 1,5-bisphosphate carboxylase/oxygenase large subunit-like mRNA, partial sequence
                descriptors = record.description.split(" ")
                otu = descriptors[1] + " " + descriptors[2]
                if otu not in otus.keys():
                    otus[otu] = Otu(otu)

        # now concatenate the sequences
        total_length = 0
        for alignment in alignments.files: 
            records = SeqIO.parse(alignment, "fasta")
            # make sure to only add 1 sequence per cluster for each otu
            already_added = []
            for record in records:
                descriptors = record.description.split(" ")
                otu = descriptors[1] + " " + descriptors[2]
                if otu not in already_added:
                    otus[otu].update(record.seq, descriptors[0], self.get_ungapped_length(record.seq))
                    already_added.append(otu)
                loci_length = len(record.seq)
            total_length += loci_length
            # add gaps for any OTU that didn't have a sequence
            for otu in otus:
                if len(otus[otu].sequence) < total_length:
                    otus[otu].update(self.make_gaps(loci_length), "-", 0)

        # write to FASTA file
        f = open("alignments/combined.fasta", "w")
        for otu in otus:
            # >otu
            # otus[otu]
            f.write("> " + otu + "\n")
            sequence = str(otus[otu].sequence)
            i = 0
            while i < len(sequence):
                f.write(sequence[i:i+80] + "\n")
                i += 80
        f.close()
        self.file = "alignments/combined.fasta"
        self.otus = otus



    def make_gaps(self, length):
        """
        Inputs an integer.
        Returns a string of '-' of length
        """
        gap = ""
        for i in range(length):
            gap = "-" + gap
        return gap



    def get_ungapped_length(self, sequence):
        """
        Inputs a sequence, and returns the length of the sequence minus any gaps ('-')
        """
        length = 0
        for i in sequence:
            if i != "-":
                length += 1
        return length



    def print_data(self):
        """
        Prints out details on the final aligned supermatrix.
        """
        # TODO: make the output of this more useful
        color = Color()
        print(color.blue + "Supermatrix attributes:")
        records = SeqIO.parse(self.file, "fasta")
        num_records = 0
        total_gap = 0
        for record in records:
            otu = record.description
            gap = 0
            for letter in record.seq:
                if letter == '-':
                    gap += 1
                    total_gap += 1
            print(color.yellow + "OTU: " + color.red + otu + color.yellow + " % gaps = " + color.red + str(round(gap/float(len(record.seq)), 2)))
            num_records += 1
            matrix_length = len(record.seq)
        print(color.blue + "Total number of OTUs = " + color.red + str(num_records))
        print(color.blue + "Total length of matrix = " + color.red + str(matrix_length))
        print(color.blue + "Total % gaps = " + color.red + str(round(total_gap/float(matrix_length * num_records), 2)) + color.done)
        #for otu in self.otus: 
        #    self.otus[otu].print_data()



class Otu(object):
    """
    Class responsible for managing the data of each OTU in the supermatrix
    """

    
    name = ""               # the name of the OTU
    sequence = ""           # the full aligned sequence for this OTU in the supermatrix
    accessions = []         # list of each GenBank accession used where "-" means no sequence for that region
    sequence_lengths = []   # list of the length of each sequence



    def __init__(self, name):
        """
        Takes as input the name of the OTU
        """
        self.name = name
        self.sequence = ""
        self.accessions = []
        self.sequence_lengths = []



    def update(self, sequence, accession, sequence_length):
        """
        Inputs the aligned sequence (gaps already added), the accession #, and the unaligned sequence length.
        """
        self.sequence = self.sequence + sequence
        self.accessions.append(accession)
        self.sequence_lengths.append(sequence_length)



    def print_data(self):
        color = Color()
        print(color.blue + "Name = " + color.red + self.name)
        print(color.blue + "Sequence = " + color.red + self.sequence)
        print(color.blue + "Accessions = "  + color.red)
        print(self.accessions)
        print(color.blue + "Sequence_lengths = " + color.red)
        print(self.sequence_lengths)


