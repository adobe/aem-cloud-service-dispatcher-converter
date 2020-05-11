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
from util.conversion_report.conversion_operation import ConversionOperation
from util.conversion_report.conversion_step import ConversionStep

from collections import deque
from glob import glob
from ntpath import basename
from os import listdir, remove, rename
from os.path import exists, isfile, isdir, join, dirname
from re import search
from typing import List


class FileOperationsUtility:
    """
    A utility class that provides various static methods pertaining for manipulation of dispatcher files
    """

    @staticmethod
    def __delete_file__(file_path, conversion_step):
        """
        Deletes the file provided.

        Parameters:
            file_path (str): The path to the file to be deleted
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.

        """

        # if path exists
        if exists(file_path) and isfile(file_path):
            try:
                remove(file_path)
                logger.info("FileOperationsUtility: Deleted file %s", file_path)
                conversion_operation = ConversionOperation(constants.ACTION_DELETED, dirname(file_path),
                                                           "Deleted file " + file_path)
                conversion_step.__add_operation__(conversion_operation)
            except OSError as e:
                logger.error("FileOperationsUtility: %s - %s.", e.filename, e.strerror)

    @staticmethod
    def __delete_files_with_extension__(dir_path, extension, conversion_step):
        """
        Deletes all files with given extension in a specific directory.
        Does not check sub-directories.

        Parameters:
            dir_path (str): The path to the directory where the deletion is to be performed
            extension (str): The file extension which is to be matched for deletion
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.
        """

        if exists(dir_path) and isdir(dir_path):
            # get all files with the specified extension under the provided path
            files = [f for f in glob(join(dir_path, "*." + extension), recursive=False)]
            for f in files:
                logger.info("FileOperationsUtility: Deleted file %s", f)
                conversion_operation = ConversionOperation(constants.ACTION_DELETED, dirname(f), "Deleted file " + f)
                conversion_step.__add_operation__(conversion_operation)
                FileOperationsUtility.__delete_file__(f, conversion_step)

    @staticmethod
    def __delete_all_files_containing_substring__(dir_path, substring, conversion_step):
        """
        Deletes all files containing given substring in a specific directory.
        Does not check sub-directories.

        Parameters:
            dir_path (str): The path to the directory where the deletion is to be performed
            substring (str): The sub-string in the file name which is to be matched for deletion
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.
        """

        if exists(dir_path) and isdir(dir_path):
            # get all files with the specified substring in their names under the provided path
            files = [f for f in glob(join(dir_path, "*" + substring + "*.*"), recursive=False)]
            for f in files:
                logger.info("FileOperationsUtility: Deleted file %s", f)
                conversion_operation = ConversionOperation(constants.ACTION_DELETED, dirname(f), "Deleted file " + f)
                conversion_step.__add_operation__(conversion_operation)
                FileOperationsUtility.__delete_file__(f, conversion_step)

    @staticmethod
    def __delete_all_files_with_prefix__(dir_path, prefix, conversion_step):
        """
        Deletes all files containing given prefix in a specific directory.
        Does not check sub-directories.

        Parameters:
            dir_path (str): The path to the directory where the deletion is to be performed
            prefix (str): The file name prefix which is to be matched for deletion
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.
        """

        if exists(dir_path) and isdir(dir_path):
            # get all files with the specified prefix under the provided path
            files = [f for f in glob(join(dir_path, prefix + "*.*"), recursive=False)]
            for f in files:
                logger.info("FileOperationsUtility: Deleted file %s", f)
                conversion_operation = ConversionOperation(constants.ACTION_DELETED, dirname(f), "Deleted file " + f)
                conversion_step.__add_operation__(conversion_operation)
                FileOperationsUtility.__delete_file__(f, conversion_step)

    @staticmethod
    def __delete_all_files_not_conforming_to_pattern__(dir_path, pattern, conversion_step):
        """
        Delete all files in a given directory (recursively) on conforming to the given pattern (eg. '*.vars').
        Returns the files remaining.

        Parameters:
            dir_path (str): The path to the directory where the deletion is to be performed
            pattern (str): The file pattern to be persisted
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.

        Returns:
             a list containing the names of the files in the directory.

        """
        files = [f for f in glob(join(dir_path, "**", pattern), recursive=True)]
        # delete any other file present in the folder that doesn't match the pattern '*.vars'
        for f in [f for f in glob(join(dir_path, "*.*"), recursive=True)]:
            if f not in files:
                FileOperationsUtility.__delete_file__(f, conversion_step)
        return [f for f in glob(join(dir_path, "**", pattern), recursive=True)]

    @staticmethod
    def __rename_file__(src_path, dest_path, conversion_step):
        """
        Rename a file.

        Parameters:
            src_path (str): The path to file to be renamed
            dest_path (str): The renamed file path string
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.
        """

        # if path exists
        if exists(src_path) and isfile(src_path):
            try:
                rename(src_path, dest_path)
                logger.info("FileOperationsUtility: Renamed file %s to %s", src_path, dest_path)
                conversion_operation = ConversionOperation(constants.ACTION_RENAMED, dirname(src_path), "Renamed file "
                                                           + basename(src_path) + " to " + basename(dest_path))
                conversion_step.__add_operation__(conversion_operation)
            except OSError as e:
                logger.error("FileOperationsUtility: %s - %s.", e.filename, e.strerror)

    @staticmethod
    def __get_content_from_file__(file_path):
        """
        Returns the content of a given file.

        Parameters:
            file_path (str): The path to file whose content is to be retrieved

        Returns:
            str: Content of the file
        """

        # add the file name as comment in 1st line, to denote the source of the content
        rules = ["# Content from file : '" + file_path[file_path.index("src"):] + "'\n"]
        if exists(file_path) and isfile(file_path):
            try:
                # open the file and read the file
                with open(file_path) as file:
                    file_content = file.readlines()
                file.close()
                # all lines (except blank newlines) in the file are added to content
                for line in file_content:
                    if line != "\n":
                        rules.append(line)
                logger.debug("FileOperationsUtility: Extracted content from file %s", file_path)
            except OSError as e:
                logger.error("FileOperationsUtility: %s - %s.", e.filename, e.strerror)
        return rules

    @staticmethod
    def __remove_virtual_host_sections_not_port_80__(dir_path, conversion_step):
        """
        Remove any VirtualHost section not referring to port 80 from all vhost files under specified directory.

        Parameters:
            dir_path (str): The path to dir where the vhost files reside
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.
        """

        if exists(dir_path) and isdir(dir_path):
            files = [f for f in glob(join(dir_path, "*.vhost"), recursive=False)]
            for vhost_file in files:
                if isfile(vhost_file):
                    try:
                        # flag denoting whether the
                        virtual_host_section_not_port_80_flag = False
                        # open the file in read-mode and read the file
                        with open(vhost_file, "r") as file:
                            file_content = file.readlines()
                        file.close()
                        # open the file in write-mode and write to the file,
                        # removing the VirtualHost sections not referring to port 80
                        with open(vhost_file, "w") as file:
                            for line in file_content:
                                # if it is start of a virtual host section which does not refer to port 80
                                # mark the start of the virtual host section, i.e. lines to be removed
                                if line.startswith(constants.VIRTUAL_HOST_SECTION_START) and not \
                                        line.strip("\n").endswith(constants.VIRTUAL_HOST_SECTION_START_PORT_80):
                                    virtual_host_section_not_port_80_flag = True
                                    logger.debug(
                                        "FileOperationsUtility: Found virtual host section (not port 80) found in %s",
                                        vhost_file)
                                    continue
                                # if it end of is a virtual host section which does not refer to port 80
                                # mark the end of the virtual host section, i.e. lines to persist
                                if line.strip() == constants.VIRTUAL_HOST_SECTION_END and \
                                        virtual_host_section_not_port_80_flag:
                                    virtual_host_section_not_port_80_flag = False
                                    logger.info(
                                        "FileOperationsUtility: Removed virtual host section (not port 80) found in %s",
                                        vhost_file)
                                    conversion_operation = ConversionOperation(constants.ACTION_REMOVED,
                                                                               vhost_file, "Removed virtual host"
                                                                                           " section (not port 80)")
                                    conversion_step.__add_operation__(conversion_operation)
                                    continue
                                # if current line belongs to a virtual host section which refers to port 80, keep it
                                if not virtual_host_section_not_port_80_flag:
                                    file.write(line)
                    except OSError as e:
                        logger.error("FileOperationsUtility: %s - %s.", e.filename, e.strerror)

    @staticmethod
    def __remove_or_replace_file_include(conversion_step, file_path, include_statement_syntax, old_rule_name,
                                         new_rule_name=None, replace_rule=None):
        """
        Remove or replace inclusion of some file. If replacement file is not specified, the include statement is removed.
        """

        if exists(file_path) and isfile(file_path):
            try:
                # open the file in read mode and read it
                with open(file_path) as file:
                    file_content = file.readlines()
                file.close()
                # open the file in write-mode and write to the file,
                # replacing/removing the include statements as applicable
                with open(file_path, "w") as file:
                    for line in file_content:
                        stripped_line = line.strip()
                        if stripped_line.startswith(include_statement_syntax) and stripped_line.find(old_rule_name) > 1:
                            logger.debug("FileOperationsUtility: Found include statement '%s' in file %s.",
                                         stripped_line, file_path)
                            # in the include statements, replace the old rule file with the new one
                            if new_rule_name is not None:
                                if replace_rule is not None:
                                    line = line[:len(line) - len(
                                        stripped_line) - 1] + include_statement_syntax + " " + new_rule_name + '\n'
                                    file.write(line)
                                    logger.info(
                                        "FileOperationsUtility: Replacing include statement '%s' with '%s' in %s",
                                        stripped_line, line.strip(), file_path)
                                    conversion_operation = ConversionOperation(constants.ACTION_REPLACED, file_path,
                                                                               "Replacing include statement rule "
                                                                               + stripped_line + " with " + line.strip())
                                else:
                                    line = line.replace(old_rule_name, new_rule_name)
                                    file.write(line)
                                    logger.info(
                                        "FileOperationsUtility: Replacing include statement '%s' with '%s' in %s",
                                        stripped_line, line.strip(), file_path)
                                    conversion_operation = ConversionOperation(constants.ACTION_REPLACED, file_path,
                                                                               "Replacing include statement "
                                                                               + old_rule_name + " with " + new_rule_name)
                                conversion_step.__add_operation__(conversion_operation)
                            # removing the include statements
                            else:
                                logger.info("FileOperationsUtility: Removing include statement '%s' from %s",
                                            stripped_line, file_path)
                                conversion_operation = ConversionOperation(constants.ACTION_REMOVED, file_path,
                                                                           "Removing include statement "
                                                                           + old_rule_name)
                                conversion_step.__add_operation__(conversion_operation)
                                continue
                        else:
                            file.write(line)
            except OSError as e:
                logger.error("FileOperationsUtility: %s - %s.", e.filename, e.strerror)

    @staticmethod
    def __remove_include_statement_for_some_rule__(dir_path, include_statement_syntax,
                                                   file_extension, rule_file_name_to_remove,
                                                   conversion_step):
        """
        Remove inclusion of some file from all files os given file-extension in specified directory and sub-directories.

        Parameters:
            dir_path (str): The path to directory whose files are to be processed
            include_statement_syntax (str): The syntax of the include statement to be looked for
            file_extension (str): The extension of the type that needs to be processed
            rule_file_name_to_remove (str): The rule file name (in include statement) that is to be removed
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.
        """

        if exists(dir_path) and isdir(dir_path):
            # get all files under given directory and sub-directories with given file extension
            files = [f for f in glob(join(dir_path, "**", "*." + file_extension), recursive=True)]
            #  lookup for include statements of the specified rule and remove them
            for file in files:
                FileOperationsUtility.__remove_or_replace_file_include(conversion_step, file, include_statement_syntax,
                                                                       rule_file_name_to_remove)

    @staticmethod
    def __replace_file_name_in_include_statement__(dir_path, file_extension, include_statement_syntax,
                                                   file_to_replace, file_to_replace_with,
                                                   conversion_step):
        """
        Replace the file name (with new file name) in all include statements from all files os given file-extension in
        specified directory and sub-directories.
        Usage scenario : In all include statements including the file `ams_publish_filters.any` replace it with
        inclusion of the file `"filters.any"`.


        Parameters:
            dir_path (str): The path to directory whose files are to be processed
            include_statement_syntax (str): The syntax of the include statement to be looked for
            file_extension (str): The extension of the type that needs to be processed
            file_to_replace (str): The rule file name (in include statement) that is to be replaced
            file_to_replace_with (str): The rule file name (in include statement) that is to be replaced with
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.
        """

        if exists(dir_path) and isdir(dir_path):
            # get all files under given directory and sub-directories with given file extension
            files = [f for f in glob(join(dir_path, "**", "*." + file_extension), recursive=True)]
            # lookup for include statements of the specified rule, and replace them with new rule
            for file in files:
                FileOperationsUtility.__remove_or_replace_file_include(conversion_step, file, include_statement_syntax,
                                                                       file_to_replace,
                                                                       file_to_replace_with)

    @staticmethod
    def __replace_rule_in_include_statement__(dir_path, file_extension, include_statement_syntax,
                                              file_to_replace, rule_to_replace_with,
                                              conversion_step):
        """
        Replace inclusion rule (with new rule) from all files os given file-extension in specified directory
        and sub-directories.
        Usage scenario : In all include statements including the file `ams_publish_filters.any` replace with the
        rule `"../filters/filters.any"`

        Parameters:
            dir_path (str): The path to directory whose files are to be processed
            include_statement_syntax (str): The syntax of the include statement to be looked for
            file_extension (str): The extension of the type that needs to be processed
            file_to_replace (str): The file name (in the rule) that is to be replaced
            rule_to_replace_with (str): The complete rule (in include statement) that is to be replaced with
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.
        """

        if exists(dir_path) and isdir(dir_path):
            # get all files under given directory and sub-directories with given file extension
            files = [f for f in glob(join(dir_path, "**", "*." + file_extension), recursive=True)]
            # lookup for include statements of the specified rule, and replace them with new rule
            for file in files:
                FileOperationsUtility.__remove_or_replace_file_include(conversion_step, file, include_statement_syntax,
                                                                       file_to_replace,
                                                                       rule_to_replace_with, True)

    @staticmethod
    def __remove_or_replace_include_pattern_in_section(file_path, section_header, include_pattern_to_replace,
                                                       include_pattern_to_replace_with, conversion_step):
        """
        Remove-replace include statements of certain pattern within specified sections of a file.
        """

        if exists(file_path) and isfile(file_path):
            start_of_section = False
            already_replaced = False
            section_indentation = 0
            try:
                # open the file in read mode and read it
                with open(file_path) as file:
                    file_content = file.readlines()
                file.close()
                # open the file in write-mode and write to the file,
                with open(file_path, "w") as file:
                    for line in file_content:
                        stripped_line = line.strip()
                        # remove any contents in the given section
                        # and replace with given include statements as applicable
                        if stripped_line.startswith(section_header):
                            section_indentation = len(line) - len(stripped_line)
                            start_of_section = True
                            file.write(line)
                        # if section is found, replace the include statements within of the section
                        elif start_of_section:
                            if stripped_line.startswith(include_pattern_to_replace):
                                # say we want to replace any clientheader include statements that looks as follows:
                                # $include "/etc/httpd/conf.dispatcher.d/clientheaders/ams_publish_clientheaders.any"
                                # $include "/etc/httpd/conf.dispatcher.d/clientheaders/ams_common_clientheaders.any"
                                # with the statement:
                                # $include "../clientheaders/default_clientheaders.any"
                                # we only need to replace the include statement once.
                                if already_replaced:
                                    logger.info(
                                        "FileOperationsUtility: Removed include statement '%s' in %s section of file "
                                        "%s.", stripped_line, section_header, file_path)
                                    conversion_operation = ConversionOperation(constants.ACTION_REMOVED, file_path,
                                                                               "Removed include statement '" + stripped_line
                                                                               + "' in section '" + section_header + "'")
                                    conversion_step.__add_operation__(conversion_operation)
                                    continue
                                else:
                                    already_replaced = True
                                    file.write(line[:len(line) - len(stripped_line) - 1] +
                                               include_pattern_to_replace_with + '\n')
                                    logger.info(
                                        "FileOperationsUtility: Replaced include statement '%s' of %s section with "
                                        "include statement '%s' in file %s.",
                                        stripped_line, section_header, include_pattern_to_replace_with, file_path)
                                    conversion_operation = ConversionOperation(constants.ACTION_REPLACED, file_path,
                                                                               "Replaced include statement '" + stripped_line
                                                                               + "' in section '" + section_header
                                                                               + "' with '"
                                                                               + include_pattern_to_replace_with + "'")
                                    conversion_step.__add_operation__(conversion_operation)
                            elif stripped_line == "}" and len(line) - len(stripped_line) == section_indentation:
                                start_of_section = False
                                file.write(line)
                            else:
                                file.write(line)
                        # write out other lines as is
                        else:
                            file.write(line)
            except OSError as e:
                logger.error("FileOperationsUtility: %s - %s.", e.filename, e.strerror)

    @staticmethod
    def __replace_include_pattern_in_section__(dir_path, file_extension, section_header, pattern_to_replace,
                                               file_to_replace_with, conversion_step):
        """
        Replace include statements of certain pattern within specified sections of all files (of given file extension)
        in specified directory and sub-directories.

        Parameters:
            dir_path (str): The path to directory whose files are to be processed
            file_extension (str): The extension of the type that needs to be processed
            section_header (str): The section header (within the file), whose content is to be processed
            pattern_to_replace (str): include statement pattern that is to be replaced
            file_to_replace_with (str): include statement pattern that is to be replaced with
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.
        """

        if exists(dir_path) and isdir(dir_path):
            # get all files under given directory and sub-directories with given file extension
            files = [f for f in glob(join(dir_path, "**", "*." + file_extension), recursive=True)]
            # lookup for include statements of the specified rule, and replace them with new rule
            for file in files:
                FileOperationsUtility.__remove_or_replace_include_pattern_in_section(file, section_header,
                                                                                     pattern_to_replace,
                                                                                     file_to_replace_with,
                                                                                     conversion_step)

    @staticmethod
    def __replace_file_include_with_file_content(file_path, include_statement_syntax, rule_file_to_replace,
                                                 rule_file_content, conversion_step):
        """
        Replace file include statements with the content of the included file itself.
        """

        if exists(file_path) and isfile(file_path):
            try:
                # open the file in read mode and read it
                with open(file_path) as file:
                    file_content = file.readlines()
                file.close()
                # open the file in write-mode and write to the file,
                # replacing/removing the include statements as applicable
                with open(file_path, "w") as file:
                    for line in file_content:
                        stripped_line = line.strip()
                        if stripped_line.startswith(include_statement_syntax) and (
                                stripped_line.endswith(rule_file_to_replace) or stripped_line.endswith(
                            rule_file_to_replace + '"')):
                            logger.debug("FileOperationsUtility: Found include statement '%s' in file %s.",
                                         stripped_line, file_path)
                            # get the indentation of the include statement
                            indentation = len(line) - len(stripped_line)
                            # replace the include statement with the rule file's content
                            if rule_file_content is not None:
                                for line_from_rule_file_content in rule_file_content:
                                    # adjust the line to match the include statement's indentation
                                    file.write(line[:indentation - 1] + line_from_rule_file_content)
                            logger.info("FileOperationsUtility: Replaced include statement '%s' in file %s.",
                                        stripped_line, file_path)
                            conversion_operation = ConversionOperation(constants.ACTION_REPLACED, file_path,
                                                                       "Replaced include statement '" + stripped_line
                                                                       + " with content of file '"
                                                                       + rule_file_to_replace + "'")
                            conversion_step.__add_operation__(conversion_operation)
                        # write out other lines as is
                        else:
                            file.write(line)
            except OSError as e:
                logger.error("FileOperationsUtility: %s - %s.", e.filename, e.strerror)

    @staticmethod
    def __replace_include_statement_with_content_of_rule_file__(dir_path, file_extension,
                                                                rule_file_to_replace, content,
                                                                include_statement_syntax, conversion_step):
        """
        Replace file include statements with the content of the included file itself, in all files of given file-type
        in specified directory and sub-directories.

        Parameters:
            dir_path (str): The path to directory whose files are to be processed
            file_extension (str): The extension of the type that needs to be processed
            rule_file_to_replace (str): include statement pattern that is to be replaced
            content (str): The content of file with which the include statement is to be replaced
            include_statement_syntax (str): The syntax of the include statement to be replaced
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.
        """

        if exists(dir_path) and isdir(dir_path):
            # get all files under given directory and sub-directories with given file extension
            files = [f for f in glob(join(dir_path, "**", "*." + file_extension), recursive=True)]
            # lookup for include statements of the specified rule, and replace them with new rule
            for file in files:
                FileOperationsUtility.__replace_file_include_with_file_content(file, include_statement_syntax,
                                                                               rule_file_to_replace, content,
                                                                               conversion_step)

    @staticmethod
    def __replace_variable_usage(file_path, variable_to_replace, new_variable, conversion_step):
        """
        Replace usage of a variable with a new variable.
        """

        if exists(file_path) and isfile(file_path):
            try:
                # open the file in read mode and read it
                with open(file_path) as file:
                    file_content = file.readlines()
                file.close()
                # open the file in write-mode and write to the file,
                # replacing the variable, if found, with the new variable
                with open(file_path, "w") as file:
                    for line in file_content:
                        if line.find(variable_to_replace) != -1:
                            file.write(line.replace(variable_to_replace, new_variable))
                            logger.info("FileOperationsUtility: Replaced variable '%s' with variable '%s' in file %s.",
                                        variable_to_replace, new_variable, file_path)
                            conversion_operation = ConversionOperation(constants.ACTION_REPLACED, file_path,
                                                                       "Replaced variable '" + variable_to_replace
                                                                       + " with new variable '" + new_variable + "'")
                            conversion_step.__add_operation__(conversion_operation)
                        else:
                            file.write(line)
            except OSError as e:
                logger.error("FileOperationsUtility: %s - %s.", e.filename, e.strerror)

    @staticmethod
    def __replace_all_usage_of_old_variable_with_new_variable__(dir_path, file_extension, variable_to_replace,
                                                                new_variable, conversion_step):
        """
        Replace usage of a variable with a new variable in all files of given file-type in specified directory and
        sub-directories.

        Parameters:
            dir_path (str): The path to directory whose files are to be processed
            file_extension (str): The extension of the type that needs to be processed
            variable_to_replace (str): The variable that is to be replaced
            new_variable (str): The variable that is to be replaced with
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.
        """

        if exists(dir_path) and isdir(dir_path):
            # get all files under given directory and sub-directories with given file extension
            files = [f for f in glob(join(dir_path, "**", "*." + file_extension), recursive=True)]
            # lookup for include statements of the specified rule, and replace them with new rule
            for file in files:
                FileOperationsUtility.__replace_variable_usage(file, variable_to_replace, new_variable, conversion_step)

    @staticmethod
    def __remove_variable_usage(file_path, variable_to_replace, conversion_step):
        """
        Remove usage of specified variable.
        """

        if exists(file_path) and isfile(file_path):
            try:
                # open the file in read mode and read it
                with open(file_path) as file:
                    file_content = file.readlines()
                file.close()
                # a FIFO based record to keep track of nested if-block opening and closing
                # (something like parentheses balancing)
                stack = deque([], 10)
                # a flag denoting whether the current statement being processed lies inside a if-block
                # which is to be removed
                skip_flag = False
                # open the file in write-mode and write to the file,
                with open(file_path, "w") as file:
                    for line in file_content:
                        # if variable to be removed is used in if-statement, remove the whole if-block
                        # keeping track of if-block opening and closing (for nested if-blocks) in the FIFO record
                        if line.strip().startswith(constants.IF_BLOCK_START) and line.find(variable_to_replace) != -1:
                            stack.append(constants.IF_BLOCK_START)
                            skip_flag = True
                            logger.debug(
                                "FileOperationsUtility: Found usage of variable '%s' in 'if' condition in file %s.",
                                variable_to_replace, file_path)
                        # if variable to be removed is used in normal line of statement, remove the line
                        elif line.find(variable_to_replace) != -1:
                            logger.info("FileOperationsUtility: Removed usage of variable '%s' in file %s.",
                                        variable_to_replace, file_path)
                            conversion_operation = ConversionOperation(constants.ACTION_REMOVED, file_path,
                                                                       "Removed variable '" + variable_to_replace + "'")
                            conversion_step.__add_operation__(conversion_operation)
                            continue
                        # if current line is under an if-block which used the variable to replace
                        # remove the current line, take care of inner if blocks if present
                        elif skip_flag:
                            # when a new nested if-block starts, keep track of it,
                            # by adding entry denoting start of new if-block
                            if line.strip().startswith(constants.IF_BLOCK_START):
                                stack.append(constants.IF_BLOCK_START)
                            # when if-block ends, remove the entry for the if-block previously recorded,
                            # this will continue until the original if-block is processed and stack becomes empty
                            elif line.strip().endswith(constants.IF_BLOCK_END):
                                stack.pop()
                                # stack is empty, i.e. the whole if-block has been removed, set skip flag to False
                                if not stack:
                                    skip_flag = False
                                    logger.debug(
                                        "FileOperationsUtility: Removed usage of variable '%s' in 'if' condition in "
                                        "file %s.", variable_to_replace, file_path)
                                    conversion_operation = ConversionOperation(constants.ACTION_REMOVED, file_path,
                                                                               "Removed 'if' condition which used "
                                                                               "variable '" + variable_to_replace + "'")
                                    conversion_step.__add_operation__(conversion_operation)
                        # if it is just a normal statement, keep it
                        else:
                            file.write(line)
            except OSError as e:
                logger.error("FileOperationsUtility: %s - %s.", e.filename, e.strerror)

    @staticmethod
    def __remove_all_usage_of_old_variable__(dir_path, file_extension, variable_to_remove, conversion_step):
        """
        Replace usage of specified variable in all files of given file-type in specified directory and sub-directories.

        Parameters:
            dir_path (str): The path to directory whose files are to be processed
            file_extension (str): The extension of the type that needs to be processed
            variable_to_remove (str): The variable that is to be removed
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.
        """

        if exists(dir_path) and isdir(dir_path):
            # get all files under given directory and sub-directories with given file extension
            files = [f for f in glob(join(dir_path, "**", "*." + file_extension), recursive=True)]
            # lookup for include statements of the specified rule, and replace them with new rule
            for file in files:
                FileOperationsUtility.__remove_variable_usage(file, variable_to_remove, conversion_step)

    @staticmethod
    def __replace_particular_section_content_with_include_statement(file_path, section_header,
                                                                    include_statement_to_replace_with,
                                                                    conversion_step):
        """
        Replace the content of specified section with given file include statement.
        """

        if exists(file_path) and isfile(file_path):
            start_of_section = False
            retrieved_content_indentation = False
            content_indentation = ""
            section_indentation = 0
            try:
                # open the file in read mode and read it
                with open(file_path) as file:
                    file_content = file.readlines()
                file.close()
                # open the file in write-mode and write to the file,
                with open(file_path, "w") as file:
                    for index, line in enumerate(file_content):
                        stripped_line = line.strip()
                        # remove any contents in the given section
                        # and replace with given include statements as applicable
                        if stripped_line.startswith(section_header):
                            section_indentation = len(line) - len(stripped_line)
                            start_of_section = True
                            file.write(line)
                            if not stripped_line.endswith("{"):
                                next_line = file_content[index + 1]
                                file.write(next_line)
                                section_indentation = len(next_line) - len(next_line.strip())
                        # if section is found, replace the content of the section
                        elif start_of_section:
                            if stripped_line == "}" and len(line) - len(stripped_line) == section_indentation:
                                start_of_section = False
                                file.write(content_indentation + include_statement_to_replace_with + '\n')
                                file.write(line)
                                logger.info(
                                    "FileOperationsUtility: Replaced content of %s section with include statement "
                                    "'%s' in file %s.", section_header, include_statement_to_replace_with, file_path)
                                conversion_operation = ConversionOperation(constants.ACTION_REPLACED, file_path,
                                                                           "Replaced content of section '"
                                                                           + section_header + "' with include statement "
                                                                           + include_statement_to_replace_with)
                                conversion_step.__add_operation__(conversion_operation)
                            # for any content inside the section, retrieve the line's indentation
                            elif not retrieved_content_indentation:
                                content_indentation = line[:len(line) - len(stripped_line) - 1]
                                retrieved_content_indentation = True
                        # write out other lines as is
                        else:
                            file.write(line)
            except OSError as e:
                logger.error("FileOperationsUtility: %s - %s.", e.filename, e.strerror)

    @staticmethod
    def __replace_content_of_section__(dir_path, extension, section_header, include_statement_to_replace_with,
                                       conversion_step):
        """
        Replace the content of specified section with given file include statement, in all files of specified type
        in provided directory and sub-directories.

        Parameters:
            dir_path (str): The path to directory whose files are to be processed
            section_header (str): The section header (within the file), whose content is to be replaced
            include_statement_to_replace_with (str): include statement pattern that is to be replaced with
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.
        """

        if exists(dir_path) and isdir(dir_path):
            # get all farm files under given directory and sub-directories
            files = [f for f in glob(join(dir_path, "**", "*." + extension), recursive=True)]
            # lookup and remove any contents in the given section and replace them with given include statement
            for file in files:
                FileOperationsUtility.__replace_particular_section_content_with_include_statement(file, section_header,
                                                                                                  include_statement_to_replace_with,
                                                                                                  conversion_step)

    @staticmethod
    def __remove_non_whitelisted_directives_in_vhost_files__(dir_path, whitelisted_directives_set, conversion_step):
        """
        Report and remove usage of non-whitelisted directives in configuration files

        Parameters:
            dir_path (str): The path to directory whose files are to be processed
            whitelisted_directives_set (str): The set of whitelisted directives that are allowed (lowercase)
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.
        """

        if exists(dir_path) and isdir(dir_path):
            # get files of the format dir_path/*.vhost
            files = [f for f in glob(join(dir_path, "*.vhost"), recursive=False)]
            non_whitelisted_directive_usage = []
            for file_path in files:
                # open the file in read mode and read it
                with open(file_path) as file:
                    file_content = file.readlines()
                file.close()
                line_count = 0
                start_of_section_directives_list = []
                # open the file in write-mode and write to the file,
                with open(file_path, "w") as file:
                    for line in file_content:
                        line_count += 1
                        stripped_line = line.strip()
                        file_path_with_line = file_path[file_path.find("conf.d"):] + ':' + str(line_count)
                        # if section with non-whitelisted directive is found
                        if len(start_of_section_directives_list) > 0:
                            # we need to comment all lines in the section
                            file.write(constants.COMMENT_ANNOTATION + line)
                            logger.info(
                                "FileOperationsUtility: Commenting non-whitelisted directive usage in %s.",
                                file_path_with_line)
                            # check if start of section, pop last added directive from stack
                            if stripped_line.startswith('</'):
                                directive = stripped_line.replace('/', '')
                                # if non-whitelisted directive is found, add to log
                                if directive.lower() not in whitelisted_directives_set:
                                    non_whitelisted_directive_usage.append(file_path_with_line + ' ' + directive)
                                start_of_section_directives_list.pop()
                            elif stripped_line.startswith('<'):
                                # check if start of section, push directive to stack
                                directive = stripped_line.split()[0] + '>'
                                start_of_section_directives_list.append(directive)
                        elif not stripped_line.startswith(constants.COMMENT_ANNOTATION) and not stripped_line == "" \
                                and not stripped_line.startswith('\\'):
                            # if line is not empty or a comment, or is not a continuation of previous line
                            # check if end of section
                            if stripped_line.startswith('</'):
                                directive = stripped_line.replace('/', '')
                                # if non-whitelisted directive is found, add to log and comment line
                                if directive.lower() not in whitelisted_directives_set:
                                    non_whitelisted_directive_usage.append(file_path_with_line + ' ' + directive)
                                    file.write(constants.COMMENT_ANNOTATION + line)
                                    logger.info(
                                        "FileOperationsUtility: Commenting non-whitelisted directive usage in %s.",
                                        file_path_with_line)
                                else:
                                    file.write(line)
                            elif stripped_line.startswith('<'):
                                # check if start of section
                                directive = stripped_line.split()[0] + '>'
                                # if non-whitelisted directive is found, add to log and comment line
                                if directive.lower() not in whitelisted_directives_set:
                                    start_of_section_directives_list.append(directive)
                                    non_whitelisted_directive_usage.append(file_path_with_line + ' ' + directive)
                                    file.write(constants.COMMENT_ANNOTATION + line)
                                    logger.info(
                                        "FileOperationsUtility: Commenting non-whitelisted directive usage in %s.",
                                        file_path_with_line)
                                else:
                                    file.write(line)
                            else:
                                # if non-whitelisted directive is used, comment the line
                                directive = stripped_line.split()[0]
                                if directive.lower() not in whitelisted_directives_set:
                                    non_whitelisted_directive_usage.append(file_path_with_line + ' ' + directive)
                                    file.write(constants.COMMENT_ANNOTATION + line)
                                    logger.info(
                                        "FileOperationsUtility: Commenting non-whitelisted directive usage in %s.",
                                        file_path_with_line)
                                else:
                                    file.write(line)
                        else:
                            file.write(line)
                file.close()
            if len(non_whitelisted_directive_usage) > 0:
                print('\nApache configuration uses non-whitelisted directives:')
                logger.error('Apache configuration uses non-whitelisted directives:')
                for usage in non_whitelisted_directive_usage:
                    print(usage)
                    logger.error('%s', usage)
                    conversion_operation = ConversionOperation(constants.ACTION_REMOVED, usage,
                                                               "Commented out usage of non-whitelisted directives")
                    conversion_step.__add_operation__(conversion_operation)
                logger.info('Commented out all usages of non-whitelisted directives listed above.')
                print('Commented out all usages of non-whitelisted directives.')

    @staticmethod
    def __remove_variable_usage_in_section_in_file(file_path, section_header, conversion_step):
        """
        Remove usage of variables within specified sections of a file.
        """

        if exists(file_path) and isfile(file_path):
            start_of_section = False
            section_indentation = 0
            try:
                # open the file in read mode and read it
                with open(file_path) as file:
                    file_content = file.readlines()
                file.close()
                # open the file in write-mode and write to the file,
                with open(file_path, "w") as file:
                    for line in file_content:
                        stripped_line = line.strip()
                        # identify the start of section
                        if stripped_line.startswith(section_header):
                            section_indentation = len(line) - len(stripped_line)
                            start_of_section = True
                            file.write(line)
                        elif start_of_section:
                            # if section is found, remove all variable usages within of the section
                            # find usage of variable via regular expression (${variable_name})
                            # The regex matches the first "${", then it matches everything that's not a "}":
                            # \$\{ matches the character "${" literally
                            # the capturing group ([^}]+) greedily matches anything that's not a "}"
                            if search('\${([^}]+)', stripped_line):
                                logger.info(
                                    "FileOperationsUtility: Removed usage of variable '%s' in %s section of file "
                                    "%s.", stripped_line, section_header, file_path)
                                conversion_operation = ConversionOperation(constants.ACTION_REMOVED, file_path,
                                                                           "Removed usage of variable '" + stripped_line
                                                                           + "' in section '" + section_header + "'")
                                conversion_step.__add_operation__(conversion_operation)
                                # comment out the line
                                file.write(constants.COMMENT_ANNOTATION + line)
                            elif stripped_line == "}" and len(line) - len(stripped_line) == section_indentation:
                                # mark the end of section
                                start_of_section = False
                                file.write(line)
                            else:
                                file.write(line)
                        # write out other lines as is
                        else:
                            file.write(line)
            except OSError as e:
                logger.error("FileOperationsUtility: %s - %s.", e.filename, e.strerror)

    @staticmethod
    def __remove_variable_usage_in_section__(dir_path, file_extension, section_header, conversion_step):
        """
        Remove the usage of variables within specified sections of all files (of given file extension)
        in specified directory and sub-directories.

        Parameters:
            dir_path (str): The path to directory whose files are to be processed
            file_extension (str): The extension of the type that needs to be processed
            section_header (str): The section header (within the file), whose content is to be processed
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.
        """

        if exists(dir_path) and isdir(dir_path):
            # get all files under given directory and sub-directories with given file extension
            files = [f for f in glob(join(dir_path, "**", "*." + file_extension), recursive=True)]
            for file in files:
                FileOperationsUtility.__remove_variable_usage_in_section_in_file(file, section_header, conversion_step)

    @staticmethod
    def __remove_non_matching_files_by_name__(src_dir, dest_dir, conversion_step):
        """
        Remove files in destination dir which are not present in source dir (comparision by name)

        Parameters:
            src_dir (str): The source directory's path
            dest_dir (str): The destination directory's path
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.
        """

        enabled_dir_files = set()
        for file in listdir(src_dir):
            if isfile(join(src_dir, file)):
                enabled_dir_files.add(file)
        for file in listdir(dest_dir):
            if isfile(join(dest_dir, file)):
                if file not in enabled_dir_files:
                    FileOperationsUtility.__delete_file__(join(dest_dir, file), conversion_step)

    @staticmethod
    def __consolidate_variable_files__(files: List[str], new_file_path, conversion_step):
        """
        Returns a list of the variables after consolidating the variables (duplicates not allowed)
        from given files into a single new file.

        Parameters:
            files (List[str]): The variable files to be consolidated
            new_file_path (str): The new file that will contain the consolidated variables
            conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.

        Returns the list of variables consolidated.
        """
        # list of defined variables (only the variable)
        variables_list = []
        # list of variable definitions
        variables_definition_list = []
        # get the content of each vars file
        for file in files:
            variables_extracted_from_file = FileOperationsUtility.__get_content_from_file__(file)
            for variable_def in variables_extracted_from_file:
                if not variable_def.startswith(constants.COMMENT_ANNOTATION):
                    var_definition = variable_def.split()
                    # if not duplicate
                    if var_definition[1] not in variables_list:
                        variables_list.append(var_definition[1])
                        variables_definition_list.append(variable_def)
        with open(new_file_path, "w") as f:
            pass
            # write the list of consolidated variables into the new file
            for variable_def in variables_definition_list:
                f.write(variable_def)
        return variables_list

    @staticmethod
    def __check_for_undefined_variables__(dir_path, defined_variables_list: List[str]):
        """
        Check vhost files for usage of undefined variables.
        If found, print warning in terminal and log error.

        Parameters:
            dir_path (str): The directory to be searched under
            defined_variables_list (List[str]): The list of variables that are defined
        """
        flag_first = True
        files = [f for f in glob(join(dir_path, "**", "*.vhost"), recursive=True)]
        for vhost_file in files:
            with open(vhost_file, "r") as file:
                file_content = file.readlines()
            file.close()
            line_index = 0
            for line in file_content:
                line_index += 1
                stripped_line = line.strip()
                # if line is not a comment
                if not stripped_line.startswith(constants.COMMENT_ANNOTATION):
                    # find usage of variable via regular expression (${variable_name}), and check if it is defined
                    # The regex matches the first "${", then it matches everything that's not a "}":
                    # \$\{ matches the character "${" literally
                    # the capturing group ([^}]+) greedily matches anything that's not a "}"
                    match = search('\${([^}]+)', stripped_line)
                    if match and match.group(1) not in defined_variables_list:
                        if flag_first:
                            flag_first = False
                            print("\nFound usage of undefined variable:")
                        print(vhost_file + ":" + str(line_index) + " : " + match.group(1))
                        logger.error("Undefined variable usage found at : %s",
                                     vhost_file + ":" + str(line_index) + " : " + match.group(1))
