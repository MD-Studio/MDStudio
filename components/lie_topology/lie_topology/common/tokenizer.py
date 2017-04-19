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

class Tokenizer:
    
    def _ParseFile( self, ifile):
    
        currentBlock = None;
        tokens = [];
        
        for line in ifile.split("\n"):
        
            line = line.strip();
            
            if len( line ) == 0 or line.strip()[0] == '#':
                
                continue;
            
            elif currentBlock == None:
                
                currentBlock = line;
                continue;
         
            elif line == "END" or line == "[END]":
                
                if currentBlock in self._blocks:
                    
                    self._blocks[currentBlock].append(tokens);
                
                else:
                    
                    self._blocks[currentBlock] = [ tokens ];
                    
                currentBlock = None;
                tokens = [];
                continue;
            
            else: 
                
                for token in line.split():
                    
                    if token[0] == "#":
                
                    	break;
                    
                    else:
                        
                        tokens.append( token );
            
    
    def __init__(self, ifile):
        
        self._blocks = {}
        
        self._ParseFile( ifile );
        
    def GetStream(self):
        
        return self._blocks;
