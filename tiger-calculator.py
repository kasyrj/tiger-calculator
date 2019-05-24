#!/usr/bin/python3

import sys
import argparse
import formats

PARSER_DESC = "Simple TIGER rates calculator."
FORMAT_ERROR_MSG = "Please specify one of the available formats: " + formats.getFormatsAsString()

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

    for x in char_dict.keys():
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
        print(sum(agr_array)/len(agr_array)) # TIGER rate for the current character
