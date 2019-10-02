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

It decides which published file to return, or if it needs to raise a TankError.

This implementation returns the first published file it finds, with the proper fields.

"""
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class GetPublishedFile(HookBaseClass):

    def resolve_single_file(self, published_file_type, published_files):
        """
        Decide wether or not to return the published file, or raise a TankError.
        This default implementation returns it.

        :param str published_file_type: PublishedFile or TankPublishedFile.
        :param list published_files: A list of published files, typically
               containing only one element.
        :returns: The published file with the right fields.
        """
        return self.get_published_file(published_file_type, published_files[0]["id"])

    def resolve_multiple_files(self, published_file_type, published_files):
        """
        Decide which published file to return, or raise a TankError.
        This default implementation returns the first one.
        :param str published_file_type: PublishedFile or TankPublishedFile.
        :param list published_files: The published files.
        :returns: The first published file with the right fields.
        """
        return self.get_published_file(published_file_type, published_files[0]["id"])
