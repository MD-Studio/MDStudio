
class Atom( object ):

    def __init__( self, uid, name, reference = None, element = None, sybyl = None, occupancy = None, bFactor = None,
                  mass = None, partialCharge = None, chargeGroup = None, polarizability = None, cosCharge = None,
                  vdwType = None, position = None, velocity = None, force = None, cosOffset = None  ):

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
        self._bFactor = bFactor

        # Mass type, to be combined with a force field input
        self._mass = mass
        
        # charge assignment
        self._partialCharge = partialCharge

        # Charge group indiciation
        self._chargeGroup = chargeGroup

        # Atom polarizability
        self._polarizability = polarizability

        # charge on the cos particle
        self._cosCharge = cosCharge

        # Van der waals type
        self._vdwType = vdwType

        # Current position
        self._position = position

        # Current velocity
        self._velocity = velocity

        # Current force
        self._force = force

        # Current cos offset
        self._cosOffset

