
import json
import yaml

from lie_md.general.runinput import RunInput
# from pygromos.protocolBuilder import ProtocolBuilder
# from pygromos.writers.imdWriter import GenerateImd

def main():
    
    runinput = None
    
    with open( '../tests/gromos/imd/gromos_1_3_1.mdpp','r') as ifs:
        runinput = RunInput(ifs)


    # if imdControl:
        
    #     with open( argv[1],'r') as ifs:
            
    #         protoBuilder = ProtocolBuilder( ifs );
    #         variables=dict();
    #         variables["@LAST_SOLUTE_ATOM"] = 8;
    #         variables["@LAST_SOLVENT_ATOM"] = 5000;
    #         variables["@N_SOLV"] = 1664 
    #         variables["$C_FRIC"] = 24
    #         variables["$N_STEPS"] = 3000
    #         variables["$T_START"] = 0
    #         variables["$DT"] = 0.002
    #         variables["$TEMP"] = 298.15
    #         variables["$COMP"] = 4.575E-4
    #         variables["$REF_P"] = 0.06102
    #         imdFile = protoBuilder.BuildProtocol( imdControl, "solute_minimize", variables);
    	    
    #         print( GenerateImd(imdFile) );

if __name__ == '__main__':

    main()