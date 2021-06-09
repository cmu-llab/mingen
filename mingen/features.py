# -*- coding: utf-8 -*-

# Feature matching and unification, convert feature matrices to/from strings

import re
import config
from functools import lru_cache


def match_ftrs_(F, seg):
    """
    Subsumption relation between feature matrix and segment
    [Args: feature dicts]
    """
    seg_ftrs = config.seg2ftrs[seg]
    for (ftr, val) in F.items():
        if seg_ftrs[ftr] != val:
            return False
    return True


def match_ftrs(F, seg):
    """
    Subsumption relation between feature matrix and segment
    [Args: feature vectors]
    """
    seg_ftrs = config.seg2ftrs_[seg]
    n = len(seg_ftrs)
    for i, F_i in enumerate(F):
        if F_i == '0':
            continue
        if seg_ftrs[i] != F_i:
            return False
    return True


def unify_ftrs_(F1, F2):
    """
    Shared values of two feature matrices
    [Args: feature dicts]
    """
    # Unify(Sigma*,F2) = unify(F1,Sigma*) = Sigma*
    if (F1 == 'X') or (F2 == 'X'):
        return 'X'
    # Ordinary unification
    # todo: built-in dictionary function?
    F = {}
    for (ftr, val) in F1.items():
        if (ftr in F2) and (F2[ftr] == val):
            F[ftr] = val
    return F


def unify_ftrs(F1, F2):
    """
    Shared values of two feature matrices
    [Args: feature vectors]
    """
    if (F1 == 'X') or (F2 == 'X'):
        return 'X'
    n = len(F1)
    F = ['0'] * n
    any_match = False
    for i, F1_i in enumerate(F1):
        F2_i = F2[i]
        if (F1_i == '0') or (F2_i == '0'):
            continue
        if F1_i == F2_i:
            F[i] = F1_i
            any_match = True
    return tuple(F), any_match


#@lru_cache(maxsize=1024)
def subsumes(F1, F2):
    """
    Subsumption relation between feature matrices F1 and F2
    [Args: feature vectors]
    """
    if (F1 == 'X'):
        return True
    if (F2 == 'X'):
        return False
    n = len(F1)
    for i, F1_i in enumerate(F1):
        if F1_i == '0':
            continue
        if F1_i != F2[i]:
            return False
    return True


def ftrs2regex(F):
    """
    Segment regex for sequence of feature matrices
    Note: excludes X (Sigma*), which is assumed to appear only at edges of rule contexts and is always implicit at those positions in cdrewrite compilation
    """
    return ' '.join([ftrs2regex1(Fi) for Fi in F if Fi != 'X'])


def ftrs2regex1(F):
    """ Segment regex for single feature matrix """
    if F == 'X':
        return 'X'
    segs = [seg for seg in config.seg2ftrs \
            if match_ftrs(F, seg)]
    return '(' + '|'.join(segs) + ')'


def ftrs2str(F):
    """ String corresponding to sequence of feature matrices """
    return ' '.join([ftrs2str1(Fi) for Fi in F])


def ftrs2str1(F):
    """ String corresponding to feature matrix, with non-zero values only """
    if F == 'X':
        return 'X'
    ftr_names = config.ftr_names
    ftrvals = [f'{F[i]}{ftr_names[i]}' \
                for i in range(len(F)) if F[i] != '0']
    val = '[' + ', '.join(ftrvals) + ']'
    return val


def str2ftrs(x):
    """ String to sequence of feature matrices (inverse of ftrs2str) """
    y = re.sub('X', '[X', x)  # Pseudo-matrix for Sigma*
    y = y.split(' [')
    try:
        y = [str2ftrs1(yi) for yi in y]
    except:
        print(f'Error in str2ftrs for input {y}')
        sys.exit(0)
    return tuple(y)


def str2ftrs1(x):
    """ String to feature matrix (inverse of ftrs2str1) """
    y = re.sub('\\[', '', x)
    y = re.sub('\\]', '', y)
    # X (Sigma*)
    if y == 'X':
        return 'X'
    # Ordinary feature matrix, non-zero specs only
    y = y.split(', ')
    ftrs = ['0'] * len(config.ftr_names)
    ftr_names = config.ftr_names
    for spec in y:
        if spec == '':  # xxx document
            continue
        val = spec[0]
        ftr = spec[1:]
        ftrs[ftr_names.index(ftr)] = val
    return tuple(ftrs)
