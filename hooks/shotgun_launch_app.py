# Copyright (c) 2019 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Hook for launching the published file in an app. The path to the app
in different platforms is defined in the configuration.

This hook can be used in conjunction with the `shotgun_get_valid_published_file`
hook in order to be sure a proper published file with a valid extension is provided
to the app.

"""

import os
import sys
import sgtk
from tank import TankError

HookBaseClass = sgtk.get_hook_baseclass()


class LaunchApp(HookBaseClass):

    def execute(self, published_file, **kwargs):
        # Will raise an error if the path is not defined or cannot be resolved
        # The app will take care of it.
        publish_path = self.get_publish_path(published_file)
        self.logger.error("Launching app for file %s" % publish_path)
        self._launch_app(publish_path)

    def _launch_app(self, path):
        """
        Launches an app based on config settings.
        We assume that the path to the file is just passed as a param to the app.
        This seems to be standard for most apps.
        """
        # get the setting
        system = sys.platform
        try:
            app_setting = {"linux2": "app_path_linux",
                           "darwin": "app_path_mac",
                           "win32": "app_path_windows"}[system]
            app_path = self.parent.get_setting(app_setting)
            if not app_path:
                raise KeyError()
        except KeyError:
            raise TankError("Cannot find app path for platform '%s'." % system)

        # run the app
        if system.startswith("linux"):
            cmd = '%s "%s" &' % (app_path, path)
        elif system == "darwin":
            cmd = 'open -n -a "%s" "%s"' % (app_path, path)
        elif system == "win32":
            cmd = 'start /B "Maya" "%s" "%s"' % (app_path, path)
        else:
            raise TankError("Platform '%s' is not supported." % system)

        self.logger.debug("Executing launch command '%s'" % cmd)
        exit_code = os.system(cmd)
        if exit_code != 0:
            raise TankError("Failed to launch App! This is most likely because the path "
                          "to the app executable is not set to a correct value. The "
                          "current value is '%s' - please double check that this path "
                          "is valid and update as needed in this app's configuration. "
                          "If you have any questions, don't hesitate to contact support "
                          "on support@shotgunsoftware.com." % app_path)
