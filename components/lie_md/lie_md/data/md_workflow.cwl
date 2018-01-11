cwlVersion: v1.0
class: Workflow
inputs:
  protein_pdb:
    type: File
  protein_top:
    type: File
  ligand_pdb:
    type: File
  ligand_top:
    type: File
  forcefield:
    type: string
    default: "amber99sb"    
  periodic_distance:
    type: double
    default: 1.8
  pressure:
    type: double
    default: 1.01325
  prfc:
    type: string
    default: "10000,5000,50,0"
  ptau:
    type: double
    default: 0.5
  residues:
    type: string
  resolution:
    type: double
    default: 0.002
  salinity:
    type: double
    default: 0.1539976
  sim_time:
    type: double
    default: 1
  solvent:
    type: string
    default: "tip3p"
  temperature:
    type: string
    default: "100,200,300"
  ttau:
    type: double
    default: 0.1

outputs:
  gromitout:
    type: File
    outputSource: gromit/gromitout
  gromiterr:
    type: File
    outputSource: gromit/gromiterr
  gromacslog:
    type: File
    outputSource: gromit/gromacslog_step9
  trajectory:
    type: File
    outputSource: gromit/trajectory
  gro:
    type: File
    outputSource: gromit/gro
  ndx:
    type: File
    outputSource: gromit/ndx
  top:
    type: File
    outputSource: gromit/top
  mdp:
    type: File
    outputSource: gromit/mdp
  energy:
    type: File
    outputSource: gromit/energy
  energy_dataframe:
    type: File
    outputSource: energy/energy_dataframe
  energyout:
    type: File
    outputSource: energy/energyout
  energyerr:
    type: File
    outputSource: energy/energyerr
  decompose_dataframe:
    type: File
    outputSource: decompose/decompose_dataframe
  decompose_err:
    type: File
    outputSource: decompose/decompose_err
  decompose_out:
    type: File
    outputSource: decompose/decompose_out
    
steps:
  gromit:
    run: mdstudio/gromit.cwl
    in:
      protein_pdb: protein_pdb
      protein_top: protein_top
      ligand_pdb: ligand_pdb
      ligand_top: ligand_top
      forcefield: forcefield
      periodic_distance: periodic_distance
      pressure: pressure
      prfc: prfc
      ptau: ptau
      resolution: resolution
      salinity: salinity
      sim_time: sim_time
      solvent: solvent
      temperature: temperature
      ttau: ttau
    out: [gromitout,gromiterr,gromacslog_step9,trajectory, energy,
          gro, ndx, top, mdp]
  energy:
    run: mdstudio/energies.cwl
    in:
      edr:
        source: gromit/energy
    out: [energy_dataframe, energyout, energyerr]

  decompose:
    run: mdstudio/decompose.cwl
    in:
      res: residues
      ligand_top: ligand_top
      protein_top: protein_top
      gro:
        source: gromit/gro
      ndx:
        source: gromit/ndx
      trr:
        source: gromit/trajectory
      top:
        source: gromit/top
      mdp:
        source: gromit/mdp      
    out: [decompose_dataframe, decompose_err, decompose_out]
