# https://forum.dynamobim.com/t/change-color-of-the-revit-ribbon-with-dynamo/74257/3
# https://thebuildingcoder.typepad.com/blog/2011/02/pimp-my-autocad-or-revit-ribbon.html
# https://stackoverflow.com/questions/737151/how-to-get-the-list-of-properties-of-a-class
# https://www.notion.so/Extension-Hooks-b771ecf65f6a45fe87ae12beab2a73a6

# https://pyrevit.readthedocs.io/en/latest/pyrevit/coreutils/envvars.html
def ui_change(doc):
    from pyrevit import clr
    from pyrevit.coreutils import envvars
    from datetime import datetime
    # Custom module for this system
    from SyncTimer.swc_timer import change_ribbon_colours, make_collab_tab_active, change_collab_tab_colour, make_times

    '''for use with doc changed event'''
    doc_id = str(doc.GetHashCode())

    '''for use with app idle hook - there's a memory leak though https://github.com/eirannejad/pyRevit/issues/1252 '''
    # try:
    #     doc = __revit__.ActiveUIDocument.Document
    # except:
    #     import sys as sys
    #     sys.exit()

    # Most variables in the system are stored in environment variables so they do not need to be constantly recreated.
    # Items that are specific to a given document are identified using the document's hash code.
    base_colour = envvars.get_pyrevit_env_var("base_colour")
    env_var_ribbon_name = doc_id + "_ribbon"
    ribbon = envvars.get_pyrevit_env_var(env_var_ribbon_name)
    if ribbon is not None:
        # ribbon will be none when using view-activated hook and opening a new document
        if doc.IsWorkshared and not doc.IsDetached and not doc.IsFamilyDocument:
            # only change ribbon colours in a workshared project environment

            # get variables
            env_var_timer_name = doc_id + "_timer"
            env_var_last_colour_name = doc_id + "_last"
            env_var_last_duration_name = doc_id + "_duration"
            env_var_nag_time_name = doc_id + "_nag_time"

            colour_gradient = envvars.get_pyrevit_env_var("warning_gradient")
            highlight_colour = envvars.get_pyrevit_env_var("highlight_colour")
            history_datetime = envvars.get_pyrevit_env_var(env_var_timer_name)
            last_tab_colour = envvars.get_pyrevit_env_var(env_var_last_colour_name)
            duration = int(envvars.get_pyrevit_env_var(env_var_last_duration_name))  # requires int sanitation
            nag_time = int(envvars.get_pyrevit_env_var(env_var_nag_time_name))       # requires int sanitation
            nag_disabled = envvars.get_pyrevit_env_var("nag_enabled")

            # looking to see if the user has disabled automatic tab switching
            if nag_disabled is None:
                nag_disabled = False
            # find how long automatic tab switching is to be disabled for
            nag_disabled_timer = envvars.get_pyrevit_env_var("nag_disabled_timer")
            # need to check where the script was last run to ensure we colour the ribbon correctly
            last_doc = envvars.get_pyrevit_env_var("last_doc")

            # make a range of time values based on number of steps in the colour gradient and the desired time
            times = make_times(nag_time, duration)

            # failsafe for fresh setup
            if last_tab_colour is None:
                last_tab_colour = base_colour

            # find how long it has been since the user has synced in minutes
            now = datetime.now()
            difference = now - history_datetime
            minutes = difference.total_seconds() / 60

            # reset automatic tab switching if timer has expired
            if nag_disabled_timer is None:
                nag_disabled = False
            elif now > nag_disabled_timer:
                nag_disabled = False

            # if we haven't reached the first step in the colour gradient, the UI should be set to default.
            # if we have, find the colour corresponding to where we are in the time range.
            if minutes < times[0]:
                new_tab_colour = base_colour
            else:
                for t, g in zip(times, colour_gradient):
                    if minutes > t:
                        new_tab_colour = g

            # this controls the annoyance piece when the user exceeds maximum time values but nothing else has changed
            # only force auto tab switching if it is not turned off
            if last_tab_colour == new_tab_colour and doc == last_doc:
                if minutes > duration:
                    change_collab_tab_colour(ribbon, highlight_colour)
                    if not nag_disabled:
                        make_collab_tab_active(ribbon)

            else:
                # if something has, or needs to change, we then trigger ribbon colour changes
                # change ui colours back to default
                if new_tab_colour == base_colour:
                    change_ribbon_colours(ribbon, base_colour)

                # change ui colours to new value based on where we are in the time range, force auto tab switching
                else:
                    change_ribbon_colours(ribbon, new_tab_colour)
                    if minutes > duration:
                        change_collab_tab_colour(ribbon, highlight_colour)
                        if not nag_disabled:
                            make_collab_tab_active(ribbon)

                # record the last colour we set so we can compare the next run
                envvars.set_pyrevit_env_var(env_var_last_colour_name, new_tab_colour)

        # if the UI has been coloured previously, reset the UI to default if the project is not workshared
        else:
            if ribbon.Tabs[0].Panels[0].CustomPanelBackground is not base_colour:
                change_ribbon_colours(ribbon, base_colour)

    # record the last active document to compare to next run
    envvars.set_pyrevit_env_var("last_doc", doc)
