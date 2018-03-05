#!/usr/bin/env python

"""
Provides an interface for HADDOCK XMLRPC endpoint through
either command-line arguments like

usage: python run_haddock.py --list_users

Or through a complete console-like environment with login/logout capabilities

usage: python run_haddock.py
...
(HADDOCK) > list_users

Author: {0} ({1})
"""


import argparse
from HADDOCKInterface import HADDOCKInterface
from HADDOCKCmdLineApp import HADDOCKCmdLineApp
import os, sys
from urllib2 import urlopen

__author__ = "Mikael Trellet"
__email__ = "mikael.trellet@gmail.com"


parser = argparse.ArgumentParser(description="Run HADDOCK and monitor jobs via XMLRPC interface")

parser.add_argument("-lu", '--list_users', action='store_true', help="List HADDOCK users (admin rights needed)")
parser.add_argument("-lp", '--list_projects', action='store_true', help="List HADDOCK projects")
parser.add_argument("-u", "--url", type=str, nargs=1, metavar='project_name', help="Get HADDOCK project URL")
parser.add_argument("-d", "--download", type=str, nargs='+', metavar=('project_name', 'output_path'),
                    help="Download HADDOCK project archive")
parser.add_argument('-r', '--run', type=argparse.FileType(), nargs='+', metavar=('param_path', 'project_name'),
                    help="Run HADDOCK with parameter file as input")
parser.add_argument('-p', '--params', type=str, nargs='+', metavar=('project_name', 'output_path'),
                    help='Download HADDOCK project parameters file')
parser.add_argument('-s', '--status', type=str, nargs=1, metavar='project_name',
                    help='Get HADDOCK project status')

args = parser.parse_args()

interface = HADDOCKInterface()

if args.list_users:
    try:
        users = interface.list_users()
    except:
        raise
    for usr in users:
        print usr[0], usr[-2]
elif args.list_projects:
    try:
        projects = interface.list_projects()
    except:
        raise
    if len(projects):
        for proj in projects:
            print proj
    else:
        print "No recent projects for the specified user"
elif args.url:
    try:
        url = interface.get_url(str(args.url[0]))
        print "URL: {}".format(url)
    except:
        raise
elif args.status:
    try:
        status = interface.get_status(str(args.status[0]))
        print "STATUS: {}".format(status)
    except:
        raise
elif args.params:
    try:
        haddockparams = interface.get_params(args.params[0])
    except:
        print "ERROR: User name or password not correct or not known"
        sys.exit(0)
    if not args.params[1]:
        output = os.path.join(os.curdir, 'haddockparam.web')
        f = open('haddockparam.web', 'wb')
    else:
        if os.path.isdir(args.params[1]):
            output = os.path.join(args.params[1], 'haddockparam.web')
            f = open(output, 'wb')
        elif os.path.isdir(os.path.dirname(args.params[1])):
            output = args.params[1]
            f = open(output, 'wb')
        else:
            raise Exception("Directory path not found, aborting...")
    f.write(haddockparams)
    f.close()
    print "Parameters saved in: {}".format(output)
elif args.download:
    try:
        url = interface.get_url(str(args.download[0]))
    except:
        print "ERROR: User name or password not correct or not known"
        sys.exit(0)
    file_name = url.split('/')[-1]
    u = urlopen(url)
    extension = os.path.splitext(file_name)[1]
    if len(args.download) < 2:
        output = os.path.join(os.curdir, file_name)
        f = open(output, 'wb')
    else:
        if os.path.isdir(args.download[1]):
            output = os.path.join(args.download[1], file_name)
            f = open(output, 'wb')
        elif extension == os.path.splitext(args.download[1]):
            output = args.download[1]
            f = open(output, 'wb')
        elif not os.path.isdir(args.download[1]):
            raise Exception("Directory path does not exist, aborting...")
        else:
            raise Exception("Wrong file extension in the output path, aborting...")
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (file_name, file_size)
    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break
        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status += chr(8) * (len(status) + 1)
        print status,
    f.close()
    print "Download finished successfully at: {}".format(output)
elif args.run:
    print "####\nLaunching HADDOCK...\n####"
    #print "Project name: {}".format("default" if not args.run[1] else args.run[1])
    print "Parameter file: {}".format(args.run[0])
    # if os.path.exists(args.run[0]):
#         with open(args.run[0], 'r') as o:
#             haddockparams = o.read()
#     else:
#         raise Exception("Parameter file not found at: {}".format(args.run[0]))
    haddockparams = args.run[0].read()
    output = interface.launch_project(haddockparams, "" if len(args.run) == 1 else args.run[1])
    print output
else:
    app = HADDOCKCmdLineApp()
    app.cmdloop()
