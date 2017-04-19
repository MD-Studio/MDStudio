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


from lie_topology.common.exception import LieTopologyException;

class ContiguousMap( object ):
    
    class Pair(object):
        
        def __init__(self, first, second):
            
            self.first = first;
            self.second = second;
    
    def __init__( self ):
        
        self.mSearchStorage = {};
        self.mContiguousStorage = [];
    
    def Insert( self, key, element ):
        
        if key in self.mSearchStorage:
            
            raise LieTopologyException( "ContiguousMap::PushBack", "Key %s already in use" % ( key ) );
            
        newIndex = len( self.mContiguousStorage );
        
        self.mContiguousStorage.append( ContiguousMap.Pair( key, element ) );
        self.mSearchStorage[ key ] = newIndex;
        
    def Find( self, key ):
        
        if key in self.mSearchStorage:
            
            return self.At( self.mSearchStorage[key] );
        
        return None;
    
    def Set( self, key, value ):
        
        if not key in self.mSearchStorage:
            
            raise LieTopologyException( "ContiguousMap::Set", "Key %s not in use" % ( key ) );
        
        index = self.mSearchStorage[key];
        
        self.mContiguousStorage[index].second = value;
    
    def KeyValueAt( self, index ):
        
        if index >= len( self.mContiguousStorage ):
            
            raise LieTopologyException( "ContiguousMap::KeyValueAt", "Index %i out of range" % ( index ) );
        
        pair = self.mContiguousStorage[index];
        
        return pair.first, pair.second;
    
    def At( self, index ):
        
        key, value = self.KeyValueAt( index );
        
        return value;
    
    def KeyAt( self, index ):
        
        key, value = self.KeyValueAt( index );
        
        return key;
    
    def Size( self ):
        
        return len( self.mContiguousStorage );
        
    def IndexOf( self, key ):
        
        if key in self.mSearchStorage:
            
            return self.mSearchStorage[key];
        
        return -1;
    
    def Remove( self, key ):
        
        if not key in self.mSearchStorage:
            
            raise LieTopologyException( "ContiguousMap::Remove", "Key %s not in use" % ( key ) );
        
        else:
            
            index = self.mSearchStorage[key];
            
            del self.mContiguousStorage[index];
            del self.mSearchStorage[key];
            
    def Clear( self ):
        
        self.mSearchStorage = {};
        self.mContiguousStorage = [];
    
    def Values(self):
        
        for i in range(0,len(self.mContiguousStorage),1):
            
            key, value = self.KeyValueAt( i );
            
            yield value;
    
    def Keys(self):
        
        for i in range(0,len(self.mContiguousStorage),1):
            
            key, value = self.KeyValueAt( i );
            
            yield key;
    
    def Items(self):
        
        for i in range(0,len(self.mContiguousStorage),1):
            
            key, value = self.KeyValueAt( i );
            
            yield key, value; 
