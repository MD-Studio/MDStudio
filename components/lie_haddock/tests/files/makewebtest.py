# -*- coding: utf-8 -*-

import os
import logging
import pkg_resources

from lie_graph.graph_io.io_web_format import read_web, write_web
from lie_graph.graph_axis.graph_axis_mixin import NodeAxisTools

from lie_haddock.haddock_model import (remove_haddock_data_block, load_project, save_project, edit_parameter_block,
                                       new_parameter_block, new_project)
from lie_haddock.haddock_model_classes import haddock_orm
from lie_haddock.haddock_helper_methods import validate_model

logging.basicConfig(level=logging.INFO)
currpath = os.path.dirname(__file__)
schemadir = pkg_resources.resource_filename('lie_haddock', '/schemas/endpoints')

# project = read_web('test_project.web')
# project.orm = haddock_orm
# project.node_tools = NodeAxisTools

project = new_project('mdstudio')

# Add first partner
partner1 = {'pdb': {'mode': 'submit', 'chain': 'A', 'code': None, 'pdbdata': open('1ckaA.pdb').read()},
            'r': {'auto_passive': True,
                  'activereslist': [141, 142, 143, 144, 145, 146, 166, 167, 168, 169, 184, 185, 186]}}
block_id, params = new_parameter_block(project, 'haddock-partner-request.v1',
                                       'HaddockPartnerParameters', max_mult=5)
edit_parameter_block(project, block_id, partner1)

# Add second partner
partner2 = {'pdb': {'mode': 'submit', 'chain': 'B', 'code': None, 'pdbdata': open('1ckaB.pdb').read()},
            'r': {'activereslist': [1,2,3,4,5,6,7,8,9]}}
block_id, params = new_parameter_block(project, 'haddock-partner-request.v1',
                                       'HaddockPartnerParameters', max_mult=5)
edit_parameter_block(project, block_id, partner2)

# Add fully-flexible segments to first partner
block_id, params = new_parameter_block(project, 'haddock-flexrange-request.v1', 'Range',
                                       attach='{0}.fullyflex.segments'.format(block_id))
edit_parameter_block(project, block_id, {'start': 1, 'end': 9})

# Set username
edit_parameter_block(project, 'project', {'username': 'marcvdijk'})

# Run final validation
project.getnodes(project.root).validate()
print(write_web(project))
