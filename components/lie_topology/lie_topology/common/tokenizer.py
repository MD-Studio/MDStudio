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

class Tokenizer:
    
    def __init__(self, ifstream ):
        
        # Storage of known blocks
        self.blocks = {}
        
        # Parse the input stream
        self._ParseFile( ifstream );
    
    
    def _ParseFile( self, ifstream ):
        	
        # Record the current block name
        currentBlock = None;
        
        # Store tokens till END
        tokens = [];
        
        # Read line by line
        for line in ifstream.split("\n"):
        
            # Strip whitespace at ends
            line = line.strip();
            
            # Split by basic delimiters
            fragments = line.split();
            
            # If there are no fragments or a comment -> skip
            if len( fragments ) == 0 or line[0] == '#':
                
                continue;
            
           # If we havent recorded what block this is
            elif currentBlock == None:
                currentBlock = fragments.pop(0);
                continue;
         
            for token in fragments:
                
                if token[0] == "#":
                    break;
                
                tokens.append( token )
                
                if tokens[-1] == "END" or tokens[-1] == "[END]":
                
                    tokens.pop();
                    
                    if currentBlock in self.blocks:
                        
                        self.blocks[currentBlock].append(tokens)
                    
                    else:
                        self.blocks[currentBlock] = [ tokens ]
                        
                    currentBlock = None
                    tokens = []