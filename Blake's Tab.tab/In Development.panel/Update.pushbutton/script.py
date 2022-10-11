# -*- coding: UTF-8 -*-
"""Updates all pyRevit Extensions and Reloads pyRevit"""
from pyrevit import script
from pyrevit.loader import sessionmgr
from pyrevit.loader import sessioninfo
import os

os.system('cmd /c "pyrevit extensions update --all"')

logger = script.get_logger()
results = script.get_results()

# re-load pyrevit session.
logger.info('Reloading....')
sessionmgr.reload_pyrevit()

results.newsession = sessioninfo.get_session_uuid()
