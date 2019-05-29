#!/usr/bin/python3

import absreader
import csv
import os
import sys

class HarvestReader(absreader.AbstractReader):

    def getReaderName():
        return "harvest"

    def __init__(self):
        pass
    
    def __del__(self):
        pass
        
    def getContents(self, file_or_dir):
        if file_or_dir == None:
            print("Please specify an input Harvest-style CSV file.", file=sys.stderr)
            exit(1)
        if not os.path.exists(file_or_dir):
            print("Dataset %s does not exist." % file_or_dir, file=sys.stderr)
            exit(1)

        with open(file_or_dir, "r") as fp:
            reader = csv.reader(fp)
            headers = next(reader)
            N_features = len(headers) - 1
            taxa = []
            chars = []
            for i in range(0, N_features):
                chars.append([])
            try:
                for row in reader:
                    taxa.append(row[0])
                    for i, point in enumerate(row[1:]):
                        chars[i].append(point)
            except IndexError:
                print("Unable to parse file %s." % file_or_dir, file=sys.stderr)
                exit(1)
        return [taxa,chars]
        
if __name__ == '__main__':
    print("Harvest-style CSV reader class for tiger-calculator")
