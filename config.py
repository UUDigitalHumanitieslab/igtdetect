# -------------------------------------------
# Various Directories for where Files are Stored.
# -------------------------------------------
CHECK_DIR = '/Users/rgeorgi/Documents/treebanks/ODIN_data/2009_09_02'
FREKI_DIR = '/Users/rgeorgi/Documents/code/igt-detect/3-freki'
MATCH_DIR = '/Users/rgeorgi/Documents/code/igt-detect/4-match'
FEAT_DIR  = '/Users/rgeorgi/Documents/code/igt-detect/5-feats'

# -------------------------------------------
# Path to wordlist file
# -------------------------------------------
WORDLIST = '/Users/rgeorgi/Documents/code/igt-detect/ngrams/wordsEn.txt'

# -------------------------------------------
# Dependent file libraries.
# -------------------------------------------
XIGT_DIR  = '/NLP_TOOLS/uwcl/xigt/xigt-1.1.0/'
ODIN_UTIL_DIR = '../odinutils'

# -------------------------------------------
# Where is Mallet
# -------------------------------------------
MALLET_DIR = '/Users/rgeorgi/Documents/code/mallet-2.0.7'

# -------------------------------------------
# Regular Expressions
# -------------------------------------------

# These grams will be searched for case-insensitive.
GRAM_LIST = ['1SG', '1PL', '1SM',
             '2SG', '2P', '2SM',
             '3SG', '3REFL', '3SGP', '3SM', '3P']

# These grams will be searched for case sensitive.
CASED_GRAM_LIST = ['POSS',
                   'ACC','NOM', 'DAT', 'ERG', 'AOR', 'ABS', 'OBL', 'DUAL', 'REFL',
                   'NEG', 'TOP',
                   'FUT', 'PROG', 'PRES', 'PASS']

REGEXES = '''
\s*(\()\d*\).*\n
\s*.*\n
\s*\[`'"].*\n
~
\s*(\()\d*\)\s\w\..*\n
\s*.*\n
\s\[`'"].*\n
~
\s*(\(\d)*\)\s*\(.*\n
\s.*\n
\s*.*\n
\s\[`'"].*\n
~
\s*(\()\d*\).*\n
\s*\w\..*\n
\s*.*\n
\s\[`'"].*\n
~
\s*\w.\s*.*\n
\s*.*\n
\s*\[`'"].*\n
~
\s*\w\)\s*.*\n
\s*.*\n
\s*\[`'"].*\n
~
\s*(\()\w*\).*\n
\s*.*\n
\s*\[`'"].*\n
~
//added 02-03-2005
\s*\d.*.*\n
\s*.*\n
\s*\[`'"].*\n
~
\s*(\()\d*\).*\n
.*\n
\s*.*\n
\s*\[`'"].*\n
~'''