#!/usr/bin/env python
'''
Created on Jan 26, 2011

@author: quandtan
'''
import os,sys,shutil
from applicake.app import CollectorApplication
from applicake.interprophet import InterProphet
from applicake.pepxml2csv import PepXML2CSV
from applicake.proteinprophet import ProteinProphet
from applicake.openbisexport import OpenbisExport
from applicake.utils import ThreadPool

class TppCollector(CollectorApplication):
    '''
    classdocs
    '''
    def _sequence(self, filename):
        if self._exit_code == 0: 
            self.log.debug('ini file to process [%s]' % filename)
            prog = InterProphet(use_filesystem=True, name=None, log_console=False)
            exit_code = prog(['interprophet.py', '-p', 'InterProphetParser', '-i', filename, '-t', self._template_filenames[0], '-o', filename])
            if exit_code == 0:
                self.log.debug('prog [%s] with finished with exit_code [%s]' % (prog.name, exit_code))
                #copy the log file to the working dir
                for fn in [prog._log_filename, prog._stderr_filename, prog._stdout_filename]:
                    shutil.move(fn, os.path.join(prog._wd, fn))
                
                prog = PepXML2CSV(use_filesystem=True, name=None, log_console=False)
                exit_code = prog(['pepxml2csv.py', '--prefix=pepxml2csv', '--prefix=fdr2probability', '--input=' + filename, '--template=' + self._template_filenames[1], '--output=' + filename])
            if exit_code == 0:
                self.log.debug('prog [%s] with finished with exit_code [%s]' % (prog.name, exit_code))
            #copy the log file to the working dir
                for fn in [prog._log_filename, prog._stderr_filename, prog._stdout_filename]:
                    shutil.move(fn, os.path.join(prog._wd, fn))
                
                prog = ProteinProphet(use_filesystem=True, name=None, log_console=False)
                exit_code = prog(['proteinprophet.py', '--prefix=ProteinProphet', '--input=' + filename, '--template=' + self._template_filenames[2], '--output=' + filename])
            if exit_code == 0:
                self.log.debug('prog [%s] with finished with exit_code [%s]' % (prog.name, exit_code))
                #copy the log file to the working dir
                for fn in [prog._log_filename, prog._stderr_filename, prog._stdout_filename]:
                    shutil.move(fn, os.path.join(prog._wd, fn))
                
                prog = OpenbisExport(use_filesystem=True, name=None, log_console=False)
                exit_code = prog(['openbisexport.py', '--prefix=protxml2spectralcount', '--prefix=protxml2openbis', '--input=' + filename, '--template=' + self._template_filenames[3], '--output=' + filename])
            if exit_code == 0:
                self.log.debug('prog [%s] with finished with exit_code [%s]' % (prog.name, exit_code))
                #copy the log file to the working dir
                for fn in [prog._log_filename, prog._stderr_filename, prog._stdout_filename]:
                    shutil.move(fn, os.path.join(prog._wd, fn))
            
            if exit_code != 0:
                self.log.error('content of the log file[%s]: [\n%s\n]' % (prog._log_filename, open(prog._log_filename, 'r').read()))
                self._exit_code = exit_code
        else:
            self.log.error('file [%s] was not processed because a previous exit was != 0' % filename)

    def _run(self,ini_filenames):   
        pool = ThreadPool(self._num_threads)
        self._exit_code = 0
        for filename in ini_filenames:
            pool.add_task(self._sequence, filename)
#            exit_code = self._sequence(filename)                
        return self._exit_code                             

if "__main__" == __name__:
    # init the application object (__init__)
    a = TppCollector(use_filesystem=True,name=None)
    # call the application object as method (__call__)
    exit_code = a(sys.argv)
    #copy the log file to the working dir
    for filename in [a._log_filename]:
        if os.path.exists(filename):
            shutil.move(filename, os.path.join(a._wd,filename))
        else:
            sys.stdout.write('file does not exit [%s] and was therefore not moved to [%s]\n' % (filename,os.path.join(a._wd,filename)) )
    print(exit_code)
    
#    sys.exit(1)
    sys.exit(exit_code)   
    