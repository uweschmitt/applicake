#!/usr/bin/env python
import os
import tempfile

from applicake.apputils import validation

from applicake.app import WrappedApp
from applicake.coreutils.arguments import Argument
from applicake.coreutils.keys import Keys, KeyHelp


class DiaUmpire(WrappedApp):

    def add_args(self):
        ret = [
            Argument(Keys.WORKDIR, KeyHelp.WORKDIR),
            Argument('PARAMETER_FILE', 'optional parameter file', default=""),
            Argument('DSSOUT', "if key MZXML not set, get from DSSOUT file (after getdataset)"),
            Argument('TMPDIR', "tmpdir to use for intermediate results", default="/tmp"),
        ]
        return ret

    def _getmzxml_from_dssout(self, info, log):
        # in case getdataset instead of getmsdata was used key MZXML is not set but mzXML.gz is in DSSOUT list
        if not isinstance(info['DSSOUT'], list):
            info['DSSOUT'] = [info['DSSOUT']]
        for written_file in info['DSSOUT']:
            log.info("check for mzXML(.gz) extension: %s " % written_file)
            if written_file.endswith('/ms-injection.properties'):
                interesting = [line for line in open(written_file, "r") if "SAMPLE_CODE" in line]
                if not interesting:
                    raise Exception("no field SAMPLE_CODE found in %s" % written_file)
                if len(interesting) > 1:
                    # should never happen:
                    raise RuntimeError("duplicate SAMPLE_CODE found in %s" % written_file)
                __, __, sample_code = interesting[0].partition("=")
                sample_code = sample_code.strip()
                if not sample_code:
                    raise RuntimeError("no value for SAMPLE_CODE in %s" % written_file)
                info["SAMPLE"] = sample_code
                log.info("SAMPLE is %s" % sample_code)

            if '.mzXML' in written_file or '.mzXML.gz' in written_file:
                info[Keys.MZXML] = written_file
                log.info("MZXML is %s" % written_file)
                break
        return info

    def prepare_run(self, log, info):
        hostname = os.environ.get("HOSTNAME")
        log.info("prepare run of dia_umpire.sh on host %s", hostname)
        info = self._getmzxml_from_dssout(info, log)
        for k, v in info.items():
            log.info("%s = %s" % (k, v))

        working_dir = info[Keys.WORKDIR]

        if "TMPDIR" in info:
            tempfile.tempdir = info["TMPDIR"]
        tmpdir = tempfile.mkdtemp()
        tmpdir = tempfile.mkdtemp()
        tmpmzxml = os.path.join(tmpdir, os.path.basename(info['MZXML']))

        parameters = info["PARAMETER_FILE"].strip()
        command_0 = 'cp -v "%s" "%s"'  % (info["MZXML"], tmpmzxml)
        command_1 = 'dia-umpire.sh "%s" %s' % (tmpmzxml, parameters)
        commands = [command_0, command_1]

        mzxml_stem = os.path.splitext(info["MZXML"])[0]
        info["Q_FILES"] = []
        for i in (1, 2, 3):
            expected = mzxml_stem + "_Q%d.mzXML.gz" % i
            full_path = os.path.join(tmpdir, os.path.basename(expected))
            command = "cp -v %s %s" % (full_path, working_dir)
            info["Q_FILES"].append(os.path.join(working_dir, os.path.basename(expected)))
            commands.append(command)
            command = "cp -v %s %s" % (full_path + ".md5", working_dir)
            commands.append(command)

        param_file_name = "diaumpire_se.params"
        param_file = os.path.join(tmpdir, param_file_name)
        commands.append("cp -v %s %s" % (param_file, working_dir))
        info["USED_PARAMETER_FILE"] = os.path.join(working_dir, param_file_name)

        command = " && ".join(commands)
        return info, command

    def validate_run(self, log, info, exit_code, stdout):
        validation.check_stdout(log, stdout)
        validation.check_exitcode(log, exit_code)
        info["MD5_SUMS"] = []
        for p in info["Q_FILES"]:
            validation.check_file(log, p)
            md5sum = open(p + ".md5", "r").read().split(" ")[0].strip()
            info["MD5_SUMS"].append(md5sum)
        return info


if __name__ == "__main__":
    DiaUmpire.main()
