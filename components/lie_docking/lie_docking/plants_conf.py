# -*- coding: utf-8 -*-

import textwrap

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
    write_protein_splitted       {write_protein_splitted}
    write_merged_protein         {write_merged_protein}
    write_merged_ligand          {write_merged_ligand}
    write_merged_water           {write_merged_water}
    write_per_atom_scores        {write_per_atom_scores}
    merge_multi_conf_output      {merge_multi_conf_output}
    """)
