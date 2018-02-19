
class AtomExperimentalData(object):

    def __init__(self, occupancy = None, bfactor = None): 

        # If from a crystallographic source store the occupancy
        self._occupancy = occupancy

        # If from a crystallographic source store the bfactor
        self._bfactor = bfactor

    @property
    def occupancy(self):
        return self._occupancy

    @property
    def bfactor(self):
        return self._bfactor

    @occupancy.setter
    def occupancy(self, val):
        self._occupancy = val 

    @bfactor.setter
    def bfactor(self, val):
        self._bfactor = val 

class AtomForceFieldData(object):

    def __init__(self, mass = None, partial_charge = None, charge_group = None, 
                 polarizability = None, cos_charge = None, vdw_type = None):

        # Mass type, to be combined with a force field input
        self._mass = mass
        
        # charge assignment
        self._partial_charge = partial_charge

        # Charge group indiciation
        self._charge_group = charge_group

        # Atom polarizability
        self._polarizability = polarizability

        # charge on the cos particle
        self._cos_charge = cos_charge

        # Van der waals type
        self._vdw_type = vdw_type

    @property
    def mass(self):
        return self._mass

    @property
    def partial_charge(self):
        return self._partial_charge

    @property
    def charge_group(self):
        return self._charge_group

    @property
    def polarizability(self):
        return self._polarizability

    @property
    def cos_charge(self):
        return self._cos_charge

    @property
    def vdw_type(self):
        return self._vdw_type

    @mass.setter
    def mass(self, val):
        self._mass = val 

    @partial_charge.setter
    def partial_charge(self, val):
        self._partial_charge = val 

    @charge_group.setter
    def charge_group(self, val):
        self._charge_group = val 
    
    @polarizability.setter
    def polarizability(self, val):
        self._polarizability = val 
    
    @cos_charge.setter
    def cos_charge(self, val):
        self._cos_charge = val 

    @vdw_type.setter
    def vdw_type(self, val):
        self._vdw_type = val 

class AtomState(object):

    def __init__(self, position = None, velocity = None, force = None, cos_offset = None):

        # Current position
        self._position = position

        # Current velocity
        self._velocity = velocity

        # Current force
        self._force = force

        # Current cos offset
        self._cos_offset = cos_offset

    @property
    def position(self):
        return self._position

    @property
    def velocity(self):
        return self._velocity

    @property
    def force(self):
        return self._force
    
    @property
    def cos_offset(self):
        return self._cos_offset

    @position.setter
    def position(self, val):
        self._position = val 

    @velocity.setter
    def velocity(self, val):
        self._velocity = val 

    @force.setter
    def force(self, val):
        self._force = val 

    @cos_offset.setter
    def cos_offset(self, val):
        self._cos_offset = val 

class Atom(object):

    def __init__(self, uid, name = None, atom_number = None, element = None, sybyl = None, experimental_data = None,
                 force_field = None, state = None):

        # key of the atom
        self._uid = uid
        
        # actual name of the atom type
        self._name = name

        # Identifier number defined by external sources
        self._atom_number = atom_number

        # Element of the atom
        self._element = element
        
        # Indicates if this atom is part of an aromatic system
        self._sybyl = sybyl

        # struct with experimental data
        self._experimental_data = experimental_data

        # force field references
        self._force_field = force_field

        # state (e.g. position)
        self._state = state
    
    @property
    def uid(self):
        return self._uid

    @property
    def name(self):
        return self._name

    @property
    def atom_number(self):
        return self._atom_number

    @property
    def element(self):
        return self._element

    @property
    def sybyl(self):
        return self._sybyl

    @property
    def experimental_data(self):
        return self._experimental_data
    
    @property
    def force_field(self):
        return self._force_field
    
    @property
    def state(self):
        return self._state
    
    @name.setter
    def name(self, val):
        self._name = val 
    
    @atom_number.setter
    def atom_number(self, val):
        self._atom_number = val 
    
    @element.setter
    def element(self, val):
        self._element = val 
    
    @sybyl.setter
    def sybyl(self, val):
        self._sybyl = val 
    
    @experimental_data.setter
    def experimental_data(self, val):
        self._experimental_data = val 

    @force_field.setter
    def force_field(self, val):
        self._force_field = val 
    
    @state.setter
    def state(self, val):
        self._state = val 