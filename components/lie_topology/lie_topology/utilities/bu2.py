
def _FinalizeLinking( topology, solute_group, chain_cap_map ):

    molecule_remove_list = []
    for i in range(0, solute_group.molecules.size()):
        molecule = solute_group.molecules.at(i) 

        # test if this sequence item is a start merge operation
        if molecule.key in chain_cap_map: 
            molecule_remove_list.append(molecule.key)
            chain_cap_map_entry = chain_cap_map[molecule.key]
            
            target=None
            prepend=False
            
            # if this is a chain start
            if chain_cap_map_entry == BlendPosition.chain_start:
               target  = solute_group.molecules.at(i+1)
               prepend = True

            elif chain_cap_map_entry == BlendPosition.chain_end:
               target = solute_group.molecules.at(i-1)

            else:
               raise LieTopologyException("Molecule::_FinalizeLinking", "Unknow capping type" )

            #re-key
            molecule_cpy = molecule.SafeCopy( molecule_key=target.key )
            atom_count = molecule_cpy.atoms.size()

            for j in range(0,atom_count):
                fetch_index = j if not prepend else (atom_count-j-1)
                atom=molecule_cpy.atoms.at(fetch_index)
                
                target.AddAtom( atom=atom, prepend=prepend )

            for bond in molecule_cpy.bonds:
                # test if already present
                bond_index = target.IndexOfBond(bond)

                #if not exists
                if bond_index < 0:
                    target.AddBond(bond)
                else:
                    target.bonds[bond_index] = bond

            for angle in molecule_cpy.angles:
                # test if already present
                angle_index = target.IndexOfAngle(angle)

                #if not exists
                if angle_index < 0:
                    target.AddAngle(angle)
                else:
                    target.angles[angle_index] = angle

            for dihedral in molecule_cpy.dihedrals:
                # test if already present
                dihedral_index = target.IndexOfDihedral(dihedral)

                #if not exists
                if dihedral_index < 0:
                    target.AddDihedral(dihedral)
                else:
                    target.dihedrals[dihedral_index] = dihedral
                    
            for improper in molecule_cpy.impropers:
                # test if already present
                improper_index = target.IndexOfImproper(improper)

                #if not exists
                if improper_index < 0:
                    target.AddImproper(improper)
                else:
                    target.impropers[improper_index] = improper

    for remove_item in molecule_remove_list:
        solute_group.molecules.remove( remove_item )
    

def _AssertCovelent( molecule, group, reference, template_atom_counts ):

    response = None
    this_index = group.molecules.indexOf(molecule.key)

    if reference.external_index >= 0:
        #find the relative index of this
        #we use the mapped original atom count at start and end groups
        #might have modified the current atom count
        original_atom_count = template_atom_counts[molecule.key]
        atom_index = reference.external_index - original_atom_count
        molecule_index = this_index + 1
        next_molecule = group.molecules.at( molecule_index )
        
        if next_molecule:
            if atom_index < next_molecule.atom_count:
                response = next_molecule.atoms.at(atom_index).ToReference()
    
    else:

        molecule_index = this_index - 1
        prev_molecule = group.molecules.at( molecule_index )

        print( "Covelent ", reference.external_index, this_index, this_index - 1, prev_molecule.atom_count )

        if prev_molecule:
            if abs(reference.external_index) <= prev_molecule.atom_count:
                print( "Trials ", reference.external_index)
                atom_index = prev_molecule.atom_count + reference.external_index
                print( "Trials2 ",molecule.key, atom_index, prev_molecule.atom_count, reference.external_index )
                response = prev_molecule.atoms.at(atom_index).ToReference()


    if response:
        reference.external_index = None
        reference.group_key = response.group_key
        reference.atom_key = response.atom_key
        reference.molecule_key = response.molecule_key

def _BondedAtomsWithPrevious( molecule, prev_molecule, atom_keys, capping_treatment=False ):
    
    response = []

    for bond in prev_molecule.bonds:

        atom_references = bond.atom_references
        ref_1 = atom_references[0].ToReference()
        ref_2 = atom_references[1].ToReference()

        print("option ", ref_1.molecule_key, ref_1.atom_key, ref_2.molecule_key, ref_2.atom_key, " | ", prev_molecule.key, molecule.key ) 

        if ref_2.molecule_key == molecule.key and\
           ref_2.atom_key in atom_keys:
            print( "YEEEEEB2 ", bond.Debug() )
            response.append(ref_1)

        # inmolecule search is what we use for bonds in capping ends, where the actual connecting bond still describes the
        # renamed atom. 
        elif capping_treatment and\
             ref_2.atom_key not in prev_molecule.atoms and\
             ref_2.atom_key in atom_keys and\
             ref_1.atom_key not in atom_keys:
             response.append(ref_1)
             print( "YEEEEEB1 ", bond.Debug() )

    return response

def _AssertCovalentEnd( molecule, group, reference, atom_keys, template_atom_counts ):

    print( "COV_END ", reference.external_index)

    # can be handled by the normal routine
    if reference.external_index >= 0:
        _AssertCovelent( molecule, group, reference, template_atom_counts )
    
    else:
        this_index = group.molecules.indexOf(molecule.key)
        prev_molecule = group.molecules.at( this_index - 1 )

        bond_options = _BondedAtomsWithPrevious( molecule, prev_molecule, atom_keys, capping_treatment=True )

        if len(bond_options) != 1:
            for ambig in bond_options:
                print( "DEBUG AMBIG ", ambig.Debug(), atom_keys )
            raise LieTopologyException("Molecule::_AssertCovalentEnd", "Ambiguous assignment of indexed bonded option" )
        
        reference.external_index = None
        reference.group_key = bond_options[0].group_key
        reference.atom_key = bond_options[0].atom_key
        reference.molecule_key = bond_options[0].molecule_key

def _AssertBonded( molecule, bonded_list, is_capping, template_atom_counts ):
    
    for bonded in bonded_list:
        if not bonded.IsReferenceResolved():
            #save all named references
            atom_keys=[]
            for reference in bonded.atom_references:
                if reference.IsNamedReference():
                    atom_keys.append(reference.atom_key)

            for reference in bonded.atom_references:
                if reference.IsIndexedReference():

                    group = molecule.group
                    if group is None:
                        raise LieTopologyException("Molecule::_AssertBonded", "Cannot resolve indexed references when group link is undefined" )
                    
                    if is_capping:
                        _AssertCovalentEnd( molecule, group, reference, atom_keys, template_atom_counts )

                    else:
                        _AssertCovelent( molecule, group, reference, template_atom_counts )

def _RemoveOutOfBoundsBonded( bonded_src, num_atoms_overlap, template_count_count, molecule,
                              is_start = False, is_end = False ):

    capping_atom_count = molecule.atoms.size()

    to_remove=[]
    for i in range(0, len(bonded_src) ):
        bonded = bonded_src[i]

        schedule_removal=False
        reference_index=0
        for atom_ref in bonded.atom_references:
            naked_reference = atom_ref.ToReference()

            print ( "TT ", naked_reference.Debug())

            if naked_reference.IsIndexedReference():

                print ( "INDEXED REF ", naked_reference.external_index)

                if is_start and naked_reference.external_index <= 0:
                   #or is_end and naked_reference.external_index > 0:
                   schedule_removal = True
                   break # hard override on remove
                
                # START GROMOS EDIT
                # to make output compatible
                elif is_end and naked_reference.external_index > 0:
                    # in this case check if it is in range
                    # target local index
                    local_offset = naked_reference.external_index - template_count_count
                    local_cap_index = num_atoms_overlap + local_offset

                    print ( "FORWARD EDIT TRY:: ", local_cap_index, capping_atom_count)

                    if local_cap_index >= capping_atom_count:
                        schedule_removal = True
                        break # hard override on remove
                    else:
                        # apply a forward reference edit
                        local_atom = molecule.atoms[local_cap_index]

                        naked_reference.external_index = None
                        naked_reference.group_key    = molecule.group.key
                        naked_reference.atom_key     = local_atom.key
                        naked_reference.molecule_key = molecule.key

                        print ( "FORWARD EDIT CHANGED:: ", naked_reference.DEBUG() )

                        bonded.atom_references[reference_index] = naked_reference
                # END GROMOS EDIT

            reference_index+=1

        if schedule_removal:
            to_remove.append(i)
    
    for i in sorted(to_remove, reverse=True):
        print( "DELETING: ", bonded_src[i].Debug())
        del bonded_src[i]

def _AssertBondedInMerge(topology, solute_group, chain_cap_map, template_atom_counts):

    for i in range(0, solute_group.molecules.size()):
        molecule = solute_group.molecules.at(i) 
        is_start = False
        is_end = False

        # test if this sequence item is a start merge operation
        if molecule.key in chain_cap_map:
            chain_cap_map_entry = chain_cap_map[molecule.key]
            chain_molecule = None
            
            # if this is a chain start
            if chain_cap_map_entry == BlendPosition.chain_start:
               chain_molecule = solute_group.molecules.at(i+1)
               is_start = True
            
            # this is a chain end
            elif chain_cap_map_entry == BlendPosition.chain_end:
                chain_molecule = solute_group.molecules.at(i-1)
                is_end = True
            
            if chain_molecule:

                # START GROMOS EDIT
                # introduced to reproduce gromos output
                # compute the intersection between 
                chain_molecule_keyset = []
                for atom_key in chain_molecule.atoms:
                    chain_molecule_keyset.append(atom_key)

                cap_molecule_keyset = []
                for atom_key in molecule.atoms:
                    cap_molecule_keyset.append(atom_key)

                num_atoms_overlap = len( set(chain_molecule_keyset).intersection(cap_molecule_keyset) )
                template_count_count = template_atom_counts[chain_molecule.key]
                # END

                print (molecule.key, "||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")

                _RemoveOutOfBoundsBonded( chain_molecule.bonds, num_atoms_overlap, template_count_count,
                                          molecule, is_start=is_start, is_end=is_end )
                _RemoveOutOfBoundsBonded( chain_molecule.angles, num_atoms_overlap, template_count_count,
                                          molecule, is_start=is_start, is_end=is_end )
                _RemoveOutOfBoundsBonded( chain_molecule.dihedrals, num_atoms_overlap, template_count_count,
                                          molecule, is_start=is_start, is_end=is_end )
                _RemoveOutOfBoundsBonded( chain_molecule.impropers, num_atoms_overlap, template_count_count,
                                          molecule, is_start=is_start, is_end=is_end )

        is_capping = is_start or is_end
        
        # Fix bonded
        print( "ASSERT BONDS ")
        _AssertBonded( molecule, molecule.bonds, is_capping, template_atom_counts )
        print( "ASSERT ANGLES ")
        _AssertBonded( molecule, molecule.angles, is_capping, template_atom_counts )
        print( "ASSERT DIHEDRALS ")
        _AssertBonded( molecule, molecule.dihedrals, is_capping, template_atom_counts )
        print( "ASSERT IMPROPERS ")
        _AssertBonded( molecule, molecule.impropers, is_capping, template_atom_counts )


def _RenameBondedReferences( bonded_list, group_key, molecule_key, old_atom_key, new_atom_key):

    for bonded in bonded_list:
        for atom_ref in bonded.atom_references:

            if old_atom_key == atom_ref.atom_key:

                # only if we talk about the same molecule
                if atom_ref.group_key is None or\
                    atom_ref.group_key == group_key:

                    if atom_ref.molecule_key is None or\
                    atom_ref.molecule_key == molecule_key: 
                        atom_ref.atom_key = new_atom_key
                  


def _PrepareStartMerge( i, chain_size, solute_group, molecule, chain_cap_map ):

    # check error states
    if chain_size != 0:
        raise LieTopologyException("MakeTopology", "Can only use a blend start at chain length == 0")
    
    if (i+1) >= solute_group.molecules.size():
        raise LieTopologyException("MakeTopology", "Chain start cannot be at the end of a sqeuence")
    
    # find the next molecule in the chain
    next_molecule = solute_group.molecules.at(i+1)
    
    if next_molecule.key in chain_cap_map:
        raise LieTopologyException("MakeTopology", "Chain start cannot be followed by another blend molecule")
    
    trailing_count = molecule.trailing_count

    # first step is to rename all atoms in the target to the new
    # atom naming scheme. While these atoms will be deleted anyway
    # this is still required to correct all references to the bondeds
    for j in range(0, trailing_count):

        # as we directly delete the atoms, the index of 0
        # is always the start
        old_atom_key = next_molecule.atoms.keyAt(0)
        new_atom_key = molecule.atoms.keyAt(-trailing_count + j)

        # delete the atom
        next_molecule.atoms.remove(old_atom_key)

        # while the atom is deleted for now (will be replaced later on),  we must make sure that
        # the bonded references are also up to date
        _RenameBondedReferences( next_molecule.bonds,     solute_group.key, next_molecule.key, old_atom_key, new_atom_key)
        _RenameBondedReferences( next_molecule.angles,    solute_group.key, next_molecule.key, old_atom_key, new_atom_key)
        _RenameBondedReferences( next_molecule.dihedrals, solute_group.key, next_molecule.key, old_atom_key, new_atom_key)
        _RenameBondedReferences( next_molecule.impropers, solute_group.key, next_molecule.key, old_atom_key, new_atom_key)

def _PrepareEndMerge( i, chain_size, solute_group, molecule, chain_cap_map ):

    if chain_size == 0:
        raise LieTopologyException("MakeTopology", "Cannot cap an empty chain")

    if (i-1) < 0:
        raise LieTopologyException("MakeTopology", "Capping group cannot be the first in sequence")

    prev_molecule = solute_group.molecules.at(i-1)    

    #truncate the preceding atoms
    preceding_count = molecule.preceding_count
    previous_atom_count = prev_molecule.atom_count
    if preceding_count >= previous_atom_count:
        raise LieTopologyException("MakeTopology", "Preceding count of capping group is >= number of atoms previous molecule")
    
    for i in range(0, preceding_count):
        # does not increment as we directly delete the atoms
        fetch_index = previous_atom_count-preceding_count
        old_atom_key = prev_molecule.atoms.keyAt(fetch_index)
        new_atom_key = molecule.atoms.keyAt(i)

        prev_molecule.atoms.remove(old_atom_key)
        
        # while the atom is deleted for now (will be replaced later on),  we must make sure that
        # the bonded references are also up to date
        _RenameBondedReferences( prev_molecule.bonds,     solute_group.key, prev_molecule.key, old_atom_key, new_atom_key)
        _RenameBondedReferences( prev_molecule.angles,    solute_group.key, prev_molecule.key, old_atom_key, new_atom_key)
        _RenameBondedReferences( prev_molecule.dihedrals, solute_group.key, prev_molecule.key, old_atom_key, new_atom_key)
        _RenameBondedReferences( prev_molecule.impropers, solute_group.key, prev_molecule.key, old_atom_key, new_atom_key)
    
    # remove all preceding atoms
    remove_list=[]
    for atom_key, atom in molecule.atoms.items():
        if atom.preceding:
            remove_list.append(atom_key)
    
    #perform the actual removing
    for remove_key in remove_list:
        molecule.atoms.remove(remove_key)

    #remove out of bounds bonded
    # _RemoveOutOfBoundsBonded( prev_molecule.bonds, is_end=True )
    # _RemoveOutOfBoundsBonded( prev_molecule.angles, is_end=True )
    # _RemoveOutOfBoundsBonded( prev_molecule.dihedrals, is_end=True )
    # _RemoveOutOfBoundsBonded( prev_molecule.impropers, is_end=True )

def _PrepareMoleculeMerge(solute_group, chain_cap_map):
    
    """ Prepares molecules for merging

    Blend groups are not residues by themselfs and therefore have to be merged into
    others. Before we can do this we need to make sure that we remove the blended atoms
    from the target and filter the bonded interactions to reflect this.
    """
    chain_size=0
    for i in range(0, solute_group.molecules.size()):
        molecule = solute_group.molecules.at(i)

        # test if this sequence item is a start merge operation
        if molecule.key in chain_cap_map:
            chain_cap_map_entry = chain_cap_map[molecule.key]

            # if this is a chain start
            if chain_cap_map_entry == BlendPosition.chain_start:

                _PrepareStartMerge( i, chain_size, solute_group, molecule, chain_cap_map )
            
            # this is a chain end
            elif chain_cap_map_entry == BlendPosition.chain_end:

                _PrepareEndMerge( i, chain_size, solute_group, molecule, chain_cap_map )

        # Otherwise start a capping operation       
        else: 
            chain_size+=1