#!/usr/bin/env python
'''
Created on Aug 17, 2012

@author: blum, quandtan
'''

import subprocess
from ruffus import *
from applicake.utils.drmaautils import DrmaaSubmitter

    
def setup():
    subprocess.call("rm lsf.* *ini*",shell=True)
    with open("input.ini", 'w+') as f:
        f.write("""
BASEDIR = /cluster/scratch/malars/workflows
LOG_LEVEL = DEBUG
STORAGE = file
COMMENT = ruffus with LSF through drmaa

DATASET_DIR = /cluster/scratch/malars/datasets
DATASET_CODE = 20110721073234274-201170, 20110721054532782-201128, 20110721034730308-201103
DBASE = /cluster/scratch/malars/biodb/ex_sp/current/decoy/ex_sp_9606.fasta

DECOY_STRING = DECOY_ 
FRAGMASSERR = 0.4
FRAGMASSUNIT = Da
PRECMASSERR = 15
PRECMASSUNIT = ppm
MISSEDCLEAVAGE = 0
ENZYME = Trypsin
STATIC_MODS = Carbamidomethyl (C)
THREADS = 4
XTANDEM_SCORE = k-score
IPROPHET_ARGS = MINPROB=0
FDR=0.01
SPACE = LOBLUM
PROJECT = TEST
DROPBOX = /cluster/scratch/malars/drop-box_prot_ident
WORKFLOW = ruffus_drmaa_xtandem
""" )

@follows(setup)
@split("input.ini", "generate.ini_*")
def generator(input_file_name, notused_output_file_names):
    submitter.run('run_guse_generator.py',['-i', input_file_name, '--GENERATORS', 'generate.ini'],lsfargs)
    
    
@transform(generator, regex("generate.ini_"), "dss.ini_")
def dss(input_file_name, output_file_name):   
    submitter.run('run_dss.py', ['-i',  input_file_name,'-o', output_file_name,'--PREFIX', 'getmsdata'],lsfargs)

@transform(dss, regex("dss.ini_"), "xtandem.ini_")
def tandem(input_file_name, output_file_name):
    submitter.run('run_xtandem.py', ['-i',  input_file_name,'-o', output_file_name,'--PREFIX', 'tandem.exe'],lsfargs)

@transform(tandem, regex("xtandem.ini_"), "xtandem2xml.ini_")
def tandem2xml(input_file_name, output_file_name):
    submitter.run('run_tandem2xml.py', ['-i',  input_file_name,'-o', output_file_name],lsfargs)  

@transform(tandem2xml, regex("xtandem2xml.ini_"), "interactparser.ini_")
def interactparser(input_file_name, output_file_name):
    submitter.run('run_interactparser.py', ['-i',  input_file_name,'-o', output_file_name],lsfargs)

@transform(interactparser, regex("interactparser.ini_"), "refreshparser.ini_")
def refreshparser(input_file_name, output_file_name):
    submitter.run('run_refreshparser.py', ['-i',  input_file_name,'-o', output_file_name],lsfargs)

@transform(refreshparser, regex("refreshparser.ini_"), "peptideprophet.ini_")
def peptideprophet(input_file_name, output_file_name):
    submitter.run('run_peptideprophet.py', ['-i',  input_file_name,'-o', output_file_name],lsfargs)
    
@merge(xinteract, "collector.ini")
def collector(notused_input_file_names, output_file_name):
    submitter.run('run_guse_collector.py', ['--COLLECTORS', 'xinteract.ini' ,'-o', output_file_name],lsfargs)    

@follows(collector)
def unifier():
    submitter.run('run_unify.py', ['-i', 'collector.ini','-o', 'unifier.ini' , '--UNIFIER_REDUCE'],lsfargs)  

        
### MAIN ###
lsfargs = '-q vip.1h -R lustre' 
submitter = DrmaaSubmitter()
pipeline_run([unifier], multiprocess=5)
