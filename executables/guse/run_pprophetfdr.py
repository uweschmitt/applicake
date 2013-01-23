#!/usr/bin/env python
'''
Created on May 24, 2012

@author: quandtan
'''

import sys
from applicake.framework.runner import WrapperRunner
from applicake.applications.proteomics.tpp.proteinprophetFDR import ProteinProphetFDR

runner = WrapperRunner()
application = ProteinProphetFDR()
exit_code = runner(sys.argv,application)
print exit_code
sys.exit(exit_code)