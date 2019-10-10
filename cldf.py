#!/usr/bin/python3

import absreader
import collections
import csv
import os
import sys
import random

class CldfReader(absreader.AbstractReader):

    def getReaderName():
        return "cldf"

    def __init__(self):
        self.synonym_strategy = "minimum"
    
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
        meanings = set(form_to_param.values())

        cognates = {}
        for taxon in taxa:
            cognates[taxon] = {}
            for meaning in meanings:
                cognates[taxon][meaning] = set()

        with open(os.path.join(file_or_dir, "cognates.csv"), "r") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                lang = form_to_lang[row["Form_ID"]]
                assert lang in taxa
                meaning = form_to_param[row["Form_ID"]]
                cognate = row["Cognateset_ID"]
                cognates[lang][meaning].add(cognate)

        # Resolve synonyms
        cognates = resolve_synonyms(taxa, meanings, cognates, self.synonym_strategy)

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
 
def resolve_synonyms(languages, meanings, cognates, strategy):
    if strategy == "random":
        return resolve_synonyms_random(languages, meanings, cognates)
    elif strategy == "minimum":
        return resolve_synonyms_minimax(languages, meanings, cognates, "min")
    elif strategy == "maximum":
        return resolve_synonyms_minimax(languages, meanings, cognates, "max")

def resolve_synonyms_random(languages, meanings, cognates):
    for meaning in meanings:
        for lang in languages:
            if not cognates[lang][meaning]:
                cognates[lang][meaning] = "?"
            elif len(cognates[lang][meaning]) == 1:
                cognates[lang][meaning] = cognates[lang][meaning].pop()
            else:
                cognates[lang][meaning] = random.sample(cognates[lang][meaning], 1)[0]
    return cognates

def resolve_synonyms_minimax(languages, meanings, cognates, mode="min"):
    for meaning in meanings:
        # Count cognate classes
        cognate_class_counts = collections.Counter()
        for lang in languages:
            for c in cognates[lang][meaning]:
                if c != "?":
                    cognate_class_counts[c] += 1
        # Divide languages into easy and hard cases
        easy_langs = [l for l in languages if len(cognates[l][meaning]) < 2]
        hard_langs = [l for l in languages if l not in easy_langs]
        # Make easy assignments
        attested_cognates = set()
        for lang in easy_langs:
            if not cognates[lang][meaning]:
                cognates[lang][meaning] = "?"
            elif len(cognates[lang][meaning]) == 1:
                cognates[lang][meaning] = cognates[lang][meaning].pop()
            attested_cognates.add(cognates[lang][meaning])
        # Make hard assignments
        for lang in hard_langs:
            options = [(cognate_class_counts[c], c) for c in cognates[lang][meaning]]
            # Sort cognates from rare to common if we want to maximise cognate
            # class count, or from common to rare if we want to minimise it.
            options.sort(reverse = mode == "min")
            # Preferentially assign a cognate which has already been
            # assigned if we're trying to minimise, or one which has
            # not if we're trying to maximise.
            for n, c in options:
                if (mode == "min" and c in attested_cognates) or (mode == "max" and c not in attested_cognates):
                    cognates[lang][meaning] = c
                    break
            # Otherwise just pick the most/least frequent cognate.
            else:
                cognates[lang][meaning] = options[0][1]
            attested_cognates.add(cognates[lang][meaning])
    return cognates

if __name__ == '__main__':
    print("CLDF reader class for tiger-calculator")
