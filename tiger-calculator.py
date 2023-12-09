#!/usr/bin/python3

import sys
import argparse
import formats
import os
import multiprocessing
multiprocessing.set_start_method('fork') # multiprocessing fix for Mac Pythons changing the default start method in Python 3.7.

PARSER_DESC = "Simple TIGER rates calculator."
FORMAT_ERROR_MSG = "Please specify one of the available formats: " + formats.getFormatsAsString()
N_PROCESSES = int(multiprocessing.cpu_count())


class ActivePool(object):
    def __init__(self):
        super(ActivePool, self).__init__()
        self.mgr = multiprocessing.Manager()
        self.active = self.mgr.list()
        self.result = self.mgr.dict()
        self.data = self.mgr.dict()
        self.lock = multiprocessing.Lock()

    def makeActive(self, name):
        with self.lock:
            self.active.append(name)

    def makeInactive(self, name):
        with self.lock:
            self.active.remove(name)

    def __str__(self):
        with self.lock:
            return str(self.active)


def split_list(alist, wanted_parts=1):
    '''Split a list equally into a specified number of parts'''
    length = len(alist)
    return [ alist[i*length // wanted_parts: (i+1)*length // wanted_parts] 
             for i in range(wanted_parts) ]


def calculate_tiger_rates(analyzed_keys):
    '''Calculate partition agreements and TIGER rates for the characters specified by the array keys'''
    results = {}
    for x in analyzed_keys:
        agr_array = []
        for y in char_dict.keys():
            if x == y:
                continue
            agreements = 0 # numerator of pa(i,j)
            total = 0      # denominator of pa(i,j). Equal to len(char_dict)-1.
            valid_taxa = set()
            for sp_x in set_parts[x]:
                valid_taxa = valid_taxa|set_parts[x][sp_x] # set of taxa without missing data for site x
            for sp_y in set_parts[y]:
                match = False
                for sp_x in set_parts[x]:
                    current_x = set_parts[x][sp_x]
                    current_y = set_parts[y][sp_y]
                    if current_y.intersection(valid_taxa).issubset(current_x): # Compare taxa in y minus missing taxa in x to taxa in x
                        match = True
                        break # Found a match; don't compare the remaining ones
                total += 1
                if match:
                    agreements += 1
            agr_array.append(float(agreements)/total)
        # Calculate TIGER rates
        results[x] = sum(agr_array) / len(agr_array) # TIGER rate for the current character
    return results


def calculate_tiger_rates_multiprocessing(analyzed_keys, pool, s):
    '''Calculate partition agreements and TIGER rates for the characters specified by the array keys (multiprocessing)'''
    name = multiprocessing.current_process().name
    with s:
        pool.makeActive(name)
        data = pool.data
        result = calculate_tiger_rates(analyzed_keys)
        for k in result.keys():
            pool.result[k] = result[k]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=PARSER_DESC)

    parser.add_argument(dest="in_file",
                        help="Input file to analyze.",
                        metavar='IN_FILE',
                        default=None,
                        type=str)

    parser.add_argument("-f", "--format",
                        dest="format",
                        help="Specify input format. Available formats: " + formats.getFormatsAsString(),
                        default="",
                        type=str)

    parser.add_argument("-i","--ignored-characters",
                        dest="ignored_chars",
                        help="A comma-separated list of ignored characters. Missing characters should be included here.",
                        default="",
                        type=str)

    parser.add_argument("-x","--excluded-taxa",
                        dest="excluded_taxa",
                        help="A comma-separated list of taxa excluded from the calculations.",
                        default="",
                        type=str)

    parser.add_argument("-p","--processes",
                        dest="n_processes",
                        help="Number of processes (threads) to use. Default: %i (the detected number of logical CPUs). Currently only works on Linux and Mac." % N_PROCESSES,
                        default=N_PROCESSES,
                        type=int)

    parser.add_argument("-n","--named-characters",
                        dest="named_characters",
                        help="Include a column identifying which TIGER rate belongs to which aligned character.",
                        default=False,
                        action='store_true')

    parser.add_argument("-s","--synonym-strategy",
                        dest="synonym_strategy",
                        help="Strategy for resolving synonyms.  Available strategies: random, minimum, maximum.",
                        default="minimum",
                        type=str)

    if len(sys.argv) == 1:
        parser.print_help()
        exit(0)
    args = parser.parse_args()
    if args.format == None:
        print(FORMAT_ERROR_MSG, file=sys.stderr)
        exit(1)

    reader = formats.getReader(args.format)
    if args.format == "cldf":
        reader.synonym_strategy = args.synonym_strategy

    if reader == None:
        print(FORMAT_ERROR_MSG, file=sys.stderr)
        exit(1)

    content = reader.getContents(args.in_file)
    taxa = content[0]
    chars = content[1]
    try:
        names = content[2]
    except:
        names = range(1, len(chars[0]) + 1)

    excluded_taxa = args.excluded_taxa.split(",")
    if excluded_taxa != [""]:
        excluded_taxa = set(excluded_taxa)
        for taxon in excluded_taxa:
            if taxon not in taxa:
                print("Taxon %s not found in data." % taxon, file=sys.stderr)
                exit(1)
        while len(excluded_taxa) > 0:
            for i in range(len(taxa)):
                if taxa[i] in excluded_taxa:
                    current_taxon = taxa[i]
                    excluded_taxa.remove(current_taxon)
                    del taxa[i]
                    del chars[i]
                    break

    ignored_chars = args.ignored_chars.split(",")

    if len(taxa) == 0 or len(chars) == 0:
        print("Error: Empty characters or taxa in input file.", file=sys.stderr)
        exit(1)

    # set up a dict with [char_num][taxon] format. Each terminal node contains an aligned character

    char_dict = {}
    for i in range(len(chars[0])):
        char_dict[i] = {}
        for j in range(len(taxa)):
            char_dict[i][taxa[j]] = chars[j][i]

    # Step 1: collect set partitions

    # set up a dict with [site][char] format, where each terminal node contains a set of taxa
    set_parts = {}
    for i in range(len(chars[0])):
        set_parts[i] = {}

    for site in char_dict.keys():
        # Collect a set of what chars this site contains. Set up the necessary arrays in set_parts.
        chars_at_site = set()
        for taxon in char_dict[site].keys():
            chars_at_site.add(char_dict[site][taxon])
        for c in chars_at_site:
            set_parts[site][c] = set()

        # Determine set partitions: collect a list corresponding to each multistate character
        for taxon in char_dict[site].keys():
            content = char_dict[site][taxon]
            set_parts[site][content].add(taxon)

        # Remove ignored characters from set_parts
        for c in ignored_chars:
            removed = set_parts[site].pop(c,None)
        if set_parts[site] == {}:
            print("Error: Empty character alignment at position " + str(site) + ". TIGER rates not calculated.", file=sys.stderr)
            exit(1)

    # Steps 2 and 3: calculate partition agreements and TIGER rates

    result = None

    # multiprocessing

    # Disable multiprocessing on Windows for now (would need a different implementation)
    multiprocessing_allowed = os.name != 'nt'

    if not multiprocessing_allowed and args.n_processes > 1:
        print("Multiprocessing disabled for current system", file=sys.stderr)

    if args.n_processes > 1 and os.name != 'nt':
        pool = ActivePool()
        pool.data.update(char_dict)
        s = multiprocessing.Semaphore(args.n_processes)
        jobs = [ multiprocessing.Process(target=calculate_tiger_rates_multiprocessing, name=str(k), args=(k, pool, s))
              for k in split_list(list(char_dict.keys()),args.n_processes)]

        for j in jobs:
          j.start()

        for j in jobs:
          j.join()

        result = pool.result

    # single-threaded
    else:
        result = calculate_tiger_rates(char_dict.keys())

    for k in sorted(result.keys()):
        line = ""
        if args.named_characters:
            line += str(names[k]) + "\t"
        line += str(result[k])
        print(line)
