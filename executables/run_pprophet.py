#!/usr/bin/env python
'''
Created on May 24, 2012

@author: quandtan
'''

import sys
from applicake.framework.runner import WrapperRunner
from applicake.applications.proteomics.tpp.proteinprophet import ProteinProphet

runner = WrapperRunner()
application = ProteinProphet()
exit_code = runner(sys.argv,application)
print exit_code
sys.exit(exit_code)