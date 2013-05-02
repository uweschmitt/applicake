#!/usr/bin/env python
'''
Created on Mar 28, 2012

@author: loblum
'''

import os
from applicake.framework.interfaces import IWrapper
from applicake.framework.templatehandler import BasicTemplateHandler
from applicake.utils.fileutils import FileUtils
from applicake.utils.xmlutils import XmlValidator

class Direct2TraML(IWrapper):
    """
    Wrapper for the famous spectrast2traml.sh script
    """
    def prepare_run(self,info,log):

        consensuslib = os.path.join(info[self.WORKDIR],'consensuslib')
        if not os.access(os.path.dirname(info['LIBOUTBASE']), os.W_OK):
            log.warn("The folder [%s] is not writable, falling to workflow folder [%s]!" %(info['LIBOUTBASE'],info[self.WORKDIR]))
            info['LIBOUTBASE'] = os.path.join(info[self.WORKDIR], os.path.basename(info['LIBOUTBASE']))
        info[self.TRAML] = info['LIBOUTBASE'] + '_' + info[self.PARAM_IDX] +  '.TraML'
        self._result_file = info[self.TRAML]
        
        consensustype = ""  #None
        if info['CONSENSUS_TYPE'] == "Consensus":
            consensustype = "C"
        elif  info['CONSENSUS_TYPE'] == "Best replicate":
            consensustype = "B"


        tsvopts = '-k openswath '
        tsvopts += ' -l ' + info['TSV_MASS_LIMITS'].replace("-",",")
        mini,maxi = info['TSV_ION_LIMITS'].split("-")
        tsvopts += ' -o %s -n %s ' % (mini,maxi)
        tsvopts += ' -p ' + info['TSV_PRECISION']
        if info.has_key('TSV_REMOVE_DUPLICATES') and info['TSV_REMOVE_DUPLICATES'] == "True": tsvopts += ' -d'
        else: log.debug("no tsv rm duplicates")
        
        if info.has_key('TSV_EXACT') and info['TSV_EXACT'] == "True": tsvopts += ' -e'
        else: log.debug("no tsv exact")
            
        if info.has_key('TSV_CHARGE') and info['TSV_CHARGE'] != "": tsvopts += ' -x '+info['TSV_CHARGE'].replace(";",",")
        else: log.debug("no rm duplicates")
        
        if info.has_key('TSV_GAIN') and info['TSV_GAIN'] != "": tsvopts += ' -g '+info['TSV_GAIN'].replace(";",",")           
        else: log.debug("no tsv gain")
        
        if info.has_key('TSV_SERIES') and info['TSV_SERIES'] != "": tsvopts += ' -s '+info['TSV_SERIES'].replace(";",",")
        else: log.debug("no tsv series")
        
        decoyopts = '-append -exclude_similar ' 
        decoyopts += '-method ' + info['SWDECOY_METHOD']
        decoyopts += ' -min_transitions %s -max_transitions %s ' % (mini,maxi)        
        if info.has_key('SWDECOY_THEORETICAL') and info['SWDECOY_THEORETICAL'] == "True": decoyopts += ' -theoretical'
        else: log.debug("no decoy theoretical")
        
        command = 'spectrast -c_BIN! -cA%s -cN%s %s && direct2traml.sh -s "%s" -d "%s" -i %s -o %s' % (consensustype,
                                                                              consensuslib,
                                                                              info['SPLIB'],
                                                                              tsvopts, 
                                                                              decoyopts,
                                                                              consensuslib + '.splib',
                                                                              info[self.TRAML])
        
        
        return command,info
    
    
    def set_args(self,log,args_handler):
        """
        See interface
        """        
        args_handler.add_app_args(log, self.SPLIB, 'Spectrast library in .splib format')
        args_handler.add_app_args(log, self.WORKDIR, 'workdir')
        
        args_handler.add_app_args(log, 'LIBOUTBASE', 'Folder to put output libraries')
        args_handler.add_app_args(log, self.PARAM_IDX, 'Parameter index to distinguish')   
        
        args_handler.add_app_args(log, 'SWDECOY_METHOD', 'decoy generation method (shuffle, pseudo-reverse, reverse, shift)')
        args_handler.add_app_args(log, 'SWDECOY_THEORETICAL', 'Set true if only annotated transitions should be used and be corrected to the theoretical mz')        
        
        args_handler.add_app_args(log, 'TSV_MASS_LIMITS','Lower and Upper mass limits.')
        args_handler.add_app_args(log, 'TSV_ION_LIMITS','Min and Max number of reported ions per peptide/z')
        args_handler.add_app_args(log, 'TSV_PRECISION','Maximum error allowed at the annotation of a fragment ion')
        
        args_handler.add_app_args(log, 'TSV_REMOVE_DUPLICATES','Remove duplicate masses from labeling')        
        args_handler.add_app_args(log, 'TSV_EXACT','Use exact mass.')
        args_handler.add_app_args(log, 'TSV_GAIN','List of allowed fragment mass modifications. Useful for phosphorilation.')
        args_handler.add_app_args(log, 'TSV_CHARGE','Fragment ion charge states allowed.')
        args_handler.add_app_args(log, 'TSV_SERIES','List of ion series to be used')

        return args_handler
    
    def validate_run(self,info,log,run_code, out_stream, err_stream):
        if 0 != run_code:
            return run_code,info

        if not FileUtils.is_valid_file(log, self._result_file):
            log.critical('[%s] is not valid' %self._result_file)
            return 1,info
        if not XmlValidator.is_wellformed(self._result_file):
            log.critical('[%s] is not well formed.' % self._result_file)
            return 1,info    
        return 0,info     

