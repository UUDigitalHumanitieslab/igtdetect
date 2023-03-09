import os
import sys
import subprocess
import glossharvester
import logging
from pathlib import Path


def main(input_path, output_path, model_path='../sample/new-model.pkl.gz', config_path='../defaults.ini.sample'):
    '''
    Looks in the input_path directory for PDFs, 
    scans them into txt files,
    derives features from those txt files, 
    analyzes the feature file using igt-detect,
    analyzes the output from igt-detect with our own gloss-harvest script
    '''
    logging.basicConfig(filename='pdf2gloss.log', encoding='utf8', level=logging.INFO)
    logging.debug('Started analysis.')
    
    temp_path = setup_temp_dir(Path(output_path))

    scanned_texts = scan_pdfs(Path(input_path), temp_path)

    features = get_features_from_txts(scanned_texts, temp_path)
    
    detected_igts = detect_igts(features, temp_path, model_path, config_path)

    IGT_list = harvest_glosses(detected_igts)

    save_glosses_as_txt(IGT_list, output_path)


def setup_temp_dir(output_path):
    '''
    Sets up the temporary environment to save the different output files that are generated
    '''
    temp_path = output_path / 'temp'
    Path.mkdir(temp_path, exist_ok=True)
    Path.mkdir(temp_path / 'txt', exist_ok=True)
    Path.mkdir(temp_path / 'features', exist_ok=True)
    Path.mkdir(temp_path / 'analyzed_features', exist_ok=True)
    logging.debug('Created temporary directories.')
    return temp_path
    

def scan_pdfs(input_path, temp_path):
    '''
    Iterates over a directory to find PDFs and converts them to txt files.
    Returns path to the txt file directory.
    '''
    scanned_files_path = temp_path / 'txt'
    for filename in os.listdir(input_path):
        if filename.lower().endswith('.pdf'):
            path_to_pdf = input_path / filename
            text_file = os.path.basename(path_to_pdf).split('.pdf')[0] + '-scanned.txt'
            path_to_txt = scanned_files_path / text_file
            subprocess.run(['pdf2txt.py', '-t', 'xml', '-o', path_to_txt, path_to_pdf])
            logging.info("Scanned {}".format(filename))
        else:
            logging.info("Could not process: {} - Not a PDF.".format(filename))
    
    logging.info("PDF scanning complete, scanned {} files".format(len(os.listdir(scanned_files_path))))
    return scanned_files_path


def get_features_from_txts(input_path, temp_path):
    '''
    Iterates over txt files in a directory in order to derive the features from them.
    Returns a path to a directory with freki files.
    '''
    features_path = temp_path / 'features'
    for filename in os.listdir(input_path):
        if filename.endswith('.txt'):
            path_to_txt = input_path / filename
            filename = os.path.basename(filename).split('-scanned')[0] + '-features.txt'
            path_to_feature = features_path / filename
            subprocess.run(['freki', path_to_txt, path_to_feature, '-r', 'pdfminer'])
            logging.info("Got features from " + filename)
        else:
            logging.info("Could not get features from: {} - Not a txt.".format(filename))
    
    logging.info("Feature analysis complete: {} files analyzed.".format(len(os.listdir(features_path))))
    return features_path



def detect_igts(input_path, temp_path, model_path, config_path):
    '''
    Runs the igt-detect script with a provided model or config, resulting in a freki features file with tags
    '''
    analyzed_features_path = temp_path / 'analyzed_features'
    subprocess.run(['python', './detect-igt', 'test', '--config', config_path, '--classifier-path', model_path, '--test-files', input_path, '--classified-dir', analyzed_features_path])
    logging.info('igt-detect finished: analyzed {} files'.format(len(os.listdir(analyzed_features_path))))
    return analyzed_features_path


def harvest_glosses(input_path):
    '''
    Runs a harvesting script on top of the igt-detect analysis
    '''
    IGT_list_complete = []
    for freki_file in os.listdir(input_path):
        path_to_freki_feature_file = input_path / freki_file
        IGT_list = glossharvester.harvest_IGTs(path_to_freki_feature_file)
        IGT_list_complete += IGT_list
        logging.info("Harvested glosses from {}, total of {} IGTs.".format(freki_file, len(IGT_list)))

    return IGT_list_complete


def save_glosses_as_txt(IGT_list, output_path):
    '''
    Saves the IGTs to a txt file
    '''
    filename = 'IGTs_harvested.txt'
    with open(os.path.join(output_path, filename), 'w') as file:
        for item in IGT_list:
            file.writelines(str(item) + "\n")


if __name__ == '__main__':
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    model_path = sys.argv[3]
    config_path = sys.argv[4]
    main(input_path, output_path, model_path, config_path) 