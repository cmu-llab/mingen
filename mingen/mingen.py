# -*- coding: utf-8 -*-

import re, sys
import pandas as pd

import config
from util import *
from features import *
from rules import *

# TODO: phonology, cross-context, impugnment, etc.


def make_base_rule(x, y):
    """
    Create SegRule A -> B / C __D by aligning two segment sequences
    """
    x = x.split(' ')
    y = y.split(' ')
    # Left-hand context
    C = lcp(x, y, 'LR->')
    # Right-hand context
    x = x[len(C):]
    y = y[len(C):]
    D = lcp(x, y, '<-RL')
    # Change
    A = x[:-len(D)]
    B = y[:-len(D)]
    return SegRule(tuple(A), tuple(B), tuple(C), tuple(D))


def featurize_rule(R):
    """
    Convert SegRule to FtrRule by replacing segments in context with feature matrices
    """
    C = [config.seg2ftrs_[seg] for seg in R.C]
    D = [config.seg2ftrs_[seg] for seg in R.D]
    return FtrRule(R.A, R.B, tuple(C), tuple(D))


def generalize_context(X1, X2, direction='LR->'):
    """
    Apply minimal generalization to pair of FtrRule contexts
    """
    assert ((direction == 'LR->') or (direction == '<-RL'))
    n_X1 = len(X1)
    n_X2 = len(X2)
    n_min = min(n_X1, n_X2)
    n_max = max(n_X1, n_X2)
    if direction == '<-RL':
        X1 = X1[::-1]
        X2 = X2[::-1]

    Y = []
    seg_ident_flag = True
    for i in range(n_max):
        # X (= Sigma*) and terminate if have exceeded shorter context
        # or have already unified features
        if (i >= n_min) or (not seg_ident_flag):
            Y.append('X')
            break
        # X (Sigma*) and terminate if either is X
        if (X1[i] == 'X') or (X2[i] == 'X'):
            Y.append('X')
            break
        # Match segments perfectly
        # (NB. Conforms to A&H spec only if at least one
        # of the rules has contexts specified with segments)
        if X1[i] == X2[i]:
            Y.append(X1[i])
            continue
        # Unify features at first segment mismatch
        ftrs, any_match = unify_ftrs(X1[i], X2[i])
        if not any_match:
            Y.append('X')
            break
        Y.append(ftrs)
        seg_ident_flag = False

    if direction == '<-RL':
        Y = Y[::-1]

    Y = tuple(Y)
    return Y


def generalize_rules(R1, R2):
    """
    Apply minimal generalization to pair of FtrRules
    """
    # Check for matching change A -> B
    if (R1.A != R2.A) or (R1.B != R2.B):
        return None

    # Generalize left and right contexts
    C = generalize_context(R1.C, R2.C, '<-RL')
    D = generalize_context(R1.D, R2.D, 'LR->')
    if C is None or D is None:
        return None

    R = FtrRule(R1.A, R1.B, C, D)
    return R


def generalize_rules_rec(Rs):
    """
    Recursively apply minimal generalization to set of FtrRules
    """
    # (invariant) Rules grouped by common change
    # Word-specific rules
    R_base = {}
    for R in Rs:
        change = ' '.join(R.A) + ' -> ' + ' '.join(R.B)
        if change in R_base:
            R_base[change].append(R)
        else:
            R_base[change] = [R]
    R_base = {change: set(rules) \
                for change, rules in R_base.items()}
    R_all = {change: rules.copy() \
                for change, rules in R_base.items()}

    # First-step minimal generalization
    print('First-step mingen ...')
    R_new = {}
    for change, rules_base in R_base.items():
        print(f'\t{change} [{len(rules_base)}]')
        rules_base = [R for R in rules_base]
        rules_new = set()
        n = len(rules_base)
        for i in range(n - 1):
            R1 = rules_base[i]
            for j in range(i + 1, n):
                R2 = rules_base[j]
                R = generalize_rules(R1, R2)
                if R is None:
                    continue
                rules_new.add(R)
        R_new[change] = rules_new
    for change in R_all:
        R_all[change] |= R_new[change]

    # Recursive minimal generalization
    for i in range(10):  # xxx loop forever
        # Report number of rules by change
        print(f"iteration {i}")

        # One-step minimal generalization
        R_old = R_new
        R_new = {}
        for change, rules_base in R_base.items():
            rules_old = R_old[change]
            print(f'\t{change} [{len(rules_base)} x {len(rules_old)}]')
            rules_new = set()
            for R1 in rules_base:
                for R2 in rules_old:
                    R = generalize_rules(R1, R2)
                    if R is None:
                        continue
                    rules_new.add(R)
            R_new[change] = (rules_new - R_all[change])

        # Update rule sets
        new_rule_flag = False
        for change in R_all:
            size_old = len(R_all[change])
            R_all[change] |= R_new[change]
            size_new = len(R_all[change])
            if size_new > size_old:
                new_rule_flag = True

        # Stop if no new rules added for any context
        if not new_rule_flag:
            break

    # Write rules
    rules_out = [str(R) for change, rules in R_all.items() \
                    for R in rules]
    rules_out = pd.DataFrame(rules_out, columns=['rule'])
    rules_out['rule_len'] = [len(x) for x in rules_out['rule']]
    rules_out.to_csv('rules_out.tsv', index=False, sep='\t')

    return R_all
