# -*- coding: utf-8 -*-

from __future__ import with_statement
from __future__ import absolute_import
from urllib2 import urlopen, Request
from urllib2 import HTTPError
from urllib import urlencode
import json
import pickle
from copy import deepcopy
from sys import stderr
import inspect
from sys import stderr
from requests import post
from tempfile import TemporaryFile
from itertools import imap


MISSING_VALUE = Exception(u'Missing value')
INCORRECT_VALUE = Exception(u'Incorrect value')


def stderr_write(a_str):
    stderr.write(u'API Client Debug: ' + a_str + u'\n')


def deserializer_fct_for(api_format):
    if api_format == u'json':
        def deserializer_fct(x): return json.loads(x)
    elif api_format == u'yaml':
        def deserializer_fct(x): return yaml.load(x)
    elif api_format == u'pickle':
        def deserializer_fct(x): return pickle.loads(x)
    else:
        raise Exception(u'Incorrect API serialization format.')
    return deserializer_fct


class API(object):
    HOST = u'https://atb.uq.edu.au'
    TIMEOUT = 45
    API_FORMAT = u'json'
    ENCODING = u'utf-8'

    def __init__(self, host=HOST, api_token=None, debug=False, timeout=TIMEOUT, api_format=API_FORMAT):
        # Attributes
        self.host = host
        self.api_token = api_token
        self.api_format = api_format
        self.debug = debug
        self.timeout = timeout
        self.deserializer_fct = deserializer_fct_for(api_format)

        # API namespaces
        self.Molecules = Molecules(self)
        self.RMSD = RMSD(self)

    def encoded(self, something):
        if isinstance(something, dict):
            return dict((self.encoded(key), self.encoded(value)) for (key, value) in something.items())
        elif type(something) in (unicode, int, str):
            return something.encode(self.ENCODING)
        elif something is None:
            return something
        else:
            raise Exception(
                u'''Can't uncode object of type {0}: {1}'''.format(
                    type(something),
                    something,
                )
            )

    def safe_urlopen(self, url, data={}, method=u'GET'):
        data[u'api_token'] = self.api_token
        data[u'api_format'] = self.api_format
        try:
            if method == u'GET':
                url = url + u'?' + urlencode(data)
                data = None
            elif method == u'POST':
                url = url
                data = data
            else:
                raise Exception(u'Unsupported HTTP method: {0}'.format(method))
            if self.debug:
                print >>stderr, u'Querying: {url}'.format(url=url)

            if method == u'POST' and any([isinstance(value, (str, unicode)) or u'read' in dir(value) for (key, value) in data.items()]):
                def file_for(content):
                    u'''Cast a content object to a file for request.post'''
                    if u'read' in dir(content):
                        return content
                    else:
                        file_handler = TemporaryFile(mode=u'w+b')
                        file_handler.write(
                            content if isinstance(content, (str, unicode)) else unicode(content).encode(),
                        )
                        file_handler.seek(0)  # Rewind the files to future .read()
                        return file_handler

                files = dict(
                    [
                        (key, file_for(value))
                        for (key, value) in data.items()
                    ]
                )

                request = post(
                    url,
                    files=files,
                )
                response_content = request.text

                if self.debug:
                    print u'INFO: Will send binary data.'
            else:
                response = urlopen(
                    Request(
                        url,
                        data=self.encoded(urlencode(data),) if data else None,
                    ),
                    timeout=self.timeout,
                )
                if self.api_format == 'pickle':
                    response_content = response.read()
                else:
                    response_content = response.read().decode()
        except Exception as e:
            if self.debug:
                stderr_write(u"Failed opening url: {0}{1}{2}".format(
                    url,
                    u'?' if data else u'',
                    urlencode(data) if data else u'',
                ))
            #if e and 'fp' in e.__dict__: stderr_write( "Response was:\n\n{0}".format(e.fp.read().decode()) )
            raise e
        return response_content

    def deserialize(self, an_object):
        try:
            return self.deserializer_fct(an_object)
        except BaseException:
            print an_object
            raise


class ATB_Mol(object):
    def __init__(self, api, molecule_dict):
        self.api = api
        self.molid = molecule_dict[u'molid']
        self.atoms = molecule_dict[u'atoms']
        self.has_TI = molecule_dict[u'has_TI']
        self.iupac = molecule_dict[u'iupac']
        self.common_name = molecule_dict[u'common_name']
        self.inchi_key = molecule_dict[u'inchi_key']
        self.experimental_solvation_free_energy = molecule_dict[u'experimental_solvation_free_energy']
        self.curation_trust = molecule_dict[u'curation_trust']
        self.pdb_hetId = molecule_dict[u'pdb_hetId']
        self.netcharge = molecule_dict[u'netcharge']
        self.formula = molecule_dict[u'formula']
        self.is_finished = molecule_dict[u'is_finished']
        self.rnme = molecule_dict[u'rnme']
        self.dihedral_fragments = molecule_dict[u'dihedral_fragments']
        self.maximum_qm_level = molecule_dict[u'maximum_qm_level']
        self.qm_level = molecule_dict[u'qm_level']
        self.commercial_set = molecule_dict[u'commercial_set']
        self.user_label = molecule_dict[u'user_label']
        self.moltype = molecule_dict[u'moltype']

        # Convert "None" or u"None" to Python None
        for key, value in self.__dict__.items():
            if value in ("None", u"None"):
                self.__dict__[key] = None

    def __repr__(self):
        return json.dumps(self.dict())

    def dict(self):
        self_dict = deepcopy(self.__dict__)
        del self_dict[u'api']

        return self_dict

    def download_file(self, **kwargs):
        if u'molid' in kwargs:
            del kwargs[u'molid']
        return self.api.Molecules.download_file(molid=self.molid, **kwargs)

    def generate_mol_data(self, **kwargs):
        if u'molid' in kwargs:
            del kwargs[u'molid']
        return self.api.Molecules.generate_mol_data(molid=self.molid, **kwargs)


class RMSD(API):

    def __init__(self, api):
        self.api = api

    def url(self, api_endpoint):
        return self.api.host + u'/api/current/' + self.__class__.__name__.lower() + u'/' + api_endpoint + u'.py'

    def align(self, **kwargs):
        assert u'molids' in kwargs or (u'reference_pdb' in kwargs and u'pdb_0' in kwargs), MISSING_VALUE
        if u'molids' in kwargs:
            if type(kwargs[u'molids']) in (list, tuple):
                kwargs[u'molids'] = u','.join(imap(unicode, kwargs[u'molids']))
            else:
                assert u',' in kwargs[u'molids']
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method=u'POST')
        return self.api.deserialize(response_content)

    def matrix(self, **kwargs):
        assert u'molids' in kwargs or (u'reference_pdb' in kwargs and u'pdb_0' in kwargs), MISSING_VALUE
        if u'molids' in kwargs:
            if type(kwargs[u'molids']) in (list, tuple):
                kwargs[u'molids'] = u','.join(imap(unicode, kwargs[u'molids']))
            else:
                assert u',' in kwargs[u'molids']
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method=u'POST')
        return self.api.deserialize(response_content)


class Molecules(API):

    def __init__(self, api):
        self.api = api
        self.download_urls = {
            u'pdb_aa': (u'download_file', dict(outputType=u'top', file=u'pdb_allatom_optimised', ffVersion=u"54A7"),),
            u'pdb_allatom_unoptimised': (u'download_file', dict(outputType=u'top', file=u'pdb_allatom_unoptimised', ffVersion=u"54A7"),),
            u'pdb_ua': (u'download_file', dict(outputType=u'top', file=u'pdb_uniatom_optimised', ffVersion=u"54A7"),),
            u'yml': (u'generate_mol_data', dict(),),
            u'mtb_aa': (u'download_file', dict(outputType=u'top', file=u'mtb_allatom', ffVersion=u"54A7"),),
            u'mtb_ua': (u'download_file', dict(outputType=u'top', file=u'mtb_uniatom', ffVersion=u"54A7"),),
            u'itp_aa': (u'download_file', dict(outputType=u'top', file=u'rtp_allatom', ffVersion=u"54A7"),),
            u'itp_ua': (u'download_file', dict(outputType=u'top', file=u'rtp_uniatom', ffVersion=u"54A7"),),
        }

    def url(self, api_endpoint):
        return self.api.host + u'/api/current/' + self.__class__.__name__.lower() + u'/' + api_endpoint + u'.py'

    def search(self, **kwargs):
        return_type = kwargs[u'return_type'] if u'return_type' in kwargs else u'molecules'
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method=u'GET')
        data = self.api.deserialize(response_content)
        if return_type == u'molecules':
            return [ATB_Mol(self.api, m) for m in data[return_type]]
        elif return_type == u'molids':
            return data[return_type]
        else:
            raise Exception(u'Unknow return_type: {0}'.format(return_type))

    def download_file(self, **kwargs):

        def write_to_file_or_return(response_content, deserializer_fct):
            # Either write response to file 'fnme', or return its content
            if u'fnme' in kwargs:
                fnme = unicode(kwargs[u'fnme'])
                with open(fnme, u'w' + (u'b' if isinstance(response_content, str, unicode) else u't')) as fh:
                    fh.write(response_content)
                return None
            else:
                return deserializer_fct(response_content)

        if all([key in kwargs for key in (u'atb_format', u'molid')]):
            # Construct donwload.py request based on requested file format
            atb_format = unicode(kwargs[u'atb_format'])
            call_kwargs = dict([(key, value) for (key, value) in list(kwargs.items()) if key not in (u'atb_format',)])
            api_endpoint, extra_parameters = self.download_urls[atb_format]
            url = self.url(api_endpoint)
            response_content = self.api.safe_urlopen(url, data=dict(list(call_kwargs.items()) + list(extra_parameters.items())), method=u'GET')
            deserializer_fct = (self.api.deserializer_fct if atb_format == u'yml' else (lambda x: x))
        else:
            # Forward all the keyword arguments to download_file.py
            response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method=u'GET')

            def deserializer_fct(x): return x
        return write_to_file_or_return(response_content, deserializer_fct)

    def duplicated_inchis(self, **kwargs):
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method=u'GET')
        return self.api.deserialize(response_content)[u'inchi_key']

    def generate_mol_data(self, **kwargs):
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method=u'GET')
        return self.api.deserialize(response_content)

    def molid(self, molid=None):
        parameters = dict(molid=molid)
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=parameters, method=u'GET')
        data = self.api.deserialize(response_content)
        return ATB_Mol(self.api, data[u'molecule'])

    def structure_search(self, method=u'POST', **kwargs):
        assert all([arg in kwargs for arg in (u'structure', u'netcharge', u'structure_format')])
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method=u"GET")
        return self.api.deserialize(response_content)

    def submit(self, request=u'POST', **kwargs):
        assert all([arg in kwargs for arg in (u'netcharge', u'pdb', u'public', u'moltype')])
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs)
        return self.api.deserialize(response_content)
