
from lie_md.common.exception import LieMdException

from lie_md.run_parameters.input_activator import MDStudioActivator
from lie_md.run_parameters.input_conditional import MDStudioConditional

class MDStudioProperty(object):
    
    def __init__( self, definition ):
        
        if not "key" in definition:
            
            raise LieMdException( "MDStudioProperty::__init__", "Property requires a key section" )
            
        if not "format" in definition:
            
            raise LieMdException( "MDStudioProperty::__init__", "Property %s requires a format section" % (definition["key"]) )

        self.key = definition["key"]
        self.vformat = definition["format"]
        self.value = None
        self.conditions = []
        self.activator = None
        self.repeatGroup = None
        self.translate = None
        
        #If there is a translate section
        if "dict" in definition:
            
            self.translate = definition["dict"]

        if "conditions" in definition:
            
            self.conditions = self._ParseConditions(definition["conditions"])
        
        if "activator" in definition:
            
            self.activator = self._ParseActivator(definition["activator"])
        
        if "repeatGroup" in definition:
            
            self.repeatGroup = definition["repeatGroup"]


    def _ParseConditions(self,definition):
        
        conditionals = []
        
        for item in definition:
            
            imdConditional = MDStudioConditional(item)
            conditionals.append( imdConditional )
         
        return conditionals   
         
    def _ParseActivator(self,definition):    
        
        if definition == "None":
            
            return None
            
        return MDStudioActivator( definition )
    
    def _CheckType( self, nval ):
        
        if self.vformat == "int":
            
            if not isinstance( nval, int ):

                raise LieMdException( "MDStudioProperty::CheckType", "Value for property %s should be of type %s, current value {%s}" % ( self.key, self.vformat, str(nval) ) )
            
        elif self.vformat == "float":
            
            # still allow int types here, the reverse def not!
            if not isinstance( nval, (float,int) ):
                
                raise LieMdException( "MDStudioProperty::CheckType", "Value for property %s should be of type %s, current value {%s}" % ( self.key, self.vformat, str(nval) ) )
        
        elif self.vformat == "int_list":
            
            if not isinstance( self.value, list ):
                raise LieMdException( "MDStudioConditional::__init__", "Value for property %s should be of type %s should be a list" % ( self.key, self.vformat ) )

            for lval in nval:
                if not isinstance( lval, int ):
                    raise LieMdException( "MDStudioProperty::CheckType", "Value for property %s should be of type %s, current value {%s}" % ( self.key, self.vformat, str(nval) ) )
                   

        elif self.vformat == "str":     
            
            if not isinstance( nval, str ):
                
                raise LieMdException( "MDStudioProperty::CheckType", "Value for property %s should be of type %s, current value {%s}" % ( self.key, self.vformat, str(nval) ) )
               
        else:
            
            raise LieMdException( "MDStudioProperty::CheckType", "Unknown type %s" % ( self.vformat ) )
    
    def _ConditionalCheck(self, nval ):
        
        self._CheckType(nval)

        check_list = nval

        if not isinstance( self.value, list ):
            check_list = [nval]

        for lval in check_list:
            for cond in self.conditions:
                if not cond.Evaluate( lval ):
                    raise LieMdException( "MDStudioProperty::Validate", "Violated conditional in %s with value %s" % ( self.key, str(lval) ) )
    
    def Validate(self):

        self._ConditionalCheck(self.value)

    def SetValue( self, nval ):
        
        if self.translate:    
            if nval in self.translate: 
                nval = self.translate[nval]
        
        self._ConditionalCheck( nval )
        self.value = nval
    
    def GetKey(self):
        
        return self.key
        
    def GetRepeat(self):
        
        return self.repeatGroup
    
    def GetActivator(self):
        
        return self.activator