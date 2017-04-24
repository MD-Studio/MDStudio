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
    
    def __init__( self, ifstream ):
        
        if ifstream.closed:
            raise LieTopologyException("Tokenizer::__init__", "Given file stream is closed")
        
        self._stream = ifstream;
        
    def Blocks(self):
        
        # Store tokens till END
        tokens = [];
        
        # Read line by line
        for line in self._stream:
            
            # Strip whitespace at ends
            line = line.strip();
            
            # Split by basic delimiters
            fragments = line.split();
            
            # If there are no fragments or a comment -> skip
            if len( fragments ) == 0 or line[0] == '#':
                continue;
            
            # Process tokens one by one         
            for token in fragments:
                
                # If this token was an END
                if token == "END" or token == "[END]":
                    
                    if len(tokens) >= 1:
                        currentBlock = tokens.pop(0)
                        yield currentBlock, tokens;
                    
                    tokens = [];
                    
                # Test if we should discard from this point
                elif token[0] == "#":
                    break;
                
                else:
                    # Add the token
                    tokens.append( token )
        
    