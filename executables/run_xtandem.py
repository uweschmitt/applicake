#!/usr/bin/env python
'''
Created on May 24, 2012

@author: quandtan
'''

import sys
from applicake.framework.runner import WrapperRunner
from applicake.applications.proteomics.searchengine.xtandem import Xtandem

runner = WrapperRunner()
app = Xtandem()
exit_code = runner(sys.argv,app)
print exit_code
sys.exit(exit_code)