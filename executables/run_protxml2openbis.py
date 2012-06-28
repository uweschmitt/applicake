#!/usr/bin/env python
'''
Created on Jun 19, 2012

@author: quandtan
'''

import sys
from applicake.framework.runner import ApplicationRunner
from applicake.applications.proteomics.sybit.protxml2openbis import ProtXml2Openbis

runner = ApplicationRunner()
application = ProtXml2Openbis()
exit_code = runner(sys.argv,application)
print exit_code