cwlVersion: v1.0
class: Workflow
inputs:
  protein_pdb: File
  protein_top: File
  protein_itp: File
  ligand_pdb: File
  ligand_top: File
  ligand_itp: File
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
  energy:
    type: File
    outputSource: gromit/energy

steps:
  gromit:
    run: mdstudio/gromit.cwl
    in:
      protein_pdb: protein_pdb
      protein_top: protein_top
      protein_itp: protein_itp
      ligand_pdb: ligand_pdb
      ligand_top: ligand_top
      ligand_itp: ligand_itp
      force_field: force_field
      sim_time: sim_time
    out: [gromitout,gromiterr,gromacslog_step9,trajectory, energy]