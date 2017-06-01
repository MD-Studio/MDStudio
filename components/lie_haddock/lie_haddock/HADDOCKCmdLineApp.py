"""
Create a console-like environment to interact with HADDOCK-XMLRPC endpoint

Author: {0} ({1})
"""
from xmlrpclib import Fault

from HADDOCKInterface import HADDOCKInterface
from cmd2 import Cmd, options, make_option
from urllib2 import urlopen
import os
import inspect

__author__ = "Mikael Trellet"
__email__ = "mikael.trellet@gmail.com"


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class HADDOCKCmdLineApp(Cmd):

    intro = "\n#### HADDOCK interface for XMLRPC API ####\n"
    intro += "\nTo list available commands, type `help`\n"
    prompt = "(HADDOCK) > "
    default_to_shell = True

    def __init__(self):
        Cmd.__init__(self)
        self.interface = HADDOCKInterface()

    def do_help_haddock(self, arg=None):
        """ Return a list of available commands and the associated documentation """
        for method in inspect.getmembers(HADDOCKCmdLineApp, predicate=inspect.ismethod):
            if method[0].startswith("do_"):
                print method[0].strip("do_")

    def do_login(self, arg=None):
        """ Login with HADDOCK username and password """
        if not self.interface.authenticated:
            try:
                self.interface.login()
                print bcolors.OKGREEN + "Login successful" + bcolors.ENDC
            except Fault as e:
                print bcolors.FAIL+"User name or password not correct or not known"+bcolors.ENDC
                return
        self.prompt = "("+bcolors.OKBLUE+self.interface.usr+bcolors.ENDC+"@HADDOCK) > "

    def do_logout(self, arg=None):
        """ Logout """
        self.interface.logout()
        self.prompt = "(HADDOCK) > "
        print bcolors.OKGREEN+"You've been logged out successfully"+bcolors.ENDC

    def do_whoami(self, arg=None):
        """ Print credentials if user connected """
        if not self.interface.authenticated:
            print "You are currently not logged in, please type login to do so."
        else:
            print 'You are currently connected as "{}"'.format(self.interface.usr)

    def do_list_users(self, arg=None):
        """List HADDOCK users """
        try:
            users = self.interface.list_users()
            self.do_login()
        except:
            raise
        for usr in users:
            print usr[0], usr[-2]

    @options([make_option('-c', '--column', action="store_true", help="Output projects as 2 distinct columns"),
              make_option('-s', '--status', action="store_true", help="Get projects' status as well")])
    def do_list_projects(self, arg, opts):
        """ List HADDOCK projects """
        try:
            projects = self.interface.list_projects()
            self.do_login()
        except Fault as e:
            if int(e.faultCode) == 1:
                self.do_logout()
            print bcolors.FAIL + e.faultString + bcolors.ENDC
            return
        except:
            raise
        if opts.column and opts.status:
            print bcolors.WARNING+"Column type output is not available with status mode ON."+bcolors.ENDC
        if opts.column and not opts.status:
            max_width = len(max(projects, key=len))
            projects_div = [projects[i:i + 2] for i in xrange(0, len(projects), 2)]
            for projs in projects_div:
                print(''.join('{: <{max_width}} | '.format(x, max_width=max_width) for x in projs))
        elif opts.status:
            status_all = []
            for proj in projects:
                try:
                    status = self.interface.get_status(proj)
                except Fault as e:
                    print bcolors.FAIL + e.faultString + bcolors.ENDC
                if status.upper() == 'DONE':
                    print proj+" ["+bcolors.OKGREEN+status.upper()+bcolors.ENDC+"]"
                elif status.upper() == 'ERROR':
                    print proj+" ["+bcolors.FAIL+status.upper()+bcolors.ENDC+"]"
                elif status.upper() == 'PROCESSING':
                    print proj+" ["+bcolors.WARNING+status.upper()+bcolors.ENDC+"]"
                else:
                	print proj+" ["+bcolors.WARNING+status.upper()+bcolors.ENDC+"]"
        else:
            for proj in projects:
                print proj

    def do_status(self, project, arg=None):
        """ Get current status of an HADDOCK project """
        try:
            status = self.interface.get_status(str(project))
            self.do_login()
        except Fault as e:
            if int(e.faultCode) == 1:
                self.do_logout()
            print bcolors.FAIL + e.faultString + bcolors.ENDC
            return
        except:
            raise
        print "Status: {}".format(status.upper())

    def do_url(self, project, arg=None):
        """ Get URL of a finished HADDOCK project """
        try:
            url = self.interface.get_url(str(project))
            self.do_login()
        except Fault as e:
            if int(e.faultCode) == 1:
                self.do_logout()
            print bcolors.FAIL + e.faultString + bcolors.ENDC
            return
        except:
            raise
        print "URL: {}".format(url)

    @options([make_option('-o', '--output', help="Destination path (/path/to/file.tgz or /path/to/directory/).")])
    def do_download(self, project, opts=None):
        """ Download tar archive of an HADDOCK project """
        try:
            url = self.interface.get_url(str(project))
            self.do_login()
        except Fault as e:
            if int(e.faultCode) == 1:
                self.do_logout()
            print bcolors.FAIL + e.faultString + bcolors.ENDC
            return
        file_name = url.split('/')[-1]
        u = urlopen(url)
        extension = os.path.splitext(file_name)[1]
        if not opts.output:
            output = os.path.join(os.curdir, file_name)
            f = open(output, 'wb')
        else:
            if os.path.isdir(opts.output):
                output = os.path.join(opts.output, file_name)
                f = open(output, 'wb')
            elif extension == os.path.splitext(opts.output):
                output = opts.output
                f = open(output, 'wb')
            elif not os.path.isdir(opts.output):
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

    @options([make_option('-o', '--output', help="Destination path (/path/to/haddockparam.web or /path/to/directory/).")])
    def do_params(self, project, opts=None):
        """ Download haddockparam.web file for a specific project """
        try:
            haddockparams = self.interface.get_params(project)
            self.do_login()
        except Fault as e:
            if int(e.faultCode) == 1:
                self.do_logout()
            raise
        if not opts.output:
            output = os.path.join(os.curdir, 'haddockparam.web')
            f = open('haddockparam.web', 'wb')
        else:
            if os.path.isdir(opts.output):
                output = os.path.join(opts.output, 'haddockparam.web')
                f = open(output, 'wb')
            elif opts.output.split('/')[-1] == "haddockparam.web":
                output = opts.output
                f = open(output, 'wb')
            else:
                raise Exception("File or directory path does not exist, aborting...")
        f.write(haddockparams)
        f.close()
        print "Parameters saved in: {}".format(output)

    @options([make_option('-n', '--name', help="Project name")])
    def do_launch_project(self, params, project=""):
        """ Launch an HADDOCK project from an haddockparam.web """
        print "####\nLaunching HADDOCK...\n####"
        print "Project name: {}".format("default" if not project.name else project.name)
        print "Parameter file: {}".format(params)
        if os.path.exists(params):
            with open(params, 'r') as o:
                haddockparams = o.read()
        else:
            raise Exception("Parameter file not found at: {}".format(params))
        try:
            output = self.interface.launch_project(haddockparams, "" if not project.name else project.name)
        except Fault as e:
            if int(e.faultCode) == 1:
                self.do_logout()
            else:
                self.do_login()
            print bcolors.FAIL + e.faultString + bcolors.ENDC
            return
        print output
