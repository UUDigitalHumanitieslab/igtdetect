import re
import os

def get_utterance(row: str):
    return row.split(':')[1].strip('\n') if ':' in row else 'NA'

def get_utterance_and_prefix(row: str):
    utterance = get_utterance(row)
    prefix = detect_prefix(utterance)
    if prefix:
        for pf in prefix:
            utterance = utterance.replace(pf, '')
    return prefix, utterance

def get_linenr(row: str):
    return row.split('line=')[1].split()[0] if 'line=' in row else 'NA'

def get_linetag(row: str):
    return row.split('tag=')[1][0] if 'tag=' in row else 'NA'

def get_iscore(row:str):
    return float(row.split('iscore=')[1][0:3]) if 'iscore' in row else 0

def get_context(lines, index, linetype='G', context_size=5):
    context = ""
    for i in range(-context_size, context_size):
        context += str(get_utterance(lines[index+i]) + "\n")
    return context

def detect_prefix(line: str):
    '''
    Detects the presence of a prefix in a line and returns the prefix
    If a prefix is found, it looks ahead to scan for double prefixes
    '''
    punctuation_pattern = r'[.\(\)\{\}\[\]]'
    number_pattern = r'\d+'
    prefix = []
    words = line.split()
    item = words[0]
    punctuations = re.findall(punctuation_pattern, item)
    numerals = re.findall(number_pattern, item)
    if (punctuations or numerals) and len(item) < 6:
        prefix.append(item)
        if len(words) > 1:
            next_prefix = detect_prefix(' '.join(words[1:]))
            if next_prefix:
                prefix += next_prefix
    else:
        return None
    return prefix


class IGT():
    '''
    A class used to represent a single item of Interlinear Glossed Text

    Attributes
    ----------
    line: str
        transcript of the original utterance in the text
    
    gloss: str
        glossed version of the transcript, usually located right underneath the transcript line

    translation: str
        translation of the transcript line, usually in English

    context: str
        the three lines before and after an IGT, to help with the enrichment, correction, and interpretation

    source: str
        title of the publication in which the IGT occurs

    linenr: int
        line number of the transcript line in the publication

    classification_methods: str[]
        list of the methods employed to arrive at this instance of the IGT, for example through igt-detect
        or l-score
    '''
    def __init__(self, line="NA", gloss="NA", translation="NA", prefix="NA", context="", source="NA", linenr=0, pagenr=0, classification_methods=[]):
        self.line = line
        self.gloss = gloss
        self.translation = translation
        self.prefix = prefix
        self.context = context
        self.source = source
        self.linenr = linenr
        self.pagenr = pagenr
        self.classification_methods = classification_methods


    def __str__(self):
        return f"Source: {self.source}\nL: {self.line}\nG: {self.gloss}\nT: {self.translation}\nClassification methods: {self.classification_methods}\n"

def harvest_IGTs(input_filepath: str, iscore_cutoff: float = 0.6):
    '''
    attempts to harvest as much information about each IGT as possible
    iterates through a freki file 
    if the iscore cutoff is lowered, the script is more generous with interpreting
    lines as Glosses or Translations based on their alignment
    '''
    IGTs = []
    saved_linenrs = []
    with open(input_filepath) as file:
        lines = file.readlines()
    
    for (i, row) in enumerate(lines):
        if row.startswith('line'):
            linetag = row.split('tag=')[1][0] if os.path.splitext(input_filepath)[1] =='.freki' else 'NA'
            linenr = get_linenr(row)
            prefix, utterance = get_utterance_and_prefix(row)
            iscore = get_iscore(row)
            
            if linetag == 'L':
                igt = IGT(line=utterance, linenr=int(linenr), source=source, pagenr=pagenr, 
                    classification_methods=['IGT initialized by L tag'])
                igt.context = get_context(lines, i, 'L')
                IGTs.append(igt)
                saved_linenrs.append(linenr)
                continue

            elif linetag == 'G' or linetag == 'T':
                #selects igt object whose L is within 2 lines of current line
                igt = [(index, igt) for (index, igt) in enumerate(IGTs) if abs(igt.linenr-int(linenr)) <= 2]
                if len(igt) > 1:
                    #TODO: A behaviour for when there are several IGTs within reach
                    pass

                #if there is only one IGT candidate this one is selected and updated
                elif len(igt) == 1:
                    index = igt[0][0]
                    igt = igt[0][1]
                    if linetag == 'G':
                        igt.classification_methods.append('updated gloss by tag')
                        igt.gloss = utterance
                    else:
                        igt.classification_methods.append('updated translation by tag')
                        igt.translation = utterance


                    IGTs[index] = igt
                    saved_linenrs.append(linenr)

                    continue

                # if there are no IGT candidates, create a new IGT
                else:
                    igt = IGT(gloss=utterance, 
                              source=source, 
                              pagenr=pagenr) if linetag == 'G' else IGT(translation=utterance, 
                                                                        source=source, 
                                                                        pagenr=pagenr
                                                                        )
                    igt.prefix, igt.line = get_utterance_and_prefix(lines[i-1]) if linetag == 'G' else get_utterance_and_prefix(lines[i-2])
                    igt.classification_methods = ['IGT initialized by G or T tag, L assigned accordingly']
                    saved_linenrs.append(linenr)
                    continue

            #if the iscore is higher than the cutoff, this might be a G
            if float(iscore) > iscore_cutoff:
                if get_linenr(lines[i-1]) in saved_linenrs:
                    continue
                else:
                    igt = IGT(gloss=utterance, source=source, pagenr=pagenr)
                    igt.prefix, igt.line = get_utterance_and_prefix(lines[i-1])
                    igt.translation = get_utterance(lines[i+1]) if i < len(lines)-2 else 'NA'
                    igt.classification_methods = ['IGT initialized by iscore L and T assigned accordingly']
                    igt.context = get_context(lines, i, 'G')
                    IGTs.append(igt)
                    saved_linenrs.append(linenr)
                    continue

        # save the doc_id as the source
        # can later maybe be expanded with page number as well (information available on the same row)
        elif row.startswith('doc_id'):
            source = row.split('doc_id=')[1].split(' ')[0]
            pagenr = row.split('page=')[1].split(' ')[0]
        else:
            pass


    return IGTs
