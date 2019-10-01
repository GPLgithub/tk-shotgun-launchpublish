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
Hook with two methods to get a PublishedFile from a single published file
or a list of published files (legacy TankPublishedFile supported).

This implementation returns the first published file it finds
matching extensions in the order of the valid_extensions parameter.

If none are found, it raises a TankError.
"""

import sgtk
from sgtk import TankError

HookBaseClass = sgtk.get_hook_baseclass()


class GetValidPublishedFile(HookBaseClass):
    """
    """

    def resolve_single_file(self, entity_type, published_file):
        """
        Decide wether or not to return the published file, or raise a TankError.
        Returns the published file only if its path's extension matches one of
        the valid_extensions.

        :param str entity_type: PublishedFile or TankPublishedFile.
        :param dict published_file: The published file.
        :returns: The published file with the right fields.
        :raises: TankError
        """
        valid_extensions = self.parent.get_setting("valid_extensions")
        if not valid_extensions:
            raise TankError(
                "Sorry, valid extensions must be provided."
            )
        sg_published_file = self.parent.published_file(entity_type, published_file["id"])
        path_on_disk = self.get_publish_path(sg_published_file)
        if path_on_disk:
            for app_extension in valid_extensions:
                if path_on_disk.endswith(".%s" % app_extension):
                    return sg_published_file
        raise TankError("PublishedFile path %s does not match valid extensions %s" % (
            path_on_disk,
            valid_extensions
        ))

    def resolve_multiple_files(self, published_file_type, published_files):
        """
        Decide which published file to return, or raise a TankError.
        Return the first published file matching one of the valid_extensions,
        otherwise raise a TankError.

        :param str published_file_type: PublishedFile or TankPublishedFile.
        :param list published_files: The published files.
        :returns: The first published file with the right fields.
        :raises: TankError
        """

        valid_extensions = self.parent.get_setting("valid_extensions")
        if not valid_extensions:
            raise TankError(
                "Sorry, valid extensions must be provided."
            )
        published_file_ids = [pf["id"] for pf in published_files]
        published_files = self.parent.shotgun.find(
            published_file_type,
            [["id", "in", published_file_ids]],
            self.parent.PUBLISHED_FILE_FIELDS
        )
        for app_extension in valid_extensions:
            for published_file in published_files:
                path_on_disk = self.get_publish_path(published_file)
                if path_on_disk and path_on_disk.endswith(".%s" % app_extension):
                    return published_file
        raise TankError(
            "Could not find a published file matching valid extensions %s. Published files: %s" % (
                valid_extensions,
                published_files
            )
        )
