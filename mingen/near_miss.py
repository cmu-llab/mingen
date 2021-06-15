# -*- coding: utf-8 -*-

import re, sys
import pandas as pd
#import edlib
import config
from rules import *
import pynini_util


def generate_wugs(rules):
    # Symbol environment
    syms = [x for x in config.seg2ftrs]
    sigstar, symtable = pynini_util.sigstar(syms)

    # Monosyllabic items in training data
    vowels = '[ɑaʌɔoəeɛuʊiɪ]'
    monosyll_regex = \
        '⋊ ([^ɑaʌɔoəeɛuʊiɪ]+ )([ɑaʌɔoəeɛuʊiɪ] )+([^ɑaʌɔoəeɛuʊiɪ]+ )*⋉'
    lex = config.dat_train
    monosyll = lex[(lex['stem'].str.match(monosyll_regex))]
    print(f'{len(monosyll)} monosyllables')

    # Attested onsets and rimes of monosyllables
    onsets = [re.sub('[ɑaʌɔoəeɛuʊiɪ].*', '', x) for x in monosyll['stem']]
    rimes = [re.sub('.+([ɑaʌɔoəeɛuʊiɪ].*)', '\\1', x) for x in monosyll['stem']]
    onsets = set([x.strip() for x in onsets])
    rimes = set([x.strip() for x in rimes])
    onset_fst = pynini_util.union( \
        pynini_util.accep([x for x in onsets], symtable))
    rime_fst = pynini_util.union( \
        pynini_util.accep([x for x in rimes], symtable))
    phonotactics = onset_fst + rime_fst
    phonotactics = phonotactics.minimize(allow_nondet=True)
    print(f'{len(onsets)} onsets')
    print(f'{len(rimes)} rimes')

    # Irregular rules
    #change = 'ɪ -> ɑ'
    change = 'i -> ɛ'
    #change = 'i p -> ɛ p t'
    A, B = change.split(' -> ')  # xxx handle zeros
    rules = rules[(rules['rule'].str.contains(f'^{change} /'))]
    rules = rules \
            .sort_values('confidence', ascending=False) \
            .reset_index(drop = True)
    R = [FtrRule.from_str(rule) for rule in rules['rule']]
    R = [rule.regexes() for rule in R]
    print(f'change: {change}')
    print(f'{len(rules)} rules')

    # Real stems within scope of rules
    stems_A = monosyll[(monosyll['stem'].str.contains(A))] \
            .reset_index(drop=True)
    stems_apply = []
    for i, stem in enumerate(stems_A['stem']):
        outpt = stems_A['output'][i]
        for j, rule in enumerate(R):
            A, B, C, D = rule
            CAD = [Z for Z in [C, A, D] if Z != '']
            CAD = ' '.join(CAD)
            if not re.search(CAD, stem):
                continue
            val = pynini_util.rewrites(rule, stem, outpt, sigstar, symtable)
            val = {
                'stem': stem,
                'output': outpt,
                'model_rating': rules['confidence'][j]
            } | val
            stems_apply.append(val)
            #print(val)
            break
    stems_apply = pd.DataFrame(stems_apply)
    stems_apply = stems_apply[(stems_apply['rewrites'] == 1)] \
                  .sort_values('model_rating', ascending=False) \
                  .reset_index(drop=True)
    print(f'{len(stems_apply)} existing stems:')
    print(stems_apply)

    # Wug stems one-edit away from real stems
    stem_fst = pynini_util.accep([stem for stem in stems_apply['stem']],
                                 symtable)
    stem_fst = pynini_util.union(stem_fst)
    edit1_fst = pynini_util.edit1_fst(sigstar, symtable)
    wug_fst = stem_fst @ edit1_fst
    wug_fst = wug_fst @ phonotactics
    wugs = pynini_util.ostrings(wug_fst, symtable)
    wugs = set(wugs)
    #wugs = [wug for wug in wugs if re.match(monosyll_regex, wug)]

    # Wug stems within/outside scope of rules
    wugs_apply = []
    wugs_A = [wug for wug in wugs if re.search(A, wug)]
    for wug in wugs_A:
        val = None
        for j, rule in enumerate(R):
            A, B, C, D = rule
            CAD = [Z for Z in [C, A, D] if Z != '']
            CAD = ' '.join(CAD)
            if not re.search(CAD, wug):
                continue
            val = pynini_util.rewrites(rule, wug, '', sigstar, symtable)
            val = {
                'stem': wug,
                'output': None,
                'model_rating': rules['confidence'][j]
            } | val
            break
        if val is None:
            val = {
                'stem': wug,
                'output': None,
                'model_rating': 0,
                'applies': 0,
                'rewrites': 0
            }
        wugs_apply.append(val)

    wugs_apply = pd.DataFrame(wugs_apply)
    wugs_apply = wugs_apply[~(wugs_apply.stem.isin(lex['stem']))] \
                 .reset_index(drop = True)
    print('wug hits:')
    print(wugs_apply[(wugs_apply['applies'] == 1)] \
          .sort_values('model_rating', ascending=False))
    print('wug near-misses:')
    print(wugs_apply[(wugs_apply['applies'] != 1)])