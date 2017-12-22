def get_docking_medians(session=None, **kwargs):

    medians = [v.get('path') for v in kwargs.get('output', {}).values() if v.get('mean', True)]
    session['status'] = 'completed'
    
    return {'medians': medians, 'session':session}


def pick_atb_query_match(session=None, **kwargs):

    matches = kwargs.get('matches', [])
    if not matches:
        session['status'] = 'failed'
        return {'session': session}

    best_match_molid = None

    # Exact match?
    exact = [m for m in matches if m['is_identical']]
    if exact:
        best_match_molid = exact[0]['molid']
    else:
        lowrmsd = min([m['blind_rmsd'] for m in matches])
        for match in matches:
            if match['blind_rmsd'] == lowrmsd:
                best_match_molid = match['molid']
                break

    if best_match_molid:
        session['status'] = 'completed'
    else:
        session['status'] = 'failed'

    return {'session': session, 'molid': best_match_molid}


def choose_atb_amber(session=None, **kwargs):

    session['status'] = 'completed'
    if len(kwargs.get('matches', [])):
        return {'session': session, 'choice': kwargs.get('pos')}
    else:
        return {'session': session, 'choice': kwargs.get('neg')}
