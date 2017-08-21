
def combine_for_docking(input_dict):
    
    output = {}
    for d in input_dict:
        output.update(d)
    
    return output

def get_docking_medians(session=None, **kwargs):
    
    medians = [v.get('path') for v in kwargs.get('output',{}).values() if v.get('mean',True)]
    session['status'] = 'completed'
    
    return {'medians': medians, 'session':session}