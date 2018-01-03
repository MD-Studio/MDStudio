

class MDStudioActivator(object):
    
    def __init__( self, definition ):
        
        if not "key" in definition:
            
            raise LieMdException( "MDStudioActivator::__init__", "Activator requires a key section" )
        
        if not "value" in definition:
            
            raise LieMdException( "MDStudioActivator::__init__", "Activator requires a value section" )
        
        self.key = definition["key"]
        self.value = definition["value"]