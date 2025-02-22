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
This allows to define in the configuration a path to a single app, maybe
not supported by Shotgun, or if it needs to be opened in a vanilla state.

Typically, a use case would be to define a viewer application, like RV.

This hook can be used in conjunction with the `get_valid_published_file`
hook in order to be sure a proper published file with a valid extension is provided
to the app.

"""

import os
import sys
import sgtk
from tank import TankError

HookBaseClass = sgtk.get_hook_baseclass()


class LaunchApp(HookBaseClass):
    """
    A Hook to open a file in a predefined app.
    """

    def execute(self, published_file, **kwargs):
        """
        Try to launch the defined application for the given
        published file's path.

        :param dict published_file: the published file entity to launch.

        :raises: TankError, PublishPathNotDefinedError, PublishPathNotSupported
        """
        # Will raise an error if the path is not defined or cannot be resolved
        # The app will take care of it.
        # Calling the default Hook implementation method.
        publish_path = self.get_publish_path(published_file)
        self.logger.debug("Launching app for file %s" % publish_path)
        self._launch_app(publish_path)

    def _launch_app(self, path):
        """
        Launches an app based on config settings.
        We assume that the path to the file is just passed as a param to the app.
        This seems to be standard for most apps.

        :param path: a path to a file.
        :raises: `TankError` if the configuration setting for the current
                 platform is not set or if the app failed to launch.
        """
        # get the setting
        system = sys.platform

        app_setting = {"linux2": "app_path_linux",
                       "darwin": "app_path_mac",
                       "win32": "app_path_windows"}.get(system)
        app_path = self.parent.get_setting(app_setting) if app_setting else None
        if not app_path:
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
