# coding: utf-8

# importing module located in parent folder
import sys
sys.path.insert(0, '../')

# maing testing library
import orcid

# additional libraries
import json
import codecs

# setting logging to the DEBUG mode
import logging

#logging.getLogger("#orcid#").setLevel(logging.DEBUG)
logging.getLogger("#orcid#").setLevel(logging.INFO)

#retrieve my own's profile from his ORCID
me = orcid.get('0000-0001-5661-4587')

def show_keyword(obj):
    print obj.keywords
    for key_word in obj.keywords:
        print key_word

def print_publications(obj):
    """
        Printing keywords
    """
    print '[i] printing the keywords set by author'
    for value in obj.publications:
        print value

def save_bibtex(bibtex, file_name='orcid-bibtex-output.bib', encoding='utf-8'):
    """
        (dict, str, str) -> None

        Saving bibtex to the file, grouped by year.
    """

    _file = codecs.open(file_name, 'w', encoding)

    for key in bibtex:
        _file.write("%%%%%%%%%%%%%%%% \n%% %s \n%%%%%%%%%%%%%%%%\n\n" % key)
        bibtex_group = ''
        for value in bibtex[key]:
            bibtex_group += value + '\n\n'
        _file.write(bibtex_group)

    _file.close()

    print '[i] bibtex was created, check following file: %s ' % (file_name)

def save_nocite(bibtex, file_name='orcid-nocite-output.tex', encoding='utf-8'):
    """
        (dict, str, str) -> None

        Saving bibtex to the file, grouped by year.
    """

    def extract_bibtex_id(s):
        start = s.find('{') + 1
        end = s.find(',', start)
        return  s[start:end]

    _file = codecs.open(file_name, 'w', encoding)

    for key in bibtex:
        _file.write("%%%%%%%%%%%%%%%% \n%% %s \n%%%%%%%%%%%%%%%%\n\n" % key)
        nocite_group = ''
        for value in bibtex[key]:
            nocite_group += '\\nocite{' + extract_bibtex_id(value) + '}' + '\n'
        _file.write(nocite_group)

    _file.close()

    print '[i] tex with \\nocite was created, check following file: %s ' % (file_name)

def extract_bitex(obj):
    """
        (Class) -> dict()

        Method takes as an input object with all publications from ORCID and forms dict with it.
    """

    bibtex = {}
    for value in obj.publications:
        if value.citation.citation_type == 'BIBTEX':
            if value.publicationyear not in bibtex:
                bibtex[value.publicationyear] = list()
                bibtex[value.publicationyear].append(value.citation.citation)
            else:
                bibtex[value.publicationyear].append(value.citation.citation)
        else:
            print '[i] this publications is having no BIBTEX %s ' % (value)

    return bibtex

def orcid_bibtex(obj):
    """
        (Class) -> None

        Extrating bibtex from ORCID, saving it to the file
    """

    # extracting bibtex
    orcid_bibtex = extract_bitex(me)

    # saving bibtex to file
    save_bibtex(orcid_bibtex)

    # citing extracted bibtex
    save_nocite(orcid_bibtex)

#show_keyword(me)
#print_publications(me)
orcid_bibtex(me)