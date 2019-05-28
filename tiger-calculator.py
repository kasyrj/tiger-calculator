#!/usr/bin/python3

import sys
import argparse
import formats
import multiprocessing

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

def calculate_tiger_rates(analyzed_keys,pool):
    '''Calculate TIGER rates for the characters specified by the array keys'''
    name = multiprocessing.current_process().name
    with s:
        pool.makeActive(name)
        data = pool.data
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
            # Step 3: Calculate TIGER rate
            pool.result[x] = sum(agr_array) / len(agr_array) # TIGER rate for the current character

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
                        help="A comma-separated list of ignored characters.",
                        default="",
                        type=str)

    parser.add_argument("-p","--processes",
                        dest="n_processes",
                        help="Number of processes (threads) to use. Default: %i (the detected number of CPUs)." % N_PROCESSES,
                        default=N_PROCESSES,
                        type=int)

    if len(sys.argv) == 1:
        parser.print_help()
        exit(0)
    args = parser.parse_args()
    if args.format == None:
        print(FORMAT_ERROR_MSG)
        exit(1)

    reader = formats.getReader(args.format)

    if reader == None:
        print(FORMAT_ERROR_MSG)
        exit(1)

    content = reader.getContents(args.in_file)
    taxa = content[0]
    chars = content[1]

    ignored_chars = args.ignored_chars.split(",")

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

    # Steps 2 and 3: calculate partition agreements; calculate TIGER rates

    pool = ActivePool()
    pool.data.update(char_dict)
    s = multiprocessing.Semaphore(args.n_processes)
    jobs = [ multiprocessing.Process(target=calculate_tiger_rates, name=str(k), args=(k, pool))
             for k in split_list(list(char_dict.keys()),args.n_processes)]

    for j in jobs:
        j.start()
        
    for j in jobs:
        j.join()

    for k in sorted(pool.result.keys()):
        print(pool.result[k])
