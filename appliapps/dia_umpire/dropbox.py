#!/usr/bin/env python

import itertools
import os
import shutil
import subprocess

from applicake.app import BasicApp
from applicake.apputils import dropbox, dirs
from applicake.coreutils.arguments import Argument
from applicake.coreutils.info import IniInfoHandler
from applicake.coreutils.keys import Keys, KeyHelp


class Copy2Dropbox(BasicApp):
    def add_args(self):
        return [
            Argument(Keys.ALL_ARGS, KeyHelp.ALL_ARGS),
            Argument(Keys.WORKDIR, KeyHelp.WORKDIR)
        ]

    def run(self, log, info):
        info['WORKFLOW'] = dropbox.extendWorkflowID(info.get('WORKFLOW',"wff"))
        dia_umpire_version = subprocess.check_output("dia-umpire-version.sh").strip()
        info['WORKFLOW'] += " dia-umpire@" + dia_umpire_version

        workdir = info[Keys.WORKDIR]
        sub_job = int(info["SUBJOBLIST"][0].split("|")[1])

        sample = info['SAMPLE']
        job_id = info['JOB_ID']
        for i, q_file, md5 in zip(itertools.count(), info["Q_FILES"], info["MD5_SUMS"]):
            # info['DROPBOXSTAGE'] = stagebox = dropbox.make_stagebox(log, info)
            stagebox = os.path.join(workdir, "dia_umpire_%s_%d_q_%s" % (job_id, sub_job, i + 1))
            dirs.makedirs_clean(stagebox)
            log.info("made stagebox at %s" % stagebox)

            shutil.copy(q_file, stagebox)

            param_file = info["USED_PARAMETER_FILE"]
            shutil.copy(param_file, stagebox)

            ds_attrs = {}
            ds_attrs['SPACE'] = 'MS_DATA'
            ds_attrs['SAMPLE'] = sample
            ds_attrs['DATASET_TYPE'] = "MZXML_DATA"
            ds_attrs['FILE_TYPE'] = "MZXML"
            ds_attrs['PARENT_DATASETS'] = info['DATASET_CODE']
            path = os.path.join(stagebox, 'dataset.attributes')
            IniInfoHandler().write(ds_attrs, path)
            log.info("wrote %s" % path)

            ds_props = {}
            ds_props['FILE_SIZE'] = os.stat(q_file).st_size
            ds_props['CONVERSION_SOFTWARE'] = "dia umpire %s" % dia_umpire_version
            ds_props['CENTROIDED'] = True
            ds_props['DATA_SET_TYPE'] = "MZXML_DATA"
            ds_props['FILE_NAME'] = os.path.basename(q_file)
            ds_props['MD5_CHECKSUM'] = md5
            ds_props['PARENT_TYPE'] = "MZXML_DATA"
            ds_props['FILE_TYPE'] = "MZXML"
            path = os.path.join(stagebox, 'dataset.properties')
            IniInfoHandler().write(ds_props, path)
            log.info("wrote %s" % path)
            dropbox.move_stage_to_dropbox(log, stagebox, info['DROPBOX'], keepCopy=True)

        return info

if __name__ == "__main__":
    Copy2Dropbox.main()
