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
App that launches a Publish from inside of Shotgun.

"""
from sgtk.util import PublishPathNotDefinedError, PublishPathNotSupported
from tank.platform import Application
from tank import TankError
from tank import Hook
import tank


class LaunchPublish(Application):

    @property
    def context_change_allowed(self):
        """
        Returns whether this app allows on-the-fly context changes without
        needing itself to be restarted.

        :rtype: bool
        """
        return True
    
    def init_app(self):
        deny_permissions = self.get_setting("deny_permissions")
        deny_platforms = self.get_setting("deny_platforms")
        title = self.get_setting("display_name", "Open in Associated Application")
        
        p = {
            "title": title,
            "deny_permissions": deny_permissions,
            "deny_platforms": deny_platforms,
            "supports_multiple_selection": False
        }
        
        self.engine.register_command("launch_publish", self.launch_publish, p)

    def launch_publish(self, entity_type, entity_ids):
        published_file_entity_type = tank.util.get_published_file_entity_type(self.tank)
        if entity_type not in [published_file_entity_type, "Version"]:
            raise Exception("Sorry, this app only works with entities of type %s or Version." % published_file_entity_type)
        if len(entity_ids) != 1:
            raise Exception("Action only accepts a single item.")

        # First, get a list of published files from the entity provided.
        if entity_type == published_file_entity_type:
            published_files = [{"type": entity_type, "id": entity_ids[0]}]
        else:
            # The entity is of type version. Retrieve
            # its published file(s)
            if published_file_entity_type == "PublishedFile":
                published_files_field = "published_files"
            else:
                published_files_field = "tank_published_file"

            v = self.shotgun.find_one(entity_type, [["id", "is", entity_ids[0]]], [published_files_field])
            if not v.get(published_files_field):
                raise TankError("Sorry, this can only be used on %ss with an associated published file." % entity_type)
            published_files = v[published_files_field]

        # Then, resolve a valid published file.
        try:
            if len(published_files) == 1:
                hook_method = "resolve_single_file"
            else:
                hook_method = "resolve_multiple_files"
            published_file = self.execute_hook_method(
                "hook_get_published_file",
                hook_method,
                published_file_type=published_file_entity_type,
                published_files=published_files,
                base_class=BaseHook
            )
        except (TankError, PublishPathNotDefinedError, PublishPathNotSupported) as e:
            self.log_error(
                "Failed to get a published file for %s %s: %s" % (
                    published_file_entity_type,
                    entity_ids[0],
                    e
                )
            )
            return

        # Finally, try to open the published file using launch hooks.
        launch_hooks = self.get_setting("launch_publish_hooks")
        errors = []
        for launch_hook_expr in launch_hooks:
            try:
                self.execute_hook_expression(
                    launch_hook_expr,
                    "execute",
                    base_class=BaseHook,
                    published_file=published_file
                )
                return
            except Exception as e:
                message = "Failed to launch publish for %s with %s: %s" % (
                    published_file,
                    launch_hook_expr,
                    e
                )
                self.logger.debug(message, exc_info=True)
                errors.append(str(e))
        self.log_error(
            "Failed to Launch publish for %s: %s" % (
                published_file, "\n".join(errors)
            ),
        )


class BaseHook(Hook):
    """
    A base hook used to share common functionality for all hooks.
    """
    PUBLISHED_FILE_FIELDS = ["project", "path", "task", "entity"]

    def get_published_file(self, published_file_type, published_file_id):
        """
        Return the PublishedFile or TankPublishedFile with path, task and entity
        fields.

        :param str published_file_type: PublishedFile or TankPublishedFile
        :param int published_file_id: a Shotgun ID.
        :returns: the published file with the right fields.
        """
        return self.parent.shotgun.find_one(
            published_file_type,
            [["id", "is", published_file_id]],
            self.PUBLISHED_FILE_FIELDS
        )
