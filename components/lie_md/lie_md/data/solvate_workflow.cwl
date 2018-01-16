cwlVersion: v1.0
class: Workflow
inputs:
  protein_pdb: File
  protein_top: File
  ligand_pdb: File
  ligand_top: File
  force_field: string
  sim_time: double

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

steps:
  gromit:
    run: mdstudio/gromit.cwl
    in:
      protein_pdb: protein_pdb
      protein_top: protein_top
      ligand_pdb: ligand_pdb
      ligand_top: ligand_top
      force_field: force_field
      sim_time: sim_time
    out: [gromitout,gromiterr,gromacslog_step9,trajectory, energy,
          gro, ndx, top, mdp]
  energy:
    run: mdstudio/energies.cwl
    in:
      edr:
        source: gromit/energy
    out: [energy_dataframe, energyout, energyerr]
