#!/usr/bin/python3

import absreader
import csv
import os
import sys

class CldfReader(absreader.AbstractReader):

    def getReaderName():
        return "cldf"

    def __init__(self):
        pass
    
    def __del__(self):
        pass
        
    def getContents(self, file_or_dir):
        if file_or_dir == None:
            print("Please specify an input CLDF dataset.", file=sys.stderr)
            exit(1)
        if not os.path.exists(file_or_dir):
            print("Dataset %s does not exist." % file_or_dir, file=sys.stderr)
            exit(1)
        if not os.path.isdir(file_or_dir):
            file_or_dir = os.path.dirname(file_or_dir)
        if not all((os.path.exists(os.path.join(file_or_dir, x)) for x in
            ("languages.csv", "forms.csv", "cognates.csv"))):
            print("CLDF dataset does not use standard filenames.", file=sys.stderr)
            exit(1)

        # Read CLDF data
        # This is basically a bunch of quick and dirty manual JOINs of RDBMS
        # tables, each encoded as CSV files.
        lang_names = {}
        with open(os.path.join(file_or_dir, "languages.csv"), "r") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                lang_names[row["ID"]] = row["Name"]

        taxa = list(lang_names.values())

        # Correct for duplicated names
        if len(set(taxa)) != len(taxa):
            for lang_id, lang_name in lang_names.items():
                if taxa.count(lang_name) > 1:
                    lang_names[lang_id] = lang_name + "_" + lang_id
            taxa = list(lang_names.values())
        assert len(set(taxa)) == len(taxa)
        taxa.sort()

        param_names = {}
        with open(os.path.join(file_or_dir, "parameters.csv"), "r") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                param_names[row["ID"]] = row["Name"]

        form_to_param = {}
        form_to_lang = {}
        with open(os.path.join(file_or_dir, "forms.csv"), "r") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                form_to_param[row["ID"]] = param_names[row["Parameter_ID"]]
                form_to_lang[row["ID"]] = lang_names[row["Language_ID"]]

        cognates = {}
        for taxon in taxa:
            cognates[taxon] = {}

        with open(os.path.join(file_or_dir, "cognates.csv"), "r") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                lang = form_to_lang[row["Form_ID"]]
                assert lang in taxa
                meaning = form_to_param[row["Form_ID"]]
                cognate = row["Cognateset_ID"]
                cognates[lang][meaning] = cognate

        # Convert to tiger-calculator form
        meanings = list(set(form_to_param.values()))
        meanings.sort()
        for meaning in meanings:
            all_values = list(set((cognates[l].get(meaning, "?") for l in taxa)))
            if "?" in all_values:
                all_values.remove("?")
            all_values.sort()
            for taxon in taxa:
                cognates[taxon][meaning] = all_values.index(cognates[taxon][meaning]) if (meaning in cognates[taxon] and cognates[taxon][meaning] != "?") else "?"

        chars = []
        for taxon in taxa:
            alignment = []
            for meaning in meanings:
                alignment.append(cognates[taxon][meaning])
            chars.append(alignment)

        return [taxa,chars,meanings]
        
if __name__ == '__main__':
    print("CLDF reader class for tiger-calculator")
