from pyrevit import EXEC_PARAMS
from datetime import datetime
from pyrevit.coreutils import envvars
# Custom module for this system
from SyncTimer.swc_timer import change_ribbon_colours

# Only make changes if sync is successful
if str(EXEC_PARAMS.event_args.Status) == "Succeeded":
    doc = EXEC_PARAMS.event_args.Document
    doc_id = str(doc.GetHashCode())

    env_var_ribbon_name = doc_id + "_ribbon"
    env_var_timer_name = doc_id + "_timer"

    # log the current time when synced and reset the ribbon colour back to default
    base_colour = envvars.get_pyrevit_env_var("base_colour")
    ribbon = envvars.get_pyrevit_env_var(env_var_ribbon_name)
    envvars.set_pyrevit_env_var(env_var_timer_name, datetime.now())
    change_ribbon_colours(ribbon, base_colour)
