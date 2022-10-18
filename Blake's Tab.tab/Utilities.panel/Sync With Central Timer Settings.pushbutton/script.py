# -*- coding: utf-8 -*-
__title__ = 'Sync With Central\nTimer Settings'
import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('IronPython.Wpf')
clr.AddReference('System')
clr.AddReference("PresentationCore")
clr.AddReference("PresentationFramework")
from pyrevit import script, forms
from pyrevit.userconfig import user_config
from pyrevit.coreutils import envvars
from pyrevit.framework import Windows
from datetime import datetime, timedelta
from SyncTimer.swc_timer import make_colour, change_ribbon_colours, make_collab_tab_active,\
    change_collab_tab_colour, make_gradient

xamlfile = script.get_bundle_file('swcTimerSettings.xaml')
import wpf

doc = __revit__.ActiveUIDocument.Document
doc_id = str(doc.GetHashCode())
cfg = script.get_config()

env_var_ribbon_name = doc_id + "_ribbon"

nag_disabled = envvars.get_pyrevit_env_var("nag_enabled")
if nag_disabled is None:
    nag_disabled = False
nag_disabled_timer = envvars.get_pyrevit_env_var("nag_disabled_timer")
ribbon = envvars.get_pyrevit_env_var(env_var_ribbon_name)


class SwcTimerSettings(Windows.Window):
    def __init__(self):
        # Setup UI
        wpf.LoadComponent(self, xamlfile)

        make_collab_tab_active(ribbon)

        # Load user configs
        warn_clr = make_colour(user_config.swc_timer.get_option("warning_colour", "#FFD43636"))
        high_clr = make_colour(user_config.swc_timer.get_option("highlight_colour", "#FF6AE26A"))
        self.warning_colour.Background = warn_clr
        self.highlight_colour.Background = high_clr
        self.swc_timer.Value = user_config.swc_timer.get_option("duration", 30)
        self.swc_nag_timer.Value = user_config.swc_timer.get_option("nag_time", 20)
        self.enabled_button.IsChecked = nag_disabled
        try:
            disabled_time = nag_disabled_timer.strftime("%I:%M %p")
        except AttributeError:
            disabled_time = "N/A"

        self.snooze_timer_display.Content = disabled_time

        change_ribbon_colours(ribbon, warn_clr)
        change_collab_tab_colour(ribbon, high_clr)
        make_collab_tab_active(ribbon)

    def window_size_change(self, sender, args):
        # self.overall_window.Height = "Auto"
        pass

    def clicked_snooze(self, sender, args):
        self.snooze_timer_label.Visibility = Windows.Visibility.Visible
        self.snooze_timer_panel.Visibility = Windows.Visibility.Visible
        snooze_length  = int(self.snooze_timer.Value)
        snooze_len_date = timedelta(minutes = snooze_length)
        now = datetime.now()
        new_time = now + snooze_len_date
        self.snooze_timer_display.Content = new_time.strftime("%I:%M %p")
        self.overall_window.MinHeight = 650
        self.overall_window.Height = 650

    def unchecked_snooze(self, sender, args):
        self.snooze_timer_label.Visibility = Windows.Visibility.Collapsed
        self.snooze_timer_panel.Visibility = Windows.Visibility.Collapsed
        self.overall_window.MinHeight = 575
        self.overall_window.Height = 575

    def snooze_slider_change(self, sender, args):
        snooze_length = int(self.snooze_timer.Value)
        snooze_len_date = timedelta(minutes=snooze_length)
        now = datetime.now()
        new_time = now + snooze_len_date
        str_time = new_time.strftime("%I:%M %p")
        self.snooze_timer_display.Content = str_time

    def swc_slider_change(self, sender, args):
        if self.swc_nag_timer.Value > int(self.swc_timer.Value) - 1:
            self.swc_nag_timer.Value = int(self.swc_timer.Value) - 1
            self.nag_value.Content = int(self.swc_timer.Value) - 1
        self.swc_nag_timer.Maximum = int(self.swc_timer.Value) - 1

        self.nag_value.Content = int(self.swc_timer.Value) - 1

        self.duration_label.Content = int(self.swc_timer.Value)

    def nag_slider_change(self, sender, args):
        self.nag_label.Content = int(self.swc_nag_timer.Value)

    def click_warning_colour(self, sender, args):
        warning_colour_old = cfg.get_option("warning_colour", "#FFD43636")
        warning_colour_str = forms.ask_for_color(default=warning_colour_old or None)
        if warning_colour_str is not None:
            warning_colour = make_colour(warning_colour_str)
            self.warning_colour.Background = warning_colour
            change_ribbon_colours(ribbon, warning_colour)
            change_collab_tab_colour(ribbon, self.highlight_colour.Background)

    def click_highlight_colour(self, sender, args):
        highlight_colour_str = forms.ask_for_color(default=None or "#FF6AE26A")
        if highlight_colour_str is not None:
            highlight_colour = make_colour(highlight_colour_str)
            self.highlight_colour.Background = highlight_colour
            change_collab_tab_colour(ribbon, highlight_colour)

    def data_window_closing(self, sender, args):
        duration = int(self.swc_timer.Value)
        nag_time = int(self.swc_nag_timer.Value)

        times = [x / 20.0 for x in range((nag_time * 20), (duration * 20), duration)]
        now = datetime.now()
        env_var_timer_name = doc_id + "_timer"
        history_datetime = envvars.get_pyrevit_env_var(env_var_timer_name)
        colour_gradient = envvars.get_pyrevit_env_var("warning_gradient")
        base_colour = envvars.get_pyrevit_env_var("base_colour")

        if history_datetime is None:
            minutes = 0
        else:
            difference = now - history_datetime
            minutes = difference.total_seconds() / 60

        # new_tab_colour = base_colour
        if minutes < times[0]:
            new_tab_colour = base_colour
        else:
            for t, g in zip(times, colour_gradient):
                if minutes > t:
                    new_tab_colour = g
        for tab in ribbon.Tabs:
            for panel in tab.Panels:
                panel.CustomPanelBackground = new_tab_colour
                panel.CustomPanelTitleBarBackground = new_tab_colour

    def click_save_settings(self, sender, args):
        try:
            user_config.add_section('swc_timer')
        except:
            pass

        user_config.swc_timer.duration = self.swc_timer.Value
        user_config.swc_timer.nag_time = self.swc_nag_timer.Value
        warning_colour_str = self.warning_colour.Background.Color.ToString()
        user_config.swc_timer.warning_colour = warning_colour_str
        user_config.swc_timer.highlight_colour = self.highlight_colour.Background.Color.ToString()
        user_config.save_changes()

        gradient_colours = make_gradient("#EEEEEE", warning_colour_str)

        snooze_length = int(self.snooze_timer.Value)
        snooze_len_date = timedelta(minutes=snooze_length)
        now = datetime.now()
        new_time = now + snooze_len_date

        env_var_duration_name = doc_id + "_duration"
        env_var_nag_time_name = doc_id + "_nag_time"
        envvars.set_pyrevit_env_var("warning_colour", self.warning_colour.Background)
        envvars.set_pyrevit_env_var("warning_gradient", gradient_colours)
        envvars.set_pyrevit_env_var("highlight_colour", self.highlight_colour.Background)
        envvars.set_pyrevit_env_var(env_var_duration_name, int(self.swc_timer.Value))
        envvars.set_pyrevit_env_var(env_var_nag_time_name, int(self.swc_nag_timer.Value))
        envvars.set_pyrevit_env_var("nag_enabled", self.enabled_button.IsChecked)
        envvars.set_pyrevit_env_var("nag_disabled_timer", new_time)

        self.Close()


SwcTimerSettings().ShowDialog()
