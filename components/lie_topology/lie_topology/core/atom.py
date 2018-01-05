
class Atom( object ):

    def __init__( self, uid, name, reference = None, element = None, sybyl = None, occupancy = None ):

        # key of the atom
        self._uid = uid
        
        # actual name of the atom type
        self._name = name

        # Identifier number defined by external sources
        self._reference = reference

        # Element of the atom
        self._element = element
        
        # Indicates if this atom is part of an aromatic system
        self._sybyl = sybyl
        
        # If from a crystallographic source store the occupancy
        self._occupancy = occupancy

        # If from a crystallographic source store the bfactor
        self._bFactor

        # Mass type, to be combined with a force field input
        self._mass
        
        # charge assignment
        self._partialCharge 

        # Charge group indiciation
        self._chargeGroup

        # Atom polarizability
        self._polarizability

        # charge on the cos particle
        self._cosCharge

        # Van der waals type, to be combined with a force field input
        self._vdwType

        # Current position
        self._position

        # Current velocity
        self._velocity

        # Current force
        self._force

        # Current cos offset
        self._cosOffset

