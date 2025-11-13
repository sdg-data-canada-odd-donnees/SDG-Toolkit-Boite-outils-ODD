import yaml
import os
import glob
import html

# This script was used to extract the translated metadata and indicator-config information from all indicators that do not have exclusively Government of Canada source organisations.
# The idea is to be able to send only the relevant metadata for translation/revision rather than all metadata.
# It would have to be adapted to be used for other purposes.

# set containing source organisations for which we don't want to check metadata translation
gc_orgs = {
    'Affaires mondiales Canada',
    'Agence de la santé publique du Canada',
    'Agriculture et Agroalimentaire Canada',
    'Conseil de la radiodiffusion et des télécommunications canadiennes',
    'Conseil des ministres de l’Éducation (Canada)',
    'Environnement et Changement Climatique Canada (ECCC)',
    'Environnement et Changement climatique Canada',
    'Environnement et Changement climatique Canada (ECCC)',
    'Femmes et Égalité des genres Canada',
    'Immigration, Réfugiés et Citoyenneté Canada (IRCC)',
    "Institut canadien d'information sur la santé (ICIS)",
    'Patrimoine canadien',
    'Ressources naturelles Canada (RNCan)',
    'Ressources naturelles Canada et Statistique Canada',
    'Secrétariat du Conseil du Trésor',
    'Statistics Canada',
    'Statistique Canada',
    'Statistique Canada, Santé Canada',
    'Sécurité publique Canada',
}

# For proper parsing of newlines, replace all >- with |-

source_dir = 'sdg-data-donnees-odd'
path_pattern = '*.yml'
language = 'fr' # set to empty string '' for untranslated metadata

# Select these metadata keys
meta_keys = ['STAT_CONC_DEF', 'DATA_COMP', 'REC_USE_LIM']
# Select these indicator-config keys
indicator_config_keys = ['indicator_available', 'page_content']
# Select only these goals
goals = ['2', '5', '6', '7', '8', '9', '11', '12', '14']

# Get all metadata, indicator-config and translation files
meta_dir = os.path.join(source_dir, 'meta', language, path_pattern) # get all metadata files
indicator_config_dir = os.path.join(source_dir, 'indicator-config', path_pattern) # get all indicator-config files
translations_dir = os.path.join(source_dir, 'translations', language, path_pattern) # get all translation keys

meta_files = glob.glob(meta_dir)
indicator_config_files = {os.path.basename(file).split('.')[0]: file for file in glob.glob(indicator_config_dir)}
translation_files = glob.glob(translations_dir)

# Do all the fun filtering stuff!
# 1) Retrieve indicator source organization(s) from metadata.
# 2) If there is no source or the sources are not an exact subset of gc_orgs, add the selected metadata and indicator-config keys to a combined metadata dict.
meta = {} # dict combining selected metadata and indicator-config keys and values
# all_sources = []
# Read metadata files and add selected keys to dict
for file in meta_files:
    inid = os.path.basename(file).split('.')[0]
    with open(file, 'r', encoding='utf-8') as f:
        content = yaml.safe_load(f)
    # Get set of source organizations
    sources = {content[key].rstrip() for key in content if key.startswith('source_organisation')}
    # for source in sources:
    #     all_sources.append(source)
    # Continue only if there is no source or the sources are not an exact subset of gc_orgs
    if (len(sources) == 0) or (not sources.issubset(gc_orgs)):
        # Add selected keys from meta to dict
        meta[inid] = {}
        sources = []
        for key in meta_keys:
            if key in content.keys():
                meta[inid][key] = content[key]
        # Read and add selected keys from indicator_config
        with open(indicator_config_files[inid], 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        for key in indicator_config_keys:
            if key in content.keys():
                meta[inid][key] = content[key]
    # else:
    #     print(f'{inid}: {sources}')

# Get translation keys
translations = {}
for file in translation_files:
    filename = os.path.basename(file).split('.')[0]
    with open(file, 'r', encoding='utf-8') as f:
        content = yaml.safe_load(f)
    for key in content:
        translations[filename+'.'+key] = content[key]

# Apply translations
for inid in meta:
    for key, value in meta[inid].items():
        if value in translations.keys():
            meta[inid][key] = translations[value]

# Write indicator content from selected goals to txt
with open('meta.txt', 'w', encoding='utf-8') as f:
    for inid in meta.keys():
        goal = inid.split('-')[0]
        if goal in goals:
            f.write(inid+'\n')
            for key, value in meta[inid].items():
                if (value is not None) and (value.rstrip() != ''):
                    f.write(f'{key}: {html.unescape(value)}\n')
            f.write('---\n')