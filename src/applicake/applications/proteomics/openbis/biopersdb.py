#!/usr/bin/env python
"""
Created on 7 Jun 2013

@author: lorenz
"""

from applicake.framework.interfaces import IWrapper
from applicake.framework.keys import Keys

class BioPersonalDB(IWrapper):
    def set_args(self, log, args_handler):
        args_handler.add_app_args(log, Keys.WORKDIR, 'workdir')
        args_handler.add_app_args(log, "DB_SOURCE", 'workdir')
        args_handler.add_app_args(log, "DBASE", 'workdir')
        return args_handler

    def prepare_run(self, info, log):
        if info["DB_SOURCE"] == "BioDB":
            command = "echo %s" % info["DBASE"]
        elif info["DB_SOURCE"] == "PersonalDB":
            command = "getdataset -r getdataset.out -o %s %s && grep fasta getdataset.out | cut -f2" % \
                      (info["WORKDIR"], info["DBASE"])
        else:
            raise Exception("Unkwnown DB_SOURCE " + info["DB_SOURCE"])
        return command, info

    def validate_run(self, info, log, run_code, out_stream, err_stream):
        if run_code != 0:
            return run_code, info

        out_stream.seek(0)
        info["DBASE"] = out_stream.readlines()[-1].strip()
        return run_code, info
