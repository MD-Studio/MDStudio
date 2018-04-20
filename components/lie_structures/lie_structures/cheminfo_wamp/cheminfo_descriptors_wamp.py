# -*- coding: utf-8 -*-

from lie_structures.cheminfo_molhandle import mol_read


class CheminfoDescriptorsWampApi(object):
    """
    Cheminformatics descriptors WAMP API
    """
    def get_descriptors(self, request, claims):

        # Import the molecule
        molobject = mol_read(
            request["structure"], mol_format=request["mol_format"],
            toolkit=request["toolkit"])
        desc = molobject.calcdesc()

        if desc is not None:
            status = 'completed'
            output = desc
        else:
            status = 'failed'
            output = None

        return {'session': status, 'descriptors': output}
