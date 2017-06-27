class Bookkeeping(object):

    def __init__(self):

        self.residue_index = 1
        self.atom_index    = 1
        self.chain_length  = 0
        self.blend_into = False

##
## We generate references so that we can relink in the new molecule
##
def _GenerateRenameEntry( rtype, entry_name ):

    return "%s::%s" % ( rtype, entry_name )

def _GenerateReference( ref_input, rename_dict ):
    reference = None

    if isinstance( ref_input, Atom ):
        reference = ref_input.ToReference()

    elif isinstance( ref_input, AtomReference ):
        reference = deepcopy(ref_input)

    else:
        raise LieTopologyException("MakeTopology", "Unrecognised type of atom reference")  
    
    # test if we need to apply rename schemes
    if reference.atom_key is not None:
        rename_entry = _GenerateRenameEntry("a", reference.atom_key)
        if rename_entry in rename_dict:
            reference.atom_key = rename_dict[rename_entry]

    if reference.molecule_key is not None:
        rename_entry = _GenerateRenameEntry("m", reference.molecule_key)
        if rename_entry in rename_dict:
            reference.molecule_key = rename_dict[rename_entry]
    
    if reference.group_key is not None:
        rename_entry = _GenerateRenameEntry("g", reference.group_key)
        if rename_entry in rename_dict:
            reference.group_key = rename_dict[rename_entry]

    return reference

def _CopyBonds( src_molecule, dest_molecule, rename_dict ):

    if src_molecule.bonds:
        for bond in src_molecule.bonds:

            if len(bond.atom_references) != 2:
                raise LieTopologyException("MakeTopology", "Bonds require 2 atom references")  
            
            ref_1 = _GenerateReference( bond.atom_references[0], rename_dict )
            ref_2 = _GenerateReference( bond.atom_references[1], rename_dict )

            dest_molecule.AddBond( Bond( atom_references=[ref_1, ref_2], bond_type=bond.bond_type, sybyl=bond.sybyl ) ) 

def _CopyAngles( src_molecule, dest_molecule, rename_dict ):

    if src_molecule.angles:
        for angle in src_molecule.angles:

            if len(angle.atom_references) != 3:
                raise LieTopologyException("MakeTopology", "Angles require 3 atom references")  

            ref_1 = _GenerateReference( angle.atom_references[0], rename_dict )
            ref_2 = _GenerateReference( angle.atom_references[1], rename_dict )
            ref_3 = _GenerateReference( angle.atom_references[2], rename_dict )

            dest_molecule.AddAngle( Angle( atom_references=[ref_1, ref_2,ref_3], angle_type=angle.angle_type ) )  

def _CopyDihedrals( src_molecule, dest_molecule, rename_dict ):

    if src_molecule.dihedrals:
        for dihedral in src_molecule.dihedrals:

            if len(dihedral.atom_references) != 4:
                raise LieTopologyException("MakeTopology", "Dihedrals require 4 atom references")  

            ref_1 = _GenerateReference( dihedral.atom_references[0], rename_dict )
            ref_2 = _GenerateReference( dihedral.atom_references[1], rename_dict )
            ref_3 = _GenerateReference( dihedral.atom_references[2], rename_dict )
            ref_4 = _GenerateReference( dihedral.atom_references[3], rename_dict )

            dest_molecule.AddDihedral( Dihedral( atom_references=[ref_1,ref_2,ref_3,ref_4], dihedral_type=dihedral.dihedral_type ) )

def _RemoveBonded( bonded_src, remove_set, is_start = False, is_end = False):

    to_remove=[]
    for i in range(0, len(bonded_src) ):
        bonded = bonded_src[i]

        schedule_removal=True
        for atom_ref in bonded.atom_references:
            naked_reference = _GenerateReference( atom_ref, {} )

            if naked_reference.IsNamedReference():
                if not naked_reference.atom_key in remove_set:
                    schedule_removal = False

            elif naked_reference.IsIndexedReference():
                if is_start and naked_reference.external_index <= 0 or\
                   is_end   and naked_reference.external_index > 0:
                   schedule_removal = True
                   break # hard override on remove
            else:
                raise LieTopologyException("MakeTopology", "Undefined bonded reference")  

        ##
        ## DEBUG
        debug_keys = []
        for atom_ref in bonded.atom_references:
            naked_reference = _GenerateReference( atom_ref, {} )
            debug_keys.append(naked_reference.atom_key if naked_reference.IsNamedReference() else naked_reference.external_index)
        # END

        if schedule_removal:
            to_remove.append(i)
            print ("BONDED REMOVAL: ", debug_keys)
    
    for i in sorted(to_remove, reverse=True):
        del bonded_src[i]

def _CopyVsite( vsite, rename_dict ):

    response = None

    if vsite is not None:
        response = deepcopy( vsite )
        response.atom_references = []

        # generate deferred references
        for atom_ref in vsite.atom_references:
            deferred_ref = _GenerateReference( atom_ref, rename_dict )
            response.atom_references.append( deferred_ref )

    return response 


def _CopyAtoms( src_molecule, dest_molecule, start_index, it_from, it_to ):

    # add atoms
    #for key, atom in src_molecule.atoms.items():
    for i in range(it_from, it_to):

        key, atom=src_molecule.atoms.keyValueAt(i)

        # make sure we ignore preceding atoms that might be in blend data
        if atom.preceding is None or not atom.preceding:

            vdw_type_cpy = None
            mass_type_cpy = None
            virtual_site_cpy = None
            coulombic_type_cpy = None
            
            if atom.vdw_type:
                vdw_type_cpy = deepcopy(atom.vdw_type)
            
            if atom.mass_type:
                mass_type_cpy = deepcopy(atom.mass_type)

            if atom.coulombic_type:
                coulombic_type_cpy = deepcopy(atom.coulombic_type)
            
            if atom.virtual_site:
                virtual_site_cpy = _CopyVsite(atom.virtual_site, rename_dict )

            dest_molecule.AddAtom(  key=key, type_name=atom.type_name, element=atom.element,\
                                    identifier=start_index, sybyl=atom.sybyl,\
                                    mass_type=mass_type_cpy, vdw_type=vdw_type_cpy,\
                                    coulombic_type=coulombic_type_cpy, charge_group=atom.charge_group,\
                                    virtual_site=virtual_site_cpy, trailing=atom.trailing )
                                    
            start_index+=1
            #print( atom.key )

def _AddBlend( solute_group, template_molecule, book_keeping ):

    print( "BLEND ", template_molecule.key )
    
    linear_molecule = None
    linear_molecule_key = None
    rename_dict=dict()
    ignore_set=set()

    if template_molecule.trailing_count > 0:
        if book_keeping.chain_length != 0 or book_keeping.blend_into:
            raise LieTopologyException("MakeTopology", "Can only use a blend start at chain length == 0")
        
        linear_molecule_key = "%s_%i" % (template_molecule.key,book_keeping.residue_index)
        linear_molecule = Molecule( key=linear_molecule_key, type_name=template_molecule.type_name, identifier=book_keeping.residue_index )
    
        # start a new  chain
        book_keeping.blend_into = True
        solute_group.AddMolecule( molecule=linear_molecule )

    elif template_molecule.preceding_count > 0:
        if book_keeping.chain_length == 0:
            raise LieTopologyException("MakeTopology", "Cannot cap an empty chain")

        # this is were we apply the capping group
        linear_molecule = solute_group.molecules.back()
        linear_molecule_key = linear_molecule.key

        #truncate the preceding atoms
        preceding_count = template_molecule.preceding_count
        previous_atom_count = linear_molecule.atom_count
        if preceding_count >= previous_atom_count:
            raise LieTopologyException("MakeTopology", "Preceding count of capping group is >= number of atoms previous molecule")

        to_remove=[]
        for i in range(0, preceding_count):
            fetch_index=previous_atom_count-preceding_count+i
            fetch_key=linear_molecule.atoms.keyAt(fetch_index)
            to_remove.append(fetch_key)
        
        for remove_key in to_remove:
            linear_molecule.atoms.remove(remove_key)

        # now we have to remove redundant bondeds
        _RemoveBonded( linear_molecule.bonds, set(to_remove), is_end=True )
        _RemoveBonded( linear_molecule.angles, set(to_remove), is_end=True )
        _RemoveBonded( linear_molecule.dihedrals, set(to_remove), is_end=True )
        _RemoveBonded( linear_molecule.impropers, set(to_remove), is_end=True )

        # reset length
        book_keeping.chain_length=0

    else:
        raise LieTopologyException("MakeTopology", "Sequence item %s is not a chain start or cap, while blending was requested" % (molecule.key))
    
    # make sure we update references to the new situation
    molecule_rename_key = _GenerateRenameEntry("m", template_molecule.key)
    rename_dict[molecule_rename_key] = linear_molecule_key

    _CopyAtoms( template_molecule, linear_molecule, book_keeping.atom_index, 0, template_molecule.atom_count )
    _CopyBonds( template_molecule, linear_molecule, rename_dict )
    _CopyAngles( template_molecule, linear_molecule, rename_dict )
    _CopyDihedrals( template_molecule, linear_molecule, rename_dict )

def _BlendInto( solute_group, src_molecule, rename_dict, atom_index, linear_molecule_key ):

    #pop the last residue which is a blend
    last_key, last_linear_molecule = solute_group.molecules.popitem(pop_last=True) 

    #skip set of atoms
    trailing_count = last_linear_molecule.trailing_count

    # perform a range check!
    if trailing_count >= src_molecule.atom_count:
        raise LieTopologyException("MakeTopology", "While blending into a chain start, the number of trailing atoms exceeds or equals the blendin residue count")

    # generate rename
    # we want to keep the blend atom names, so perform a rename
    remove_set=[]
    for i in range(0, trailing_count):
        old_atom_key = src_molecule.atoms.keyAt(i)
        new_atom_key = last_linear_molecule.atoms.keyAt(-trailing_count + i)
        remove_set.append(old_atom_key)

        if old_atom_key != new_atom_key:
            atom_rename_key = _GenerateRenameEntry("a", old_atom_key)
            rename_dict[atom_rename_key] = new_atom_key

    # we want to keep the NEW molecule name, so perform a backwards rename
    molecule_rename_key = _GenerateRenameEntry("m", last_key)
    rename_dict[molecule_rename_key] = linear_molecule_key

    print( "DEBUG", molecule_rename_key, linear_molecule_key)
    merged_molecule = Molecule( key=src_molecule.key, type_name=src_molecule.type_name, identifier=src_molecule.identifier )

    # copy stored information into the new molecule with rename
    last_linear_atom_count = last_linear_molecule.atom_count
    _CopyAtoms( last_linear_molecule, merged_molecule, atom_index, 0, last_linear_atom_count )
    _CopyBonds( last_linear_molecule, merged_molecule, rename_dict )
    _CopyAngles( last_linear_molecule, merged_molecule, rename_dict )
    _CopyDihedrals( last_linear_molecule, merged_molecule, rename_dict )       

    atom_index+=merged_molecule.atom_count

    # remove redundant bonded information before merging to the final molecule
    _RemoveBonded( src_molecule.bonds, set(remove_set), is_start=True )
    _RemoveBonded( src_molecule.angles, set(remove_set), is_start=True )
    _RemoveBonded( src_molecule.dihedrals, set(remove_set), is_start=True )
    _RemoveBonded( src_molecule.impropers, set(remove_set), is_start=True )

    _CopyAtoms( src_molecule, merged_molecule, atom_index, trailing_count, src_molecule.atom_count )
    _CopyBonds( src_molecule, merged_molecule, rename_dict )
    _CopyAngles( src_molecule, merged_molecule, rename_dict )
    _CopyDihedrals( src_molecule, merged_molecule, rename_dict )

    return merged_molecule

def _AddSolute( solute_group, template_molecule, book_keeping ):

    print( "SOLUTE ", template_molecule.key )

    rename_dict=dict()

    linear_molecule_key = "%s_%i" % (template_molecule.key,book_keeping.residue_index)
    linear_molecule = Molecule( key=linear_molecule_key, type_name=template_molecule.type_name, identifier=book_keeping.residue_index )
    
    # make sure we update references to the new situation
    molecule_rename_key = _GenerateRenameEntry("m", template_molecule.key)
    rename_dict[molecule_rename_key] = linear_molecule_key

    _CopyAtoms( template_molecule, linear_molecule, book_keeping.atom_index, 0, template_molecule.atom_count )
    _CopyBonds( template_molecule, linear_molecule, rename_dict )
    _CopyAngles( template_molecule, linear_molecule, rename_dict )
    _CopyDihedrals( template_molecule, linear_molecule, rename_dict )

    if book_keeping.blend_into:
        linear_molecule = _BlendInto( solute_group, linear_molecule, rename_dict, book_keeping.atom_index, linear_molecule_key )

    solute_group.AddMolecule( molecule=linear_molecule )

    book_keeping.atom_index+=linear_molecule.atom_count
    book_keeping.chain_length+=1
    book_keeping.residue_index+=1

    # reset flags
    book_keeping.blend_into = False

def _GenerateSequence( forcefield, blueprint, sequence, topology ):
    
    book_keeping = Bookkeeping()
    solute_group = topology.GroupByKey("solute")
    residue_index = 0

    for seq_item in sequence:

        molecule_template=blueprint.FindMolecule(seq_item)
        blend_template=blueprint.FindBlend(seq_item)

        if molecule_template != None:
            _AddSolute( solute_group, molecule_template, book_keeping )
            book_keeping.blend_into = False
            
        elif blend_template != None:

            if blend_template.preceding_count > 0 and\
               blend_template.trailing_count > 0:
               raise LieTopologyException("MakeTopology", "Sequence item %s cannot be both chain start and cap" % (seq_item))

            _AddBlend( solute_group, blend_template, book_keeping )

        else:
             raise LieTopologyException("MakeTopology", "Sequence item %s not present in the blueprint" % (seq_item))      
