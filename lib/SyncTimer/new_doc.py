def new_doc(doc):

    from pyrevit import EXEC_PARAMS, HOST_APP
    from pyrevit.coreutils import envvars
    from pyrevit.userconfig import user_config
    from datetime import datetime
    # Custom module for this system
    from SyncTimer.swc_timer import make_colour, change_ribbon_colours, make_gradient, get_ribbon

    ribbon = get_ribbon()

    app = __revit__.Application
    rvt_year = int(app.VersionNumber)
    if rvt_year > 2023:
        import Autodesk.Revit.UI as UI
        theme = UI.UIThemeManager.CurrentTheme;
        if theme == UI.UITheme.Dark:
            base_colour_str = "#3b4453"
        else:
            base_colour_str = "#EEEEEE"
    else:
        base_colour_str = "#EEEEEE"



    if doc.IsWorkshared and not doc.IsDetached:

        doc_id = str(doc.GetHashCode())

        # Create variables

        base_colour = make_colour(base_colour_str)
        try:
            warning_colour_str = user_config.swc_timer.get_option("warning_colour", "#FF0000")
        except AttributeError:
            user_config.add_section("swc_timer")
            warning_colour_str = user_config.swc_timer.get_option("warning_colour", "#FF0000")

        warning_colour = make_colour(warning_colour_str)
        highlight_colour_str = user_config.swc_timer.get_option("highlight_colour", "#00FF2A")
        highlight_colour = make_colour(highlight_colour_str)
        duration = user_config.swc_timer.get_option("duration", 30)
        nag_time = user_config.swc_timer.get_option("nag_time", 20)
        timer = datetime.now()

        gradient_colours = make_gradient(base_colour_str, warning_colour_str)

        env_var_ribbon_name = doc_id + "_ribbon"
        env_var_timer_name = doc_id + "_timer"
        env_var_duration_name = doc_id + "_duration"
        env_var_nag_time_name = doc_id + "_nag_time"

        # Save variables
        envvars.set_pyrevit_env_var("base_colour", base_colour)
        envvars.set_pyrevit_env_var("warning_colour", warning_colour)
        envvars.set_pyrevit_env_var("warning_gradient", gradient_colours)
        envvars.set_pyrevit_env_var("highlight_colour", highlight_colour)
        envvars.set_pyrevit_env_var(env_var_ribbon_name, ribbon)
        envvars.set_pyrevit_env_var(env_var_timer_name, timer)
        envvars.set_pyrevit_env_var(env_var_duration_name, duration)
        envvars.set_pyrevit_env_var(env_var_nag_time_name, nag_time)
        envvars.set_pyrevit_env_var("last_doc", doc)

        # Apply changes to the UI
        change_ribbon_colours(ribbon, base_colour)

    # if the document is not workshared, record the document and reset colours
    else:
        doc = EXEC_PARAMS.event_args.Document
        doc_id = str(doc.GetHashCode())
        env_var_ribbon_name = doc_id + "_ribbon"
        envvars.set_pyrevit_env_var(env_var_ribbon_name, ribbon)
        envvars.set_pyrevit_env_var("last_doc", doc)

        change_ribbon_colours(ribbon, make_colour(base_colour_str))
