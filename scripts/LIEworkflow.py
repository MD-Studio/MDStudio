import sys
import os
import json
import time

from   OpenSSL                     import crypto
from   autobahn.twisted.wamp       import ApplicationRunner
from   autobahn.twisted.util       import sleep
from   twisted.internet.defer      import inlineCallbacks, returnValue, Deferred
from   twisted.internet._sslverify import OpenSSLCertificateAuthorities
from   twisted.internet.ssl        import CertificateOptions

from   lie_graph.io.io_json_format import read_json, write_json
from   lie_corelib                  import BaseAppliationSession, WAMPTaskMetaData
from   lie_workflow                import WorkflowSpec

class LIEWorkflow(BaseAppliationSession):
    
    """
    This script will perform a binding affinity calculation using the 
    Linear Interaction Energy (LIE) workflow in a manner as described in:
    
    - citation
    """
    
    @inlineCallbacks
    def task(self, task_data, callback=None, *args, **kwargs):
        """
        Run a task based on the information in the task_data.
        Task_data is validated accoridng to the JSON task schema
        """
        
        # Retrieve the WAMP session information
        session = task_data.get('session')
        if session:
            session = WAMPTaskMetaData(metadata=task_data.get('session'))
            session._metadata['itime'] = int(time.time())
        else:
            session = self.session_config
        
        # Prepaire the input to the task
        inp = task_data.get('input')
        
        # Get the task configuration
        conf = task_data.get('configuration', {})
        session._update_time(time_stamp='utime')
        
        # Call the service
        deferred = yield self.call(task_data['uri'], *inp.values(), session=session.dict(), **conf)
        
        # Attach callback if needed
        if callback:
            deffered.addCallback(callback)
        else:        
            # Prepaire the output
            task_data['output'] = {session['task_id']: deferred['result']}
            task_data.update(deferred['session'])
        
            returnValue(task_data)
    
    @inlineCallbacks
    def onRun(self, details):
        
        # Load LIE workflow spec
        workflow = read_json('lie_workflow_spec.json')
        self.wf = WorkflowSpec(workflow=workflow)
        self.wf.task_runner = self
        
        # Update metadata
        self.wf.workflow.nodes[self.wf.workflow.root].update(self.session_config())
        
        # Run the workflow
        self.wf.workflow.nodes[1]['active'] = True
        self.wf.next()
        
        # Non blocking sleep until workflow is completed
        maxitr = 5
        while not self.wf.is_completed and maxitr > 0:
            yield sleep(1)       
            maxitr -= 1
        
        with open('project.json','w') as pf:
            pf.write(write_json(self.wf.workflow))
        
        print('LEAVING')
        return
        
        # Create project
        project = {}
        
        # Get protein structure from structure database
        protein = yield self.task(u'liestudio.structures.get_structure', 'protein')
        project['protein'] = protein
        print(protein)
        self.leave()
        return
        
        
        # Get ligands from the structure database
        lig_cids = {'cid001': None, 'cid002': None, 'cid003': None, 'cid004': None, 'cid005': None}
        self.logger.info('Dock {0} structures'.format(len(lig_cids)))
        for ligand in lig_cids:
            lig = yield self.task(u'liestudio.structures.get_structure', ligand)
            lig_cids[ligand] = lig
        project['ligands'] = lig_cids
        
        # Perform a docking for a number of ligands from the structure database
        docked = {}
        for ligid, ligand in project['ligands'].items():
            docked[ligid] = self.task(u'liestudio.plants_docking.run_docking', project['protein']['result'], ligand['result'],
                workdir='/Users/mvdijk/Documents/WorkProjects/liestudio-master/liestudio/tmp',
                bindingsite_center=[7.79934,9.49666,3.39229])
        
        # Check the ATB server for ligand topologies
        atb = {}
        for ligid, ligand in project['ligands'].items():
            atb[ligid] = self.task(u'liestudio.atb.structure_query', ligand['result'], structure_format='mol2')
        
        # Resolve docking results
        project['docked'] = {}
        for lig_dock in docked:
            project['docked'][lig_dock] = yield docked[lig_dock]
        
        # Resolve ATB query
        project['topol'] = {}
        for atbq in atb:
            f = yield atb[atbq]
            for query_result in f['result']:
                if query_result.get('is_identical',False):
                    self.logger.info('Exact ATB match found for {0}, molid: {1}'.format(atbq, query_result.get('molid')))
                    topol = yield self.task(u'liestudio.atb.get_topology', query_result.get('molid'))
                    
        outfile = open('project.json','w')
        json.dump(project, outfile, indent=4)
        
        self.leave()
        self.disconnect()
        return
        

if __name__ == '__main__':
    
    # load the self-signed cert the server is using
    certpath = os.path.join(os.path.dirname(__file__), '../data/crossbar/server_cert.pem')
    cert = crypto.load_certificate(crypto.FILETYPE_PEM, open(certpath, 'r').read())
    
    # tell Twisted to use just the one certificate we loaded to verify connections
    options = CertificateOptions(trustRoot=OpenSSLCertificateAuthorities([cert]))
        
    runner = ApplicationRunner(
        u"ws://localhost:8080/ws",
        u"liestudio",
        extra={'authid':u'lieadmin', 'password':u'liepw@#', 'authmethod':u'ticket'},
        #ssl=options
    )
    runner.run(LIEWorkflow, auto_reconnect=False)
    