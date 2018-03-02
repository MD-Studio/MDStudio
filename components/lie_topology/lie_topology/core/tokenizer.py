class Tokenizer:
    def __init__(self, ifstream):
        if ifstream.closed:
            raise Exception("Tokenizer::__init__ Given file stream is closed")
        self._stream = ifstream
        
    def blocks(self):
        # Store tokens till END
        tokens = []      
        # Read line by line
        for line in self._stream:

            # Strip whitespace at ends
            line = line.strip()
            # Split by basic delimiters
            fragments = line.split()
            
            # If there are no fragments or a comment -> skip
            if len( fragments ) == 0 or line[0] == '#':
                continue
            
            # Process tokens one by one         
            for token in fragments:
                # If this token was an END
                if token == "END" or token == "[END]":  
                    if len(tokens) >= 1:
                        currentBlock = tokens.pop(0)
                        yield currentBlock, tokens
                    tokens = []
                    
                # Test if we should discard from this point
                elif token[0] == "#":
                    break
                
                else:
                    # Add the token
                    tokens.append( token )
        
    