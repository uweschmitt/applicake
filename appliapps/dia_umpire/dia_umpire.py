#!/usr/bin/env python
import os

from applicake.apputils import validation

from applicake.app import WrappedApp
from applicake.coreutils.arguments import Argument
from applicake.coreutils.keys import Keys, KeyHelp


class DiaUmpire(WrappedApp):

    def add_args(self):
        ret = [
            Argument(Keys.WORKDIR, KeyHelp.WORKDIR),
            Argument(Keys.MZXML, KeyHelp.MZXML),
            Argument('PARAMETER_FILE', 'optional parameter file', default=""),
        ]
        return ret

    def prepare_run(self, log, info):
        input_file = info["MZXML"]
        parameters = info["PARAMETER_FILE"].strip()
        command = "dia_umpire.sh %s %s" % (input_file, parameters)
        return info, command

    def validate_run(self, log, info, exit_code, stdout):
        validation.check_stdout(log, stdout)
        validation.check_exitcode(log, exit_code)

if __name__ == "__main__":
    DiaUmpire.main()
