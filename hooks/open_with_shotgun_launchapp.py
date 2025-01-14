# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Hook for launching the Shotgun app with its engine for a published file.

This hook typically looks at the extension of the published file's path
and based on this determine which launcher app to dispatch
the request to.

If no suitable launcher is found, raise an error, and the app
will try other launch hooks, if provided.
"""

import os

import sgtk
from sgtk import TankError

HookBaseClass = sgtk.get_hook_baseclass()


class LaunchShotgunApp(HookBaseClass):
    def execute(self, published_file, **kwargs):
        """
        Launches the associated app and starts tank.

        :param dict published_file: The published file entity to launch.
        :raises: `TankError` if no valid application was found.
        """
        ########################################################################
        # Example implementation below:
        path = self.get_publish_path(published_file)

        if published_file.get("task"):
            context = self.tank.context_from_entity("Task", published_file["task"].get("id"))
        else:
            context = self.tank.context_from_path(path)
            # In case the path is not relative to the project, or the project has no schema,
            # try to still get a relevant context from the entity or the project.
            # context_from_path calls tank.context.from_path which always returns a context, which at least contains the
            # url. That's why context.project needs to be checked.
            # https://github.com/shotgunsoftware/tk-core/blob/a98bbec19446244f4cfed8895aa926e0a34668d4/python/tank/context.py#L1434
            if not context or not context.project:
                if published_file.get("entity"):
                    context = self.tank.context_from_entity_dictionary(published_file["entity"])
                elif published_file.get("project"):
                    context = self.tank.context_from_entity_dictionary(published_file["project"])
        if context is None:
            raise TankError("Failed to get a valid context from published file: %s" % published_file)
        if path.endswith(".nk"):
            # nuke
            self._do_launch("launchnuke", "tk-nuke", path, context)
            return
        elif path.endswith(".ma") or path.endswith(".mb"):
            # maya
            self._do_launch("launchmaya", "tk-maya", path, context)
            return
        elif path.endswith(".fbx"):
            # Motionbuilder
            self._do_launch("launchmotionbuilder", "tk-motionbuilder", path, context)
            return
        elif path.endswith(".hrox"):
            # Hiero
            self._do_launch("launchhiero", "tk-hiero", path, context)
            return
        elif path.endswith(".max"):
            # 3ds Max
            self._do_launch("launch3dsmax", "tk-3dsmaxplus", path, context)
            return
        elif os.path.splitext(path)[1] in [".psd", ".jpg", ".jpeg", ".png", ".tiff", ".tga"]:
            # Photoshop
            self._do_launch("launchphotoshop", "tk-photoshopcc", path, context)
            return
        # The extension is not valid. Return
        raise TankError("No valid Shotgun Launcher found for %s" % path)

    def _do_software_launcher_launch(self, path, engine_instance_name):
        """
        Attempts to find a Software-entity-style launcher and uses that to
        launch if one is found.

        :param str path: The path to the file to open after launch.
        :param str engine_instance_name: The name of the engine instance to
            bootstrap.

        :raises: RuntimeError when a usable launcher isn't found.
        """
        engine = self.parent.engine
        launchapp_system_name = "tk-multi-launchapp"

        # The apps are keyed by app instance name. We don't actually care
        # what the specific instance is called, as we just want some instance
        # of tk-multi-launchapp. Because of that, we need to check more than
        # just whether the name of the app is a key in the engine's apps
        # property.
        launchapp_commands = []

        for command_name, command_data in engine.commands.iteritems():
            props = command_data["properties"]
            app = props.get("app")
            if app is not None and app.name == launchapp_system_name:
                if props.get("engine_name") == engine_instance_name:
                    launchapp_commands.append(command_data)

        if not launchapp_commands:
            raise RuntimeError(
                "Unable to find an instance of %s currently running!" % launchapp_system_name
            )

        # Check to see if there's a group default. Use that if there is, and if
        # there isn't then we take the first one off the top.
        launch_callback = launchapp_commands[0]["callback"]

        for command_data in launchapp_commands:
            if command_data["properties"].get("group_default"):
                launch_callback = command_data["callback"]
                break

        launch_callback(file_to_open=path)

    def _get_legacy_launch_command(self, launch_app_instance_name):
        """
        Looks for a legacy-style launcher in the current list of running apps.

        :param str launch_app_instance_name: The name of the launchapp instance to look for.

        :returns: A launcher app instance, or None.
        """
        # in older configs, launch instances were named tk-shotgun-launchmaya
        # in newer configs, launch instances are named tk-multi-launchmaya
        old_config = "tk-shotgun-%s" % launch_app_instance_name
        new_config = "tk-multi-%s" % launch_app_instance_name
        app_instance = None
        
        if old_config in self.parent.engine.apps:
            # we have a tk-shotgun-xxx instance in the config
            app_instance = old_config
        elif new_config in self.parent.engine.apps:
            # we have a tk-multi-xxx instance in the config
            app_instance = new_config

        return app_instance

    def _do_launch(self, launch_app_instance_name, engine_name, path, context):
        """
        Tries to create folders then launch the publish.
        """
        # first create folders based on the context - this is important because we 
        # are creating them in deferred mode, meaning that in some cases, new user sandboxes
        # maybe created at this point.
        # This can fail with different kinds of exceptions if the filesystem schema is not configured
        # correctly on the current projet. In this case, just continue.
        try:
            if context.task:
                self.parent.tank.create_filesystem_structure("Task", context.task["id"], engine_name)
            elif context.entity:
                self.parent.tank.create_filesystem_structure(context.entity["type"], context.entity["id"], engine_name)
            elif context.project:
                self.parent.tank.create_filesystem_structure("Project", context.project["id"], engine_name)
        except Exception as e:
            self.logger.warning("Cannot create filesystem structure (skipped): %s" % e)
            self.logger.debug("Cannot create filesystem structure: %s" % e, exc_info=True)
        
        # in ancient configs, launch instances were named tk-shotgun-launchmaya
        # in less-ancient configs, launch instances are named tk-multi-launchamaya
        app_instance = self._get_legacy_launch_command(launch_app_instance_name)

        if app_instance is not None:
            # now try to launch this via the tk-multi-launchapp
            try:
                # use new method
                self.parent.engine.apps[app_instance].launch_from_path_and_context(path, context)
                return
            except AttributeError:
                # fall back onto old method
                self.parent.engine.apps[app_instance].launch_from_path(path)
                return
        else:
            # If we didn't find an old-style launcher, then we need to check for
            # Software entity launchers in the current context.
            try:
                self._do_software_launcher_launch(path, engine_name)
                return
            except RuntimeError:
                # We just need to continue on if this didn't work. It means we're
                # going to be changing to the launch context prior to looking for
                # launchers again.
                pass

        # If we didn't find anything useful in the current context, then we
        # can check the target context. This type of configuration is the approach
        # taken in modern configurations based on tk-config-default2 for secondary
        # entity types like PublishedFile and Version, hence it's likely that this
        # approach will get us where we need to go.
        #
        # Changing context here allows us to find the launchapp that is
        # configured in the target context rather than requiring configuration
        # for every engine in the source context. This is a result of launchapp's
        # need of engine configurations to be present for the Software launcher
        # functionality to be used.
        #
        # The end goal is as follows: For environments using the tk-shotgun-launchpublish
        # app, we do not want launchers registered as engine commands. This is because
        # those will show up in the action menu in the web app as things like "Maya",
        # "Nuke", etc. Instead, we want the user to launch the relevant DCC by way of
        # the command registered by tk-shotgun-launchpublish, which looks at file
        # extensions and determines the correct launcher. The way that this is handled
        # in modern configurations is that the environment where tk-shotgun-launchpublish
        # is configured does NOT contain a launchapp instance (or any old-style launcher
        # app instances). This means no launchapp launchers show up in the web app
        # action menu, but it also means we don't have the launchers available in the
        # current environment. Changing context here means we're moving away from the
        # PublishedFile's specific environment into what it's linked to -- most likely
        # a Task context's shot_step or asset_step environment -- which will have a
        # launchapp instance configured for the tk-shotgun engine.
        sgtk.platform.change_context(context)

        # One last chance to find a legacy-style launcher.
        app_instance = self._get_legacy_launch_command(launch_app_instance_name)

        if app_instance is not None:          
            # now try to launch this via the tk-multi-launchapp
            try:
                # use new method
                self.parent.engine.apps[app_instance].launch_from_path_and_context(path, context)
            except AttributeError:
                # fall back onto old method
                self.parent.engine.apps[app_instance].launch_from_path(path)

        # We're likely in a situation where Software-entity launchers are
        # being used. The route to finding the correct launcher is different
        # in this case, so we can branch the logic here.
        try:
            self._do_software_launcher_launch(path, engine_name)
        except RuntimeError:
            raise TankError(
                "Unable to find a suitable launcher in context "
                "%r for file %s." % (context, path)
            )
            
        

