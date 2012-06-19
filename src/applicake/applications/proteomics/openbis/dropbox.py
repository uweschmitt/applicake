'''
Created on Jun 19, 2012

@author: quandtan
'''

import os
from applicake.framework.interfaces import IApplication
from applicake.utils.fileutils import FileUtils
import shutil

class Copy2Dropbox(IApplication):
    '''
    Copy certain files to the openbis dropbox.
    '''


    def _get_dropboxdir(self, info):
        space = info['SPACE']
        project = info['PROJECT']
        prefix = ''
        if info.has_key('JOBIDX'):
            prefix = info['JOBIDX']
        if info.has_key('PARAM_IDX'):
            prefix = '%s.%s' (prefix,info['PARAM_IDX'])
        dirname = '%s+%s+%s' % (space, project, prefix)
        return os.path.join(info['DROPBOX'],dirname)

    def main(self,info,log):
        path = self._get_dropboxdir(info)
        FileUtils.makedirs_safe(log, path,clean=True)
        
        keys = ['PEPXMLS','PEPCSV','PROTXML']
        files = []
        for key in keys:
            if info.has_key(key):
                if isinstance(info[key], list):
                    files = info[key]
                else:
                    files = [info[key]]
                for file in files:
                    try:
                        shutil.copy(file,path)
                        log.debug('Copy [%s] to [%s]' % (file,path))
                    except:
                        if FileUtils.is_valid_file(log, file):
                            log.debug('file [%s] already exists' % file)
                        else:
                            log.fatal('Stop program because could not copy [%s] to [%s]' % (file,path))
                            return(1,info,log)
            else:
                log.error('info did not contain key [%s]' % key)
                return 1, info
        return 0,info
        
    def set_args(self,log,args_handler):
        """
        See interface
        """        
        args_handler.add_app_args(log, 'DROPBOX', 'Path to the dropbox folder used to upload data to OpenBIS.')
        args_handler.add_app_args(log, 'SPACE', 'OpenBIS space')
        args_handler.add_app_args(log, 'PROJECT', 'Project in the OpenBIS space.')
        args_handler.add_app_args(log, 'JOBIDX', 'Job id of the workflow')
        args_handler.add_app_args(log, 'PARAMIDX', 'Index of the parameter set (if a sweep was performed).')
        args_handler.add_app_args(log, 'PEPXMLS', 'List of pepXML files',action='append')
        args_handler.add_app_args(log, 'PROTXML', 'Path to a file in protXML format')
        args_handler.add_app_args(log, 'PEPCSV', 'Path to a csv file generated by pepxml2csv.')        
        args_handler.add_app_args(log, self.COPY_TO_WD, 'Files which are created by this application', action='append')
#        self.PARAM_IDX,self.DATASET_CODE,self.DATASET_CODE        
        return args_handler        
           