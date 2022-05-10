"""
Python 3.7
Code for PCORTF FY18 project on National Hopsital Care Survey
Designed to flag opioids and opioid overdoses

updated 6/10/21
@author: oxf7
"""
import copy
import configparser
import csv
import logging
from pathlib import Path
import re
import sys
#below used in case to import from paths not in default sys.path
#code_dir = Path(r'\\path_to_class_imports')
#if str(code_dir) not in sys.path:
#    sys.path.append(str(code_dir))

from negex_adjusted import negTagger, sortRules
from nltk.tokenize import sent_tokenize
from build_queries import Query


def search_plain_text(note_text, standalone_regex, tups, negrules, 
                      date_exclusion, NER_model,
                      last_resort_dict, diagnosis):
    #in the original code, sentence_level_exclusions could be specified elsewhere and passed
    #into search_plain_text. For now, to simplify config file, just hard-coding this in.
    #Consider adding as user-level option?
    sentence_level_exclusions = re.compile(r'family hx|family history|as needed|\bprn\b', flags=re.IGNORECASE)
    #tups is a list of tuples, combination searches
    #sentence_level_exclusions is a regex, ignorecase
    all_confirmed_matches = set() #members are strings

    #02/25/21 update, adding diagnosis flag. if false, single word
    # last resort searches not done because these yield lots of false positives
    #had to change regex type to join style to be able to change it here
    
    sentences = sent_tokenize(note_text)

    post_weedouts = []
    for sentence in sentences:
        if re.search(sentence_level_exclusions, sentence) is not None:
            continue
        if not date_exclusion:
            post_weedouts.append(sentence)
            continue
        else:
            doc = NER_model(sentence)
            for ent in doc.ents:
                if ent.label_ == "DATE" and re.search(date_exclusion, ent.text) is not None:
                    continue
                else:
                    post_weedouts.append(sentence)
        post_weedouts.append(sentence)

    sentences = copy.deepcopy(post_weedouts)

        
    #next block is to reduce # of sentence by sentence searches, hopefully        
    standalone_match = False
    if re.search(standalone_regex, note_text):
        standalone_match = True
    tup_match = False
    for tup in tups:
        if re.search(tup[0], note_text) and re.search(tup[1], note_text):
            tup_match = True
    if last_resort_dict:
        last_search_match = False
        if last_resort_dict["standalone"] is not None:
            last_resort_standalone_spec = True
            #if  diagnosis = True, this means this is a note type that is considered a diagnosis note type
            #if it is, freely search for all patterns in last_resort regex. If not, there is an additional restriction
            #on what last resort searches you can search for in a non-diagnosis note. The way the code is written,
            #that restriction is imposed based on # of words in the search term because that's how our data played out
            #So only terms greater than length 1, when split on whitespace, get included, and single words get weeded out
            #Consider making this more flexible for user? Also, this only works if pattern built with pipes, not as Trie
            if diagnosis:
                last_resort_standalone_regex = last_resort_dict["standalone"]
            else:
                last_resort_standalone_regex = re.compile('|'.join([r'%s' % x for x in last_resort_dict["standalone"].pattern.split('|') if len(x.split())>1]), re.IGNORECASE)
            if re.search(last_resort_standalone_regex, note_text):
                last_search_match = True
        else:
            last_resort_standalone_spec = False
        if last_resort_dict["tup"] is not None:
            last_resort_tup_spec = True
            last_resort_combo_A_regex = last_resort_dict["tup"][0]
            last_resort_combo_B_regex = last_resort_dict["tup"][1]
            if re.search(last_resort_combo_A_regex, note_text):
                last_search_match = True
        else:
            last_resort_tup_spec = False
              
    for sentence in sentences:
        sentence_match = False #only search last resort if this is false
        if standalone_match:
            standalone_matches = set([x.lower() for x in re.findall(standalone_regex, sentence)])     
            if standalone_matches:
                sentence_match = True
            for match in standalone_matches:
                tagger = negTagger(sentence, [match], negrules, negP=False)
                if tagger.getNegationFlag()=="negated":
                    continue
                all_confirmed_matches.add(match.lower())
        if tup_match:
            for tup in tups:
                regex_A = tup[0] #general terms
                regex_B = tup[1] #specific terms that determine category of match
                if not re.search(regex_A, sentence):
                    continue
                variable_terms = re.findall(regex_B, sentence) #finds all
                if not variable_terms:
                    continue
                sentence_match = True
                for specific_term in variable_terms:
                        #TODO: test what multiple terms in negex mean
    #                    tagger = negTagger(sentence, [general_match, specific_term], negrules, negP=False)
                    tagger = negTagger(sentence, [specific_term], negrules, negP=False)
                    if tagger.getNegationFlag()=="negated":
                        continue
                    all_confirmed_matches.add(f"{specific_term.lower()}")
                    
        if last_resort_dict and (not sentence_match) and last_search_match: 
            #if you've turned on last resort and there are no other matches
            #in the sentence and there's a match somewhere in the whole text for 
            #last search combo A
            if last_resort_standalone_spec:
                last_resort_matches = re.findall(last_resort_standalone_regex, sentence)
                for match in last_resort_matches:
                    tagger = negTagger(sentence, [match], negrules, negP=False)
                    if tagger.getNegationFlag()=="negated":
                        continue
                    all_confirmed_matches.add(f"{match.lower()}")
            
            if last_resort_tup_spec:
                if not re.search(last_resort_combo_A_regex, sentence):
                    continue
                variable_terms = re.findall(last_resort_combo_B_regex, sentence) #finds all
                if not variable_terms:
                    continue
#                print(f"Variable matches, non last result: {str(variable_terms)}")
                for specific_term in variable_terms:
                        #TODO: test what multiple terms in negex mean
    #                    tagger = negTagger(sentence, [general_match, specific_term], negrules, negP=False)
                    tagger = negTagger(sentence, [specific_term], negrules, negP=False)
                    if tagger.getNegationFlag()=="negated":
                        continue
                    all_confirmed_matches.add(f"{specific_term.lower()}")


    return(all_confirmed_matches)


def build_category_map(mapping_file_list):

    term_to_category_dictionary = {}
    for f in mapping_file_list:
        with f.open(encoding='utf-8', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) < 2:
                    continue               
                term = row[0].lower().strip()
                category = row[1].lower().strip()
                if term.endswith("*"):
                    term = term[:-1]
                term_to_category_dictionary[term]= category     
    return(term_to_category_dictionary)



def build_regex(query_path, search_type = "boundary with s"):
    query = Query(query_path)
    regex = query.build_re(search_type)         
    return (regex)

def main_search(input_args):
 

    input_type, cnxn_string, cursor_execute_string, csv_input_file, standalone_terms_path,\
            combination_paths, standalone_last_path, last_combination_paths,\
            negex_triggers_path, results_file, search_column, output_vars, upfront_val_exclusions,\
            val_exclusion_column, upfront_val_inclusions, val_inclusion_column,\
            upfront_string_exclusions, NER_model, \
            date_exclusion, output_zeros, diagnosis_column, diagnosis_types = input_args

    #category mapping will, for standalone terms, be done based on just that standalone term
    #while for combination terms, will be done based on the 2nd of the combinations. Incoming files
    #should, for combination search types, should be done by listing the 1st part of the required
    #combination by itself, and the 2nd part (in a separate file) with the category it maps to
    logging.info("Building term to category dictionary ...")   
    category_mapping_paths = [standalone_terms_path, standalone_last_path]+combination_paths + last_combination_paths
    term_to_category_dictionary = build_category_map(category_mapping_paths)

    logging.info("Building search terms regular expressions ...")      
    #built search function to accept: standalone regular expression,
    #list of combination searches as list of 2-tuples
    #last resort as a dictionary that has "standalone" key with single standalone regular expression
    #and "tup" key with 2-tuple value
    standalone_terms_regex = build_regex(standalone_terms_path)
    tups = []
    for i in range(len(combination_paths)-1):
        if i%2!=0:
            continue
        regex_1 = build_regex(combination_paths[i])
        regex_2 = build_regex(combination_paths[i+1])
        tups.append((regex_1, regex_2))
    last_resort_dict = {"standalone":None, "tup":None}

    if standalone_last_path:
        last_resort_dict["standalone"] = build_regex(standalone_last_path, search_type = "join with boundary")
    if last_combination_paths:
        #there should be exactly 2 if this is not None
        last_resort_dict["tup"] = [build_regex(last_combination_paths[0]), build_regex(last_combination_paths[1])]


    logging.info("Building negation rules ...")
    with negex_triggers_path.open(encoding='utf-8-sig') as RFILE:
        negrules = sortRules(RFILE.readlines())
    
    logging.info("Building specified inclusions and exclusions ...")
    #upfront val inclusions and exclusions already come as None or a set from the config parse
    #and can be applied directly during cursor iteration
    if upfront_string_exclusions:
        string_exclusion_values = r"|".join(upfront_string_exclusions)
        logging.info(f"Read in string exclusions and building regular expression as {string_exclusion_values}")
        string_exclusion_regex = re.compile(string_exclusion_values, flags = re.IGNORECASE)
    else:
        string_exclusion_values = None
        logging.info("No text exclusions specified")
        

    variable_flags = sorted(set([x[1].upper() for x in term_to_category_dictionary.items()])) #header 
    
#    categories_set = set()
#    for k, v in term_to_category_dictionary.items(): #v is a set
#        for item in v:
#            categories_set.add(item)
#    variable_flags = sorted(categories_set)      
    
    
    logging.info("Preparing to read input file or database table ...")
    if input_type == "CSV":
        infile = csv_input_file
        #read and get  headers, make all upper case, and specify upper case as fieldnames, also strip whitespace
        #remove? Specify to users that headers are case-sensitive?
        with infile.open(encoding='utf-8', newline='') as csvin:
            cursor = csv.DictReader(csvin)  
            modified_fieldnames = [x.strip().upper() for x in cursor.fieldnames]
        #now open file for reading and advance one to not process first line
        csvin = infile.open(encoding='utf-8', newline='')
        cursor = csv.DictReader(csvin, fieldnames = modified_fieldnames)
        cursor.__next__()


    else:
        import pyodbc     
        logging.info(f"Connecting to database with connection string {cnxn_string} and starting cursor selection ...")
        cnxn = pyodbc.connect(cnxn_string)
        cursor = cnxn.cursor()
        cursor.execute(cursor_execute_string)
        logging.info(f'Connected to database with string {cursor_execute_string}')




    logging.info(f"Opening file for writing results at {results_file.name}")
    OUTCSV = open(results_file, "w", encoding='utf-8', newline='')
    writer = csv.writer(OUTCSV)
    #linkage_vars either must assume case-insensitivity or instruct user to ensure case is correct
    
    #header is going to be all the values to keep that the user specified for keeping plus
    #all the variable flags
    header = output_vars + variable_flags   
    writer.writerow(header) #header row      
    
    #we'll use the below dictionary for flagging vars with each observation
    observation_flags =  {x:0 for x in variable_flags}

    for counter, row in enumerate(cursor):
        if counter%100000==0:
            logging.info(f"At row {counter} ...")
        #these are values user always wants printed out, like linkage variables
        output_vars_vals = [row[x] for x in output_vars]

        #check if observation should be excluded based up upfront val exclusions
        if upfront_val_exclusions and str(row[val_exclusion_column]) in upfront_val_exclusions:
            # Hospital Discharge Instructions todo, get EHR version of this
            if output_zeros:
                row_results = output_vars_vals + [0]*len(variable_flags)
                writer.writerow(row_results)
                continue                
            else:
                continue
#        print("Passed upfront val exclusions")
        #check if observation should be excluded based on string exclusion
        #restricting to first 300 chars is a leftover based on NHCS data. Keep?
        if upfront_string_exclusions:
            excl_m = re.search(string_exclusion_regex, row[search_column][:300])
            if excl_m is not None:
                if output_zeros:
                    row_results = output_vars_vals + [0]*len(variable_flags)
                    writer.writerow(row_results)
                    continue                
                else:
                    continue
#        print("Passed string exclusions")
        #check if observation should be excluded because inclusions have been
        #specified and this observation is not in them
        if upfront_val_inclusions and str(row[val_inclusion_column]) not in upfront_val_inclusions:
            # Hospital Discharge Instructions todo, get EHR version of this
            if output_zeros:
                row_results = output_vars_vals + [0]*len(variable_flags)
                writer.writerow(row_results)
                continue                
            else:
                continue
#        print("Passed upfront val inclusion")
        note_text = row[search_column]

        """ search_plain_text expects:
        sentences, standalone_regex, tups, negrules, 
                      date_exclusion = None,
                      last_resort_dict=None, diagnosis=False
                     """
        #default for diagnosis will be True, so that there is no restriction of flagging any search
        #term based on whether the note type it is in is a diagnosis not type or not
        diagnosis = True
        
        #But, if the user specifies they do want that restriction, if this note type is not 
        #of a diagnosis type (as indicated by user), then set diagnosis to false
        if diagnosis_types:
            if str(row[diagnosis_column]) not in diagnosis_types:
                diagnosis = False
            
#        return(note_text, standalone_terms_regex, tups, negrules, date_exclusion, NER_model, last_resort_dict, diagnosis)       
        term_matches = search_plain_text(note_text, standalone_terms_regex, tups, negrules, date_exclusion, NER_model, last_resort_dict, diagnosis)
#        print(f"For sentence {note_text}")
#        print(term_matches)
            
        for match in term_matches:
            match = match.lower()
            if match not in term_to_category_dictionary and match.endswith('s'):
                match = match[:-1]
            try:
                category = term_to_category_dictionary[match].upper() #category is an upper case string
#                print(category)
                observation_flags[category] = 1
#                print(observation_flags)
            except Exception as e:
                print(f"Couldn't find term {match} in term to cats dictionary, with error {str(e)}")
                   
        category_values = [observation_flags[category] for category in sorted(variable_flags)]
#        print(category_values)
#        return(note_text, standalone_terms_regex, tups, negrules, date_exclusion, NER_model, last_resort_dict, diagnosis)
        if not output_zeros and max(category_values)==0:
                continue

        row_results = output_vars_vals + category_values 
        writer.writerow(row_results)
        observation_flags =  {x:0 for x in variable_flags}#reset

            
    logging.info(f"Finished at {counter} rows")
    OUTCSV.close()  
    if input_type == "CSV":      
        csvin.close()

 

def parse_config(configfile):


    config = configparser.ConfigParser()   
    config.read(configfile)

    #OUTPUT. Let's start here to get logfile up and running
    if "results_file" not in config['OUTPUT'] or "logging_file" not in config['OUTPUT']:
        raise KeyError("You must specify results_file path and logging_file path")
    results_file = config['OUTPUT']['results_file'].strip()
    logging_file = config['OUTPUT']['logging_file'].strip()
    if results_file == '' or logging_file == '':
        raise ValueError("You must specify results_file and logging_file")
    results_file = Path(results_file)
    logging_file = Path(logging_file)
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                        level=logging.INFO, filemode='w', filename=logging_file) 
    logging.info(f"Your output file has been specified as: {results_file.name}")
    #INPUT_SETTINGS

    if config['INPUT_SETTINGS']['input_type'].upper().strip() == "DB":
        input_type="DB"
        import pyodbc
        if ("cnxn_string" not in config['INPUT_SETTINGS']) or ("cursor_execute_string" not in config["INPUT_SETTINGS"]):
            raise KeyError("You specified input type as DB but did not specify cnxn_string or did not specify cursor_execute_string")

        cnxn_string = config['INPUT_SETTINGS']['cnxn_string'].strip()
        cursor_execute_string = config['INPUT_SETTINGS']['cursor_execute_string'].strip()
        
        if cnxn_string =='' or cursor_execute_string=="":
            raise ValueError("You have not specified cnxn_string or cursor_execute_string")
        csv_input_file = None            

    elif config['INPUT_SETTINGS']['input_type'].upper().strip() == "CSV":
        input_type="CSV"
        if "csv_input_file" not in config["INPUT_SETTINGS"]:
            raise KeyError("You specified input type as CSV but did not specify csv_input_file")
        csv_input_file = config['INPUT_SETTINGS']['csv_input_file'].strip()
        if csv_input_file=="":
            raise ValueError("You have specified input_type as CSV but did not specified csv_input_file")
        csv_input_file = Path(csv_input_file)
        cnxn_string = None
        cursor_execute_string = None
    else:
        sys.exit("You must specify input_type as DB or CSV")
    logging.info(f"Your input type has been specified as {input_type}")

    
    #TERMS
    if "standalone_terms_path" not in config['TERMS'] or config['TERMS']["standalone_terms_path"].strip()=='':
        raise KeyError("You must specify standalone search terms path")
    if "negex_triggers_path" not in config['TERMS'] or config['TERMS']["negex_triggers_path"].strip()=='':
        raise KeyError("You must specify negex_triggers_path")
    standalone_terms_path = Path(config['TERMS']["standalone_terms_path"].strip())
    negex_triggers_path = Path(config['TERMS']["negex_triggers_path"].strip())
    
    combination_configs = [x.strip() for x in config['TERMS'] if x.startswith("combination") and x.strip()]
    if len(combination_configs)%2 != 0:
        raise KeyError("Combination paths must be specified in pairs")
    elif len(combination_configs)==0:
        combination_paths = None
    else:
        combination_paths = [Path(config['TERMS'][x].strip()) for x in combination_configs ]
        
    if "last_standalone" in config['TERMS'] or config['TERMS']["last_standalone"].strip()!='':
        standalone_last_path = Path(config['TERMS']["last_standalone"].strip())
    else:
        standalone_last_path = None


    last_combination_configs = [x.strip() for x in config['TERMS'] if x.startswith("last_combination") and x.strip()]
    if len(last_combination_configs) not in (0, 2):
        raise KeyError("If used, there must be exactly two 'last_combination' paths")
    elif len(last_combination_configs)==0:
        last_combination_paths = None
    else:
        last_combination_paths = [Path(config['TERMS'][x].strip()) for x in last_combination_configs ]
        

   
    #SEARCH_CONFIG
    if "col_to_search" not in config['SEARCH_CONFIG']:
        raise KeyError("You must specify which column to search")
    search_column = config['SEARCH_CONFIG']['col_to_search'].strip()
    if search_column == '':
        raise ValueError("You must specify which column to search")
        
    if "output_columns" not in config['SEARCH_CONFIG'] or config['SEARCH_CONFIG']['output_columns'].strip()=='':
        output_vars = []
    else:
        output_vars = [x.upper().strip() for x in config['SEARCH_CONFIG']['output_columns'].split(',') if x.strip()]

    if "upfront_val_exclusions" not in config['SEARCH_CONFIG'] or config['SEARCH_CONFIG']['upfront_val_exclusions'].strip()=='':        
        upfront_val_exclusions=None
        val_exclusion_column = None
    else:
        upfront_val_excl_in = [x.strip() for x in config['SEARCH_CONFIG']['upfront_val_exclusions'].split(",") if x.strip()]
        upfront_val_exclusions = set(upfront_val_excl_in[1:])
        val_exclusion_column = upfront_val_excl_in[0]
        

    if "upfront_val_inclusions" not in config['SEARCH_CONFIG'] or config['SEARCH_CONFIG']['upfront_val_inclusions'].strip()=='':        
        upfront_val_inclusions=None
        val_inclusion_column=None
    else:
        upfront_val_incl_in = [x.strip() for x in config['SEARCH_CONFIG']['upfront_val_inclusions'].split(",") if x.strip()]
        upfront_val_inclusions = set(upfront_val_incl_in[1:])
        val_inclusion_column = upfront_val_incl_in[0]

    if "upfront_string_exclusions" not in config['SEARCH_CONFIG'] or config['SEARCH_CONFIG']["upfront_string_exclusions"].strip()=='':
        upfront_string_exclusions=None
    else:
        upfront_string_exclusions = [x.strip() for x in config['SEARCH_CONFIG']['upfront_string_exclusions'].split(",") if x.strip()]

    if "NER_model" not in config['SEARCH_CONFIG'] or config['SEARCH_CONFIG']['NER_model'].strip() =='':
        NER_model = None
        date_exclusion = None
        logging.info("No NER model specified and no date exclusion will be performed")
    else:
        NER_model_path = Path(config['SEARCH_CONFIG']['NER_model'].strip())
        import spacy
        NER_model = spacy.load(str(NER_model_path))
        logging.info(f"NER model successfully loaded from path {NER_model_path.name}")
        
        if "custom_date_exclusion" not in config['SEARCH_CONFIG'] or config['SEARCH_CONFIG']['custom_date_exclusion'].strip()=='':
            custom_date_exclusion = None
        else:
            custom_date_exclusion = config['SEARCH_CONFIG']['custom_date_exclusion'].strip()
            #TODO: make sure re.escape behaves as expected
            date_exclusion = re.compile(re.escape(custom_date_exclusion)) 

        if not custom_date_exclusion:
            if "year_excluded" not in config['SEARCH_CONFIG'] or config['SEARCH_CONFIG']['year_excluded'].strip()=='':
                raise KeyError("You specified an NER model but did not specify custom_date_exclusion or year_excluded")
            else:
                year_excluded = config['SEARCH_CONFIG']['year_excluded'].strip()
                
            if not (year_excluded.isdigit() and len(year_excluded)==4):
                raise ValueError("Year excluded must be 4 digits")     
            else:
                #date_exclusion = re.compile(r"\b2017\b|\b\d(\d)?/\d(\d)?/(20)?17\b")
                regex_string = r"\b%s\b|\b\d(\d)?/\d(\d)?/(%s)?%s\b" % (year_excluded, year_excluded[:2], year_excluded[-2:])
                date_exclusion = re.compile(regex_string)
            logging.info(f"Date exclusion: {str(date_exclusion)}")


    
    if "output_zeros" in config['SEARCH_CONFIG'] and config['SEARCH_CONFIG']["output_zeros"].strip().lower()=="true":
        output_zeros= True
    else:
        output_zeros = False
        
    if "diagnosis" in config['SEARCH_CONFIG'] and config['SEARCH_CONFIG']["diagnosis"].strip()!='':
        pieces = [x.strip() for x in config['SEARCH_CONFIG']["diagnosis"].split(",") if x.strip()]
        diagnosis_column = pieces[0]
        diagnosis_types = pieces[1:]
    else:
        diagnosis_types = None    
        diagnosis_column = None

#                

    return([input_type, cnxn_string, cursor_execute_string, csv_input_file, standalone_terms_path,
            combination_paths, standalone_last_path, last_combination_paths,
            negex_triggers_path, results_file, search_column, output_vars, upfront_val_exclusions,
            val_exclusion_column, upfront_val_inclusions, val_inclusion_column, 
            upfront_string_exclusions, NER_model, 
            date_exclusion, output_zeros, diagnosis_column, diagnosis_types])


def parse_and_run(configfile):
    
    parsed_args = parse_config(configfile)

    return(parsed_args)
    
    

if __name__=="__main__":
    
    #User hard-coded configfile path. Windows paths require the r, raw string for backslashes
    configfile = Path(r"FY19_SUD_test_config.txt")
    if len(sys.argv) > 1:
        configfile = sys.argv[1]
        print(f"Configfile read in as {configfile}")

    else: #if not via command line, specify configfile path here
        print(f"Config file hard-coded and specified as {configfile}")
    if not configfile:
        raise ValueError("You must specify a config file either hard-coded in main or via a config file")
    parsed_args = parse_and_run(configfile)
    main_search(parsed_args)


        
        
