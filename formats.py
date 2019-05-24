#!/usr/bin/python3

import cldf
import fasta

_readers = {}
_readers[fasta.FastaReader.getReaderName()] = fasta.FastaReader()
_readers[cldf.CldfReader.getReaderName()] = cldf.CldfReader()

def getFormats():
    '''List available formats (reader names).'''
    return _readers.keys()

def getReader(format):
    '''Return a reader instance with the specified format (reader name)'''
    if format not in getFormats():
        return None
    return _readers[format]

def getFormatsAsString():
    '''Return available formats as comma-separated string'''
    result = ""
    for f in getFormats():
        result += ", " + f
    return result[2:]
    
if __name__ == '__main__':
    print("File format handling functions for tiger-calculator.")
