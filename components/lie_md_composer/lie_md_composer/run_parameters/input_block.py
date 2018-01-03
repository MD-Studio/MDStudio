
from collections import OrderedDict

from lie_md.run_parameters.input_property import MDStudioProperty

class MDStudioRepeat(object):
    
    def __init__(self):
        
        self.template = MDStudioBlock(None)
        self.sets = []
        
    def AddTemplateProperty( self, prop ):
        
        self.template.properties[prop.GetKey()] = prop
        
    def Add(self):
        
        self.sets.append( deepcopy( self.template ) )
        
        return self.sets[-1]
    
    def Length(self):
        
        return len(self.sets)
 
    def LastItem(self):
        
        return self.sets[-1]
 
    def Validate( self ):

        for iset in self.sets:
            iset.Validate()

    def __getitem__( self,  index ):
    
        if index >= len( self.sets ):
            raise LieMdException(  "MDStudioRepeat::__getitem__", "Index overflow in MDStudioRepeat::GetItem()"  )

        return self.sets[index]


class MDStudioBlock(object):
    
    def __init__(self, definition):
        
        if definition:
            
            if not "key" in definition:
                
                raise LieMdException( "MDStudioBlock::__init__", "Block requires a key section" )
    
            if not "properties" in definition:
                
                raise LieMdException( "MDStudioBlock::__init__", "Block requires a properties section" )
    
            self.key = definition["key"]
            #self.repeatRegions = OrderedDict()
            self.properties = self._ParseProperties(definition["properties"])
        
        else:
            
            self.key = None
            #self.repeatRegions = None
            self.properties = OrderedDict()
        
    def _ParseProperties(self, definition):
        
        properties = OrderedDict()
        
        for itemdef in definition:
            
            imdProperty = MDStudioProperty( itemdef )
            repeat = imdProperty.GetRepeat()
            
            if repeat:
                
                if not repeat in properties:
                    
                    properties[repeat] = MDStudioRepeat()
                
                properties[repeat].AddTemplateProperty( imdProperty )
                
            else:
                
                properties[imdProperty.GetKey()] = imdProperty
                
        return properties

    def _FetchProperty( self, key ):
        
        fetch = None
        
        if "properties" in self.__dict__:
            
            if self.properties and key in self.properties:
                
                fetch = self.properties[key]
                
                if not isinstance( fetch, MDStudioRepeat ):
                    
                    activator = fetch.GetActivator()
    
                    if activator:
    
                        activatorFetch = self._FetchProperty( activator.key )
                        
                        if not activatorFetch:
                            
                            raise LieMdException( "MDStudioBlock::_FetchProperty", "Unknown property key %s" % ( activator.key ) )
                        
                        if activatorFetch.value != activator.value:
                            
                            raise LieMdException( "MDStudioBlock::_FetchProperty", "Tried to fetch a disabled property key %s" % ( key ) )

        return fetch

    def __getitem__(self, key):
        
        return self._FetchProperty( key )
                
    def __setitem__(self, key, value):
        
        fetch = self._FetchProperty( key )
        
        if fetch:
            
            if isinstance(fetch, MDStudioRepeat):
                
                raise LieMdException( "MDStudioBlock::__setitem__", "Cannot set on a repeat region %s" % (key) )
            
            fetch.SetValue( value )
       
        else:
            
            raise LieMdException( "MDStudioBlock::__setitem__", "Unknown key %s" % (key) )

    def __getattr__( self, key ):
        
        fetch = self._FetchProperty( key )
        
        if fetch:
            return fetch
        else:
            if not key in self.__dict__:
                raise AttributeError
            else:
                return self.__dict__[key] 
        
    def __setattr__(self, key, value):
        
        fetch = self._FetchProperty( key )

        if fetch:
            
            if isinstance(fetch,MDStudioRepeat):
                
                raise LieMdException( "MDStudioBlock::__setattr__", "Cannot set on a repeat region %s" % (key) )
            
            fetch.SetValue( value )
       
        else:
            
            self.__dict__[key] = value

    def Validate( self ):

        for prop in self.properties.values():
            prop.Validate()

    def GetKey(self):
        
        return self.key