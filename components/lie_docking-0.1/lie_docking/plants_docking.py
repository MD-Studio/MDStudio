# -*- coding: utf-8 -*-

"""
Classes for protein-ligand docking using the PLANTS software:

  PLANTS: Protein-Ligand ANT System.
  "An ant colony optimization approach to flexible protein-ligand docking" Swarm Intell. 1, 115-134 (2007).
  O. Korb, T. Stützle, T.E. Exner
  URL: http://www.tcd.uni-konstanz.de/research/plants.php
"""

import os
import csv
import json
import textwrap

from   twisted.logger import Logger
from   lie_config     import configwrapper

from   settings       import SETTINGS
from   docking_base   import DockingBase
from   utils          import prepaire_work_dir, cmd_runner
from   clustering     import coords_from_mol2, ClusterStructures

PLANTS_CONF_FILE_TEMPLATE = textwrap.dedent("""
    # Scoring function and search settings
    scoring_function             {scoring_function}
    search_speed                 {search_speed}
    rescore_mode                 {rescore_mode}
    outside_binding_site_penalty {outside_binding_site_penalty}
    enable_sulphur_acceptors     {enable_sulphur_acceptors}
    ligand_intra_score           {ligand_intra_score}
    chemplp_clash_include_14     {chemplp_clash_include_14}
    chemplp_clash_include_HH     {chemplp_clash_include_HH}
    plp_steric_e                 {plp_steric_e}
    plp_burpolar_e               {plp_burpolar_e}
    plp_hbond_e                  {plp_hbond_e}
    plp_metal_e                  {plp_metal_e}
    plp_repulsive_weight         {plp_repulsive_weight}
    plp_tors_weight              {plp_tors_weight}
    chemplp_weak_cho             {chemplp_weak_cho}
    chemplp_charged_hb_weight    {chemplp_charged_hb_weight}
    chemplp_charged_metal_weight {chemplp_charged_metal_weight}
    chemplp_hbond_weight         {chemplp_hbond_weight}
    chemplp_hbond_cho_weight     {chemplp_hbond_cho_weight}
    chemplp_metal_weight         {chemplp_metal_weight}
    chemplp_plp_weight           {chemplp_plp_weight}
    chemplp_plp_steric_e         {chemplp_plp_steric_e}
    chemplp_plp_burpolar_e       {chemplp_plp_burpolar_e}
    chemplp_plp_hbond_e          {chemplp_plp_hbond_e}
    chemplp_plp_metal_e          {chemplp_plp_metal_e}
    chemplp_plp_repulsive_weight {chemplp_plp_repulsive_weight}
    chemplp_tors_weight          {chemplp_tors_weight}
    chemplp_lipo_weight          {chemplp_lipo_weight}
    chemplp_intercept_weight     {chemplp_intercept_weight}
    
    # Input file specification
    protein_file                 {protein_file} 
    ligand_file                  {ligand_file}
   
    # Output settings
    output_dir                   {output_dir}
    write_multi_mol2             {write_multi_mol2}
    
    # Ligand settings
    flip_amide_bonds             {flip_amide_bonds}
    flip_planar_n                {flip_planar_n}
    flip_ring_corners            {flip_ring_corners}
    force_flipped_bonds_planarity {force_flipped_bonds_planarity}
    force_planar_bond_rotation   {force_planar_bond_rotation}
    
    # Binding site definition
    bindingsite_center           {bindingsite_center[0]} {bindingsite_center[1]} {bindingsite_center[2]}
    bindingsite_radius           {bindingsite_radius}
    
    # cluster algorithm
    cluster_structures           {cluster_structures}
    cluster_rmsd                 {cluster_rmsd}
    
    # Writer
    write_ranking_links          {write_ranking_links}
    write_protein_bindingsite    {write_protein_bindingsite}
    write_protein_conformations  {write_protein_conformations}
    write_merged_protein         {write_merged_protein}
    write_merged_ligand          {write_merged_ligand}
    write_merged_water           {write_merged_water}
    write_per_atom_scores        {write_per_atom_scores}
    merge_multi_conf_output      {merge_multi_conf_output}
    """)

@configwrapper('plants')        
class PlantsDocking(DockingBase):
    """
    Class for running a protein-ligand docking using the PLANTS docking
    software:

      PLANTS: Protein-Ligand ANT System.
      "An ant colony optimization approach to flexible protein-ligand 
       docking" Swarm Intell. 1, 115-134 (2007).
      O. Korb, T. Stützle, T.E. Exner
      URL: http://www.tcd.uni-konstanz.de/research/plants.php
    
    This class is compatible with PLANTS versions 1.1 and 1.2. 
    If not otherwise defined, the PLANTS executable files are available
    in the bin directory of the lie_docking package suffixed by the
    OS identifier as returned by `sys.platform`.
    
    Support is available for all of PLANTS default configuration options
    described in sections 1.0 of the manual.
    
    :param workdir:     working directory for PLANTS to perform docking in
    :type workdir:      str
    :param exec_path:   path to PLANTS executable file
    :type exec_path:    str
    :param kwargs:      additional keyword arguments are considered as
                        PLANTS configuration options
    :type kwargs:       dict
    """
    
    method = 'plants'
    allowed_config_options = SETTINGS.get(method,{})
    logging = Logger()
    
    def __init__(self, workdir, exec_path=None, **kwargs):
        
        # Class internal attributes
        self._exec = exec_path
        self._workdir = workdir
        self._config = kwargs
        
    def results(self):
        """
        Return PLANTS results
        
        PLANTS general docking results are stored in the features.csv
        and ranking.csv Comma Seperated Value files.
        Ranking is a subset of features. The latter contains additional
        scoring function specific data and is parsed in favour of the
        first.
        
        Results are parsed into a dictionary with the docking pose 
        identifier as key. These identifiers are already sorted by 
        PLANTS docking score.
        
        :return: general PLANTS docking results
        :rtype:  dict
        """
        
        # Read docking results: first try features.csv, else ranking.csv
        results = {}
        for resultcsv in ('features.csv', 'ranking.csv'):
            resultcsv = os.path.join(self._workdir,resultcsv)
            if os.path.isfile(resultcsv):
                
                csvfile = open(resultcsv, 'r')
                reader = csv.DictReader(csvfile)
                for i,row in enumerate(reader):
                    results[row.get('TOTAL_SCORE',i)] = row
                break
        
        # Run a clustering
        structures = [os.path.join(self._workdir,'{0}.mol2'.format(mol2)) for mol2 in results]
        xyz = coords_from_mol2(structures)
        c = ClusterStructures(xyz, labels=results.keys())
        clusters = c.cluster(4, min_cluster_count=2)
        
        for structure,res in clusters.items():
          results[structure].update(res)        
        
        return results
    
    def format_config_file(self):
        """
        Format configuration as PLANTS *.conf file format
        
        The PLANTS_CONF_FILE_TEMPLATE serves as a template where
        option values are replaced by format placeholders with the
        same name as the keys in the configuration dictionary.
        
        Consistency of the configuration options is checked before
        configuration file creation to ensure that all required 
        options are available. If options are missing from the 
        configuration dictionary they will be added with default 
        values.
        
        :return: PLANTS configuration file
        :rtype:  str
        """
        
        for key, value in self.allowed_config_options.items():
            if not key in self._config:
                self._config[key] = value
                self.logging.warn('Required "{0}" configuration option not defined. Add with default option {1}'.format(key, value))
        
        confstring = PLANTS_CONF_FILE_TEMPLATE.format(**self._config)
        return confstring
    
    def run(self, protein, ligand, mode='screen'):
        """
        Run a PLANTS docking for a given protein and ligand in mol2
        format in either 'screen' or 'rescore' mode.
        
        :param protein: protein 3D structure in mol2 format
        :type protein:  str
        :param ligand:  ligand 3D structure in mol2 format
        :type ligand:   str
        :param mode:    PLANTS execution mode as either virtual
                        screening 'screen' or rescoring 'rescore'
        :type mode:     str
        """
        
        # Prepair working directory
        if not prepaire_work_dir(self._workdir):
            return False
        
        # Check if executable is available
        if not os.path.exists(self._exec):
            self.logging.error('{0} executable not available at: {1}'.format(self.method, self._exec))
            return False
        
        # Copy files to working directory
        conf_file = os.path.join(self._workdir, 'plants.config') 
        with open(conf_file, 'w') as conf:
            conf.write(self.format_config_file())    
        
        with open(os.path.join(self._workdir, 'protein.mol2'), 'w') as protein_file:
            protein_file.write(protein)
        
        with open(os.path.join(self._workdir, 'ligand.mol2'), 'w') as ligand_file:
            ligand_file.write(ligand)
            
        cmd = [self._exec, '--mode', mode, 'plants.config']
        output, error = cmd_runner(cmd, self._workdir)
               
        return True
