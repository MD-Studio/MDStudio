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

import sys

from lie_topology.common.serializable import Serializable
from lie_topology.common.exception import LieTopologyException

"""
class Pair( Serializable ):
        
    def __init__(self, key = None, value = None):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )
        
        self.key = key
        self.value = value
"""

class ContiguousMap( Serializable ):

    def __init__( self ):
        
        # Call the base class constructor with the parameters it needs
        Serializable.__init__(self, self.__module__, self.__class__.__name__ )
        
        self._indices = {}
        self._items = []
    
    def setValue( self, key, value ):
        
        if not key in self._indices:
            
            raise LieTopologyException( "ContiguousMap::Set", "Key %s not in use" % ( key ) )
        
        index = self._indices[key]
        
        self._items[index].value = value

    def remove( self, key ):
        
        if not key in self._indices:
            raise LieTopologyException( "ContiguousMap::Remove", "Key %s not in use" % ( key ) )
        
        else:
            index = self._indices[key]
            (key,value) = self._items[index]
            del self._items[index]
            del self._indices[key]

            return key,value


    def clear( self ):
        self._indices.clear()
        self._items.clear()

    def popitem(self, pop_last=True):

        (key,value) = self._items.pop() if pop_last else self._items.pop(0)
        del self._indices[key]

        return key, value

    def __setitem__(self, key, value ):
        self.setValue(key,value)
    
    def __delitem__(self, key):
        self.remove(key)

    def __iter__(self):
        return self._indices.__iter__()     

    def __reversed__(self):
        return self._indices.__reversed__()

    def __sizeof__(self):
        return self._items.__sizeof__() + self._indices.__sizeof__()

    
    def values(self):
        
        for i in range(0, len(self._items), 1):
            key, value = self.keyValueAt( i )
            yield value
    
    def keys(self):
        
        for i in range( 0, len(self._items), 1):
            key, value = self.keyValueAt( i )
            yield key
    
    def items(self):
        
        for i in range(0, len(self._items), 1 ):
            key, value = self.keyValueAt( i )
            yield key, value; 

    
    def pop(self, key ):

        self.remove( key )

    def copy(self):
        return self.__class__(self)

    def __getitem__( self, key ):
    
        return self.find( key )
    
    def __contains__(self, key):

        return self.find( key ) != None

    def insert( self, key, element ):
        
        if key in self._indices:
            
            raise LieTopologyException( "ContiguousMap::PushBack", "Key %s already in use" % ( key ) )
            
        newIndex = len( self._items )
        
        self._items.append( ( key, element ) )
        self._indices[ key ] = newIndex
        
    def find( self, key ):
        
        if key in self._indices:
            
            return self.at( self._indices[key] )
        
        return None
    
    def keyValueAt( self, index ):
        
        if index >= len( self._items ):
            
            raise LieTopologyException( "ContiguousMap::KeyValueAt", "Index %i out of range" % ( index ) )
        
        (key,value) = self._items[index]
        
        return key,value
    
    def at( self, index ):
        
        key, value = self.keyValueAt( index )
        
        return value
    
    def keyAt( self, index ):
        
        key, value = self.keyValueAt( index )
        
        return key
    
    def size( self ):
        
        return len( self._items )
        
    def indexOf( self, key ):
        
        if key in self._indices:
            
            return self._indices[key]
        
        return -1
    
    
            
    
    
    