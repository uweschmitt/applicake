#!/usr/bin/env python
import os
import sys
import subprocess

from ruffus import *


basepath = os.path.dirname(os.path.abspath(__file__)) + '/../../'


def setup():
    if len(sys.argv) > 1 and sys.argv[1] == 'cont':
        print 'Continuing with existing input.ini (Ruffus should skip to the right place automatically)'
    else:
        print 'Starting from scratch by creating new input.ini'
        subprocess.call("rm *ini* *.log", shell=True)
        with open("input.ini", 'w+') as f:
            f.write("""
COMMENT = WFTEST - newUPS LC

WORKFLOW = wf
LOG_LEVEL = DEBUG

BASEDIR = /cluster/project/aebersold/workflows
DATASET_DIR = /cluster/project/aebersold/datasets
DROPBOX = /cluster/project/aebersold/dropbox/generic

EXPERIMENT = E1309101552
DATASET_CODE = 20120320163951515-361883, 20120320163653755-361882, 20120320164249179-361886

FDR_CUTOFF = 0.01
FDR_TYPE = iprophet-pepFDR

MS_TYPE = CID-QTOF
RUNRT = True
RSQ_THRESHOLD = 0.95
RTKIT = /cluster/apps/imsbtools/stable/files/irtkit.txt
CONSENSUS_TYPE = Consensus

TSV_MASS_LIMITS = 400-2000
TSV_ION_LIMITS = 2-6
TSV_PRECISION = 0.05
TSV_CHARGE = 1;2
TSV_REMOVE_DUPLICATES = True
TSV_EXACT = False
TSV_GAIN =
TSV_SERIES =
SWATH_WINDOW_FILE = /cluster/apps/imsbtools/stable/files/swath_wnd_32.txt
""")

def tool_path(tool):
    return os.path.normpath(os.path.join(basepath, tool))

@follows(setup)
@files('input.ini', 'getexperiment.ini')
def getexperiment(infile, outfile):

    subprocess.check_call(['python', tool_path('appliapps/openbis/dss.py'),
                           '--INPUT', infile, '--OUTPUT', outfile, '--EXECUTABLE', 'getexperiment'])
@follows(getexperiment)
@files('getexperiment.ini', 'processexperiment.ini')
def processexperiment(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/openbis/processexperiment.py',
                           '--INPUT', infile, '--OUTPUT', outfile])


################################################################################################

@follows(processexperiment)
@split('processexperiment.ini', "split.ini_*")
def split_dataset(infile, unused_outfile):
    subprocess.check_call(['python', basepath + 'appliapps/flow/split.py',
                           '--INPUT', infile, '--SPLIT', 'split.ini', '--SPLIT_KEY', 'DATASET_CODE'])


@transform(split_dataset, regex("split.ini_"), "dss.ini_")
def dss(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/openbis/dss.py',
                           '--INPUT', infile, '--OUTPUT', outfile, '--EXECUTABLE', 'getmsdata'])


@merge(dss, "mergedataset.ini_0")
def merge_dataset(unused_infile, unused_outfile):
    subprocess.check_call(['python', basepath + 'appliapps/flow/merge.py',
                           '--MERGE', 'dss.ini', '--MERGED', 'mergedataset.ini'])


################################################################################################

@follows(merge_dataset)
@files("mergedataset.ini_0", "rtcalib.ini")
def rtcalib(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/libcreation/spectrastrtcalib.py',
                           '--INPUT', infile, '--OUTPUT', outfile])

#########DONE BY DEFAULT########################

@follows(rtcalib)
@files("rtcalib.ini", "totraml.ini")
def totraml(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/libcreation/spectrast2tsv2traml.py',
                           '--INPUT', infile, '--OUTPUT', outfile])

@follows(totraml)
@files("totraml.ini", "cp2dropbox.ini")
def cp2dropbox(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/libcreation/dropbox.py',
                           '--INPUT', infile, '--OUTPUT', outfile])


pipeline_run([cp2dropbox], multiprocess=3)
