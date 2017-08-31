#!/usr/bin/env python
import os

from appliapps.tpp.searchengines.enzymes import enzymestr_to_engine
from appliapps.tpp.searchengines.modifications import genmodstr_to_engine
from applicake.apputils.templates import read_mod_write, get_tpl_of_class
from applicake.apputils.validation import check_exitcode, check_xml, check_stdout
from applicake.coreutils.arguments import Argument
from applicake.coreutils.keys import Keys
from appliapps.tpp.searchengines.searchenginebase import SearchEnginesBase


class Comet(SearchEnginesBase):
    """
    Wrapper for the search engine comet.
    """
    def add_args(self):
        args = super(Comet, self).add_args()
        args.append(Argument('COMET_DIR', 'executable location.', default=''))
        args.append(Argument('COMET_EXE', 'executable name.', default='comet'))
        args.append(Argument('COMET_FRAGMENT_IONS', 'fragment ions (ms/ms resolution)', default='ion_trap'))

        return args

    def get_fragment_ions_values(self, msms_type):
        '''Return tuple corresponding to, respectively:
            fragment_bin_tol, fragment_bin_offset, theoretical_fragment_ions
        parameters of the Comet search binary.
        '''
        if msms_type == 'high_res':
            return (0.02, 0.0, 0)
        if msms_type == 'ion_trap':
            return (1.0005, 0.4, 1)
        raise RuntimeError('Unknown "Fragment ions" option value "%s"' % msms_type)


    def prepare_run(self, log, info):
        wd = info[Keys.WORKDIR]
        basename = os.path.join(wd, os.path.splitext(os.path.split(info[Keys.MZXML])[1])[0])
        info[Keys.PEPXML] = basename + '.pep.xml'

        # need to create a working copy to prevent replacement or generic definitions
        # with app specific definitions
        app_info = info.copy()

        if info['PRECMASSUNIT'] == 'Da':
            app_info['PRECMASSUNIT'] = '0'
        elif info['PRECMASSUNIT'] == 'ppm':
            app_info['PRECMASSUNIT'] = '2'
        else:
            raise RuntimeError("Precmassunit %s unknown" % info['PRECMASSUNIT'])

        if info['FRAGMASSUNIT'] == 'ppm':
            raise RuntimeError("Comet does not support frag mass error unit PPM")

        # Note: FRAGMASSERR does not apply to Comet; instead use pre-defined
        #       FRAGBINTOL and FRAGBINOFF values
        frag_bin_tol, frag_bin_off, frag_ions_theor = self.get_fragment_ions_values(
            info.get('COMET_FRAGMENT_IONS', None))
        app_info.update({
            'FRAGBINTOL': frag_bin_tol,
            'FRAGBINOFF': frag_bin_off,
            'FRAGIONSTHEOR': frag_ions_theor,
        })

        app_info["STATIC_MODS"], app_info["VARIABLE_MODS"], _ = genmodstr_to_engine(info["STATIC_MODS"],
                                                                                 info["VARIABLE_MODS"], 'Comet')
        app_info['ENZYME'], app_info['NUM_TERM_CLEAVAGES'] = enzymestr_to_engine(info['ENZYME'], 'Comet')

        tplfile = os.path.join(wd, "comet.params")
        template = get_tpl_of_class(self)
        read_mod_write(app_info,template, tplfile)

        exe_path = app_info['COMET_DIR']
        exe = app_info['COMET_EXE']

        command = "{exe} -N{basename} -P{tplfile} {mzxml}".format(exe=os.path.join(exe_path, exe), basename=basename, tplfile=tplfile, mzxml=info[Keys.MZXML])
        return info, command

    def validate_run(self, log, info, exit_code, stdout):
        if "Warning - no spectra searched" in stdout:
            raise RuntimeError("No spectra in mzXML!")
        if "CometMemAlloc" in stdout:
            #print to stdout to reach gUSE rescue functionality. ugly, no?
            print "MemoryError"
            raise RuntimeError("The job run out of RAM!")
        check_stdout(log,stdout)
        if exit_code:
            log.warn("exit_code is %s", exit_code)
            mzxml = info[Keys.MZXML]
            log.warn("maybe the input file %s does not exist any more. check this !" % mzxml)
        check_exitcode(log, exit_code)
        check_xml(log, info[Keys.PEPXML])
        return info


if __name__ == "__main__":
    Comet.main()
