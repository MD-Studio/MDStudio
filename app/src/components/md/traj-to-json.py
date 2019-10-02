#!/usr/bin/env python

import glob
import json

ff = glob.glob('/Users/mvdijk/Documents/WorkProjects/eTox/lie_results_3eqm_md/BHC*-1-*.ene')

for i, f in enumerate(ff, start=1):
    ele = []
    vdw = []
    with open(f, 'r') as ene:
        for line in ene.readlines():
            if not line.startswith('#'):
                line = line.split()
                fr = int(line[1])
                e = float(line[9])
                v = float(line[10])

                ele.append([fr, e])
                vdw.append([fr, v])

    rawj = [{'values': ele, 'key': 'Elec'}, {'values': vdw, 'key': 'Vdw'}]
    ser = json.dumps(rawj)

    with open('md-traj-{0}.json'.format(i), 'w') as out:
        out.write(ser)
