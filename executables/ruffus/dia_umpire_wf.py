#!/usr/bin/env python
import os
import sys
import subprocess

from ruffus import *



basepath = os.path.dirname(os.path.abspath(__file__)) + '/../../'
print(basepath)


def setup():
    if len(sys.argv) > 1 and sys.argv[1] == 'cont':
        print 'Continuing with existing input.ini (Ruffus should skip to the right place automatically)'
    else:
        print 'Starting from scratch by creating new input.ini'
        try: subprocess.call("rm *ini* *.log", shell=True)
        except: pass
        with open("input.ini", 'w') as f:
            f.write("""
DATASET_CODE = 20151221172246046-1129816
PARAMETERSETFILE =

WORKFLOW = DIA_UMPIRE_WITH_MERGE
LOG_LEVEL = DEBUG

BASEDIR = /cluster/project/aebersold/workflows
DATASET_DIR = /cluster/project/aebersold/datasets
DROPBOX = /cluster/project/aebersold/dropbox/generic

TMPDIR = /scratch
""")


@follows(setup)
@files("input.ini", "output_job_id.ini")
def job_id(infile, outfile):
    subprocess.check_call(['scripts/job_id.sh'])
    os.rename("output.ini", "output_job_id.ini")


@follows(job_id)
@split("output_job_id.ini", "split.ini_*")
def split_dataset(infile, unused_outfile):
    subprocess.check_call(['python', basepath + 'appliapps/flow/split.py',
                           '--INPUT', infile, '--SPLIT', 'split.ini', '--SPLIT_KEY', 'DATASET_CODE'])


@transform(split_dataset, regex("split.ini_"), "dss.ini_")
def dss(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/openbis/dss.py',
                           '--INPUT', infile, '--OUTPUT', outfile, '--EXECUTABLE', 'getdataset'])


@transform(dss, regex("dss.ini_"), "dia_umpire.ini_")
def dia_umpire(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/dia_umpire/dia_umpire.py',
                           '--INPUT', infile, '--OUTPUT', outfile])


#@files("mergedataset.ini_0", "cp2dropbox.ini")
@transform(dia_umpire, regex("dia_umpire.ini_"), "cp2dropbox.ini_")
def cp2dropbox(infile, outfile):
    subprocess.check_call(['python', basepath + 'appliapps/dia_umpire/dropbox.py',
                           '--INPUT', infile, '--OUTPUT', outfile])



pipeline_run([cp2dropbox], multiprocess=3, verbose=2)
