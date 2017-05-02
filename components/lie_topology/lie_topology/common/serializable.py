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

import json
import inspect
import numpy as np

from copy import deepcopy

from lie_topology.common.util import ClassFromName
from lie_topology.common.exception import LieTopologyException


def _Seria

def _SerializeNumpyType(value):

    valChain = _SerializeValueChain( value.tolist(), logger )
    rvalue = { "array_type" : value.dtype.name,
                "values" : valChain }


def _IsBasicType( value ):

    return isinstance( value, ( float, int, long, str ) )

def _IsBasicMap( value ):

    return isinstance( value, dict )

def _IsBasicSequence( value ):

    return isinstance( value, ( list, tuple ) )

def _IsNumpyType( value ):

    return isinstance( value, np.ndarray )

def _IsValid( value ):

    rvalue = False

    if ( _IsBasicType(value) or _IsBasicSequence(value) or _IsBasicMap(value) or _IsNumpyType( value ) ):
        rvalue = True

    elif inspect.isclass( type(value) ) and value != None:
        rvalue = True
        
    return rvalue

def _DeserializeValueChain( value, logger ):
        
    rvalue = None
    
    if _IsBasicType(value):
        rvalue = value
    
    elif _IsBasicSequence(value):
        # in case of a list we need to process each value of the list
        # As they might be objects themself
        
        rvalue = []
        for item in value:
            
            valChain = _DeserializeValueChain( item, logger )
            rvalue.append( valChain )

    elif _IsBasicMap(value):
        # Two options: either full blown object or a case of a traditional dict
        if "_moduleName" in value and "_className" in value:
            rvalue =  ClassFromName( value["_moduleName"], value["_className"] )
            rvalue.OnDeserialize( value, logger )

        elif "array_type" in value and "values" in value:

            # Typed array, construct a numpy array
            rvalue = np.array( value["values"], value["array_type"] )

        else:
            rvalue = {}
            for key, item in value.items():
                
                valChain = _DeserializeValueChain( item, logger )
                rvalue[key] = valChain
    
    # catch None
    #elif inspect.isclass( type(value) ):
    #    rvalue = value
    
    else:
        raise LieTopologyException( "Serializable::_DeserializeValueChain", "Unknown value type %s" % ( str(value) ) );
    
    return rvalue


def _SerializeValueChain( value, logger ):
    
    rvalue = None
 
    if _IsBasicType(value):
        rvalue = value

    elif _IsNumpyType( value ):

        valChain = _SerializeValueChain( value.tolist(), logger )
        rvalue = { "array_type" : value.dtype.name,
                   "values" : valChain }

    elif _IsBasicSequence(value):
        # in case of a list we need to process each value of the list
        # As they might be objects themself
        
        rvalue = []
        for item in value:
            
            valChain = _SerializeValueChain( item, logger )
            
            if _IsValid( valChain ):
                rvalue.append( valChain )
                    
    elif _IsBasicMap(value):
        
        rvalue = {}
        for key, item in value.items():
            
            valChain = _SerializeValueChain( item, logger )
            
            if _IsValid( valChain ):
                rvalue[key] = valChain
    
    elif inspect.isclass( type(value) ):
        
        # catch None
        if _IsValid( value ):
            rvalue = value.OnSerialize( logger )
    
    else:
        raise LieTopologyException( "Serializable::_SerializeValueChain", "Unknown value type %s" % ( str(value) ) )
        
    return rvalue

class Serializable( object ):
    
    def __init__(self, moduleName, className):
        
        self._moduleName = moduleName
        self._className = className
        
    def _IsValidCategory( self, cat ):
        
        return cat in self.__dict__
    
    def OnDeserialize( self, data, logger = None ):
        
        if not _IsBasicMap(data):
            raise LieTopologyException( "Serializable::OnDeserialize", "Deserialize data presented is not a map" );
        
        for cat, value in data.items():
            
            if self._IsValidCategory( cat ):
    	       
               valChain =  _DeserializeValueChain( value, logger ) 
               
               if _IsValid( valChain ):
                	setattr(self, cat, _DeserializeValueChain( value, logger ) )
                
            else:
                # If a python logger is present
                if logger:
                    logger.warning("Serializable::OnDeserialize category %s not valid for deserialization" % ( cat ) )
                    
            
    def OnSerialize( self, logger = None ):          
        
        rvalue = {}
        for cat, value in self.__dict__.items():
            
            valChain =  _SerializeValueChain( value, logger )
            
            if _IsValid( valChain ):
    	       	rvalue[cat] = valChain
            
        return rvalue