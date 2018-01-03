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
