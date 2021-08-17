# coding: utf-8

import sys
import json
import requests
import logging

from .constants import (ORCID_PUBLIC_BASE_URL, ORCID_SANDBOX_BASE_URL)
from .utils import dictmapper, u, MappingRule as to

from .exceptions import NotFoundException

#
# configure logger
#

_logger_depth = 'INFO'

logger = logging.getLogger("#orcid#")
logger.setLevel(getattr(logging, _logger_depth))
stdout_sh = logging.StreamHandler(sys.stdout)
stdout_sh.setLevel(getattr(logging, _logger_depth))
custom_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stdout_sh.setFormatter(custom_formatter)
logger.addHandler(stdout_sh)

BASE_HEADERS = {'Accept':'application/orcid+json',
                'Content-Type': 'application/json;charset=UTF-8'}

#
# HELPERS
#

def _parse_keywords(d):
    # XXX yes, splitting on commas is bad- but a bug in ORCID
    # (https://github.com/ORCID/ORCID-Parent/issues/27) makes this the  best
    # way. will fix when they do
    if d is not None:
        #return d.get('keyword',[{}])[0].get('value','').split(',')
        return [val['content'] for val in d['keyword']]
    return []

def _parse_researcher_urls(l):
    if l is not None:
        return [Website(d) for d in l]
    return []

def _parse_publications(l):
    _publications = []

    if l is not None:
        # logger.debug(json.dumps(l, sort_keys=True, indent=4, separators=(',', ': ')))
        # getting through all works
        for d in l:
            path = d['work-summary'][0]['path']
            _url = '{0}{1}'.format(ORCID_PUBLIC_BASE_URL, path[1:]) # remove first symbol '/'
            _res = requests.get(_url, headers = BASE_HEADERS)
            _json_body = _res.json()
            logger.debug('REQUEST (PUBLICATIONS): {0}'.format(json.dumps(_json_body, sort_keys=True, indent=4, separators=(',', ': '))))
            _publications.append(Publication(_json_body))

    return _publications

def _parse_educations(l):
    _educations = []

    if l is not None:
        for d in l:
            name = d['organization']['name']
            _educations.append(name)

    return _educations


#
# MAPPERS
#

AuthorBase = dictmapper('AuthorBase', {
    #'orcid'            :['orcid-profile','orcid-identifier','path'],
    'orcid'             :['orcid-identifier', 'path'],
    'family_name'       :['person', 'name', 'family-name','value'],
    'given_name'        :['person', 'name', 'given-names','value'],
    'biography'         :['person', 'biography', 'content'],
    'keywords'          :to(['person', 'keywords'], _parse_keywords),
    'researcher_urls'   :to(['person', 'researcher-urls','researcher-url'], _parse_researcher_urls),
    'educations'        :to(['activities-summary', 'educations', 'education-summary'], _parse_educations),
    'employments'       :to(['activities-summary', 'employments', 'employment-summary'], _parse_educations)
})


Works = dictmapper('Works', {
    'publications': to(['group'], _parse_publications),
})

PublicationBase = dictmapper('PublicationBase',{
    'title'         : ['title','title', 'value'],
    'url'           : ['external-ids','external-id', 'external-id-url'],
    #'citation'      : to(['citation'], lambda l: map(CitationBase, l) if l is not None else None),
    'citation_value': ['citation', 'citation-value'],
    'citation_type' : ['citation', 'citation-type'],
    'publicationyear': [u'publication-date', u'year', u'value']
})

ExternalIDBase = dictmapper('ExternalIDBase', {
    'id'    : ['work-external-identifier-id','value'],
    'type'  : ['work-external-identifier-type']
})

CitationBase = dictmapper('CitationBase', {
    'type'  : ['citation-type'],
    'value' : ['citation-value']
})

WebsiteBase = dictmapper('WebsiteBase', {
    'name'  : ['url-name'],
    'url'   : ['url', 'value']
})

class Author(AuthorBase):
    _loaded_works = None

    def _load_works(self):
        _url = '{0}{1}/{2}'.format(ORCID_PUBLIC_BASE_URL, self.orcid, 'works')
        _res = requests.get(_url, headers = BASE_HEADERS)
        _json_body = _res.json()
        logger.debug('RESPONSE (WORKS): {0}'.format(json.dumps(_json_body, sort_keys=True, indent=4, separators=(',', ': '))))
        self._loaded_works = Works(_json_body)

    @property
    def publications(self):
        if self._loaded_works is None:
            self._load_works()
        return self._loaded_works.publications

    @property
    def affiliations(self):
        return self.educations + self.employments

    def __repr__(self):
        obj_repr = "<{} {} {}, ORCID {}>" 
        return obj_repr.format(type(self).__name__, 
                               self.given_name.encode('utf-8') if self.given_name else 'None',
                               self.family_name.encode('utf-8') if self.family_name else 'None', 
                               self.orcid)

    def __str__(self):
        return self.__repr__()


class Website(WebsiteBase):
    def __unicode__(self):
        return self.url

    def __repr__(self):
        return "<%s %s [%s]>" % (type(self).__name__, self.name, self.url)


class Citation(CitationBase):
    def __unicode__(self):
        return self.text

    def __repr__(self):
        return '<%s [type: %s]>' % (type(self).__name__, self.type)


class ExternalID(ExternalIDBase):
    def __unicode__(self):
        return unicode(self.id)

    def __repr__(self):
        return '<%s %s:%s>' % (type(self).__name__, self.type, str(self.id))


class Publication(PublicationBase):
    def __repr__(self):
        return '<%s "%s">' % (type(self).__name__, self.title)

#
# MAIN FUNCTIONS
#

def get(orcid_id):
    """ Get an author based on an ORCID identifier. """

    if sys.version_info[0] >= 3:
        unicode = str

    _url = '{0}{1}'.format(ORCID_PUBLIC_BASE_URL, unicode(orcid_id))
    _res = requests.get(_url, headers=BASE_HEADERS)

    json_body = _res.json()
    #print(logger)
    logger.debug('RESPONSE (BASE): {0}'.format(json.dumps(json_body, sort_keys=True, indent=4, separators=(',', ': '))))

    return Author(json_body)

# def get_with_json(orcid_id):
#     """
#     Get an author based on an ORCID identifier and json
#     """
#     resp = requests.get(ORCID_PUBLIC_BASE_URL + u(orcid_id),
#                         headers=BASE_HEADERS)
#     json_body = resp.json()
#     write_logs(resp)
#     return Author(json_body), json_body

def search(query, verbose = False):
    """
    https://members.orcid.org/api/tutorial/search-orcid-registry
    
    example_query = {'q':'family-name:Malavolti+AND+given-names:Marco'}
    
    """

    if verbose:
        logger.setLevel(logging.DEBUG)
        stdout_sh.setLevel(logging.DEBUG)
    _url = '{0}{1}?q={2}'.format(ORCID_PUBLIC_BASE_URL, 
                                 'search',
                                 query)
    resp = requests.get(_url, headers=BASE_HEADERS)
    logger.debug(resp.url)
    json_body = resp.json()
    logger.debug(json_body)
    return (get(res.get('orcid-identifier', {}).get('path')) for res in json_body.get('result', {}))
