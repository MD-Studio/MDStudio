# -*- coding: utf-8 -*-

from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import urlencode
import json
import pickle
from copy import deepcopy
from sys import stderr
import inspect
from sys import stderr
from requests import post
from tempfile import TemporaryFile
from typing import Any, List, Dict, Callable, Optional, Union, Tuple

MISSING_VALUE = Exception('Missing value')
INCORRECT_VALUE = Exception('Incorrect value')

ATB_MOLID = Union[str, int]

ATB_OUTPUT = str

API_RESPONSE = Dict[Any, Any]


def stderr_write(a_str) -> None:
    stderr.write('API Client Debug: ' + a_str + '\n')


def deserializer_fct_for(api_format: str) -> Callable[[str], API_RESPONSE]:
    if api_format == 'json':
        def deserializer_fct(x): return json.loads(x)
    elif api_format == 'yaml':
        def deserializer_fct(x): return yaml.load(x)
    elif api_format == 'pickle':
        def deserializer_fct(x): return pickle.loads(x)
    else:
        raise Exception('Incorrect API serialization format.')
    return deserializer_fct


class API(object):
    HOST = 'https://atb.uq.edu.au'
    TIMEOUT = 45
    API_FORMAT = 'json'
    ENCODING = 'utf-8'

    def __init__(self, host: str = HOST, api_token: Optional[str] = None, debug: bool = False, timeout: int = TIMEOUT, api_format: str = API_FORMAT) -> None:
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

    def encoded(self, something: Any) -> Union[Dict[bytes, Any], bytes, None]:
        if type(something) == dict:
            return {self.encoded(key): self.encoded(value) for (key, value) in something.items()}
        elif type(something) in (str, int):
            return something.encode(self.ENCODING)
        elif something is None:
            return something
        else:
            raise Exception(
                '''Can't uncode object of type {0}: {1}'''.format(
                    type(something),
                    something,
                )
            )

    def safe_urlopen(self, url: str, data: Dict[str, Any] = {}, method: str = 'GET') -> str:
        data['api_token'] = self.api_token
        data['api_format'] = self.api_format
        try:
            if method == 'GET':
                url = url + '?' + urlencode(data)
                data = None
            elif method == 'POST':
                url = url
                data = data
            else:
                raise Exception('Unsupported HTTP method: {0}'.format(method))
            if self.debug:
                print('Querying: {url}'.format(url=url), file=stderr)

            if method == 'POST' and any([isinstance(value, bytes) or 'read' in dir(value) for (key, value) in data.items()]):
                def file_for(content):
                    '''Cast a content object to a file for request.post'''
                    if 'read' in dir(content):
                        return content
                    else:
                        file_handler = TemporaryFile(mode='w+b')
                        file_handler.write(
                            content if isinstance(content, bytes) else str(content).encode(),
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
                    print('INFO: Will send binary data.')
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
            self.debug:
                stderr_write("Failed opening url: {0}{1}{2}".format(
                    url,
                    '?' if data else '',
                    urlencode(data) if data else '',
                ))
            #if e and 'fp' in e.__dict__: stderr_write( "Response was:\n\n{0}".format(e.fp.read().decode()) )
            raise e
        return response_content

    def deserialize(self, an_object: Any) -> Any:
        try:
            return self.deserializer_fct(an_object)
        except BaseException:
            print(an_object)
            raise


class ATB_Mol(object):
    def __init__(self, api, molecule_dict: Dict[str, Any]) -> None:
        self.api = api
        self.molid = molecule_dict['molid']
        self.atoms = molecule_dict['atoms']
        self.has_TI = molecule_dict['has_TI']
        self.iupac = molecule_dict['iupac']
        self.common_name = molecule_dict['common_name']
        self.inchi_key = molecule_dict['inchi_key']
        self.experimental_solvation_free_energy = molecule_dict['experimental_solvation_free_energy']
        self.curation_trust = molecule_dict['curation_trust']
        self.pdb_hetId = molecule_dict['pdb_hetId']
        self.netcharge = molecule_dict['netcharge']
        self.formula = molecule_dict['formula']
        self.is_finished = molecule_dict['is_finished']
        self.rnme = molecule_dict['rnme']
        self.dihedral_fragments = molecule_dict['dihedral_fragments']
        self.maximum_qm_level = molecule_dict['maximum_qm_level']
        self.qm_level = molecule_dict['qm_level']
        self.commercial_set = molecule_dict['commercial_set']
        self.user_label = molecule_dict['user_label']
        self.moltype = molecule_dict['moltype']

        # Convert "None" or u"None" to Python None
        for key, value in self.__dict__.items():
            if value in ("None", u"None"):
                self.__dict__[key] = None

    def __repr__(self) -> str:
        self_dict = deepcopy(self.__dict__)
        del self_dict['api']
        return yaml.dump(self_dict)

    def download_file(self, **kwargs) -> Union[None, ATB_OUTPUT]:
        if 'molid' in kwargs:
            del kwargs['molid']
        return self.api.Molecules.download_file(molid=self.molid, **kwargs)

    def generate_mol_data(self, **kwargs) -> bool:
        if 'molid' in kwargs:
            del kwargs['molid']
        return self.api.Molecules.generate_mol_data(molid=self.molid, **kwargs)


class RMSD(API):

    def __init__(self, api: API) -> None:
        self.api = api

    def url(self, api_endpoint: str) -> str:
        return self.api.host + '/api/current/' + self.__class__.__name__.lower() + '/' + api_endpoint + '.py'

    def align(self, **kwargs) -> API_RESPONSE:
        assert 'molids' in kwargs or ('reference_pdb' in kwargs and 'pdb_0' in kwargs), MISSING_VALUE
        if 'molids' in kwargs:
            if type(kwargs['molids']) in (list, tuple):
                kwargs['molids'] = ','.join(map(str, kwargs['molids']))
            else:
                assert ',' in kwargs['molids']
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='POST')
        return self.api.deserialize(response_content)

    def matrix(self, **kwargs) -> API_RESPONSE:
        assert 'molids' in kwargs or ('reference_pdb' in kwargs and 'pdb_0' in kwargs), MISSING_VALUE
        if 'molids' in kwargs:
            if type(kwargs['molids']) in (list, tuple):
                kwargs['molids'] = ','.join(map(str, kwargs['molids']))
            else:
                assert ',' in kwargs['molids']
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='POST')
        return self.api.deserialize(response_content)


class Molecules(API):

    def __init__(self, api: API) -> None:
        self.api = api
        self.download_urls = {
            'pdb_aa': ('download_file', dict(outputType='top', file='pdb_allatom_optimised', ffVersion="54A7"),),
            'pdb_allatom_unoptimised': ('download_file', dict(outputType='top', file='pdb_allatom_unoptimised', ffVersion="54A7"),),
            'pdb_ua': ('download_file', dict(outputType='top', file='pdb_uniatom_optimised', ffVersion="54A7"),),
            'yml': ('generate_mol_data', dict(),),
            'mtb_aa': ('download_file', dict(outputType='top', file='mtb_allatom', ffVersion="54A7"),),
            'mtb_ua': ('download_file', dict(outputType='top', file='mtb_uniatom', ffVersion="54A7"),),
            'itp_aa': ('download_file', dict(outputType='top', file='rtp_allatom', ffVersion="54A7"),),
            'itp_ua': ('download_file', dict(outputType='top', file='rtp_uniatom', ffVersion="54A7"),),
        }

    def url(self, api_endpoint: str) -> str:
        return self.api.host + '/api/current/' + self.__class__.__name__.lower() + '/' + api_endpoint + '.py'

    def search(self, **kwargs) -> Any:
        return_type = kwargs['return_type'] if 'return_type' in kwargs else 'molecules'
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='GET')
        data = self.api.deserialize(response_content)
        if return_type == 'molecules':
            return [ATB_Mol(self.api, m) for m in data[return_type]]
        elif return_type == 'molids':
            return data[return_type]
        else:
            raise Exception('Unknow return_type: {0}'.format(return_type))

    def download_file(self, **kwargs: Dict[str, Any]) -> Union[None, ATB_OUTPUT]:

        def write_to_file_or_return(response_content, deserializer_fct) -> Union[None, ATB_OUTPUT]:
            # Either write response to file 'fnme', or return its content
            if 'fnme' in kwargs:
                fnme = str(kwargs['fnme'])
                with open(fnme, 'w' + ('b' if isinstance(response_content, bytes) else 't')) as fh:
                    fh.write(response_content)
                return None
            else:
                return deserializer_fct(response_content)

        if all([key in kwargs for key in ('atb_format', 'molid')]):
            # Construct donwload.py request based on requested file format
            atb_format = str(kwargs['atb_format'])
            call_kwargs = dict([(key, value) for (key, value) in list(kwargs.items()) if key not in ('atb_format',)])
            api_endpoint, extra_parameters = self.download_urls[atb_format]
            url = self.url(api_endpoint)
            response_content = self.api.safe_urlopen(url, data=dict(list(call_kwargs.items()) + list(extra_parameters.items())), method='GET')
            deserializer_fct = (self.api.deserializer_fct if atb_format == 'yml' else (lambda x: x))
        else:
            # Forward all the keyword arguments to download_file.py
            response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='GET')

            def deserializer_fct(x): return x
        return write_to_file_or_return(response_content, deserializer_fct)

    def duplicated_inchis(self, **kwargs) -> API_RESPONSE:
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='GET')
        return self.api.deserialize(response_content)['inchi_key']

    def generate_mol_data(self, **kwargs) -> API_RESPONSE:
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='GET')
        return self.api.deserialize(response_content)

    def molid(self, molid: ATB_MOLID = None) -> ATB_Mol:
        parameters = dict(molid=molid)
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=parameters, method='GET')
        data = self.api.deserialize(response_content)
        return ATB_Mol(self.api, data['molecule'])

    def structure_search(self, method: str = 'POST', **kwargs) -> API_RESPONSE:
        assert all([arg in kwargs for arg in ('structure', 'netcharge', 'structure_format')])
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method="GET")
        return self.api.deserialize(response_content)

    def submit(self, request: str = 'POST', **kwargs) -> API_RESPONSE:
        assert all([arg in kwargs for arg in ('netcharge', 'pdb', 'public', 'moltype')])
        response_content = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs)
        return self.api.deserialize(response_content)
