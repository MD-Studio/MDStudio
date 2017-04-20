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


import yaml

from collections import OrderedDict
from copy import deepcopy

from pygromos.common.contiguousMap import ContiguousMap;
from pygromos.common.exception import PygromosException;

class AtbData( object ):
    
    def __init__( self, deserializeData = None ):
        
        self.formula = "Undefined";
        self.inchi   = "Undefined";
        self.iupac   = "Undefined";
        self.common  = "Undefined";
        self.smiles  = "Undefined";
        self.atbid   = -1; 
        self.numAtoms = 0;
        self.totalCharge = 0.0;
        
        if deserializeData:
            
            self.OnDeserialize( deserializeData );
            
    def OnDeserialize( self, data ):
        
        if not isinstance( data, OrderedDict ):
            
            raise PygromosException( "AtbData::OnDeserialize", "Deserialize data presented is not a map" );
        
        for section in ( "Formula", "IUPAC-InChI", "IUPAC-Name", "Common-Name", "SMILES", "N-atoms", "Charge", "id" ):
            
            if not section in data:
            
                raise PygromosException( "AtbData::Deserialize", "ATB data requires a %s section" % (section) );
                
        self.formula = data["Formula"];
        self.inchi = data["IUPAC-InChI"];
        self.iupac = data["IUPAC-Name"];
        self.common = data["Common-Name"];
        self.smiles = data["SMILES"];
        self.numAtoms = data["N-atoms"];
        self.totalCharge = data["Charge"];
        self.atbid = data["id"]
        
    def OnSerialize( self ):
        
        obj = OrderedDict();
        
        obj["Formula"] = self.formula;
        obj["IUPAC-InChI"] = self.inchi;
        obj["IUPAC-Name"] = self.iupac;
        obj["Common-Name"] = self.common;
        obj["SMILES"] = self.smiles;
        obj["N-atoms"] = self.numAtoms;
        obj["Charge"] = self.totalCharge;
        obj["id"] = self.atbid;
        
        return obj;
        
class ExperimentalData( object ):
    
    def __init__( self, deserializeData = None ):
        
         self.temperature = 0.0;
         self.value = 0.0;
         self.unit = "Undefined";
         self.reference = "Undefined";
         self.note = "";
         
         if deserializeData:
            
            self.OnDeserialize( deserializeData );
            
    def OnDeserialize( self, data ):
        
        if not isinstance( data, OrderedDict ):
            
            raise PygromosException( "ExperimentalData::OnDeserialize", "Deserialize data presented is not a map" );
        
        for section in ( "temperature", "value", "unit", "reference", "note" ):
            
            if not section in data:
            
                raise PygromosException( "ExperimentalData::Deserialize", "Experimental data requires a %s section" % (section) );
        
        self.temperature = data["temperature"];
        self.value = data["value"];
        self.unit = data["unit"];
        self.reference = data["reference"];
        self.note = data["note"];
    
    def OnSerialize( self ):
        
        obj = OrderedDict();
        
        obj["temperature"] = self.temperature;
        obj["value"] = self.value;
        obj["unit"] = self.unit;
        obj["reference"] = self.reference;
        obj["note"] = self.note;
        
        return obj;

class SoluteBond( object ):
    
    def __init__( self, deserializeData = None ):
        
         self.atom_i = "Undefined";
         self.atom_j = "Undefined";
         self.type = "Undefined";
         
         if deserializeData:
            
            self.OnDeserialize( deserializeData );
            
    def OnDeserialize( self, data ):
        
        if not isinstance( data, OrderedDict ):
            
            raise PygromosException( "SoluteBond::OnDeserialize", "Deserialize data presented is not a map" );
        
        for section in ( "i", "j", "type" ):
            
            if not section in data:
            
                raise PygromosException( "SoluteBond::Deserialize", "Solute bond data requires a %s section" % (section) );
                
        self.atom_i = data["i"];
        self.atom_j = data["j"];
        self.type = data["type"];
    
    def OnSerialize( self ):
        
        obj = OrderedDict();
        
        obj["i"] = self.atom_i;
        obj["j"] = self.atom_j;
        obj["type"] = self.type;
        
        return obj;


class SoluteAngle( object ):
    
    def __init__( self, deserializeData = None ):
        
        self.atom_i = "Undefined";
        self.atom_j = "Undefined";
        self.atom_k = "Undefined";
        self.type = "Undefined"; 
    
        if deserializeData:
            
            self.OnDeserialize( deserializeData );
            
    def OnDeserialize( self, data ):
        
        if not isinstance( data, OrderedDict ):
            
            raise PygromosException( "SoluteAngle::OnDeserialize", "Deserialize data presented is not a map" );
        
        for section in ( "i", "j", "k", "type" ):
            
            if not section in data:
            
                raise PygromosException( "SoluteAngle::Deserialize", "Solute angle data requires a %s section" % (section) );
                
        self.atom_i = data["i"];
        self.atom_j = data["j"];
        self.atom_k = data["k"];
        self.type = data["type"];
    
    def OnSerialize( self ):
        
        obj = OrderedDict();
        
        obj["i"] = self.atom_i;
        obj["j"] = self.atom_j;
        obj["k"] = self.atom_k;
        obj["type"] = self.type;
        
        return obj;
        
class SoluteDihedral( object ):
    
    def __init__( self, deserializeData = None ):
        
        self.atom_i = "Undefined";
        self.atom_j = "Undefined";
        self.atom_k = "Undefined";
        self.atom_l = "Undefined";
        self.type = "Undefined"; 
    
        if deserializeData:
            
            self.OnDeserialize( deserializeData );
            
    def OnDeserialize( self, data ):
        
        if not isinstance( data, OrderedDict ):
            
            raise PygromosException( "SoluteDihedral::OnDeserialize", "Deserialize data presented is not a map" );
        
        for section in ( "i", "j", "k", "l", "type" ):
            
            if not section in data:
            
                raise PygromosException( "SoluteDihedral::Deserialize", "Solute dihedral data requires a %s section" % (section) );
                
        self.atom_i = data["i"];
        self.atom_j = data["j"];
        self.atom_k = data["k"];
        self.atom_l = data["l"];
        self.type = data["type"];
    
    def OnSerialize( self ):
        
        obj = OrderedDict();
        
        obj["i"] = self.atom_i;
        obj["j"] = self.atom_j;
        obj["k"] = self.atom_k;
        obj["l"] = self.atom_l;
        obj["type"] = self.type;
        
        return obj;
        
class SoluteImproper( object ):
    
    def __init__( self, deserializeData = None ):
        
        self.atom_i = "Undefined";
        self.atom_j = "Undefined";
        self.atom_k = "Undefined";
        self.atom_l = "Undefined";
        self.type = "Undefined"; 
    
        if deserializeData:
            
            self.OnDeserialize( deserializeData );
            
    def OnDeserialize( self, data ):
        
        if not isinstance( data, OrderedDict ):
            
            raise PygromosException( "SoluteImproper::OnDeserialize", "Deserialize data presented is not a map" );
        
        for section in ( "i", "j", "k", "l", "type" ):
            
            if not section in data:
            
                raise PygromosException( "SoluteImproper::Deserialize", "Solute improper data requires a %s section" % (section) );
                
        self.atom_i = data["i"];
        self.atom_j = data["j"];
        self.atom_k = data["k"];
        self.atom_l = data["l"];
        self.type = data["type"];
    
    def OnSerialize( self ):
        
        obj = OrderedDict();
        
        obj["i"] = self.atom_i;
        obj["j"] = self.atom_j;
        obj["k"] = self.atom_k;
        obj["l"] = self.atom_l;
        obj["type"] = self.type;
        
        return obj;

class Vsite( object ):
    
    def __init__( self, deserializeData = None ):
        
        self.atom_iv = "Undefined";
        self.atom_jv = "Undefined";
        
        if deserializeData:
            
            self.OnDeserialize( deserializeData );
            
    def OnDeserialize( self, data ):
        
        if not isinstance( data, OrderedDict ):
            
            raise PygromosException( "Vsite::OnDeserialize", "Deserialize data presented is not a map" );
        
        for section in ( "iv", "jv" ):
            
            if not section in data:
            
                raise PygromosException( "Vsite::Deserialize", "Vsite data requires a %s section" % (section) );
                
        self.atom_iv = data["iv"];
        self.atom_jv = data["jv"];
    
    def OnSerialize( self ):
        
        obj = OrderedDict();
        
        obj["iv"] = self.atom_iv;
        obj["jv"] = self.atom_jv;
        
        return obj;



class QmAtom( object ):
    
    def __init__( self, deserializeData = None ): 
        
        self.xyz = ( 0.0, 0.0, 0.0 );
        
        if deserializeData:
            
            self.OnDeserialize( deserializeData );
            
    def OnDeserialize( self, data ):
        
        if not isinstance( data, list ):
            
            raise PygromosException( "QmAtom::OnDeserialize", "Deserialize data presented is not a list" );
        
        self.xyz = data; 
        
    def OnSerialize( self ):
        
        return self.xyz;

class Solute( object ):
    
    def __init__( self, deserializeData = None ): 
        
        self.atoms = ContiguousMap();
        self.numDefaultAtoms = 0;
        self.numPrecedingAtoms = 0;
        self.numTrailingAtoms = 0;
        self.bonds = list();
        self.angles = list();
        self.dihedrals = list();
        self.impropers = list();
        
        if deserializeData:
            
            self.OnDeserialize( deserializeData );
    
    def TotalTrailingAtoms( self ):
        
        # num expected based on preceding and the external definitions
        return self.numPrecedingAtoms + self.numTrailingAtoms;
    
    def OnDeserialize( self, data ):
        
        if not isinstance( data, OrderedDict ):
            
            raise PygromosException( "Solute::OnDeserialize", "Deserialize data presented is not a map" );
        
        for section in ( "atoms", "bonds", "angles", "dihedrals", "impropers" ):
            
            if not section in data:
            
                raise PygromosException( "Solute::Deserialize", "Solute data requires a %s section" % (section) );
        
        for key, ldata in data["atoms"].items():
            
            if self.atoms.Find(key):
                
                raise PygromosException( "Solute::Deserialize", "Duplicate key %s in section %s" % (key, "atoms") );
            
            latom = Atom( ldata )
            
            # process counts
            if latom.flag == "default":
                self.numDefaultAtoms+=1;
            elif latom.flag == "preceding":
                self.numPrecedingAtoms+=1;
            elif latom.flag == "extern":
                self.numTrailingAtoms+=1;
            else:
                raise PygromosException( "Solute::Deserialize", "Unrecognised atom flag %s" % (latom.flag) );
            
            self.atoms.Insert( key, latom );
        
        #assign atom identifiers
        defaultID = 1;
        precedingID = ((-self.numPrecedingAtoms)+1)
        
        for atom in self.atoms.Values():
            
            if atom.flag == "default":
                atom.identifier = defaultID;
                defaultID+=1;
                
            elif atom.flag == "preceding":
                
                atom.identifier = precedingID;
                precedingID+=1;
                
            # added after the normal atoms, so count as default
            elif atom.flag == "extern":
                
                #case of extern we have 2 options, ether we have an identifier override,
                #or we append;
                
                if atom.identifier == "append":
                    
                    atom.identifier = defaultID;
                    defaultID+=1;
                
                if not isinstance( atom.identifier, int ):
                    
                    raise PygromosException( "Solute::Deserialize", "Atom identifier override was not an int" );
                
            else:
                
                raise PygromosException( "Solute::Deserialize", "Unrecognised atom flag %s" % (latom.flag) );
                
        
        for ldata in data["bonds"]:
            
            self.bonds.append( SoluteBond( ldata ) );
            
        for ldata in data["angles"]:
            
            self.angles.append( SoluteAngle( ldata ) );
            
        for ldata in data["dihedrals"]:
            
            self.dihedrals.append( SoluteDihedral( ldata ) );
            
        for ldata in data["impropers"]:
            
            self.impropers.append( SoluteImproper( ldata ) );
        
        ##
        ## Trailing test
        ## 
        
        for i in range ( self.atoms.Size() - self.numPrecedingAtoms, self.atoms.Size() ):
            
            if len( self.atoms.At(i).exclusions ) != 0:
                
                raise PygromosException( "Solute::OnDeserialize", "Considering %i trailing the last %i atoms cannot have exclusions defined" % ( self.numPrecedingAtoms, self.numPrecedingAtoms ) );

    def OnSerialize( self ):
        
        obj = OrderedDict();
        
        obj["atoms"] = OrderedDict();
        obj["bonds"] = list();
        obj["angles"] = list();
        obj["dihedrals"] = list();
        obj["impropers"] = list();
        
        for key, value in self.atoms.Items():
            
            obj["atoms"][key] = value.OnSerialize();
            
        for value in self.bonds:
            
            obj["bonds"].append( value.OnSerialize() );
            
        for value in self.angles:
            
            obj["angles"].append( value.OnSerialize() );
            
        for value in self.dihedrals:
            
            obj["dihedrals"].append( value.OnSerialize() );
        
        for value in self.impropers:
            
            obj["impropers"].append( value.OnSerialize() );
            
        return obj;

class MoleculeMeta( object ):
    
    def __init__( self, name, deserializeData = None ): 
        
        self.name = name;
        self.description = "";
        self.atb = AtbData();
        self.experiment = OrderedDict();
        
        if deserializeData:
            
            self.OnDeserialize( deserializeData );
            
    def OnDeserialize( self, data ):
        
        if not isinstance( data, OrderedDict ):
            
            raise PygromosException( "MoleculeMeta::OnDeserialize", "Deserialize data presented is not a map" );
        
        for section in ( "description", "atb", "experiment" ):
            
            if not section in data:
            
                raise PygromosException( "MoleculeMeta::Deserialize", "Molecule meta data requires a %s section" % (section) );
            
        self.description = data["description"];
        self.atb = AtbData( data["atb"] );
        
        for key, ldata in data["experiment"].items():
            
            if key in self.experiment:
                
                raise PygromosException( "MoleculeMeta::Deserialize", "Duplicate key %s in section %s" % (key, "experiment") );
            
            self.experiment[key] = ExperimentalData( ldata );
    
    def OnSerialize( self ):
        
        obj = OrderedDict();
        
        obj["description"] = self.description;
        obj["atb"] = self.atb.OnSerialize();
        obj["experiment"] = OrderedDict();
        
        for key, value in self.experiment.items():
            
            obj["experiment"][key] = value.OnSerialize();
        
        return obj;
        

class Molecule( object ):
    
    def __init__( self, name, deserializeData = None ): 
        
        self.meta = MoleculeMeta( name );
        self.solute = Solute();
        self.qm = OrderedDict();
        
        if deserializeData:
            
            self.OnDeserialize( name, deserializeData );
    
    def UpdateQmAtomCoords( self, qmAtoms ):
        
        if len( qmAtoms ) != len ( self.qm ):
            
            raise PygromosException( "Molecule::UpdateQmAtomCoords", "Failed to update qm atoms as the input count is not the same as len( self.qm )" );
           
        index = 0;
        for cqm in self.qm.values():
            
            cqm.xyz = qmAtoms[index];
            
            index+=1;
    
    def UpdateDefaultAtomsWithQmCoords( self ):
        
        for key, atom in self.solute.atoms.Items():
            
            if atom.flag == "default":
                
                if not key in self.qm:
                    
                    raise PygromosException( "Molecule::UpdateDefaultAtomsWithQmCoords", "Failed find a key %s in the qm atom list" % ( key ) );
                
                atom.xyz = self.qm[key].xyz;
                
    def OnDeserialize( self, name, data ):
        
        if not isinstance( data, OrderedDict ):
            
            raise PygromosException( "Molecule::OnDeserialize", "Deserialize data presented is not a map" );
        
        for section in ( "meta", "solute", "qm" ):
            
            if not section in data:
            
                raise PygromosException( "Molecule::Deserialize", "Molecule data requires a %s section" % (section) );
                
        
        self.meta = MoleculeMeta( name, data["meta"] );
        self.solute = Solute( data["solute"] );
        
        for key, ldata in data["qm"].items():
            
            if key in self.qm:
                
                raise PygromosException( "Molecule::Deserialize", "Duplicate key %s in section %s" % (key, "qm") );
            
            self.qm[key] = QmAtom( ldata );
        
    def OnSerialize( self ):
        
        obj = OrderedDict();
        
        obj["meta"] = self.meta.OnSerialize();
        obj["solute"] = self.solute.OnSerialize();
        obj["qm"] = OrderedDict();
        
        for key, value in self.qm.items():
            
            obj["qm"][key] = value.OnSerialize();
        
        return obj;
        
class Category( object ):
    
    def __init__( self, deserializeData = None ): 

        self.molecules = OrderedDict();
        
        if deserializeData:
            
            self.OnDeserialize( deserializeData );
    
    def SubSelect( self, molecules ):
        
        newCat = Category();
        molset = set(molecules);
        
        for key, ldata in self.molecules.items():
            
            if key in molset:
                
                newCat.molecules[key] = deepcopy( ldata );
            
        return newCat;
            
    def OnDeserialize( self, data ):
        
        if not isinstance( data, OrderedDict ):
            
            raise PygromosException( "Category::OnDeserialize", "Deserialize data presented is not a map" );
        
        for key, ldata in data.items():
            
            if key in self.molecules:
                
                raise PygromosException( "Category::Deserialize", "Duplicate key %s" % (key) );
            
            self.molecules[key] = Molecule( key, ldata );
    
    def OnSerialize( self ):
        
        obj = OrderedDict();
        
        for key, value in self.molecules.items():
            
            obj[key] = value.OnSerialize();
            
        return obj;

class MoleculeStorage( object ):
    
    def __init__( self, deserializeData = None ): 
        
        self.categories = OrderedDict();
        
        if deserializeData:
            
            self.OnDeserialize( deserializeData );
            
    def SubSelect( self, molecules ):
        
        molStore = MoleculeStorage();
        
        for key, category in self.categories.items():
            
            #deepcopy is returned here
            molStore.categories[key] = category.SubSelect( molecules );
        
        return molStore;
    
    def FindMolecule( self, name ):
        
        target = [];
        
        for key, category in self.categories.items():
            
            for molName, molData in category.molecules.items():
                
                if molName == name:
                    
                    target.append(molData);
                    
        if len(target) > 1:
            raise PygromosException( "Molecule::FindMolecule", "Found Duplicate key %s" % (name) );
            
        elif len(target) == 0:
            return target[0];
            
        return None;
        
    def OnDeserialize( self, fileHandle ):
        
        data = json.load( fileHandle, object_pairs_hook=OrderedDict);
        
        if not isinstance( data, OrderedDict ):
            
            raise PygromosException( "Molecule::OnDeserialize", "Deserialize data presented is not a map" );
        
        if not  "categories"  in data:
            
            raise PygromosException( "MoleculeStorage::Deserialize", "Storage data requires a %s section" % (section) );
                
        for key, ldata in data["categories"].items():
            
            if key in self.categories:
                
                raise PygromosException( "MoleculeStorage::Deserialize", "Duplicate key %s in section %s" % (key, "categories") );
            
            self.categories[key] = Category( ldata );

    def OnSerialize( self, fileHandle = None ):
        
        obj = OrderedDict();
        
        obj["categories"] = OrderedDict();
        
        for key, value in self.categories.items():
            
            obj["categories"][key] = value.OnSerialize();
        
        if fileHandle:
            
            json.dump( obj, fileHandle, indent=4 );
            
        return obj;

        
        