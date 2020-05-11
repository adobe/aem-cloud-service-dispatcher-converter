"""
*************************************************************************
* Copyright 2020 Adobe. All rights reserved.
* This file is licensed to you under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License. You may obtain a copy
* of the License at http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software distributed under
* the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
* OF ANY KIND, either express or implied. See the License for the specific language
* governing permissions and limitations under the License.
**************************************************************************/
"""

from util import constants
from util.setup_logger_utility import logger
from util.conversion_report.conversion_step import ConversionStep
from util.conversion_report.conversion_operation import ConversionOperation

from os import rename
from ntpath import basename
from os.path import exists, isdir, dirname
from shutil import rmtree


class FolderOperationsUtility:
    """
    A utility class that provides various static methods pertaining for manipulation of dispatcher files
    """

    @staticmethod
    def __delete_folder__(dir_path, conversion_step):
        """
        Delete specified folder.

        Parameters:
            dir_path (str): The directory to be deleted
            conversion_step(ConversionStep): The conversion step to which the performed actions are to be added.
        """

        # if is directory
        if exists(dir_path) and isdir(dir_path):
            try:
                rmtree(dir_path)
                conversion_operation = ConversionOperation(constants.ACTION_DELETED, dir_path,
                                                           "Deleted folder " + dir_path)
                conversion_step.__add_operation__(conversion_operation)
                logger.info("FolderOperationsUtility: Deleted folder %s", dir_path)
            except OSError as e:
                logger.error("FolderOperationsUtility: %s - %s.", e.filename, e.strerror)
        return True

    @staticmethod
    def __rename_folder__(src_path, dest_path, conversion_step):
        """
        Rename specified folder.

        Parameters:
            dir_path(str): The directory to be renamed
            conversion_step(ConversionStep): The conversion step to which the performed actions are to be added.
        """

        # if path exists
        if exists(src_path) and isdir(src_path):
            try:
                rename(src_path, dest_path)
                conversion_operation = ConversionOperation(constants.ACTION_RENAMED, dirname(src_path), "Renamed folder "
                                                           + basename(src_path) + " to " + basename(dest_path))
                conversion_step.__add_operation__(conversion_operation)
                logger.info("FolderOperationsUtility: Renamed folder %s to %s", src_path, dest_path)
            except OSError as e:
                logger.error("FolderOperationsUtility: %s - %s.", e.filename, e.strerror)
        return True
