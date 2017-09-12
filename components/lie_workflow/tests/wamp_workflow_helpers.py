
def combine_for_docking(input_dict):
    
    output = {}
    for d in input_dict:
        output.update(d)
    
    return output

def get_docking_medians(session=None, **kwargs):
    
    medians = [v.get('path') for v in kwargs.get('output',{}).values() if v.get('mean',True)]
    session['status'] = 'completed'
    
    return {'medians': medians, 'session':session}
    
def prepaire_for_md(input_dict):
    
    prot = None
    top = None
    lig = None
    for item in input_dict:
        if 'topology_file' in item:
            top = item
        elif 'ligand_file' in item:
            lig = item
        elif 'protein_file' in item:
            prot = item
        else:
            pass
    
    output = []
    for ligand in lig['ligand_file']:
        output.append({'ligand_file':ligand, 'topology_file':top['topology_file'], 'protein_file':prot['protein_file']})
        
    return {'mapper': output}