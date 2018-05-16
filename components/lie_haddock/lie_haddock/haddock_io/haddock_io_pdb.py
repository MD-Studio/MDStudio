# -*- coding: utf-8 -*-

"""
file: haddock_io_pdb.py

Haddock specific import and export of RCSB PDB files
Uses a Pandas DataFrame as intermediate format to facilitate advanced
data query.
"""

import re

from pandas import DataFrame

DEFAULT_CONTACT_COLUMN_NAMES = ['atnum', 'atname', 'atalt', 'resname', 'chain', 'model', 'label',
                                'resnum', 'resext', 'xcoor', 'ycoor', 'zcoor', 'occ', 'b', 'segid', 'elem']


class PDBParser(object):

    def __init__(self, columns=DEFAULT_CONTACT_COLUMN_NAMES):

        self.pdb_dict = dict([(n, []) for n in columns])

    def parse(self, pdb_file):

        atomline = re.compile('(ATOM)')
        hetatmline = re.compile('HETATM')
        modelline = re.compile('MODEL')

        modelcount = 0
        for line in pdb_file.splitlines():
            line = line[:-1]

            if modelline.match(line):
                modelcount += 1
                continue

            if atomline.match(line):
                atomdict = self.__processatom(line, valuedict={'label': 'atom', 'model': modelcount})
                for key, value in atomdict.items():
                    self.pdb_dict[key].append(value)
                continue

            if hetatmline.match(line):
                atomdict = self.__processatom(line, valuedict={'label': 'hetatm', 'model': modelcount})
                for key, value in atomdict.items():
                    self.pdb_dict[key].append(value)

        return self.pdb_dict

    def parse_to_pandas(self, pdb_file):

        return DataFrame(self.parse(pdb_file))

    def __processatom(self, line, valuedict=None):
        """
        Processes the atom line according to RCSB recomendations
        """

        if not valuedict:
            valuedict = {}

        valuedict['atnum'] = self.__processatomline(line, 12, minlen=6, vtype='int')
        valuedict['atname'] = self.__processatomline(line, 16, minlen=12)
        valuedict['atalt'] = self.__processatomline(line, 17, minlen=16)
        valuedict['resname'] = self.__processatomline(line, 21, minlen=17)
        valuedict['chain'] = self.__processatomline(line, 21)
        valuedict['resnum'] = self.__processatomline(line, 26, minlen=22, vtype='int')
        valuedict['resext'] = self.__processatomline(line, 27)
        valuedict['xcoor'] = self.__processatomline(line, 38, minlen=30, vtype='float')
        valuedict['ycoor'] = self.__processatomline(line, 46, minlen=38, vtype='float')
        valuedict['zcoor'] = self.__processatomline(line, 54, minlen=46, vtype='float')
        valuedict['occ'] = self.__processatomline(line, 60, minlen=54, vtype='float')
        valuedict['b'] = self.__processatomline(line, 66, minlen=60, vtype='float')
        valuedict['segid'] = self.__processatomline(line, 75, minlen=72)
        valuedict['elem'] = self.__processatomline(line, 78, minlen=76)

        return valuedict

    @staticmethod
    def __processatomline(line, maxlen, minlen=None, vtype='string'):
        """
        Test if a ATOM related parameter is found at its correct location
        within the ATOM line (within the 'maxlen', 'minlen' character location
        identifiers). If it is found it is converted to the appropriate type
        using the 'vtype' argument. If the type is a string the letters are
        converted to upper case.
        """
        if minlen is None:
            if len(line) < maxlen or len(line[maxlen].strip()) == 0:
                return None
            else:
                if vtype == 'int':
                    return int(line[maxlen])
                elif vtype == 'float':
                    return float(line[maxlen])
                else:
                    return line[maxlen].upper()
        else:
            if len(line) < maxlen or len(line[minlen:maxlen].strip()) == 0:
                return None
            else:
                if vtype == 'int':
                    return int(line[minlen:maxlen])
                elif vtype == 'float':
                    return float(line[minlen:maxlen])
                else:
                    return (line[minlen:maxlen].strip()).upper()
