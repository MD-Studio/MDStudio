
from lie_md.common.exception import LieMdException

class RunInputFile( object ):
    
    def __init__( self, orderedBlocks, version ):
    
        self._blocks = orderedBlocks
        self._version = version

    def Extend( self, rhs ):
        
        self._blocks.update( rhs.blocks )
    
    def IsPresent( self, blockName ):
        
        return blockName in self._blocks
    
    def Validate( self ):

        for block in self._blocks.values():
            block.Validate()

    @property
    def version( self ):  
        return self._version

    @property
    def blocks( self ):  
        
        return self._blocks

    def __contains__( self, query ): 

        return self.IsPresent( query )

    def __getattr__( self, key ):
    
        if "_blocks" in self.__dict__ and key in self._blocks:
            return self._blocks[key]    
            
        else :
            if not key in self.__dict__:
                raise AttributeError
                
            else:
                return self.__dict__[key]

    def __setattr__(self, key, value):
        
        if key != "_blocks" and key != "_version":
            
            raise LieMdException( "RunInputFile::__setattr__", "Set attribute not allowed on IMD files" )
        
        self.__dict__[key] = value
        
    def __getitem__(self, key):
        
        key = key.upper()
        
        if key not in self._blocks.keys():
            
            raise LieMdException( "RunInputFile::__getitem__", "Unknown key "+str( key ) )
            
        return self._blocks[key]