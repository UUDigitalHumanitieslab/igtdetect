import os
import sys
import subprocess
import glossharvester
import logging
from pathlib import Path
import xml.etree.ElementTree as ET
import pdf2doi
from datetime import date
import pickle


def main(input_path, output_path, model_path='sample/new-model.pkl.gz', config_path='defaults.ini.sample', doi_path=None):
    '''
    Looks in the input_path directory for PDFs, 
    scans them into txt files,
    derives features from those txt files, 
    analyzes the feature file using igt-detect,
    analyzes the output from igt-detect with our own gloss-harvest script
    '''
    logging.basicConfig(filename='pdf2gloss.log', encoding='utf8', level=logging.INFO)
    logging.debug('Started analysis.')
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    temp_path = setup_temp_dir(Path(output_path))

    scanned_texts, dois = scan_pdfs(Path(input_path), temp_path, doi_path)

    features = get_features_from_txts(scanned_texts, temp_path)
    
    detected_igts = detect_igts(features, 
                                temp_path, 
                                os.path.join(base_path, model_path), 
                                os.path.join(base_path,config_path), 
                                base_path)

    IGT_list = harvest_glosses(detected_igts, dois)

    save_glosses_as_xml(IGT_list, output_path)
    exit()


def setup_temp_dir(output_path):
    '''
    Sets up the temporary environment to save the different output files that are generated
    NOTE: user needs write access to output path
    '''
    temp_path = output_path / 'temp'
    Path.mkdir(temp_path, exist_ok=True)
    Path.mkdir(temp_path / 'txt', exist_ok=True)
    Path.mkdir(temp_path / 'features', exist_ok=True)
    Path.mkdir(temp_path / 'analyzed_features', exist_ok=True)
    Path.mkdir(temp_path / 'DOIs', exist_ok=True)
    logging.debug('Created temporary directories.')
    return temp_path
    

def scan_pdfs(input_path, temp_path, doi_path):
    '''
    Iterates over a directory to find PDFs and converts them to txt files
    Also collects the doi from the pdf and saves it to a dict
    Returns path to the txt file directory and the doi dict
    '''
    dois = {}
    scanned_count = 0
    scanned_files_path = temp_path / 'txt'
    check_if_empty(input_path)

    # if a doi path exists, take the existing dois
    if doi_path:
        with open(doi_path, 'rb') as doi_file:
            dois = pickle.load(doi_file)

    for filename in os.listdir(input_path):
        if filename.lower().endswith('.pdf'):
            path_to_pdf = input_path / filename
            text_file = os.path.splitext(filename)[0] + '-scanned.txt'
            path_to_txt = scanned_files_path / text_file
            try:
                subprocess.run(['pdf2txt.py', '-t', 'xml', '-o', path_to_txt, path_to_pdf])
                logging.info("Scanned {}".format(filename))
                scanned_count += 1
            except:
                logging.error('PDF scan failed for: {}'.format(filename))

            # get the doi from the pdf and save it into the dois dict
            if not doi_path:
                identifier_result = pdf2doi.pdf2doi(str(path_to_pdf))
                if identifier_result['identifier'] is None:
                    logging.error('pdf2doi was not able to find a doi for {}'.format(filename))
                else:
                    dois[os.path.splitext(filename)[0]] = identifier_result['identifier']
        else:
            logging.info("Could not process: {} - Not a PDF.".format(filename))
    
    if not doi_path:
        with open(temp_path / 'DOIs', 'wb') as doi_file:
            pickle.dump(dois, doi_file)

    logging.info("PDF scanning complete, scanned {} files".format(scanned_count))
    return scanned_files_path, dois


def get_features_from_txts(input_path, temp_path):
    '''
    Iterates over txt files in a directory in order to derive the features from them.
    Returns a path to a directory with freki files.
    '''
    features_count = 0
    features_path = temp_path / 'features'
    check_if_empty(input_path)

    for filename in os.listdir(input_path):
        if filename.endswith('.txt'):
            path_to_txt = input_path / filename
            filename = os.path.basename(filename).split('-scanned')[0] + '-features.txt'
            path_to_feature = features_path / filename
            try:
                subprocess.run(['freki', path_to_txt, path_to_feature, '-r', 'pdfminer'])
                logging.info("Got features from {}".format(filename))
                features_count += 1
            except:
                logging.error('Freki analysis failed for: {}'.format(filename))
        else:
            logging.info("Could not get features from: {} - Not a txt.".format(filename))
    
    logging.info("Feature analysis complete: {} files analyzed.".format(features_count))
    return features_path



def detect_igts(input_path, temp_path, model_path, config_path, base_path):
    '''
    Runs the igt-detect script with a provided model or config, resulting in a freki features file with tags
    Arguments: input, and temp paths to get and save data, model, config, and base paths for the igt-detect script
    '''
    analyzed_features_path = temp_path / 'analyzed_features'
    check_if_empty(input_path)

    try:
        subprocess.run(['python', os.path.join(base_path,'detect-igt'), 'test', '--config', config_path, '--classifier-path', model_path, '--test-files', input_path, '--classified-dir', analyzed_features_path])
        logging.info('igt-detect finished: analyzed {} files'.format(len(os.listdir(analyzed_features_path))))
        return analyzed_features_path
    except subprocess.CalledProcessError as e:
        logging.error('igt-detect failed: {}'.format(e.output))
        return temp_path / 'features'

def match_dois(IGT_list, dois):
    '''
    Matches DOIs to IGT objects using the source filename (without the extension)
    returns an IGT_list with the DOIs supplemented
    '''
    for igt in IGT_list:
        try:
            igt.doi = dois[igt.source]
        except:
            logging.info('No doi could be matched to {}'.format(igt.source))

def harvest_glosses(input_path, dois=None):
    '''
    Runs a harvesting script on top of the igt-detect analysis
    iterates over the freki file line-by-line and returns a list of IGT objects
    '''
    IGT_list_complete = []
    check_if_empty(input_path)


    for freki_file in os.listdir(input_path):
        path_to_freki_feature_file = os.path.join(input_path, freki_file)
        IGT_list = glossharvester.harvest_IGTs(path_to_freki_feature_file)
        IGT_list_complete += IGT_list
        logging.info("Harvested glosses from {}, total of {} IGTs.".format(freki_file, len(IGT_list)))
    
    if dois:
        match_dois(IGT_list_complete, dois)

    return IGT_list_complete


def save_glosses_as_txt(IGT_list, output_path):
    '''
    Saves the IGTs to a txt file
    '''
    filename = 'IGTs_harvested.txt'
    with open(os.path.join(output_path, filename), 'w') as file:
        for item in IGT_list:
            file.writelines(str(item) + "\n")

def save_glosses_as_xml(IGT_list, output_path):
    glosses = ET.Element('Glosses')
    for index, item in enumerate(IGT_list):
        gloss = ET.SubElement(glosses, 'gloss')
        meta = ET.SubElement(gloss, 'metadata')
        meta.set('source', item.source)
        meta.set('pagenr', str(item.pagenr))
        meta.set('linenr', str(item.linenr))
        meta.set('prefix', str(item.prefix))
        meta.set('grammarker', str(item.grammarker))
        meta.set('classification_methods', item.classification_methods)
        meta.set('index', str(index))
        meta.set('doi', item.doi)
        content = ET.SubElement(gloss, 'content')
        content.set('line', item.line)
        content.set('gloss', item.gloss)
        content.set('translation', item.translation)
        content.set('context', item.context)

    filename = "IGTs_harvested_" + str(date.today()) + ".xml"
    glosses_tree = ET.ElementTree(glosses)
    ET.indent(glosses_tree)
    
    with open(os.path.join(output_path, filename), 'w') as file:
        glosses_tree.write(file, encoding='unicode')

def check_if_empty(path):
    '''
    Checks if a directory is empty, used for debugging
    '''
    if len(os.listdir(path)) == 0:
        logging.error("No files found in {}.".format(path))
        return True
    else:
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Error: Missing arguments. Provide at least an input path and an output path.")
        exit()
    
    input_path = sys.argv[1]  # path to a dir with txt files
    output_path = sys.argv[2] # path to a dir where the gloss xmls are stored
    if len(sys.argv) > 3:
        model_path = sys.argv[3]
    else:
        logging.info('No model or config paths given, using defaults')
        main(input_path, output_path)

    if len(sys.argv) > 4:
        config_path = sys.argv[4] # path to a .sample config file
    else:
        logging.info('No config path given, using default')
        main(input_path, output_path, model_path)

    main(input_path, output_path, model_path, config_path)
