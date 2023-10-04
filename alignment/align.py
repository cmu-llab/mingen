import pandas as pd
from shared_innovation import get_alignment

if __name__ == "__main__":
    filename = "../data/ipa_lang0_cognates_30.txt"
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    word_pairs = [tuple(line.split()[:2]) for line in lines]
    aligned_pairs = [get_alignment(*pair) for pair in word_pairs]
    aligned_pairs = [(' '.join(x), ' '.join(y)) for x, y in aligned_pairs]
    df = pd.DataFrame(aligned_pairs)
    df.to_csv("../data/synth_eng_30.tsv", sep='\t', header=False, index=False)
