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
Hook for launching the default system app for a publish.
"""

import os
import sys
import sgtk
from tank import TankError

HookBaseClass = sgtk.get_hook_baseclass()


class LaunchSystemApp(HookBaseClass):
    """
    Hook for launching the default system app for a published file's path.
    """

    def execute(self, published_file, **kwargs):
        """
        Try to launch the default app defined by the operating
        system.

        :param published_file: A Shotgun published file.
        :raises: `TankError` if it failed to launch an application.
        """
        # Will raise an error if the path is not defined or cannot be resolved.
        # The app will take care of it.
        publish_path = self.get_publish_path(published_file)

        self.logger.debug("Launching default system app for file %s" % publish_path)

        # get the setting
        system = sys.platform

        # run the app
        if system == "linux2":
            cmd = 'xdg-open "%s"' % publish_path
        elif system == "darwin":
            cmd = 'open "%s"' % publish_path
        elif system == "win32":
            cmd = 'cmd.exe /C start "file" "%s"' % publish_path
        else:
            raise TankError("Platform '%s' is not supported." % system)

        self.logger.debug("Executing command '%s'" % cmd)
        exit_code = os.system(cmd)
        if exit_code != 0:
            raise TankError("Failed to launch '%s'!" % cmd)
