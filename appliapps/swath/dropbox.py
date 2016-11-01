#!/usr/bin/env python
import getpass
import os
import shutil
import subprocess

from applicake.app import BasicApp
from applicake.apputils import dropbox
from applicake.apputils.dirs import makedirs_clean
from applicake.coreutils.arguments import Argument
from applicake.coreutils.info import IniInfoHandler
from applicake.coreutils.keys import Keys, KeyHelp


class Copy2SwathDropbox(BasicApp):
    """
    Copy files to an Openbis generic dropbox.

    """

    def add_args(self):
        return [
            Argument(Keys.ALL_ARGS, KeyHelp.ALL_ARGS),
            Argument(Keys.WORKDIR, KeyHelp.WORKDIR)
        ]

    def run(self, log, info):

        info['WORKFLOW'] = dropbox.extendWorkflowID(info['WORKFLOW'])
        info['WORKFLOW'] += " msproteomicstools@" + subprocess.check_output(
            "git --git-dir=/cluster/apps/imsbtools/stable/msproteomicstools/master/.git rev-parse --short HEAD", shell=True).strip()
        info['WORKFLOW'] += " openms@" + subprocess.check_output(
            "git --git-dir=/cluster/apps/openms/2.0.0-memory/OpenMS/.git rev-parse --short HEAD", shell=True).strip()

        info['DROPBOXSTAGE'] = stagebox = dropbox.make_stagebox(log, info)
        expcode = dropbox.get_experiment_code(info)

        #copy and compress align.csv, but not the matrix REQUEST: expcode in name
        tgt = os.path.join(stagebox, expcode + '_' + os.path.basename(info['ALIGNMENT_TSV']))
        shutil.copy(info['ALIGNMENT_TSV'], tgt)
        subprocess.check_call('gzip ' + stagebox + '/* 2>&1', shell=True)

        tgt = os.path.join(stagebox, expcode + '_' + os.path.basename(info['ALIGNMENT_MATRIX']))
        shutil.copy(info['ALIGNMENT_MATRIX'], tgt)
        dropbox.keys_to_dropbox(log, info, ['ALIGNER_STDOUT'], stagebox)

        #compress all mprophet files into one zip
        archive = os.path.join(stagebox, 'pyprophet_stats.zip')
        if not 'MPROPHET_STATS' in info:
            info['MPROPHET_STATS'] = []
        if not isinstance(info['MPROPHET_STATS'], list):
            info['MPROPHET_STATS'] = [info['MPROPHET_STATS']]
        for entry in info['MPROPHET_STATS']:
            subprocess.check_call('zip -j ' + archive + ' ' + entry + " 2>&1", shell=True)

        #PATCH: reimport old classifier if existing was used
        if 'MPR_LDA_PATH' in info and info['MPR_LDA_PATH'] != "":
            subprocess.check_call('zip -j ' + archive + ' ' + info['MPR_LDA_PATH'] + " 2>&1", shell=True)

        if 'MPR_WT_PATH' in info and info['MPR_WT_PATH'] != "":
            subprocess.check_call('zip -j ' + archive + ' ' + info['MPR_WT_PATH'] + " 2>&1", shell=True)

        #SPACE PROJECT given
        dsinfo = {}
        dsinfo['SPACE'] = info['SPACE']
        dsinfo['PROJECT'] = info['PROJECT']
        dsinfo['PARENT_DATASETS'] = info[Keys.DATASET_CODE]
        if info.get("DB_SOURCE", "") == "PersonalDB":
            if isinstance(dsinfo['PARENT_DATASETS'], list):
                dsinfo['PARENT_DATASETS'].append(info["DBASE"])
            else:
                dsinfo['PARENT_DATASETS'] = [dsinfo['PARENT_DATASETS'], info['DBASE']]

        dsinfo['DATASET_TYPE'] = 'SWATH_RESULT'
        dsinfo['EXPERIMENT_TYPE'] = 'SWATH_SEARCH'
        dsinfo['EXPERIMENT'] = expcode
        path = os.path.join(stagebox, 'dataset.attributes')
        IniInfoHandler().write(dsinfo, path)

        expinfo = {}
        expinfo['PARENT-DATA-SET-CODES'] = dsinfo['PARENT_DATASETS']
        expinfo['ALIGNER_DSCORE_CUTOFF'] = info['MPR_DSCORE_CUTOFF']
        for key in ['WORKFLOW', 'COMMENT',
                    'TRAML', 'EXTRACTION_WINDOW', 'WINDOW_UNIT', 'RT_EXTRACTION_WINDOW',
                    'MIN_UPPER_EDGE_DIST', 'IRTTRAML', 'MIN_RSQ', 'MIN_COVERAGE',
                    'MPR_NUM_XVAL','MPR_LDA_PATH', 'MPR_WT_PATH', 'MPR_FRACT', 'MPR_SSL_IF', 'MPR_SSL_IL', 'MPR_SSL_TF',
                    'MPR_SSL_TL', 'MPR_SSL_NI', 'MPR_MAINVAR', 'MPR_VARS',
                    'ALIGNER_FRACSELECTED', 'ALIGNER_MAX_RT_DIFF', 'ALIGNER_METHOD', 'ALIGNER_FDR',
                    'ALIGNER_MAX_FDRQUAL', 'ALIGNER_TARGETFDR', 'ALIGNER_REALIGN_METHOD', 'DO_CHROMML_REQUANT',
                    'ALGNER_MST_USERTCORR','ALIGNER_MST_STDEVMULT',
                    'ISOTOPIC_GROUPING', 'REQUANT_METHOD',
        ]:
            if info.get(key, "") != "":
                expinfo[key] = info[key]
        path = os.path.join(stagebox, 'experiment.properties')
        IniInfoHandler().write(expinfo, path)

        #put a copy of the whole ini into the dropbox. copy() to prevent OUTPUT being removed from main ini
        IniInfoHandler().write(info.copy(), os.path.join(stagebox, 'input.ini'))

        mailtext = ""
        if info.get("RUNSWATH2VIEWER","") == "true":
            try:
                destdir = "/IMSB/ra/%s/html/tapir/%s" % (getpass.getuser(), dsinfo['EXPERIMENT'])
                makedirs_clean(destdir)
                shutil.copy(info['ALIGNMENT_TSV'],destdir)
                for chrom in info['CHROM_MZML']:
                    shutil.copy(chrom,destdir)
                subprocess.call("gunzip -v %s/*.gz 2>&1" % destdir, shell=True)
                mailtext = "\n\nswath2viewer was enabled. To visualize results use e.g.\n" \
                           "user@crick# /opt/imsb/georger/py26/bin/python " \
                           "/opt/imsb/georger/msproteomicstools/gui/TAPIR.py --in %s/*" % destdir
            except Exception, e:
                log.warn("swath2viewer failed! " + e.message)

        #create witolds SWATH report mail
        reportcmd = 'mailSWATH.sh "%s" "%s" "%s" 2>&1' % (info['ALIGNMENT_TSV'], info['COMMENT'], mailtext)
        if Keys.MODULE in info:
            reportcmd = 'module load %s && %s'%(info[Keys.MODULE],reportcmd)
        try:
            subprocess.call(reportcmd, shell=True)
            shutil.copy('analyseSWATH.pdf', stagebox)
        except:
            log.warn("SWATH report command [%s] failed, skipping" % reportcmd)

        dropbox.move_stage_to_dropbox(log, stagebox, info['DROPBOX'], keepCopy=False)

        return info


if __name__ == "__main__":
    Copy2SwathDropbox.main()
