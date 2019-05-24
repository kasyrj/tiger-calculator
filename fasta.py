#!/usr/bin/python3

import absreader

class FastaReader(absreader.AbstractReader):

    def getReaderName():
        return "fasta"

    def __init__(self):
        pass
    
    def __del__(self):
        pass
        
    def getContents(self, file_or_dir):
        if file_or_dir == None:
            print("Please specify an input FASTA file.")
            exit(1)
        try:
            f = open(file_or_dir,"r")
            infile = f.readlines()
            f.close()
        except FileNotFoundError:
            print("Could not find FASTA file %s" % file_or_dir)
            exit(1)
        # parse fasta to two arrays (one with taxa and another with chars)
        taxa = []
        chars = []
        current_chars = ""
        for line in infile:
            line = line.strip().rstrip()
            if len(line) == 0:          # empty line
                continue
            if line[0] == ";":          # comment line
                continue
            if line[0] == ">":          # taxon name line
                taxa.append(line[1:])
                if current_chars != "":
                    chars.append(current_chars)
                    current_chars = ""
            else:                       # character line
                current_chars += line
        if current_chars != "":
            chars.append(current_chars)
            current_chars = ""
        try:
            assert(len(taxa) == len(chars))
            for i in chars:
                assert(len(i) == len(chars[0]))
        except AssertionError:
            print("Unable to read file %s correctly. Please ensure that the input file is in FASTA format." % file_or_dir)
            exit(1)
        return [taxa,chars]
        
if __name__ == '__main__':
    print("FASTA reader class for tiger-calculator")
