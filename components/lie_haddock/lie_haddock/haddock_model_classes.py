# -*- coding: utf-8 -*-

import logging
import string

from lie_graph.graph_axis.graph_axis_mixin import NodeAxisTools
from lie_graph.graph_orm import GraphORM

from haddock_io.haddock_io_pdb import PDBParser
from haddock_io.haddock_io_tbl import validate_tbl
from haddock_helper_methods import haddock_validation_warning
from haddock_model_data import (haddock_dna_residues, haddock_rna_residues, haddock_protein_residues,
                                haddock_ion_residues)


class FloatArray(NodeAxisTools):

    def set(self, key, value=None):
        """
        Set list of float values
        :param key:
        :param value:
        :return:
        """

        if key == self.node_value_tag:
            assert isinstance(value, list)

            float_array = []
            for v in value:
                float_array.append(float(v))

            self.nodes[self.nid][key] = float_array
            return

        self.nodes[self.nid][key] = value

    def validate(self, key=None):

        key = key or self.node_value_tag

        return all([isinstance(n, float) for n in self.nodes[self.nid][key]])


class HaddockRunParameters(NodeAxisTools):

    def validate(self, key=None):

        is_valid = True

        # Validate number of solutions in it0, it1, w
        if self.structures_0.value < self.structures_1.value:
            message = 'Number of it0 structures "{0}" is less then it1 "{1}"'.format(self.structures_0.value,
                                                                                     self.structures_1.value)
            is_valid = haddock_validation_warning(self, message)
        if self.structures_1.value < self.waterrefine.value:
            message = 'Number of structures in it1 "{0}" cannot me smaller then water refine "{1}"'.format(
                self.structures_1.value, self.waterrefine.value)
            is_valid = haddock_validation_warning(self, message)

        # Number of it1 structures to analyze not larger then generated
        if self.structures_1.value < self.anastruc_1.value:
            self.anastruc_1.set(self.node_value_tag, self.structures_1.value)
            haddock_validation_warning(self, 'Set anastruc_1 equal to structures_1')

        # If random exclusion then partition should be larger or equal to 2
        if self.noecv.value == False and self.ncvpart.value < 2:
            is_valid = haddock_validation_warning(self,
                                                  'Number of partitions for random exclusion should be larger then 2')

        if 'tbldata' in self.keys() and self.tbldata.value is None:
            if self.noecv.value - int(self.noecv.value):
                is_valid = haddock_validation_warning(self,
                'The number of crossvalidation partitions may be fractional, but not if a restraints table is supplied')

        return is_valid


class Range(NodeAxisTools):

    def validate(self, key=None):
        """
        Validate a range to be a list/tuple of two integer values with
        first one smaller then second.
        """

        is_valid = True
        range = dict(self.children().items())
        if len(range):
            if len(range) != 2:
                is_valid = haddock_validation_warning(self, 'Range should have two items got: {0}'.format(range))
            if not all([isinstance(i, int) for i in range.values()]):
                message = 'All values should be of type integer got: {0}'.format(range.values())
                is_valid = haddock_validation_warning(self, message)
            if range['start'] > range['end']:
                message = 'Start "{start}" should be smaller then end "{end}"'.format(**range)
                is_valid = haddock_validation_warning(self, message)

        return is_valid


class ExtStageConstants(NodeAxisTools):
    """
    Methods for the validation of generic extended stage constant definitions
    """

    def validate(self, key=None):
        """
        On top of general JSON schema validation the last iteration stage
        should be larger that the first iteration stage.

        :return:    validation success
        :rtype:     :py:bool
        """

        data = dict(self.children().items())

        if data['lastit'] < data['firstit']:
            return haddock_validation_warning(self, 'lastit {0} is smaller then firstit {1}'.format(data['lastit'],
                                                                                                    data['firstit']))

        return True


class CNSRestraintFiles(NodeAxisTools):
    """
    Methods for validating Haddock CNS style restraint files
    """

    def validate(self, key=None):
        """
        Validate the Haddock CSN style restraints file using the validate_tbl
        function.

        :param key: tbl file name
        :type key:  :py:str

        :return:    validation success
        :rtype:     :py:bool
        """

        tbldata = self.get(self.node_value_tag)
        key = key or self.node_key_tag
        if tbldata is not None:

            is_pcs = self.get(key) in ('tensordata', 'pcsdata')
            try:
                validate_tbl(tbldata, pcs=is_pcs)
            except Exception, e:
                return haddock_validation_warning(self, '{0} .tbl restraints: {1}'.format(self.get(key), e))

        return True


class HaddockPartnerParameters(NodeAxisTools):

    def validate(self, key=None):
        """
        Validation for the full Haddock partner parameter block.
        """

        desc = self.descendants()
        pdbdata = desc.query_nodes(key='pdbdata')
        is_valid = True

        # PDB data could not be set yet
        if not pdbdata.empty():

            # Parse the PDB file
            pdbparser = PDBParser()
            pdbdf = pdbparser.parse_to_pandas(pdbdata.value)

            # Check if chain ID in pdb
            chain = desc.query_nodes(key='chain').value
            if chain != 'All':
                if chain not in pdbdf['chain'].unique():
                    is_valid = haddock_validation_warning(self, 'Chain ID {0} not in structure'.format(chain))

            # Clear passive residue list if auto_passive is active
            if self.r.auto_passive.value:
                self.r.passivereslist.value = []
                haddock_validation_warning(self, 'Automatic definition of passive residues enabled. Clear passive list')

            # Check if active/passive residues are in the structure
            resnum = set(pdbdf['resnum'].unique())
            if chain != 'All':
                resnum = set(pdbdf.loc[pdbdf['chain'] == chain, 'resnum'].unique())

            missing_active = set(self.r.activereslist.value).difference(resnum)
            if missing_active:
                message = 'Active residues not in structure: {0}'.format(str(sorted(missing_active)).strip('[]'))
                is_valid = haddock_validation_warning(self, message)

            missing_passive = set(self.r.passivereslist.value).difference(resnum)
            if missing_passive:
                message = 'Passive residues not in structure: {0}'.format(str(sorted(missing_passive)).strip('[]'))
                is_valid = haddock_validation_warning(self, message)

            # Check the segid used during docking, automatically set of not defined
            segid = self.segid.get()
            allsegids = [node.get() for node in self._full_graph.query_nodes(key='segid') if node.nid != self.segid.nid]
            if segid is None:
                for s in string.ascii_uppercase:
                    if not s in allsegids:
                        self.segid.set('value', s)
                        break
                haddock_validation_warning(self, 'A segid should be defined for every partner. Set to: {0}'.format(s))

            if segid and segid in allsegids:
                message = 'Segid "{0}" defined for other partner, please change'.format(segid)
                is_valid = haddock_validation_warning(self, message)

            # Check if the molecule type matches the structure a bit
            resnames = set(pdbdf['resname'].unique())
            moltype = desc.query_nodes(key='moleculetype').value
            if chain != 'All':
                resnames = set(pdbdf.loc[pdbdf['chain'] == chain, 'resname'].unique())

            if moltype == 'Protein':
                reference_set = set(haddock_protein_residues + haddock_ion_residues)
            elif moltype == 'DNA':
                reference_set = set(haddock_dna_residues + haddock_ion_residues)
            elif moltype == 'RNA':
                reference_set = set(haddock_rna_residues + haddock_ion_residues)
            elif moltype == "Protein-DNA":
                reference_set = set(haddock_protein_residues + haddock_dna_residues + haddock_ion_residues)
            elif moltype == "Protein-RNA":
                reference_set = set(haddock_protein_residues + haddock_rna_residues + haddock_ion_residues)
            else:
                reference_set = set([])

            nonmatched_residues = resnames.difference(reference_set)
            if nonmatched_residues:
                message = ('Molecule type {0} does not support residues: {1}'.format(moltype,
                                                                            str(list(nonmatched_residues)).strip('[]')))
                is_valid = haddock_validation_warning(self, message)

        else:
            is_valid = haddock_validation_warning(self, 'No molecular structure data set yet')

        return is_valid


class RestraintsInterface(NodeAxisTools):

    def validate(self, key=None):

        is_valid = True

        if self.auto_passive.value and len(self.passivereslist.value):
            message = 'You manually defined passive residues, but also that they should be determined automatically'
            is_valid = haddock_validation_warning(self, message)

        return is_valid


class FlexSegmentList(NodeAxisTools):

    def validate(self, key=None):
        """
        Validate (semi)-flexible segment lists. Check if all residues in the
        ranges are present in the molecule. A range itself is validated by the
        Range class
        """

        is_valid = True

        # Get parent molecule and chain
        parent = self.parent()
        pdbdata = parent.descendants().query_nodes(key='pdbdata')
        chain = parent.pdb.chain.get()

        resnum = []
        if not pdbdata.empty():

            # Parse the PDB file
            pdbparser = PDBParser()
            pdbdf = pdbparser.parse_to_pandas(pdbdata.value)

            # Get residues
            if chain != 'All':
                resnum = set(pdbdf.loc[pdbdf['chain'] == chain, 'resnum'].unique())
            else:
                resnum = set(pdbdf['resnum'].unique())

        # Get the ranges
        flexrange = self.segments.descendants().leaves().values()
        missing_flexrange = set(flexrange).difference(resnum)
        if missing_flexrange:
            message = 'Following (semi)-flexible not in structure: {0}'.format(
                str(sorted(missing_flexrange)).strip('[]'))
            is_valid = haddock_validation_warning(self, message)

        # If semiflex and residues defined, set mode to 'manual'
        if self.key == 'semiflex':
            if self.mode.get() == 'manual' and not len(flexrange):
                is_valid = haddock_validation_warning(self, 'Manual semi-flexible segments but no segments defined')
            elif len(flexrange):
                self.mode.set(self.node_value_tag, 'automatic')

        return is_valid


class PDBData(NodeAxisTools):

    def validate(self, key=None):
        """
        Validate molecular partner structure data. If mode equals 'submit' then
        a structure data is expected. If mode equals 'download' then a RCSB PDB
        id is expected.

        TODO: basic validation of the PDB structure file?
        """

        is_valid = True
        data = dict(self.children().items())
        pdbdata = data.get('pdbdata')

        if not (data['mode'] != 'submit' or (pdbdata is not None and data['code'] is None)):
            is_valid = haddock_validation_warning(self, 'Provide a PDB structure or a PDB code')

        if not (data['mode'] != "download" or (pdbdata is None and data['code'] is not None)):
            is_valid = haddock_validation_warning(self, 'Provide a PDB code or define PDB file using mode "submit"')

        code = data.get('code')
        if code is not None and data['mode'] == 'submit':
            if len(code) != 4 or not code[0].isdigit() or not code[1:].isalnum():
                is_valid = haddock_validation_warning(self, 'Invalid PDB code {0}'.format(code))

        return is_valid


class LabeledRangePairArray(NodeAxisTools):

    def validate(self, key=None):

        if len(self.r.children()) != 2:
            return haddock_validation_warning(self, 'Symmetry restraint should be of length 2')


class LabeledRangeTripleArray(NodeAxisTools):

    def validate(self, key=None):
        if len(self.r.children()) != 3:
            return haddock_validation_warning(self, 'Symmetry restraint should be of length 3')


class LabeledRangeQuadrupleArray(NodeAxisTools):

    def validate(self, key=None):
        if len(self.r.children()) != 4:
            return haddock_validation_warning(self, 'Symmetry restraint should be of length 4')


class LabeledRangeQuintupleArray(NodeAxisTools):

    def validate(self, key=None):
        if len(self.r.children()) != 5:
            return haddock_validation_warning(self, 'Symmetry restraint should be of length 5')


# Predefined HADDOCK ORM mapper
haddock_orm = GraphORM()
haddock_orm.map_node(HaddockRunParameters, haddock_type='HaddockRunParameters')
haddock_orm.map_node(FloatArray, haddock_type='FloatArray')
haddock_orm.map_node(Range, haddock_type='Range')
haddock_orm.map_node(ExtStageConstants, haddock_type='ExtStageConstants')
haddock_orm.map_node(HaddockPartnerParameters, haddock_type='HaddockPartnerParameters')
haddock_orm.map_node(CNSRestraintFiles, haddock_type='CNSRestraintFile')
haddock_orm.map_node(FlexSegmentList, haddock_type='SemiflexSegmentList')
haddock_orm.map_node(FlexSegmentList, haddock_type='SegmentList')
haddock_orm.map_node(PDBData, haddock_type='PDBData')
haddock_orm.map_node(LabeledRangePairArray, haddock_type='LabeledRangePairArray')
haddock_orm.map_node(LabeledRangeTripleArray, haddock_type='LabeledRangeTripleArray')
haddock_orm.map_node(LabeledRangeQuadrupleArray, haddock_type='LabeledRangeQuadrupleArray')
haddock_orm.map_node(LabeledRangeQuintupleArray, haddock_type='LabeledRangeQuintupleArray')

for tbldata in ('tbldata', 'dihedraldata', 'rdcdata', 'danidata', 'tensordata', 'pcsdata'):
    haddock_orm.map_node(CNSRestraintFiles, key=tbldata)