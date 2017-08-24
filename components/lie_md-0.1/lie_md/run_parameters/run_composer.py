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
from common.exception import LieMdException

class MDStudioConditional(object):
    
    def __init__( self, definition ):
        
        if not "type" in definition:
            
            raise LieMdException( "MDStudioConditional::__init__", "Conditional requires a type section" )
        
        if not "value" in definition:
            
            raise LieMdException( "MDStudioConditional::__init__", "Conditional requires a value section" )
        
        self.type = definition["type"]
        self.value = definition["value"]
        
        if hasattr(self.value, "__len__"):
            
            raise LieMdException( "MDStudioConditional::__init__", "Conditional value should be a scalar" )

        self.actionList = dict()
        self.actionList[">="] = self._GreaterEqual
        self.actionList[">"]  = self._Greater
        self.actionList["<="] = self._LessEqual
        self.actionList["<"]  = self._Less
        self.actionList["=="] = self._Equal
        self.actionList["!="] = self._NotEqual
        
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
    
    def Evaluate(self, query ):
        
        return self.actionList[self.type]( query )

class MDStudioActivator(object):
    
    def __init__( self, definition ):
        
        if not "key" in definition:
            
            raise LieMdException( "MDStudioActivator::__init__", "Activator requires a key section" )
        
        if not "value" in definition:
            
            raise LieMdException( "MDStudioActivator::__init__", "Activator requires a value section" )
        
        self.key = definition["key"]
        self.value = definition["value"]
        
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
        
        elif self.vformat == "txt":     
            
            if not isinstance( nval, str ):
                
                raise LieMdException( "MDStudioProperty::CheckType", "Value for property %s should be of type %s, current value {%s}" % ( self.key, self.vformat, str(nval) ) )
               
        else:
            
            raise LieMdException( "MDStudioProperty::CheckType", "Unknown type %s" % ( self.vformat ) )
    
    def Validate(self):
        
        for cond in self.conditions:
            
            if not cond.Evaluate( self.value ):
                
                raise LieMdException( "MDStudioProperty::Validate", "Violated conditional in %s with value %s" % ( self.key, str(self.value) ) )
    
    
    def SetValue( self, nval ):
        
        if self.translate:
            
            if nval in self.translate:
                
                nval = self.translate[nval]
        
        self._CheckType(nval)
        
        self.value = nval
    
    def GetKey(self):
        
        return self.key
        
    def GetRepeat(self):
        
        return self.repeatGroup
    
    def GetActivator(self):
        
        return self.activator

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

    def GetKey(self):
        
        return self.key

class RunInputFile( object ):
    
    def __init__( self, orderedBlocks ):
    
        self._blocks = orderedBlocks
    
    def Extend( self, rhs ):
        
        self._blocks.update( rhs.blocks )
    
    def IsPresent( self, blockName ):
        
        return blockName in self._blocks
    
    @property
    def blocks( self ):  
        
        return self._blocks

    def __getattr__( self, key ):
    
        key = key.upper()
    
        if "_blocks" in self.__dict__ and key in self._blocks:
            
            return self._blocks[key]    
            
        else :
            
            if not key in self.__dict__:
            
                raise AttributeError
                
            else:
                
                return self.__dict__[key]

    def __setattr__(self, key, value):
        
        if key != "_blocks":
            
            raise LieMdException( "RunInputFile::__setattr__", "Set attribute not allowed on IMD files" )
        
        self.__dict__[key] = value
        
    def __getitem__(self, key):
        
        key = key.upper()
        
        if key not in self._blocks.keys():
            
            raise LieMdException( "RunInputFile::__getitem__", "Unknown key "+str( key ) )
            
        return self._blocks[key]


class RunInput(object):
    
    def __init__( self, ifile ):
        
       self._blockDefinitions = self._ParseDefinitions( ifile )
       
    def _ParseDefinitions( self, ifstream ):
        
        tree = yaml.load(ifstream)
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

        return RunInputFile( result )
