#!/usr/bin/env python
'''
Created on Jun 19, 2012

@author: quandtan
'''

import sys
from applicake.framework.runner import WrapperRunner
from applicake.applications.proteomics.tpp.pepxmlcorrector import PepXMLCorrector

runner = WrapperRunner()
application = PepXMLCorrector()
exit_code = runner(sys.argv,application)
print exit_code
sys.exit(exit_code)