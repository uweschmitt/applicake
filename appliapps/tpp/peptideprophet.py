#!/usr/bin/env python
import os

from appliapps.tpp.searchengines.enzymes import enzymestr_to_engine
from applicake.app import WrappedApp
from applicake.apputils import validation
from applicake.coreutils.arguments import Argument
from applicake.coreutils.keys import Keys, KeyHelp


class PeptideProphetSequence(WrappedApp):
    """
    Corrects pepxml output to make compatible with TPP and openms, then executes xinteract
    (step by step because of semiTrypsin option)
    """

    def add_args(self):
        return [
            Argument(Keys.WORKDIR, KeyHelp.WORKDIR),
            Argument(Keys.PEPXML, KeyHelp.PEPXML),
            Argument('ENZYME', 'Enzyme used for digest'),
            Argument('DBASE', 'FASTA dbase'),
            Argument('MZXML', 'Path to the original MZXML inputfile')
        ]

    def prepare_run(self, log, info):
        """
        Template handler for xinteract. mapping of options:
        -dDECOY_ DECOY=DECOY_ str used for decoys
        -OA ACCMASS accurate mass binning
        -OP NONPARAM
        -Od DECOYPROBS
        -Ol LEAVE
        -OI PI
        -Ow INSTRWARN

        -dDECOY_ -OAPdlIw (dummy)
        """

        #XTINERACT
        info['XINTERACT'] = '-dDECOY_ -OAPdlIw'
        result = os.path.join(info[Keys.WORKDIR], 'interact.pep.xml')
        enz, _ = enzymestr_to_engine(info['ENZYME'], 'InteractParser')
        command = """InteractParser %s %s -E%s &&
        RefreshParser %s %s &&
        PeptideProphetParser %s DECOY=DECOY_ ACCMASS NONPARAM DECOYPROBS LEAVE PI INSTRWARN
        """ % (result, info[Keys.PEPXML], enz,
               result, info['DBASE'],
               result )
        info[Keys.PEPXML] = result
        return info, command


    def validate_run(self, log, info, run_code, out):
        if "No decoys with label DECOY_ were found" in out:
            raise RuntimeError("No DECOY_s found in fasta. Please use other fasta!")
        validation.check_stdout(log, out)
        validation.check_exitcode(log, run_code)
        validation.check_xml(log, info[Keys.PEPXML])
        return info


if __name__ == "__main__":
    PeptideProphetSequence.main()