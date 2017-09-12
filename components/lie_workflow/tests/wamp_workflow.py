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
from   lie_system                  import LieApplicationSession, WAMPTaskMetaData

from   lie_workflow                import Workflow

class LIEWorkflow(LieApplicationSession):
    
    """
    This script will perform a binding affinity calculation using the 
    Linear Interaction Energy (LIE) workflow in a manner as described in:
    
    - citation
    """
    
    @inlineCallbacks
    def onRun(self, details):
        
        workdir = '/Users/mvdijk/Documents/WorkProjects/liestudio-master/lieproject'
        
        # Build Workflow
        wf = Workflow()
        
        # Load workflow if present else, build one
        workflow_file = os.path.join(workdir, 'workflow.json')
        if os.path.isfile(workflow_file):
            wf.load(workflow_file)
            wf.task_runner = self.call
            wf.set_wamp_session(session_data={'authid': self.session_config.authid})
        
        else:
            wf.task_runner = self.call
            wf.set_wamp_session(session_data={'authid': self.session_config.authid})
            
            # Set some workflow metadata in the start node
            project_dir = os.path.join(workdir, str(int(time.time())))
            start = wf.get_task(1)
            start.set('workdir', project_dir)
        
            # Get the protein structure from the DB
            t1 = wf.add_task('Get structure', task_type='WampTask', uri='liestudio.structures.get_structure')
            wf.input(tid=t1, structure='protein.mol2')
            wf.connect_task(1, t1)
            
            # Convert protein mol2 tot PDB
            t2 = wf.add_task('Protein mol2 tot PDB', task_type='WampTask', uri='liestudio.structure.convert')
            wf.input(tid=t2, input_format='mol2', output_format='pdb')
            wf.connect_task(t1, t2, data_mapping={'structure':'mol'})
        
            # Define ligand as SMILES string and convert to mol2
            t3 = wf.add_task('Format conversion', task_type='WampTask', uri='liestudio.structure.convert')
            wf.input(tid=t3, input_format='smi', output_format='mol2', mol='CCCC(CCC)=C(c1ccc(cc1)C#N)n1ccnc1')
            wf.connect_task(1, t3)
        
            # Covert 1D mol2 to 3D mol2
            t4 = wf.add_task('Make 3D', task_type='WampTask', uri='liestudio.structure.make3d')
            wf.input(tid=t4, input_format='mol2')
            wf.connect_task(t3, t4)
        
            # Adjust ligand protonation state to a given pH if applicable
            t5 = wf.add_task('Add hydrogens', task_type='WampTask', uri='liestudio.structure.addh')
            wf.input(tid=t5, input_format='mol2', correctForPH=True, pH=7.4)
            wf.connect_task(t4, t5)
            
            # Run acpype on ligands
            t6 = wf.add_task('ACPYPE', task_type='WampTask', uri='liestudio.amber.acpype', store_output=True, retry_count=3)
            wf.connect_task(t5, t6, data_mapping={'mol':'structure'})

            # Combine data protein and ligand structures
            t7 = wf.add_task('combine', task_type='Collect', custom_func='wamp_workflow_helpers.combine_for_docking')
            wf.connect_task(t1, t7, data_mapping={'structure':'protein_file'})
            wf.connect_task(t5, t7, data_mapping={'mol':'ligand_file'})
        
            # Run PLANTS on ligand and protein (in parallel to acpype)
            t8 = wf.add_task('Plants docking', task_type='WampTask', uri='liestudio.plants_docking.run_docking', store_output=True)
            wf.input(t8, bindingsite_center=[7.79934,9.49666,3.39229])
            wf.connect_task(t7, t8)
        
            # Get cluster median structures from docking
            t9 = wf.add_task('Get cluster medians', task_type='Task', custom_func='wamp_workflow_helpers.get_docking_medians')
            wf.connect_task(t8, t9)
            
            # Combine results from docking, acpype and protein input structure
            t10 = wf.add_task('Collect results for MD', task_type='Collect', custom_func='wamp_workflow_helpers.prepaire_for_md')
            wf.connect_task(t2, t10, data_mapping={'mol':'protein_file'})
            wf.connect_task(t6, t10, data_mapping={'path':'topology_file'})
            wf.connect_task(t9, t10, data_mapping={'medians': 'ligand_file'})
            
            # Map the ligand structures
            t11 = wf.add_task('Ligand mapper', task_type='Mapper')
            wf.connect_task(t10, t11)
            
            # Run MD
            t12 = wf.add_task('MD on protein-ligand system', task_type='WampTask', uri='liestudio.gromacs.liemd', store_output=True)
            wf.connect_task(t11, t12)
        
        # Run the workflow
        wf.run()
        while wf.is_running:
            yield sleep(1)

        # Save the workflow to file
        project_dir = wf.get_task(1)['workdir']
        wf.save(path=os.path.join(project_dir, 'workflow.json'))

        self.leave()
        self.disconnect()
        return
        

if __name__ == '__main__':
    
    # load the self-signed cert the server is using
    #certpath = os.path.join(os.path.dirname(__file__), '../data/crossbar/server_cert.pem')
    #cert = crypto.load_certificate(crypto.FILETYPE_PEM, open(certpath, 'r').read())
    
    # tell Twisted to use just the one certificate we loaded to verify connections
    #options = CertificateOptions(trustRoot=OpenSSLCertificateAuthorities([cert]))
        
    runner = ApplicationRunner(
        u"ws://localhost:8080/ws",
        u"liestudio",
        extra={'authid':u'lieadmin', 'password':u'liepw@#', 'authmethod':u'ticket'},
        #ssl=options
    )
    runner.run(LIEWorkflow, auto_reconnect=False)
    