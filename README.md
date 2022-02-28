# FY19_pcortf_nlp

First release of FY19 NLP PCORTF code

FY19 Subtance Use Disorder and Mental Health Issues

Git ReadMe
  
December 20, 2021

Author: Nikki Adams; oxf7@cdc.gov 

This is the first release of the code used to analyze the clinical notes from the 2016 National Hospital Care Survey (NHCS) data for the fiscal year (FY) 2019 Office of the Secretary Patient-Centered Outcomes Research Trust Fund-funded project on the identification of patients with substance use disorders (SUD) and mental health issues (MHI) in hospitalizations and emergency department visits. The National Center for Health Statistics conducts NHCS which involves the collection of a participating hospital’s (UB)-04 administrative claims records or electronic health records (EHR) in a 12-month period. For a hospital to be eligible for NHCS, the hospital must be a non-federal, non-institutional hospital with 6 or more staffed inpatient beds. The FY 2019 project was a capstone to the FY 2018 project, which identified hospital encounters with opioid-involvement. In the complete algorithm, it was from these opioid-involved encounters that MHIs and SUDs were searched. This repository contains only the SUD and MHI search, not the opioid-involvement search, which is located here. The goal of this code is to flag MHI (mental health issue) and SUD (substance use disorder) mentions in clinical text, primarily those that rise to diagnosis-level phrasing. The code to flag opioid-involvement, SUD, and MHI in hospital encounters by medical codes from structured data is located here. 

Detailed information on the project can be obtained for the opioid-involvement portion of the project, here:

https://www.cdc.gov/nchs/data/series/sr_02/sr2-188.pdf


The methodology report for the SUD and MHI portions of the project is forthcoming, however the broad methodology referenced in the opiod report above is the same across both projects. Please note, SUD and MHI searches were designed to be run separately and perform best as separate runs.

This repository contains data file mappings for child categories under the parent categories of Substance Use Disorder and Mental Health Issues. In order to calculate the final counts for the parent categories, after running the code, the parent categories can be created by counting all observations where any value in the child category (e.g. SUD_NICOTINE) creates a positive flag in the parent category (e.g. SUD). For more information, see the data dictionary and description here:

https://www.cdc.gov/nchs/data/nhcs/FY19-RDC-2021-06-01-508.pdf

This file contains mappings for child categories under the parent categories of Substance Use Disorder, and Mental Health Issues. In order to calculate the final counts for the parent categories, after running the code, you can create these parent categories by counting all observations where any value in the child category (e.g. SUD_NICOTINE) creates a positive flag in the parent category (e.g. SUD). For more information, see the data dictionary and description here:

https://www.cdc.gov/nchs/data/nhcs/FY19-RDC-2021-06-01-508.pdf

**Usage**

Once the config file is properly set up, this code can be run either by hard-coding in the config file in the main portion of the code or by passing in the config file as a command line argument.

Option 1 – Hard-coded: Look in the main code (NCHS_PCORTF_NLP_SUD_MHI.py, near bottom of file) for these lines and put the path where indicated:



```python
configfile = Path(r"FY19_SUD_test_config.txt") 

``` 

Option 2 – Command line argument 

At a command line type: 

    python NCHS_PCORTF_NLP_SUD_MHI.py FY19_SUD_test_config.txt 


An example input csv file would be as below

| UNIQUE_ID | STATE | NOTE_TYPE | LITERAL_TEXT |
| ------ | ------ | ------ | ------ |
| 456X | UTAH | Social History | History of heroin abuse. |
| 123X | ALASKA | Discharge Diagnosis | Anxiety |
| 321X | NEBRASKA | Some other note type | Family history of anxiety |


With example output as:

| UNIQUE_ID | STATE | SUD_OPIOID | ANXIETY_OTHER |
| ------ | ------ | ------ | ------ |
| 456X | UTAH | 1 | 0 |
| 123X | ALASKA | 0 | 1 |
| 321X | NEBRASKA | 0 | 0 |

With configuration setings of 
- output_zeros = True, so that observations that have no positive flags are still output
- NOTE_TYPE="Discharge Diagnosis" as a diagnosis note type, thus allowing weaker evidence for flagging (if this is not specified, a single word like "anxiety" or "depression" is considered to not rise to the level of a diagnosis)


Note the third observation also receives no positive flags as it does not pass the filter in the code for sentences about family history.

**Package Requirements**

Running this code requires Python >= 3.4. 

All packages necessary to run this code can be obtained by downloading or cloning this repository. Included modules and data:

- [negex_adjusted.py](fy19_nlp_pcortf/negex_adjusted.py) (modified from original) 
- [build_queries.py](fy19_nlp_pcortf/build_queries.py) 
- [negation_triggers.txt](fy19_nlp_pcortf/data/negation_triggers.txt) 
- search terms used in the NCHS PCORTF algorithm and sample input and config files (all in [data](/data))


**Install 3rd party packages** 

You can do this manually (packages outlined above) or by installing all requirements via the requirements.txt document  
    pip install requirements.txt 
or if using Anaconda, within your desired environment: 
    conda install --file requirements.txt 

 

The necessary 3rd party packages in the requirements file are. SpaCy is only necessary if you are using NER for date exclusion, and pyodbc is only necessary if you are connecting to a database: 

    nltk >=3.4 
    pyodbc >=4.0 
    spacy >=2.0 

 

The original code for negex was obtained from: 

https://github.com/chapmanbe/negex/blob/master/negex.python/negex.py 

but was altered the code slightly to allow both forward and backward-looking negation for the same negation trigger, so we recommend using the negex_adjusted.py included in this repository. 

The sent_tokenize() function used here from NLTK installs in a lazy fashion such that the code is installed but the necessary model is not downloaded until called. Prior to running this code, type the below in an interpreter for the environment to force use of the model. If the model is not downloaded, NLTK will give prompts for downloading: 

    from nltk.tokenize import sent_tokenize 
    sent_tokenize("Hello.") 

 

SpaCy is only needed if NER (named entity recognition) is used, and NER is only implemented in this version for date exclusion. In the original version of this code, NER was also used for drug term detection, at which point candidates were automatically and manually reviewed as possible misspellings of previously identified opioids (see aforementioned methodology report for more information). If using spaCy, a spaCy model will also have to be downloaded. Here’s how to download a base English model: 

    python -m spacy download en_core_web_sm 

After download, obtain the path to where the model is installed. Look for the parent folder that contains the “ner” folder. If it’s not clear, in the environment in which the model was downloaded, type: 

    import spacy 
    nlp = spacy.load("en_core_web_sm") 
    nlp.path 

And it will output the path to the model. 

**Input and Output Files**

Three files serve as input for this package, and it will produce 2 output files. 

_Input file #1_ – Source data 

This package will accept two types of input data: (1) a csv file, with column names as the first row or (2) a table in Microsoft SQL for Windows. In theory, connecting to SQLite and possible other databases should work the same using the pyodbc package used here with the code as we have currently written it, but only csv and Microsoft SQL Server 2016 have been tested. 

_Input file #2 and above_  – Term mapping files 

These files are csv files where the first column is the phrase to be searched for and the second column is the output variable to be flagged if that term is found. Below is an example of the first 2 lines of what this file should look like. Do not include a header in these files. The 'standalone' type file includes terms that, on their own, trigger a flag for the indicated variable.


    unspecified anxiety disorder,ANXIETY_UNSPECIFIED
    social phobia,ANXIETY_SOCIAL

When “social phobia” is found, there will be an output variable ANXIETY_SOCIAL that will have a ‘1’ in it for the row in which “oxycontin” was found. Combination searches can also be performed where, in order to be considered a match, there must be a match of something in File A and something in File B. For these, list these two files in the config file one after the other, as in:

    combination_1_A = data\SUD_combo1_A.txt
    combination_1_B = data\SUD_combo1_B.txt

The 'A' files should include only the terms required for the first match, i.e. a single column (no header) of terms to be searched for. The 'B' files should include 2 columns, the first being the term to be searched for and the second being the category that will be flagged once the B match is confirmed.

"Last resort" terms can also be specified. These are only searched for if the searches from the other files are not found in the sentence under analysis. Both a last resort standalone and a single pair of last resort combinations may be specified.

_Input file #3_ – Config file 

This file specifies where the input files are, where the output files will go, and other allowed options. A sample config file is included in this repository, but every option is explained in the next section.  

_Output file #1_ – Results file 

This file will have the results of the term search 

_Output file #2_ – log file 

TThis file will print status updates on the search, printing an update every 100,000 rows of search, along with a final completion message.

**Setting Up Your Config File** 

**SAMPLE CONFIG FILE**

Note that values should not include quotation marks. In this example, input to be searched is coming from a SQL database connection. In the example config file included in data/ , input is a csv file:

    [INPUT_SETTINGS] 
    input_type = DB
    cnxn_string = DRIVER={SQL Server}; SERVER=DSPV-INFC-CS161\PROD; DATABASE=MyDB_2018; Trusted_Connection=yes 
    cursor_execute_string = SELECT * FROM MyDB_2018.dbo.MYDB 
    csv_input_file = 

    [TERMS] 
    search_terms_path = C:\Users\docs\FY18_mapping.txt 
    negex_triggers_path = C:\Users\docs\negex_triggers.txt 


    [OUTPUT] 
    results_file = C:\Users\docs\FY18_test_out.txt 
    logging_file = C:\Users\docs\FY18_logfile.txt 

    [SEARCH_CONFIG] 
    col_to_search = LITERAL_TEXT 
    output_columns = UNIQUE_ID, STATE 
    upfront_val_exclusions = MEDICARE, 0 
    upfront_string_exclusions = patient education 
    NER_model  = C:\Users\yourpath\en_core_web_sm\en_core_web_sm-3.0.0
    year_excluded = 2017 
    custom_date_exclusion = '\bJan(uary)?\W{1,2}(20)?18\b' 
    overdose = True 
    exclusion_terms = \yourpath\test_exclusions.txt 


**DETAILED EXPLANATION OF CONFIG FILE**

Included above are all available options, with examples. The text below explains whether they are required or optional and what to specify. For values that are dependent on another option being selected (e.g. cursor_execute_string is only applicable if input_type=DB), the dependent values are ignored when they are not relevant; it does not matter if that dependent value is left blank or not. 

    [INPUT_SETTINGS] 
    input_type: REQUIRED. Options are CSV for a csv file or DB for database connection. 

    cnxn_string: REQUIRED if input_type=DB_. The string used to connect to the database through pyodbc. 

    cursor_execute_string: REQUIRED if input_type=DB_. The query select string. 
    csv_input_file: REQUIRED if input_type=CSV. The path to the input csv file. 

    [TERMS] 
    standalone_terms_path: REQUIRED. Path to a 2-column csv file of search term/phrase and column which will be flagged when that term is found. This command will search for terms with word boundaries on either side but does allow a final “*” to indicate no word-boundary on right side. Do not include headers.

    combination_X: OPTIONAL. If used, must be an even number of files paths, where the A and B files of the combination are listed one after the other. The first file (the 'A' file) contains just a single column of terms to search file, while the second file (the 'B' file) contains 2 columns, with the first being the terms to search for and the second being the category flagged. Do not include headers.

    last_standalone: OPTIONAL. If used, this is a 2-column csv file formatted like the standalone_terms_path file. These terms are only to be searched for if the other standalone terms and combination terms are not found within that sentence.

    last_combination_X: OPTIONAL. If used, this is a file formatted like the combination A files. These last combination files work like last_standalone and will only be searched if the previous standalone and combination_X search terms were not found in that sentence.

    negex_triggers_path: REQUIRED. Path to the negex triggers file. A file is included but can be modified at user discretion. These are the negation triggers (“not”, “denies”, etc.) 

    [OUTPUT] 
    results_file: REQUIRED. Path to the output file. Output is csv format. 

    logging_file: REQUIRED. Path to where logging messages about output will print. 

    [SEARCH_CONFIG] 
    col_to_search: REQUIRED. Which column the term searches are performed in. Case-sensitive. 

    output_columns: OPTIONAL. A comma-separated list of which columns (e.g. unique identifiers or linkage variables) should always be output with each observation. Case-sensitive. 

    upfront_val_exclusions: OPTIONAL. A comma-separated list of at least length 2. The first item is the column in which the exclusion is to be searched for. Positions 1 to end are all the values to exclude. For example, entering: “STATE, ALABAMA, Alaska” (no quotes) would exclude any rows for which the value in column STATE equals “ALABAMA” or “ALASKA”. Case-sensitive. The value of the cell must equal the exclusion, i.e. this is not a substring search. 

    upfront_val_inclusions: OPTIONAL. A comma-separated list of at least length 2. The first item is the column in which the inclusion is to be searched for. Positions 1 to end are all the values to include. For example, entering: “STATE, ALABAMA, Alaska” (no quotes) would include only rows for which the value in column STATE equals “ALABAMA” or “ALASKA”. Case-sensitive. The value of the cell must equal the inclusion, i.e. this is not a substring search.

    upfront_string_exclusions: OPTIONAL. A comma-separated list of any strings that, if found, exclude that row from being searched for any of the search terms. Case-sensitive. These are regular expression searches and thus can occur anywhere in the cell (unlike upfront_val_exclusions). These exclusions are only searched for in the same col as col_to_search 

    NER_model: OPTIONAL. NER only used currently for date exclusions. 

    year_excluded: OPTIONAL, but either this or custom_date_exclusion is REQUIRED if NER_model is specified. To exclude a single year, type in the 4-digit year here 

    custom_date_exclusion: OPTIONAL, but either this or year_excluded is REQUIRED if NER_model is specified. To have a custom regular expression date exclusion beyond just a year, put it here. 

    output_zeros: OPTIONAL. Default will be false, so True must be specified if desired. If true, there will be an output for every input observation, regardless of whether anything was found. If false, only rows where something was positively flagged will be output.


**Addendum**

For the algorithm as run on NHCS, for which it was originally developed, and which produced the dataset in the NCHS RDC (link here), the results were post-processed to group into parent categories as well as to apply groupings which handle flagged "exclusion" categories. The code to do that has not been included in this release, but provided below is a code sample of how it would work for our specific categories. The output dataset was at the encounter level, but each encounter originally consisted of multiple note observations. The way these exclusion categories were processed differed with respect to whether they were applied at the encounter level or at the observation level, as shown below.

For the MHI (mental health issue) run, we had a category "DEP_EXCLUSION" which flagged terms where, if found within that observation, should negate a DEPRESSION_OTHER flag. That is, the exclusion is handled at the observation level, and then observations are grouped into encounters. Assuming output is originally at the observation level, where each observation had its own "NOTE_EVENTNUMBER",and the variables to group by are in a list "linkage_variables", the processing to group to the encounter level and handle the exclusions was:

```python
    df['DEPRESSION_OTHER'] = np.where((df['DEP_EXCLUSION']==1), 0, df['DEPRESSION_OTHER'])

    df.drop("DEP_EXCLUSION", axis=1, inplace=True)     

    df = df.groupby(linkage_variables, as_index=False).max().drop('NOTE_EVENTNUMBER', axis=1) 
```

For the SUD (substance use disorder) run, we had a "NICOTINE_EXCLUSION" which, if flagged for any observation within an encounter, negated an SUD_NICOTINE flag. That is, observations are first grouped to the encounter level, and then the exclusion is handle. With the same assumptions as above, that code was:

```python

    df = df.groupby(linkage_variables, as_index=False).max().drop('NOTE_EVENTNUMBER', axis=1)  

    df['SUD_NICOTINE'] = np.where((df['NICOTINE_EXCLUSION']==1), 0, df['SUD_NICOTINE'])
    
    df.drop("NICOTINE_EXCLUSION", axis=1, inplace=True)
```

**Licenses and Disclaimers**

**Public Domain**

This repository constitutes a work of the United States Government and is not subject to domestic copyright protection under 17 USC § 105. This repository is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/). All contributions to this repository will be released under the CC0 dedication. By submitting a pull request you are agreeing to comply with this waiver of copyright interest.

**License**

The repository utilizes code licensed under the terms of the Apache Software License and therefore is licensed under ASL v2 or later.

This source code in this repository is free: you can redistribute it and/or modify it under the terms of the Apache Software License version 2, or (at your option) any later version.

This source code in this repository is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the Apache Software License for more details.

You should have received a copy of the Apache Software License along with this program. If not, see http://www.apache.org/licenses/LICENSE-2.0.html

The source code forked from other open source projects will inherit its license.

**Privacy**

This repository contains only non-sensitive, publicly available data and information. All material and community participation is covered by the Surveillance Platform [Disclaimer](https://github.com/CDCgov/template/blob/master/DISCLAIMER.md) and [Code of Conduct](https://github.com/CDCgov/template/blob/master/code-of-conduct.md). For more information about CDC's privacy policy, please visit http://www.cdc.gov/privacy.html.

**Contributing**

Anyone is encouraged to contribute to the repository by [forking](https://help.github.com/articles/fork-a-repo) and submitting a pull request. (If you are new to GitHub, you might start with a [basic tutorial](https://help.github.com/articles/set-up-git).) By contributing to this project, you grant a world-wide, royalty-free, perpetual, irrevocable, non-exclusive, transferable license to all users under the terms of the [Apache Software License v2](http://www.apache.org/licenses/LICENSE-2.0.html) or later.

All comments, messages, pull requests, and other submissions received through CDC including this GitHub page are subject to the [Presidential Records Act](http://www.archives.gov/about/laws/presidential-records.html) and may be archived. Learn more at http://www.cdc.gov/other/privacy.html.

**Records**

This repository is not a source of government records, but is a copy to increase collaboration and collaborative potential. All government records will be published through the [CDC web site](http://www.cdc.gov/).

**Notices**

Please refer to [CDC's Template Repository](https://github.com/CDCgov/template) for more information about [contributing to this repository](https://github.com/CDCgov/template/blob/master/CONTRIBUTING.md), [public domain notices and disclaimers](https://github.com/CDCgov/template/blob/master/DISCLAIMER.md), and [code of conduct](https://github.com/CDCgov/template/blob/master/code-of-conduct.md).
