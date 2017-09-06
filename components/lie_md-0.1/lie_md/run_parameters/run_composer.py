#
# @cond ___LICENSE___
#
# Copyright (c) 2017 K.M. Visscher and individual contributors.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# @endcond
#

import yaml

from copy import deepcopy
from collections import OrderedDict

from lie_md.common.exception import LieMdException
from lie_md.run_parameters.input_block import MDStudioBlock
from lie_md.run_parameters.run_input_file import RunInputFile

class RunInput(object):
    
    def __init__( self, ifstream ):
        
       tree = yaml.load(ifstream)

       if not "Version" in tree:     
            raise LieMdException( "RunInput::_ParseDefinitions", "Version not within the input file stream" )

       self._version = tree["Version"]
       self._blockDefinitions = self._ParseDefinitions( tree )
       
    def _ParseDefinitions( self, tree ):
        
        blocks = OrderedDict()

        if not "BlockDefinitions" in tree:
            
            raise LieMdException( "RunInput::_ParseDefinitions", "BlockDefinitions not within the input file stream" )
            
        for blockdef in tree["BlockDefinitions"]:
            
            imdblock = MDStudioBlock( blockdef )
            
            if imdblock.GetKey() in blocks:
                
                raise LieMdException( "RunInput::_ParseDefinitions", "BlockDefinitions contains a duplicate %s" % ( imdblock.GetKey() ) )
            
            blocks[imdblock.GetKey()] = imdblock
            
        return blocks
        
    def Compose( self, components ):
        
        result=OrderedDict()
        
        for component in components:
            
            #find all the blocks required by components
            if not  component in self._blockDefinitions.keys():
                
                raise LieMdException( "RunInput::Compose", "No block definition found for " + component )
            
            result[component] = deepcopy( self._blockDefinitions[ component ] )

        return RunInputFile( result, self._version )
