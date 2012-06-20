#!/usr/bin/env python
'''
Created on Jun 5, 2012

@author: quandtan
'''

import os
import sys
from ruffus import *
from cStringIO import StringIO
from subprocess import Popen
from subprocess import PIPE
from applicake.framework.runner import GeneratorRunner, ApplicationRunner
from applicake.framework.runner import CollectorRunner
from applicake.framework.runner import WrapperRunner
from applicake.applications.proteomics.openbis.generator import GuseGenerator
from applicake.applications.os.echo import Echo
from applicake.applications.commons.collector import GuseCollector
from applicake.applications.proteomics.searchengine.xtandem import Xtandem
from applicake.applications.proteomics.openbis.dss import Dss
from applicake.applications.proteomics.tpp.tandem2xml import Tandem2Xml
from applicake.applications.proteomics.tpp.xinteract import Xinteract
from applicake.applications.proteomics.tpp.interprophet import InterProphet
from applicake.applications.proteomics.openms.filehandling.idfileconverter import PepXml2IdXml
from applicake.applications.proteomics.openms.peptideproteinprocessing.falsediscoveryrate import FalseDiscoveryRate
from applicake.applications.proteomics.openms.peptideproteinprocessing.peptideindexer import PeptideIndexer
from applicake.applications.proteomics.openms.peptideproteinprocessing.idfilter import IdFilter
from applicake.applications.proteomics.openms.filehandling.fileconverter import MzXml2MzMl
from applicake.applications.proteomics.openms.signalprocessing.peakpickerhighres import PeakPickerHighRes
from applicake.applications.proteomics.openms.quantification.featurefindercentroided import OrbiLessStrict
from applicake.applications.proteomics.sybit.pepxml2csv import Pepxml2Csv
from applicake.applications.proteomics.sybit.fdr2probability import Fdr2Probability
from applicake.applications.proteomics.tpp.proteinprophet import ProteinProphet
from applicake.applications.proteomics.sybit.protxml2spectralcount import ProtXml2SpectralCount
from applicake.applications.proteomics.sybit.protxml2modifications import ProtXml2Modifications
from applicake.applications.proteomics.sybit.protxml2openbis import ProtXml2Openbis
from applicake.applications.proteomics.openbis.dropbox import Copy2Dropbox
from applicake.applications.commons.inifile import Unifier
from applicake.framework.interfaces import IApplication, IWrapper

cwd = None


#helper function
def wrap(applic,  input_file_name, output_file_name,opts=None):
    argv = ['', '-i', input_file_name, '-o', output_file_name]
    if opts is not None:
        argv.extend(opts)
    application = applic()
    if isinstance(application, IApplication):
        runner = ApplicationRunner()
        print 'use application runner'
    elif isinstance(application, IWrapper):
        runner = WrapperRunner()
    else:
        raise Exception('could not identfy [%s]' % applic.__name__)    
    application = applic()
    exit_code = runner(argv, application)
    if exit_code != 0:
        raise Exception("[%s] failed [%s]" % (applic.__name__, exit_code)) 

def execute(command):
    p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)            
    output, error = p.communicate()                                                                                                                                                                            
    out_stream = StringIO(output)
    err_stream = StringIO(error) 


def setup():
    cwd = '.'
    os.chdir(cwd)
    execute("find . -type d -iname '[0-9]*' -exec rm -rf {} \;")
    execute('rm *.err')
    execute('rm *.out')
    execute('rm *.log')
    execute('rm *ini*')
#    execute('rm jobid.txt') 
    execute('rm flowchart.*')    
    with open("input.ini", 'w+') as f:
        f.write("""BASEDIR = /cluster/scratch/malars/workflows
LOG_LEVEL = DEBUG
STORAGE = file
TEMPLATE = template.tpl
DATASET_DIR = /cluster/scratch/malars/datasets
DATASET_CODE = 20120124102254267-296925,20120124121656335-296961
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
XINTERACT_ARGS = -dDECOY_ -OAPdlIw
IPROPHET_ARGS = MINPROB=0
FDR=0.01
""" 
#,20120603165413998-510432,
# 20120606045538225-517638 -> b10-01219.p.mzxml
# 20120603160111752-510155 -> b10-01219.c.mzxml 
# 20120124102254267-296925,20120124121656335-296961 -> orbi silac hela from petri
)       
        

@follows(setup)
@split("input.ini", "generate.ini_*")
def generator(input_file_name, notused_output_file_names):
    argv = ['', '-i', input_file_name, '--GENERATORS', 'generate.ini','-o','generator.ini','-l','DEBUG']
    runner = GeneratorRunner()
    application = GuseGenerator()
    exit_code = runner(argv, application)
    if exit_code != 0:
        raise Exception("generator failed [%s]" % exit_code) 
    
@transform(generator, regex("generate.ini_"), "dss.ini_")
def dss(input_file_name, output_file_name):   
    wrap(Dss,input_file_name, output_file_name,['--PREFIX', 'getmsdata'])

    
@transform(dss, regex("dss.ini_"), "xtandem.ini_")
def tandem(input_file_name, output_file_name):
    wrap(Xtandem,input_file_name, output_file_name,['--PREFIX', 'tandem.exe','-s','file','-l','DEBUG'])

@transform(tandem, regex("xtandem.ini_"), "xtandem2xml.ini_")
def tandem2xml(input_file_name, output_file_name):
    wrap(Tandem2Xml,input_file_name, output_file_name)  

@transform(tandem2xml, regex("xtandem2xml.ini_"), "xinteract.ini_")
def xinteract(input_file_name, output_file_name):
    wrap(Xinteract,input_file_name, output_file_name)   

    
@merge(xinteract, "collector.ini")
def collector(notused_input_file_names, output_file_name):
    argv = ['', '--COLLECTORS', 'xinteract.ini', '-o', output_file_name,'-s','file']
    runner = CollectorRunner()
    application = GuseCollector()
    exit_code = runner(argv, application)
    if exit_code != 0:
        raise Exception("[%s] failed [%s]" % ('collector',exit_code))    


@follows(collector)
def unifier():
    wrap(Unifier,'collector.ini','unifier.ini',['--UNIFIER_REDUCE'])   

@follows(unifier)
def interprophet():
    wrap(InterProphet,'unifier.ini','interprophet.ini',['-p'])    

@follows(interprophet)
def pepxml2csv():
    wrap(Pepxml2Csv,'interprophet.ini','pepxml2csv.ini')   
    
@follows(pepxml2csv)
def fdr2probability():
    wrap(Fdr2Probability,'pepxml2csv.ini','fdr2probability.ini')         

@follows(fdr2probability)
def proteinprophet():
    wrap(ProteinProphet,'fdr2probability.ini','proteinprophet.ini') 

@follows(proteinprophet)
def protxml2spectralcount():
    wrap(ProtXml2SpectralCount,'proteinprophet.ini','protxml2spectralcount.ini') 

@follows(protxml2spectralcount)
def protxml2modifications():
    wrap(ProtXml2Modifications,'protxml2spectralcount.ini','protxml2modifications.ini') 

@follows(protxml2modifications)
def protxml2openbis():
    wrap(ProtXml2Openbis,'protxml2modifications.ini','protxml2openbis.ini') 

@follows(protxml2openbis)
def copy2dropbox():
    wrap(Copy2Dropbox,'protxml2openbis.ini','copy2dropbox') 

#@follows()
#def ():
#    wrap(,'','') 
#    @follows()
#def ():
#    wrap(,'','') 
#    @follows()
#def ():
#    wrap(,'','')     


@transform(interprophet,regex('interprophet.ini'),'pepxml2idxml.ini')
def pepxml2idxml(input_file_name, output_file_name):
    argv = ['', '-i', input_file_name, '-o', output_file_name]
    runner = WrapperRunner()
    application = PepXml2IdXml()
    exit_code = runner(argv, application)
    if exit_code != 0:
        raise Exception("[%s] failed [%s]" % ('pepxml2idxml',exit_code)) 

@transform(pepxml2idxml,regex('pepxml2idxml.ini'),'peptideindexer.ini')
def peptideindexer(input_file_name, output_file_name):
    argv = ['', '-i', input_file_name, '-o', output_file_name]
    runner = WrapperRunner()
    application = PeptideIndexer()
    exit_code = runner(argv, application)
    if exit_code != 0:
        raise Exception("[%s] failed [%s]" % ('peptideindexer',exit_code))

@transform(peptideindexer,regex('peptideindexer.ini'),'fdr.ini')
def fdr(input_file_name, output_file_name):
    argv = ['', '-i', input_file_name, '-o', output_file_name]
    runner = WrapperRunner()
    application = FalseDiscoveryRate()
    exit_code = runner(argv, application)
    if exit_code != 0:
        raise Exception("[%s] failed [%s]" % ('fdr',exit_code)) 
    
@transform(fdr,regex('fdr.ini'),'idfilter.ini')
def idfilter(input_file_name, output_file_name):
    argv = ['', '-i', input_file_name, '-o', output_file_name]
    runner = WrapperRunner()
    application = IdFilter()
    exit_code = runner(argv, application)
    if exit_code != 0:
        raise Exception("[%s] failed [%s]" % ('idfilter',exit_code)) 
    
@transform(idfilter,regex('idfilter.ini'),'mzxml2mzml.ini')
def mzxml2mzml(input_file_name, output_file_name):
    argv = ['', '-i', input_file_name, '-o', output_file_name]
    runner = WrapperRunner()
    application = MzXml2MzMl()
    exit_code = runner(argv, application)
    if exit_code != 0:
        raise Exception("[%s] failed [%s]" % ('mzxml2mzml',exit_code)) 

@transform(mzxml2mzml,regex('mzxml2mzml.ini'),'peakpickerhighres.ini')
def peakpickerhighres(input_file_name, output_file_name):
    argv = ['', '-i', input_file_name, '-o', output_file_name,'--SIGNAL_TO_NOISE','1']
    runner = WrapperRunner()
    application = PeakPickerHighRes()
    exit_code = runner(argv, application)
    if exit_code != 0:
        raise Exception("[%s] failed [%s]" % ('peakpickerhighres',exit_code)) 
         
@transform(peakpickerhighres,regex('peakpickerhighres.ini'),'featurefindercentroided.ini')
def featurefindercentroided(input_file_name, output_file_name):
    argv = ['', '-i', input_file_name, '-o', output_file_name]
    runner = WrapperRunner()
#    application = FeatureFinderCentroided()
    application = OrbiLessStrict()
    exit_code = runner(argv, application)
    if exit_code != 0:
        raise Exception("[%s] failed [%s]" % ('featurefindercentroided',exit_code)) 
         

pipeline_run([protxml2openbis])
#pipeline_run([featurefindercentroided])


#pipeline_printout_graph ('flowchart.png','png',[collector],no_key_legend = False) #svg
