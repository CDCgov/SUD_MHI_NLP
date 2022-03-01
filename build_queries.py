# -*- coding: utf-8 -*-
"""
Created on Thu Feb  7 16:15:15 2019
Import package with functions for different types of searches
This package can build the regular expressions used for searching
with the following functions: 
    join_re(infilePath) #for ESOOS join
    no_bound_re(infilePath) #for ESOOS no word bounds
    bound_with_s_re(infilePath) #for DMI
    bound_re(infilePath) #for FDA or NEISS
    
Note: In the future, if there is another query type like FDA and NEISS,
which are the same, more efficient to 

Join_RE will build a regular expression for terms from the list
with a join, "|". Word boundaries are variably specified in this file, differing
by term, and are specified in the original infile. ESOOSNoBoundRE will build a trie
regular expression with no word boundaries. DMIOpioidsRE will build a tried regular
expression with word boundaries, and an optional s at the end. NEISSOpioidsRE will
build a trie regular expression with word boundaries, no optional s. FDAStimsDepsRE
will build a trie regular expression with word boundaries, no optional s.
NEISSOpioidsRE and FDAStimsDepsRE both call simpleREBuild to build their REs.

The package can also search text using the regular expressions built with
these functions:

    simple_re_search(compiledRE, text)
    
This function takes a compiled regex, built from the earlier functions,
and returns the results of re.findall for that regex on text (a list)

@author: oxf7
"""

from pathlib import Path
import re
class Query():
    
    def __init__(self, queries):         

        if type(queries)==list:
            self.input_type = "list"
            self.queries = queries
            self.name = "Custom List"
        else:
            self.input_type = "file"
            self.filepath = Path(queries)
            self.name = self.filepath.name


    def build_re(self, query_type="boundary"):
        allowable_query_types = ["join", "join with boundary", "no boundary", "boundary", "boundary with s"]
        if query_type in allowable_query_types:
            self.query_type = query_type
        else:
            raise ValueError(f"Unrecognized query type {query_type}, use one of {allowable_query_types}")          
        #3/5/20 update, making individual search terms a list ton attribute
        #so that the terms can be accessed as not a regex
        if self.input_type=="file":
            try:
                with open(self.filepath, encoding='utf-8-sig') as g:
                    lines = [x.strip() for x in g.readlines() if x.strip()]
            except UnicodeDecodeError:
                with open(self.filepath) as g:
                    lines = [x.strip() for x in g.readlines() if x.strip()] 
        else:
            lines = [x for x in self.queries if x.strip()]
                
        self.expression_set = set()
        mixed_type = False
        for line in lines:
            line = line.split(",")[0] #sometimes single term per line, sometimes 1st term in csv, to do re.split(r'[\t,]')
#            line = re.split(r"[,\t]", line)[0]
            if line.endswith("*"):
                mixed_type = True
            self.expression_set.add(line.lower().strip())
                    
        self.expression_list = sorted(self.expression_set, key=lambda x: len(x), reverse=True)
        if self.query_type == 'join':
            self.re = self.join_re()
        elif self.query_type == 'join with boundary':
            self.re = self.join_wb_re()
        elif mixed_type:
            self.query_type = "join_wb_re"
            self.re = self.join_wb_re()
        else:
            self.re = self.trie_re()
        return(self.re)
    
    def join_re(self): 

        catREs = sorted([r'%s' % x for x in self.expression_list])
        catREString= "|".join(catREs)
        print(f"Successfully built a regex join for {self.name} with {len(catREs)} items")    
        return(re.compile(catREString, flags=re.IGNORECASE))

    def join_wb_re(self): 
        #TODO: make single boundary in regex at beg and end, and test function
        catREs = []
        for x in self.expression_list:
            if "*" in x:
                x = x.replace('*', '')
                catREs.append(r'\b%s' % x)
            else:
                catREs.append(r'\b%s\b' % x)
#        catREs = sorted([r'\b%s\b' % x for x in self.expression_list])
        catREString= "|".join(catREs)
        print(f"Successfully built a regex join for {self.name} with {len(catREs)} items")    
        return(re.compile(catREString, flags=re.IGNORECASE))
          
    def trie_re(self):
        trie = Trie()
        for searchTerm in self.expression_list:
            trie.add(searchTerm)
        if self.query_type=="no boundary":
            searchString = r'%s' % trie.pattern()
            print(f"Successfully built trie regex query, no word boundaries, for {len(self.expression_list)} items") 
        elif self.query_type=="boundary with s":
            searchString = r'\b%ss?\b' % trie.pattern()
            print(f"Successfully built trie regex query, adding word boundaries, optional s for file:{self.name} for {len(self.expression_list)} items")
        else: #boundary condition
            searchString = r'\b%s\b' % trie.pattern()
            print(f"Successfully built trie regex query, adding word boundaries, for file:{self.name} for {len(self.expression_list)} items")     
        
        return(re.compile(searchString, flags=re.IGNORECASE))
        
class Trie():
    """Regex::Trie in Python. Creates a Trie out of a list of words. The trie can be exported to a Regex pattern.
    The corresponding Regex should match much faster than a simple Regex union. Found this in Stack Overflow ..."""

    def __init__(self):
        self.data = {}

    def add(self, word):
        ref = self.data
        for char in word:
            ref[char] = char in ref and ref[char] or {}
            ref = ref[char]
        ref[''] = 1

    def dump(self):
        return self.data

    def quote(self, char):
        return re.escape(char)

    def _pattern(self, pData):
        data = pData
        if "" in data and len(data.keys()) == 1:
            return None

        alt = []
        cc = []
        q = 0
        for char in sorted(data.keys()):
            if isinstance(data[char], dict):
                try:
                    recurse = self._pattern(data[char])
                    alt.append(self.quote(char) + recurse)
                except:
                    cc.append(self.quote(char))
            else:
                q = 1
        cconly = not len(alt) > 0

        if len(cc) > 0:
            if len(cc) == 1:
                alt.append(cc[0])
            else:
                alt.append('[' + ''.join(cc) + ']')

        if len(alt) == 1:
            result = alt[0]
        else:
            result = "(?:" + "|".join(alt) + ")"

        if q:
            if cconly:
                result += "?"
            else:
                result = "(?:%s)?" % result
        return result

    def pattern(self):
        return self._pattern(self.dump())
    
