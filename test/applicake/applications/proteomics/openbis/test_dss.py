'''
Created on Apr 10, 2012

@author: quandtan
'''
import unittest
import sys
import os
from StringIO import StringIO

from applicake.framework.keys import Keys
from applicake.framework.logger import Logger
from applicake.applications.proteomics.openbis.dss import Dss


class Test(unittest.TestCase):
    #setUp and tearDown are pre-defined test functions
    def setUp(self):
        log_stream = StringIO()
        self.log = Logger.create(level='DEBUG', name='memory_logger')
        self.info = {Keys.PREFIX: 'getmsdata',
                     'RESULT_FILE': '',
                     'DSSKEYS': '',
                     'QUIET': 'false',
                     'KEEP_NAME': 'false',
                     'FAILURE_TOLERANT': 'false',
                     'SET_MZXML_KEY': False,
                     Keys.DATASET_CODE: '20120510111600123-123456',
                     'DATASET_DIR': '.'}

    #all methods starting with 'test' tested with unittest
    def test_prepare_run(self):
        command, info = Dss().prepare_run(self.info, self.log)
        assert command == 'getmsdata --out=. --result=getmsdata.out -v -c 20120510111600123-123456'
        mod_info = self.info.copy()
        mod_info.update({Keys.DSSCLIENT: 'getmsdata'})
        self.assertDictEqual(info, mod_info)

    def test_validate_run(self):
        self.rf = open('getmsdata.out', 'w')
        for fn in [1, 2]:
            self.rf.write("xyz\t/to/dir/file%d\n" % fn)
        self.rf.close()
        dss = Dss()
        dss._result_filename = 'getmsdata.out'
        dss._codes = ['xyz']
        dss.outkeys = ['DSSOUTPUT']
        run_code, info = dss.validate_run(self.info, self.log, 0, sys.stdout, sys.stderr)
        assert run_code == 0
        assert info['DSSOUTPUT'] == ['/to/dir/file1', '/to/dir/file2']
        os.remove('getmsdata.out')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_echo']
    unittest.main()
