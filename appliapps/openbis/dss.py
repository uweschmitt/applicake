#!/usr/bin/env python
import os

from applicake.app import WrappedApp
from applicake.apputils import validation
from applicake.coreutils.arguments import Argument
from applicake.coreutils.keys import Keys, KeyHelp
from applicake.coreutils.submitter import name_of_submitting_host


class Dss(WrappedApp):
    """
    The DSS is often a initial workflow node. Requesting a workdir has thus the nice side effect
    that the DSS generates the JOB_ID for the workflow
    """

    default_keys = {'getmsdata': 'MZXML', 'getexperiment': 'SEARCH', 'getdataset': 'DSSOUT',
                    'getmsdata_fast': 'MZXML'}

    ALLOWED_PREFIXES = default_keys.keys()
    TRUES = ['TRUE', 'T', 'YES', 'Y', '1']

    def add_args(self):
        return [
            Argument(Keys.WORKDIR, KeyHelp.WORKDIR),
            Argument(Keys.EXECUTABLE, "%s %s" % (KeyHelp.EXECUTABLE, self.ALLOWED_PREFIXES)),
            Argument(Keys.DATASET_CODE, 'dataset code to get for getdataset or getmsdata'),
            Argument('EXPERIMENT', 'experiment code to get for for getexperiment'),
            Argument('DATASET_DIR', 'cache directory'),
            Argument('DSS_KEEP_NAME', "for 'getmsdata' only: output keeps original file name if set to true "
                                      "(otherwise it will be changed to samplecode~dscode.mzXML)",
                     default='false')
        ]

    def prepare_run(self, log, info):
        executable = info[Keys.EXECUTABLE].strip()

        # temporary fix because getmsdata_fast is broken:
        if executable == "getmsdata_fast":
            executable = info[Keys.EXECUTABLE] = "getmsdata"

        if not executable in self.ALLOWED_PREFIXES:
            raise Exception("Executable %s must be one of [%s]" % (executable, self.ALLOWED_PREFIXES))


        log.info("info = %r" % info)

        self.rfile = os.path.join(info[Keys.WORKDIR], executable + ".out")

        outdir = info['DATASET_DIR']

        if executable in ('getmsdata', 'getmsdata_fast') and not info['DSS_KEEP_NAME'].upper() == 'TRUE':
            koption = '-c'
        else:
            koption = ''

        if info[Keys.EXECUTABLE] == 'getexperiment':
            dscode_to_get = info['EXPERIMENT']
        else:
            dscode_to_get = info[Keys.DATASET_CODE]

        submitter = name_of_submitting_host()
        if submitter is None:
            submitter = "eulertest-portal.ethz.ch"

        openbis_stores = {
                'euler-portal.ethz.ch': 'https://ra-openbis.ethz.ch',
                'eulertest-portal.ethz.ch': 'https://openbis-test.ethz.ch'
        }

        openbis_instance = openbis_stores.get(submitter)
        if openbis_instance is None:
            raise RuntimeError("no openbis instance configures for %s. I only know %r" % (submitter, openbis_stores))

        command = "%s -H %s -v -r %s --out=%s %s %s" % (executable, openbis_instance, self.rfile, outdir, koption, dscode_to_get)
        return info, command

    def validate_run(self, log, info, exit_code, out):
        if "TypeError: expected str or unicode but got <type 'NoneType'>" in out:
            raise RuntimeError("Dataset is archived. Please unarchive first!")

        if "traceback" in out.lower():
            raise RuntimeError("traceback when talking to openbis: %s" % out)

        validation.check_exitcode(log, exit_code)
        missing = []
        for line in open(self.rfile):
            fields = line.strip().rsplit(None, 1)
            if len(fields) == 2:
                path = fields[1]
                if not os.path.exists(path):
                    missing.append(path)

        executable = info[Keys.EXECUTABLE]
        if missing:
            for p in missing:
                log.error("%s failed for %s" % (executable, p))
            raise Exception("files which should be extracted from openbis are missing")


        #KEY where to store downloaded file paths
        key = self.default_keys[executable]
        #VALUE is a list of files or the mzXMLlink
        dsfls = []
        with open(self.rfile) as f:
            for downloaded in [line.strip() for line in f.readlines()]:
                ds, fl = downloaded.split("\t")
                if ds == info[Keys.DATASET_CODE] or ds == info['EXPERIMENT']:
                    dsfls.append(fl)

        #MZXML is expected only 1
        if key == 'MZXML':
            dsfls = dsfls[0]

        log.debug("Adding %s to %s" % (dsfls, key))
        info[key] = dsfls
        return info


if __name__ == "__main__":
    Dss.main()
