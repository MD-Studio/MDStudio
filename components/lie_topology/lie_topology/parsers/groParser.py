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


def ParseGro( ifstream ):
    
    # Gro files contain a single structure 
    # and a single nameless group
    structures = []
    structure.AddGroup( key=' ', chain_id=' ' )
    structure_group = structure.groups.back()

    recorded_title = False
    recorded_n_atom = False

    n_atom = 0
    coords = []
    velocities = []

    ## Uses occurance map to be order agnostic
    for line in ifstream:

        line = line.strip()
        if len(line) == 0:
            continue

        if not recorded_title:
            structure.title = line
            recorded_title = True
            
        elif not recorded_n_atom:
            n_atom=int(line)
        
        elif n_atom == 0:
            # then record box info
        
        else: 



    return structures