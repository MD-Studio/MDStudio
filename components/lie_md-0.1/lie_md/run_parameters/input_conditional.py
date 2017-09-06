

class MDStudioConditional(object):
    
    def __init__( self, definition ):
        
        if not "type" in definition:
            
            raise LieMdException( "MDStudioConditional::__init__", "Conditional requires a type section" )
        
        if not "value" in definition:
            
            raise LieMdException( "MDStudioConditional::__init__", "Conditional requires a value section" )
        
        self.type = definition["type"]
        self.value = definition["value"]

        self.actionList = dict()
        self.actionList[">="] = self._GreaterEqual
        self.actionList[">"]  = self._Greater
        self.actionList["<="] = self._LessEqual
        self.actionList["<"]  = self._Less
        self.actionList["=="] = self._Equal
        self.actionList["!="] = self._NotEqual
        self.actionList["str_list"] = self._StrList

        if self.type == "str_list":
            if not isinstance( self.value, list ):
                raise LieMdException( "MDStudioConditional::__init__", "Conditional value should be a list" )
        else:
            if isinstance( self.value, list ):
                raise LieMdException( "MDStudioConditional::__init__", "Conditional value should be a scalar" )

        if not self.type in self.actionList:
            raise LieMdException( "MDStudioConditional::__init__", "Conditional has an unknown type %s" % ( self.type ) )
        
    def _Greater( self, query ):
        
        return query > self.value
    
    def _GreaterEqual( self, query ):
        
        return query >= self.value
        
    def _Less( self, query ):
        
        return query < self.value
    
    def _LessEqual( self, query ):
        
        return query <= self.value
    
    def _Equal( self, query ):
        
        return query == self.value
    
    def _NotEqual( self, query ):
        
        return query != self.value
    
    def _StrList( self, query ):

        return query in self.value

    def Evaluate(self, query ):
        
        return self.actionList[self.type]( query )
