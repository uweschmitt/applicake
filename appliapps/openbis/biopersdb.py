#!/usr/bin/env python
import os
from applicake.app import WrappedApp
from applicake.apputils import validation
from applicake.coreutils.arguments import Argument
from applicake.coreutils.keys import Keys,KeyHelp
from applicake.coreutils.submitter import name_of_submitting_host


class BioPersonalDB(WrappedApp):
    def add_args(self):
        return [
            Argument(Keys.WORKDIR, KeyHelp.WORKDIR),
            Argument("DB_SOURCE", 'BioDB or PersonalDB'),
            Argument("DBASE", 'Filepath (BioDB) or an openbis-dataset-code (PersonalDB)'),
            Argument("DATASET_DIR", 'dataset cache')
        ]

    def prepare_run(self, log, info):

        # For backward compatibility, by default do not provide explicit OpenBIS
        # instance URL
        openbis_alt_instances = {
                #'euler-portal.ethz.ch': 'https://ra-openbis.ethz.ch',
                'eulertest-portal.ethz.ch': 'https://openbis-test.ethz.ch'
        }

        submitter = name_of_submitting_host()

        log.info("this is %s" % os.path.abspath(__file__))
        if submitter is None:
            submitter = "eulertest-portal.ethz.ch"
        log.info("submitter is %s" % submitter)

        openbis_instance = openbis_alt_instances.get(submitter)
        openbis_instance_opt = '' if openbis_instance is None else '-H %s' % openbis_instance

        if info["DB_SOURCE"] == "BioDB":
            command = "true"
        elif info["DB_SOURCE"] == "PersonalDB":
            self.rfile = os.path.join(info[Keys.WORKDIR],"getdataset.out")
            command = "getdataset %s -v -r %s -o %s %s" % (openbis_instance_opt, self.rfile, info["DATASET_DIR"], info["DBASE"])
        else:
            raise RuntimeError("Unkwnown DB_SOURCE " + info["DB_SOURCE"])
        return info, command

    def validate_run(self, log, info, run_code, out):
        validation.check_exitcode(log,run_code)

        if info["DB_SOURCE"] == "BioDB":
            log.info("Database remains " + info["DBASE"])
        else:
            f = open(self.rfile)
            found = False
            for line in f.readlines():
                #if info['DB_TYPE'].lower in line.lower():
                if '.fasta' in line.lower() or '.txt' in line.lower():
                    info['DBASE'] = line.split()[1]
                    log.info("Database found " + info["DBASE"])
                    found = True
                if '.traml' in line.lower():
                    info['TRAML'] = line.split()[1]
                    log.info("TraML found " + info["TRAML"])
                    found = True
            f.close()
            if not found:
                log.error("No matching database (.fasta or .traml) found in dataset!")
                return info

        return info

if __name__ == "__main__":
    BioPersonalDB.main()
