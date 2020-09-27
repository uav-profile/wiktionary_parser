# parsers_py
Different parsers

# wiktionary.py:
  Requirements:
  - requests
  - BeautifulSoup (bs4)
  - lxml
  
  ### Running: 
    python wiktionary.py "Испанский_язык"
  
  ### Result:
    csv-file "Испанский_язык.csv" with pairs "word;translate"
    
  ### Also:
      
      Import:
            1. from wiktionary import make_dictionary
               make_dictionary(lang = "Испанский_язык", csv = True, print_to_console = True)
            2. from wiktionary import get_languages
               get_languages(lang_base = "languages.txt", mode = "write")
      
      Addition: use "__doc__": print(get_languages.__doc__)
                               print(make_dictionary.__doc__)
                              
