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
from util.conversion_report.conversion_step import ConversionStep
from util.conversion_report.conversion_operation import ConversionOperation
from util.file_operations_utility import FileOperationsUtility
from util.folder_operations_utility import FolderOperationsUtility
from util.setup_logger_utility import logger
from util.conversion_report.summary_report_writer import SummaryReportWriter

from glob import glob
from ntpath import basename
from os import linesep
from os.path import exists, isfile, join, dirname
from shutil import copy


class AEMDispatcherConverter:
    """
    AEMDispatcherConverter follows the conversion rules mentioned at [1] for transforming
    Adobe Managed Services dispatcher configurations to AEMaaCS Dispatcher configurations.
    [1] : https://git.corp.adobe.com/Granite/skyline-dispatcher-sdk/blob/master/docs/TransitionFromAMS.md

    Attributes:
        __sdk_src_path (str): The path to the Dispatcher SDK `src` folder.
        __dispatcher_config_directory (str): The path to the dispatcher configuration `src` folder .
    """

    # private attributes
    __sdk_src_path = None
    __dispatcher_config_directory = None
    __conversion_steps = None

    def __init__(self, sdk_src_path, dispatcher_config_path):
        """
         Parameters:
            sdk_src_path (str): path to the src folder of the dispatcher sdk
            dispatcher_config_path (str): path to dispatcher config folder where the conversion is to be performed
        """
        self.__sdk_src_path = sdk_src_path
        self.__dispatcher_config_directory = dispatcher_config_path
        self.__conversion_steps = []

    # execute all conversion rules
    def __transform__(self):
        """
        Perform the transition steps mentioned in [1].
        [1]: https://git.corp.adobe.com/Granite/skyline-dispatcher-sdk/blob/master/docs/TransitionFromAMS.md
        """

        # self.__extract_archive()
        self.__remove_unused_folders_files()
        self.__remove_non_publish_vhost_files()
        self.__remove_vhost_section_not_referring_to_port_80()
        self.__replace_variable_in_vhost_files()
        self.__check_rewrites()
        self.__check_variables()
        self.__remove_whitelists()
        self.__remove_non_publish_farms()
        self.__rename_farm_files()
        self.__check_cache()
        self.__check_client_headers()
        self.__check_filter()
        self.__check_renders()
        self.__check_virtualhosts()
        self.__replace_variable_in_farm_files()
        self.__remove_non_whitelisted_directives()
        # create the summary report for the conversion performed
        SummaryReportWriter.__write_summary_report__(self.__conversion_steps)

    # 1. Get rid of unused subfolders and files.
    # Remove subfolders conf and conf.modules.d, as well as files matching conf.d/*.conf.
    def __remove_unused_folders_files(self):
        conversion_step = self.__remove_unused_folders_files_summary_generator()
        FolderOperationsUtility.__delete_folder__(join(self.__dispatcher_config_directory, constants.CONF),
                                                  conversion_step)
        FolderOperationsUtility.__delete_folder__(join(self.__dispatcher_config_directory, constants.CONF_MODULES_D),
                                                  conversion_step)
        FileOperationsUtility.__delete_files_with_extension__(
            join(self.__dispatcher_config_directory, constants.CONF_D), constants.CONF, conversion_step)
        self.__conversion_steps.append(conversion_step)

    def __remove_unused_folders_files_summary_generator(self):
        logger.info(
            "AEMDispatcherConverter: Executing Rule : Remove subfolders conf and conf.modules.d, as well as "
            "files matching conf.d/*.conf.")
        return ConversionStep("Get rid of ununsed subfolders and files",
                              "Remove subfolders `conf` and `conf.modules.d` ,"
                              " as well as files matching `conf.d/*.conf` .")

    # 2. Get rid of all non-publish virtual hosts
    def __remove_non_publish_vhost_files(self):
        conversion_step = self.__remove_non_publish_vhost_files_summary_generator()
        enabled_vhosts_dir_path = join(self.__dispatcher_config_directory, constants.CONF_D,
                                       constants.ENABLED_VHOSTS)
        # Remove any vhost file in conf.d/enabled_vhosts that has author, unhealthy, health, lc or flush in its name.
        non_publish_keyword_list = ["author", "unhealthy", "health", "lc", "flush"]
        for keyword in non_publish_keyword_list:
            FileOperationsUtility.__delete_all_files_containing_substring__(enabled_vhosts_dir_path, keyword,
                                                                            conversion_step)
        # check for non-symlink enabled_vhost files
        enabled_vhost_files = [f for f in glob(join(enabled_vhosts_dir_path, "**", "*." + constants.VHOST), recursive=True)]
        for file in enabled_vhost_files:
            if not self.__is_symlink_file(file):
                conversion_operation = ConversionOperation(constants.WARNING, file, "Found non-symlink enabled_vhost file.")
                conversion_step.__add_operation__(conversion_operation)
                logger.info("AEMDispatcherConverter: Found non-symlink enabled_vhost file %s", file)
        # All farm files in conf.d/available_vhosts that are not linked to can be removed as well.
        # TODO : This is a hack, instead find symlinks in enabled_vhosts and their targets in available_vhosts
        available_vhosts_dir_path = join(self.__dispatcher_config_directory, constants.CONF_D,
                                         constants.AVAILABLE_VHOSTS)
        for keyword in non_publish_keyword_list:
            FileOperationsUtility.__delete_all_files_containing_substring__(available_vhosts_dir_path, keyword,
                                                                            conversion_step)
        FileOperationsUtility.__remove_non_matching_files_by_name__(enabled_vhosts_dir_path, available_vhosts_dir_path,
                                                                    conversion_step)
        self.__conversion_steps.append(conversion_step)

    def __remove_non_publish_vhost_files_summary_generator(self):
        logger.info("AEMDispatcherConverter: Executing Rule : Get rid of all non-publish virtual hosts.")
        return ConversionStep("Get rid of all non-publish virtual hosts",
                              "Remove any virtual host file in `conf.d/enabled_vhosts` that has `author` ,"
                              " `unhealthy` , `health` , `lc` or `flush` in its name. All virtual host "
                              "files in `conf.d/available_vhosts` that are not linked to should be removed.")

    # 3. Remove virtual host sections that do not refer to port 80
    # If you still have sections in your virtual host files that exclusively refer to other ports than port 80, e.g.
    #
    # <VirtualHost *:443>
    # ...
    # </VirtualHost>
    # remove them
    def __remove_vhost_section_not_referring_to_port_80(self):
        conversion_step = self.__remove_vhost_section_not_referring_to_port_80_summary_generator()
        enabled_vhost_dir_path = join(self.__dispatcher_config_directory, constants.CONF_D,
                                      constants.ENABLED_VHOSTS)
        available_vhost_dir_path = join(self.__dispatcher_config_directory, constants.CONF_D,
                                        constants.AVAILABLE_VHOSTS)
        FileOperationsUtility.__remove_virtual_host_sections_not_port_80__(enabled_vhost_dir_path, conversion_step)
        FileOperationsUtility.__remove_virtual_host_sections_not_port_80__(available_vhost_dir_path, conversion_step)
        self.__conversion_steps.append(conversion_step)

    def __remove_vhost_section_not_referring_to_port_80_summary_generator(self):
        logger.info(
            "AEMDispatcherConverter: Executing Rule : Remove virtual host sections that do not refer to port "
            "80.")
        return ConversionStep("Remove virtual host sections that do not refer to port 80",
                              "If you still have sections in your virtual host files that exclusively "
                              "refer to other ports than port 80, e.g. "
                              "`<VirtualHost *:443>...</VirtualHost>`")

    # 4. Check rewrites folder
    def __check_rewrites(self):
        conversion_step = self.__check_rewrites_summary_generator()
        conf_d_dir_path = join(self.__dispatcher_config_directory, constants.CONF_D)
        rewrites_dir_path = join(self.__dispatcher_config_directory, constants.CONF_D, "rewrites")
        # Remove any file named base_rewrite.rules and xforwarded_forcessl_rewrite.rules and remember to remove Include
        # statements in the virtual host files referring to them.
        base_rewrite_rules_file = "base_rewrite.rules"
        xforwarded_forcessl_rewrite_rules = "xforwarded_forcessl_rewrite.rules"
        if isfile(join(rewrites_dir_path, base_rewrite_rules_file)):
            logger.debug("AEMDispatcherConverter: Removing %s.", base_rewrite_rules_file)
            FileOperationsUtility.__remove_include_statement_for_some_rule__(conf_d_dir_path,
                                                                             constants.INCLUDE_SYNTAX_IN_VHOST,
                                                                             constants.VHOST,
                                                                             base_rewrite_rules_file, conversion_step)
            FileOperationsUtility.__delete_file__(join(rewrites_dir_path, base_rewrite_rules_file),
                                                  conversion_step)
        if isfile(join(rewrites_dir_path, xforwarded_forcessl_rewrite_rules)):
            logger.debug("AEMDispatcherConverter: Removing %s.", xforwarded_forcessl_rewrite_rules)
            FileOperationsUtility.__remove_include_statement_for_some_rule__(conf_d_dir_path,
                                                                             constants.INCLUDE_SYNTAX_IN_VHOST,
                                                                             constants.VHOST,
                                                                             xforwarded_forcessl_rewrite_rules,
                                                                             conversion_step)
            FileOperationsUtility.__delete_file__(join(rewrites_dir_path, xforwarded_forcessl_rewrite_rules),
                                                  conversion_step)

        files = [f for f in glob(join(rewrites_dir_path, "**", "*.rules"), recursive=True)]
        file_count = len(files)
        # If conf.d/rewrites now contains a single file
        if file_count == 1:
            # get rule file name
            old_file_name = basename(files[0])
            new_file_name = "rewrite.rules"
            # it should be renamed to rewrite.rules
            renamed_file_path = join(dirname(files[0]), new_file_name)
            FileOperationsUtility.__rename_file__(files[0], renamed_file_path, conversion_step)
            # adapt the Include statements referring to that file in the virtual host files as well.
            FileOperationsUtility.__replace_file_name_in_include_statement__(conf_d_dir_path, constants.VHOST,
                                                                             constants.INCLUDE_SYNTAX_IN_VHOST,
                                                                             old_file_name, new_file_name,
                                                                             conversion_step)
        elif file_count > 1:
            # If the folder however contains multiple virtual host specific files
            available_vhost_files = self.__get_all_available_vhost_files()
            if len(available_vhost_files) > 1:
                for file in files:
                    old_file_name = basename(file)
                    # their contents should be copied to the Include statement referring to them in the virtual host files.
                    rules_extracted_from_file = FileOperationsUtility.__get_content_from_file__(file, True)
                    FileOperationsUtility.__replace_include_statement_with_content_of_rule_file__(conf_d_dir_path,
                                                                                                  constants.VHOST,
                                                                                                  old_file_name,
                                                                                                  rules_extracted_from_file,
                                                                                                  constants.INCLUDE_SYNTAX_IN_VHOST,
                                                                                                  conversion_step)
                    FileOperationsUtility.__delete_file__(file, conversion_step)
            elif len(available_vhost_files) == 1:
                # If the folder however contains multiple rule files specific to a single vhost file, we should
                # consolidate all the included rule file into a single rule file and include it.
                # get the all the rewrite rule files names
                rule_files = FileOperationsUtility.__get_all_file_names__(files)
                # find all the rule files names that are actually included in single the vhost file
                rule_files_included = FileOperationsUtility.__get_names_of_rule_files_included__(available_vhost_files[0],
                                                                                        rule_files,
                                                                                        constants.INCLUDE_SYNTAX_IN_VHOST)
                # delete the rule files not included in the single available vhost file, and get the files actually used
                files = self.__filter_and_remove_unused_files(files, rule_files_included, conversion_step)
                # consolidate all rule files into a single rewrite.rules file
                FileOperationsUtility.__consolidate_all_rule_files_into_single_rule_file__(files,
                                                                                           join(rewrites_dir_path,
                                                                                                "rewrite.rules"),
                                                                                           conversion_step)
                rule_files = FileOperationsUtility.__get_all_file_names__(files)
                # replace all statements including the files in a IfModule with a single include statement
                FileOperationsUtility.__replace_file_includes_in_section_or_ifmodule__(conf_d_dir_path, constants.VHOST,
                                                                                       constants.REWRITES_MODULE,
                                                                                       rule_files, "rewrite.rules",
                                                                                       conversion_step)


        self.__conversion_steps.append(conversion_step)

    def __check_rewrites_summary_generator(self):
        logger.info("AEMDispatcherConverter: Executing Rule : Check rewrites folder.")
        return ConversionStep("Check rewrites folder",
                              "In directory `conf.d/rewrites`, remove any file named "
                              "`base_rewrite.rules` and `xforwarded_forcessl_rewrite.rules` and remove "
                              "Include statements in the virtual host files referring to them."
                              + linesep +
                              "If `conf.d/rewrites` now contains a single file, it should be renamed to "
                              "`rewrite.rules` and adapt the Include statements referring to that file "
                              "in the virtual host files as well."
                              + linesep +
                              "If the folder however contains multiple, virtual host specific files, "
                              "their contents should be copied to the Include statement referring to "
                              "them in the virtual host files.")

    # 5. Check variables folder
    def __check_variables(self):
        conversion_step = self.__check_variables_summary_generator()
        conf_d_dir_path = join(self.__dispatcher_config_directory, constants.CONF_D)
        variables_dir_path = join(self.__dispatcher_config_directory, constants.CONF_D, "variables")
        # Remove any file named ams_default.vars and remember to remove Include statements in the virtual host files
        # referring to them.
        ams_default_vars_file = "ams_default.vars"
        if isfile(join(variables_dir_path, ams_default_vars_file)):
            logger.debug("AEMDispatcherConverter: Removing %s.", ams_default_vars_file)
            FileOperationsUtility.__remove_include_statement_for_some_rule__(conf_d_dir_path,
                                                                             constants.INCLUDE_SYNTAX_IN_VHOST,
                                                                             constants.VHOST, ams_default_vars_file,
                                                                             conversion_step)
            FileOperationsUtility.__delete_file__(join(variables_dir_path, ams_default_vars_file), conversion_step)
        files = FileOperationsUtility.__delete_all_files_not_conforming_to_pattern__(variables_dir_path, "*.vars",
                                                                                     conversion_step)
        # consolidate all variable file into once "custom.vars"
        custom_vars_file = join(variables_dir_path, "custom.vars")
        variables_list = FileOperationsUtility.__consolidate_variable_files__(files, custom_vars_file,
                                                                              conversion_step)
        # adapt the Include statements referring to the old var files in the vhost files.
        for file in files:
            FileOperationsUtility.__replace_file_name_in_include_statement__(conf_d_dir_path,
                                                                             constants.VHOST,
                                                                             constants.INCLUDE_SYNTAX_IN_VHOST,
                                                                             basename(file),
                                                                             basename(custom_vars_file),
                                                                             conversion_step)
            # delete the old files
            FileOperationsUtility.__delete_file__(file, conversion_step)
        # check for undefined variables
        FileOperationsUtility.__check_for_undefined_variables__(conf_d_dir_path, variables_list)
        # Copy the file conf.d/variables/global.vars from the default skyline dispatcher configuration to that location.
        default_global_vars_file_from_sdk = join(self.__sdk_src_path, "conf.d", "variables", "global.vars")
        copy(default_global_vars_file_from_sdk, variables_dir_path)
        logger.info(
            "AEMDispatcherConverter: Copied file 'conf.d/variables/global.vars' from the "
            "standard dispatcher configuration to %s.", variables_dir_path)
        self.__conversion_steps.append(conversion_step)

    def __check_variables_summary_generator(self):
        logger.info("AEMDispatcherConverter: Executing Rule : Check variables folder.")
        return ConversionStep("Check variables folder",
                              "In directory `conf.d/variables`, remove any file named `ams_default.vars` "
                              "and remove Include statements in the virtual host files referring to them."
                              + linesep +
                              "Consolidate variable definitions from all remaining vars files in `conf.d/variables`"
                              "into a single file named `custom.vars` and adapt the Include statements "
                              "referring to them in the virtual host files.")

    # 6. Remove whitelists
    def __remove_whitelists(self):
        conversion_step = self.__remove_whitelists_summary_generator()
        conf_d_dir_path = join(self.__dispatcher_config_directory, constants.CONF_D)
        whitelists_dir_path = join(self.__dispatcher_config_directory, constants.CONF_D, "whitelists")
        files = [f for f in glob(join(whitelists_dir_path, "**", "*.*"), recursive=True)]
        # remove Include statements in the virtual host files referring to some file in that subfolder.
        for file in files:
            old_file_name = basename(file)
            FileOperationsUtility.__remove_include_statement_for_some_rule__(conf_d_dir_path,
                                                                             constants.INCLUDE_SYNTAX_IN_VHOST,
                                                                             constants.VHOST, old_file_name,
                                                                             conversion_step)
        # Remove the folder conf.d/whitelists
        FolderOperationsUtility.__delete_folder__(whitelists_dir_path, conversion_step)
        self.__conversion_steps.append(conversion_step)

    def __remove_whitelists_summary_generator(self):
        logger.info("AEMDispatcherConverter: Executing Rule : Remove whitelists.")
        return ConversionStep("Remove whitelists",
                              "Remove the folder `conf.d/whitelists` and remove Include statements in "
                              "the virtual host files referring to some file in that subfolder.")

    # 7. Replace any variable that is no longer available
    def __replace_variable_in_vhost_files(self):
        conversion_step = self.__replace_variable_in_vhost_files_summary_generator()
        logger.info(
            "AEMDispatcherConverter: Executing Rule : Replace any variable that is no longer available.")
        conversion_step = ConversionStep("Replace any variable that is no longer available",
                                         "In all virtual host files, rename `PUBLISH_DOCROOT` to `DOCROOT` and "
                                         "remove sections referring to variables named `DISP_ID` , "
                                         "`PUBLISH_FORCE_SSL` or `PUBLISH_WHITELIST_ENABLED`.")
        # In all virtual host files rename PUBLISH_DOCROOT to DOCROOT
        logger.debug("AEMDispatcherConverter: Renaming PUBLISH_DOCROOT to DOCROOT in all virtual host files.")
        conf_d_dir_path = join(self.__dispatcher_config_directory, constants.CONF_D)
        FileOperationsUtility.__replace_all_usage_of_old_variable_with_new_variable__(conf_d_dir_path,
                                                                                      constants.VHOST,
                                                                                      "PUBLISH_DOCROOT", "DOCROOT",
                                                                                      conversion_step)
        # In all virtual host files remove sections referring to variables named DISP_ID, PUBLISH_FORCE_SSL or
        # PUBLISH_WHITELIST_ENABLED
        logger.debug(
            "AEMDispatcherConverter: Removing sections referring to variables named DISP_ID, "
            "PUBLISH_FORCE_SSL or PUBLISH_WHITELIST_ENABLED in all virtual host files.")
        FileOperationsUtility.__remove_all_usage_of_old_variable__(conf_d_dir_path, constants.VHOST,
                                                                   "DISP_ID", conversion_step)
        FileOperationsUtility.__remove_all_usage_of_old_variable__(conf_d_dir_path, constants.VHOST,
                                                                   "PUBLISH_FORCE_SSL", conversion_step)
        FileOperationsUtility.__remove_all_usage_of_old_variable__(conf_d_dir_path, constants.VHOST,
                                                                   "PUBLISH_WHITELIST_ENABLED", conversion_step)
        self.__conversion_steps.append(conversion_step)

    def __replace_variable_in_vhost_files_summary_generator(self):
        logger.info(
            "AEMDispatcherConverter: Executing Rule : Replace any variable that is no longer available.")
        return ConversionStep("Replace any variable that is no longer available",
                              "In all virtual host files, rename `PUBLISH_DOCROOT` to `DOCROOT` and "
                              "remove sections referring to variables named `DISP_ID` , "
                              "`PUBLISH_FORCE_SSL` or `PUBLISH_WHITELIST_ENABLED`.")

    # 8. Get rid of all non-publish farms
    def __remove_non_publish_farms(self):
        conversion_step = self.__remove_non_publish_farms_summary_report()
        non_publish_keyword_list = ["author", "unhealthy", "health", "lc", "flush"]
        # Remove farm files in conf.dispatcher.d/enabled_farms that has author,unhealthy,health,lc or flush in its name.
        enabled_farms_dir_path = join(self.__dispatcher_config_directory, constants.CONF_DISPATCHER_D,
                                      constants.ENABLED_FARMS)
        for keyword in non_publish_keyword_list:
            FileOperationsUtility.__delete_all_files_containing_substring__(enabled_farms_dir_path,
                                                                            keyword, conversion_step)
        # All farm files in conf.dispatcher.d/available_farms that are not linked to can be removed as well.
        # TODO : This is a hack, instead find symlinks in enabled_farms and their targets in available_farms
        available_farms_dir_path = join(self.__dispatcher_config_directory, constants.CONF_DISPATCHER_D,
                                        constants.AVAILABLE_FARMS)
        for keyword in non_publish_keyword_list:
            FileOperationsUtility.__delete_all_files_containing_substring__(available_farms_dir_path,
                                                                            keyword, conversion_step)
        FileOperationsUtility.__remove_non_matching_files_by_name__(enabled_farms_dir_path,
                                                                    available_farms_dir_path,
                                                                    conversion_step)
        self.__conversion_steps.append(conversion_step)

    def __remove_non_publish_farms_summary_report(self):
        logger.info("AEMDispatcherConverter: Executing Rule : Get rid of all non-publish farms.")
        return ConversionStep("Get rid of all non-publish farms",
                              "Remove any farm file in `conf.dispatcher.d/enabled_farms` that has "
                              "`author , unhealthy , health , lc , flush` in its name. All farm files "
                              "in `conf.dispatcher.d/available_farms` that are not linked to can be "
                              "removed as well.")

    # 9. Rename farm files.
    # All farms in conf.d/enabled_farms and conf.d/available_farms must be renamed to match the pattern *.farm,
    # so e.g. a farm file called customerX_farm.any should be renamed customerX.farm.
    def __rename_farm_files(self):
        conversion_step = self.__rename_farm_files_summary_generator()
        available_farms_dir_path = join(self.__dispatcher_config_directory, constants.CONF_DISPATCHER_D,
                                        constants.AVAILABLE_FARMS)
        files = [f for f in glob(join(available_farms_dir_path, "**", "*.any"), recursive=True)]
        for file in files:
            new_file_name = basename(file).replace("_farm", "").replace(".any", ".farm")
            FileOperationsUtility.__rename_file__(file, join(dirname(file), new_file_name), conversion_step)
        enabled_farms_dir_path = join(self.__dispatcher_config_directory, constants.CONF_DISPATCHER_D,
                                      constants.ENABLED_FARMS)
        files = [f for f in glob(join(enabled_farms_dir_path, "**", "*.any"), recursive=True)]
        for file in files:
            new_file_name = basename(file).replace("_farm", "").replace(".any", ".farm")
            FileOperationsUtility.__rename_file__(file, join(dirname(file), new_file_name), conversion_step)
        # check for non-symlink enabled_farm files
        enabled_farm_files = [f for f in glob(join(enabled_farms_dir_path, "**", "*." + constants.FARM), recursive=True)]
        for file in enabled_farm_files:
            if not self.__is_symlink_file(file):
                conversion_operation = ConversionOperation(constants.WARNING, file, "Found non-symlink enabled_farm file.")
                conversion_step.__add_operation__(conversion_operation)
                logger.info("AEMDispatcherConverter: Found non-symlink enabled_farm file %s", file)
        self.__rename_symlink_target_links(conversion_step)
        self.__conversion_steps.append(conversion_step)

    def __rename_symlink_target_links(self, conversion_step):
        enabled_farms_dir_path = join(self.__dispatcher_config_directory, constants.CONF_DISPATCHER_D,
                                      constants.ENABLED_FARMS)
        files = [f for f in glob(join(enabled_farms_dir_path, "**", "*.farm"), recursive=True)]
        # in all enabled_farm files
        for file in files:
            # change the target links to point to the renamed files in available_farms
            content_of_file = FileOperationsUtility.__get_content_from_file__(file, False)
            # if it is s symlink file its length of content will be 2 (1. comment mentioning the source, 2. target link)
            if len(content_of_file) == 2:
                old_target = content_of_file[1]  # target link will be the 2nd item
                old_target_file_name = basename(old_target)
                new_target_file_name = old_target_file_name.replace("_farm", "").replace(".any", ".farm")
                new_target = old_target.replace(old_target_file_name, new_target_file_name)
                with open(file, "w") as f:
                    f.write(new_target)
                    conversion_operation = ConversionOperation(constants.ACTION_RENAMED, file, "Renamed symlink target "
                                                               + old_target + " to " + new_target)
                    conversion_step.__add_operation__(conversion_operation)
                    logger.info("Renamed symlink target in file %s , from '%s' to '%s'", file, old_target, new_target)

    def __rename_farm_files_summary_generator(self):
        logger.info(
            "AEMDispatcherConverter: Executing Rule : All farms in conf.d/enabled_farms and "
            "conf.d/available_farms must be renamed to match the pattern '*.farm'.")
        return ConversionStep("Rename farm files",
                              "All farms in `conf.d/enabled_farms` must be renamed to match the pattern "
                              "`*.farm` , so e.g. a farm file called `customerX_farm.any` should be "
                              "renamed `customerX.farm`.")

    # 10. Check cache
    def __check_cache(self):
        conversion_step = self.__check_cache_summary_generator()
        conf_dispatcher_d_dir_path = join(self.__dispatcher_config_directory, constants.CONF_DISPATCHER_D)
        cache_dir_path = join(self.__dispatcher_config_directory, constants.CONF_DISPATCHER_D, "cache")
        # Remove any file prefixed ams_.
        # remove include statements for the deleted files from farm files
        ams_files = [f for f in glob(join(cache_dir_path, "**", "*ams_*.any"), recursive=True)]
        cache_files = [f for f in glob(join(cache_dir_path, "**", "*.any"), recursive=True)]
        for file in ams_files:
            file_name = basename(file)
            # if not all files start with 'ams' prefix, replace the $include rule
            # if all files start with 'ams' prefix, the whole section will be replaced with $include "../cache/rules.any" later
            if len(cache_files) > len(ams_files):
                FileOperationsUtility.__replace_rule_in_include_statement__(conf_dispatcher_d_dir_path,
                                                                            constants.FARM,
                                                                            constants.INCLUDE_SYNTAX_IN_FARM,
                                                                            file_name, '"../cache/default_rules.any"',
                                                                            conversion_step)
            FileOperationsUtility.__delete_file__(file, conversion_step)
        # If conf.dispatcher.d/cache is now empty, copy the file conf.dispatcher.d/cache/rules.any from the standard
        # dispatcher configuration to this folder.
        # The standard dispatcher configuration can be found in the folder src of the SDK
        files = [f for f in glob(join(cache_dir_path, "**", "*.any"), recursive=True)]
        file_count = len(files)
        # copy the 'default_rules.any' file from sdk
        default_rules_file_from_sdk = join(self.__sdk_src_path, "conf.dispatcher.d", "cache", "default_rules.any")
        copy(default_rules_file_from_sdk, cache_dir_path)
        logger.info(
            "AEMDispatcherConverter: Copied file 'conf.dispatcher.d/cache/default_rules.any' from the "
            "standard dispatcher configuration to %s.",
            cache_dir_path)
        conversion_operation = ConversionOperation(constants.ACTION_ADDED, cache_dir_path,
                                                   "Copied file 'conf.dispatcher.d/cache/default_rules.any' "
                                                   "from the standard dispatcher configuration to " + cache_dir_path)
        conversion_step.__add_operation__(conversion_operation)
        if file_count == 0:
            rules_file_from_sdk = join(self.__sdk_src_path, "conf.dispatcher.d", "cache", "rules.any")
            copy(rules_file_from_sdk, cache_dir_path)
            logger.info(
                "AEMDispatcherConverter: Copied file 'conf.dispatcher.d/cache/rules.any' from the standard "
                "dispatcher configuration to %s.",
                cache_dir_path)
            conversion_operation = ConversionOperation(constants.ACTION_ADDED, cache_dir_path,
                                                       "Copied file 'conf.dispatcher.d/cache/rules.any' "
                                                       "from the standard dispatcher configuration to " + cache_dir_path)
            conversion_step.__add_operation__(conversion_operation)
            include_statement_to_replace_with = '$include "../cache/rules.any"'
            # adapt the $include statements referring to the the ams_*_cache.any rule files in the farm file
            FileOperationsUtility.__replace_content_of_section__(conf_dispatcher_d_dir_path,
                                           constants.FARM, constants.RULES_SECTION,
                                           include_statement_to_replace_with, conversion_step)
        # If instead conf.dispatcher.d/cache now contains a single file with suffix _cache.any
        elif file_count == 1 and files[0].endswith("_cache.any"):
            old_file_name = basename(files[0])
            #  it should be renamed to rules.any
            renamed_file_path = join(dirname(files[0]), "rules.any")
            FileOperationsUtility.__rename_file__(files[0], renamed_file_path, conversion_step)
            # adapt the $include statements referring to that file in the farm files as well
            FileOperationsUtility.__replace_rule_in_include_statement__(conf_dispatcher_d_dir_path,
                                                                        constants.FARM,
                                                                        constants.INCLUDE_SYNTAX_IN_FARM,
                                                                        old_file_name, '"../cache/rules.any"',
                                                                        conversion_step)
        elif file_count > 1:
            # If the folder however contains multiple, farm specific files with that pattern,
            # their contents should be copied to the $include statement referring to them in the farm files.
            available_farm_files = self.__get_all_available_farm_files()
            if len(available_farm_files) > 1:
                for file in files:
                    if file.endswith("_cache.any"):
                        content_from_cache_file = FileOperationsUtility.__get_content_from_file__(file, True)
                        FileOperationsUtility.__replace_include_statement_with_content_of_rule_file__(
                            conf_dispatcher_d_dir_path,
                            constants.FARM, basename(file),
                            content_from_cache_file,
                            constants.INCLUDE_SYNTAX_IN_FARM,
                            conversion_step)
                        FileOperationsUtility.__delete_file__(file, conversion_step)
            elif len(available_farm_files) == 1:
                # If the folder however contains multiple rule files specific to a single farm file,, we should
                # consolidate all the included rule file into a single rule file and include it.
                rule_files = FileOperationsUtility.__get_all_file_names__(files)
                # find all the rule files that are actually included in single the farm file
                rule_files_included = FileOperationsUtility.__get_names_of_rule_files_included__(available_farm_files[0],
                                                                                        rule_files,
                                                                                        constants.INCLUDE_SYNTAX_IN_FARM)
                # delete the rule files not included in the single available farm file, and get the files actually used
                files = self.__filter_and_remove_unused_files(files, rule_files_included, conversion_step)
                # consolidate all rule files into a single rules.any file
                FileOperationsUtility.__consolidate_all_rule_files_into_single_rule_file__(files,
                                                                                           join(
                                                                                               cache_dir_path,
                                                                                               "rules.any"),
                                                                                           conversion_step)
                rule_files = FileOperationsUtility.__get_all_file_names__(files)
                # replace all statements including the files in a cache-rules section with a single include statement
                include_statement_to_replace_with = '$include "../cache/rules.any"'
                FileOperationsUtility.__replace_file_includes_in_section_or_ifmodule__(conf_dispatcher_d_dir_path,
                                                                                       constants.FARM,
                                                                                       constants.RULES_SECTION,
                                                                                       rule_files,
                                                                                       include_statement_to_replace_with,
                                                                                       conversion_step)
        # Remove any file that has the suffix _invalidate_allowed.any
        for file in files:
            if file.endswith("_invalidate_allowed.any"):
                FileOperationsUtility.__delete_file__(file, conversion_step)
        # Copy the file conf.dispatcher.d/cache/default_invalidate_any from the default skyline dispatcher
        # configuration to that location.
        default_invalidate_file_from_sdk = join(self.__sdk_src_path, "conf.dispatcher.d", "cache",
                                                "default_invalidate.any")
        copy(default_invalidate_file_from_sdk, cache_dir_path)
        logger.info(
            "AEMDispatcherConverter: Copied file 'conf.dispatcher.d/cache/default_invalidate.any' from the "
            "standard dispatcher configuration to %s.", cache_dir_path)
        conversion_operation = ConversionOperation(constants.ACTION_ADDED, cache_dir_path,
                                                   "Copied file 'conf.dispatcher.d/cache/default_invalidate.any' "
                                                   "from the standard dispatcher configuration to " + cache_dir_path)
        conversion_step.__add_operation__(conversion_operation)
        # In each farm file, remove any contents in the cache/allowedClients section and replace it with:
        # $include "../cache/default_invalidate.any"
        include_statement_to_replace_with = '$include "../cache/default_invalidate.any"'
        FileOperationsUtility.__replace_content_of_section__(conf_dispatcher_d_dir_path,
                                                             constants.FARM, constants.ALLOWED_CLIENTS_SECTION,
                                                             include_statement_to_replace_with, conversion_step)
        self.__conversion_steps.append(conversion_step)

    def __check_cache_summary_generator(self):
        logger.info("AEMDispatcherConverter: Executing Rule : Checking cache folder.")
        return ConversionStep("Check cache",
                              "In directory `conf.dispatcher.d/cache`, remove any file prefixed `ams_`. "
                              + linesep +
                              "If `conf.dispatcher.d/cache` is now empty, copy the file "
                              "`conf.dispatcher.d/cache/rules.any` from the standard dispatcher "
                              "configuration to this folder. The standard dispatcher configuration can "
                              "be found in the folder src of the dispatcher SDK. Adapt the `$include` "
                              "statements referring to the `ams_*_cache.any` rule files in the farm "
                              "files as well."
                              + linesep +
                              " If instead `conf.dispatcher.d/cache` now contains a single "
                              "file with suffix `_cache.any`, it should be renamed to `rules.any` and "
                              "adapt the `$include` statements referring to that file in the farm files "
                              "as well."
                              + linesep +
                              "If the folder however contains multiple, farm specific files "
                              "with that pattern, their contents should be copied to the `$include` "
                              "statement referring to them in the farm files, and the delete the files. "
                              "Remove any file that has the suffix `_invalidate_allowed.any`."
                              + linesep +
                              "Copy the file `conf.dispatcher.d/cache/default_invalidate_any` from the "
                              "default AEM in the Cloud dispatcher configuration to that location. "
                              "In each farm file, remove any contents in the `cache/allowedClients` "
                              "section and replace it with:"
                              " `$include \"../cache/default_invalidate.any\"`")

    # 11. Check client headers
    def __check_client_headers(self):
        conversion_step = self.__check_client_headers_summary_generator()
        conf_dispatcher_d_dir_path = join(self.__dispatcher_config_directory, constants.CONF_DISPATCHER_D)
        client_headers_dir_path = join(self.__dispatcher_config_directory, constants.CONF_DISPATCHER_D,
                                       "clientheaders")
        # Remove any file prefixed ams_.
        ams_files = [f for f in glob(join(client_headers_dir_path, "**", "*ams_*.any"), recursive=True)]
        for file in ams_files:
            FileOperationsUtility.__delete_file__(file, conversion_step)
        files = FileOperationsUtility.__delete_all_files_not_conforming_to_pattern__(client_headers_dir_path, "*.any",
                                                                                     conversion_step)
        file_count = len(files)
        # If conf.dispatcher.d/clientheaders now contains a single file with suffix _clientheaders.any,
        if file_count == 1 and files[0].endswith("_clientheaders.any"):
            old_file_name = basename(files[0])
            # it should be renamed to clientheaders.any
            renamed_file_path = join(dirname(files[0]), "clientheaders.any")
            FileOperationsUtility.__rename_file__(files[0], renamed_file_path, conversion_step)
            # adapt the $include statements referring to that file in the farm files as well
            FileOperationsUtility.__replace_rule_in_include_statement__(conf_dispatcher_d_dir_path,
                                                                        constants.FARM,
                                                                        constants.INCLUDE_SYNTAX_IN_FARM,
                                                                        old_file_name, '"../clientheaders/clientheaders.any"',
                                                                        conversion_step)
        elif file_count > 1:
            # If the folder however contains multiple, farm specific files with that pattern,
            available_farm_files = self.__get_all_available_farm_files()
            if len(available_farm_files) > 1:
                for file in files:
                    if file.endswith("_clientheaders.any"):
                        content_from_client_header_file = FileOperationsUtility.__get_content_from_file__(file, True)
                        # their contents should be copied to the $include statement referring to them in the farm files.
                        FileOperationsUtility.__replace_include_statement_with_content_of_rule_file__(
                            conf_dispatcher_d_dir_path,
                            constants.FARM, basename(file),
                            content_from_client_header_file,
                            constants.INCLUDE_SYNTAX_IN_FARM,
                            conversion_step)
                        FileOperationsUtility.__delete_file__(file, conversion_step)
            elif len(available_farm_files) == 1:
                # If the folder however contains multiple rule files specific to a single farm file, we should
                # consolidate all the included rule file into a single rule file and include it.
                rule_files = FileOperationsUtility.__get_all_file_names__(files)
                # find all the rule files that are actually included in single the farm file
                rule_files_included = FileOperationsUtility.__get_names_of_rule_files_included__(available_farm_files[0],
                                                                                        rule_files,
                                                                                        constants.INCLUDE_SYNTAX_IN_FARM)
                # delete the rule files not included in the single available farm file, and get the files actually used
                files = self.__filter_and_remove_unused_files(files, rule_files_included, conversion_step)
                # consolidate all rule files into a single clientheaders.any file
                FileOperationsUtility.__consolidate_all_rule_files_into_single_rule_file__(files,
                                                                                           join(
                                                                                               client_headers_dir_path,
                                                                                               "clientheaders.any"),
                                                                                           conversion_step)
                rule_files = FileOperationsUtility.__get_all_file_names__(files)
                # replace all statements including the files in the clientheaders section with a single include statement
                include_statement_to_replace_with = '$include "../clientheaders/clientheaders.any"'
                FileOperationsUtility.__replace_file_includes_in_section_or_ifmodule__(conf_dispatcher_d_dir_path,
                                                                                       constants.FARM,
                                                                                       constants.CLIENT_HEADER_SECTION,
                                                                                       rule_files,
                                                                                       include_statement_to_replace_with,
                                                                                       conversion_step)
        self.__copy_default_clientheader_files_from_sdk(conf_dispatcher_d_dir_path,
                                                        client_headers_dir_path, conversion_step)
        self.__conversion_steps.append(conversion_step)

    def __check_client_headers_summary_generator(self):
        logger.info("AEMDispatcherConverter: Executing Rule : Checking clientheaders folder.")
        return ConversionStep("Check client headers",
                              "In directory `conf.dispatcher.d/clientheaders`, remove any file prefixed "
                              "`ams_` ."
                              + linesep +
                              "If `conf.dispatcher.d/clientheaders` now contains a single file with "
                              "suffix `_clientheaders.any` , it should be renamed to `clientheaders.any` "
                              "and adapt the `$include` statements referring to that file in the farm "
                              "files as well."
                              + linesep +
                              "If the folder however contains multiple, farm specific files with that "
                              "pattern, their contents should be copied to the `$include` statement "
                              "referring to them in the farm files."
                              + linesep +
                              "Copy the file `conf.dispatcher/clientheaders/default_clientheaders.any` "
                              "from the default AEM as a Cloud Service dispatcher configuration to that "
                              "location."
                              + linesep +
                              "In each farm file, replace any clientheader include statements that looks "
                              "the following : " + linesep +
                              "`$include \"/etc/httpd/conf.dispatcher.d/clientheaders/"
                              "ams_publish_clientheaders.any\"`" + linesep +
                              "`$include \"/etc/httpd/conf.dispatcher.d/clientheaders/ams_common_clientheaders.any\"` "
                              + linesep + "with the statement: "
                                          "`$include \"../clientheaders/default_clientheaders.any\"`")

    def __copy_default_clientheader_files_from_sdk(self, conf_dispatcher_d_dir_path,
                                                   client_headers_dir_path, conversion_step):
        # Copy the file conf.dispatcher.d/clientheaders/default_clientheaders.any from the default skyline dispatcher
        # configuration to that location.
        default_client_headers_file_from_sdk = join(self.__sdk_src_path, constants.CONF_DISPATCHER_D,
                                                    "clientheaders", "default_clientheaders.any")
        copy(default_client_headers_file_from_sdk, client_headers_dir_path)
        logger.info(
            "AEMDispatcherConverter: Copied file 'conf.dispatcher.d/clientheaders/default_clientheaders.any' "
            "from the standard dispatcher configuration to %s.", client_headers_dir_path)
        conversion_step.__add_operation__(ConversionOperation(constants.ACTION_ADDED, client_headers_dir_path,
                                                              "Copied file 'conf.dispatcher.d/clientheaders/default_clientheaders.any' "
                                                              "from the standard dispatcher configuration to " + client_headers_dir_path))
        if exists(join(client_headers_dir_path, "clientheaders.any")):
            # In each farm file, replace any clientheader include statements that looks as follows:
            # $include "/etc/httpd/conf.dispatcher.d/clientheaders/ams_publish_clientheaders.any"
            # $include "/etc/httpd/conf.dispatcher.d/clientheaders/ams_common_clientheaders.any"
            # with the statement:
            # $include "../clientheaders/default_clientheaders.any"
            replacement_include_file = constants.INCLUDE_SYNTAX_IN_FARM + ' "../clientheaders/default_clientheaders.any"'
            include_pattern_to_replace = constants.INCLUDE_SYNTAX_IN_FARM + ' "/etc/httpd/conf.dispatcher.d/clientheaders/ams_'
            FileOperationsUtility.__replace_include_pattern_in_section__(conf_dispatcher_d_dir_path, constants.FARM,
                                                                         constants.CLIENT_HEADER_SECTION,
                                                                         include_pattern_to_replace,
                                                                         replacement_include_file,
                                                                         conversion_step)
        else:
            # Copy the file conf.dispatcher.d/clientheaders/clientheaders.any from the default skyline dispatcher
            # configuration to that location.
            client_headers_file_from_sdk = join(self.__sdk_src_path, constants.CONF_DISPATCHER_D,
                                                "clientheaders", "clientheaders.any")
            copy(client_headers_file_from_sdk, client_headers_dir_path)
            logger.info(
                "AEMDispatcherConverter: Copied file 'conf.dispatcher.d/clientheaders/clientheaders.any' "
                "from the standard dispatcher configuration to %s.", client_headers_dir_path)
            conversion_step.__add_operation__(ConversionOperation(constants.ACTION_ADDED, client_headers_dir_path,
                                                                  "Copied file 'conf.dispatcher.d/clientheaders/clientheaders.any' "
                                                                  "from the standard dispatcher configuration to " + client_headers_dir_path))
            # In each farm file, replace any clientheader include statements that looks as follows:
            # $include "/etc/httpd/conf.dispatcher.d/clientheaders/ams_publish_clientheaders.any"
            # $include "/etc/httpd/conf.dispatcher.d/clientheaders/ams_common_clientheaders.any"
            # with the statement:
            # $include "../clientheaders/clientheaders.any"
            replacement_include_file = constants.INCLUDE_SYNTAX_IN_FARM + ' "../clientheaders/clientheaders.any"'
            include_pattern_to_replace = constants.INCLUDE_SYNTAX_IN_FARM + ' "/etc/httpd/conf.dispatcher.d/clientheaders/ams_'
            FileOperationsUtility.__replace_include_pattern_in_section__(conf_dispatcher_d_dir_path, constants.FARM,
                                                                         constants.CLIENT_HEADER_SECTION,
                                                                         include_pattern_to_replace,
                                                                         replacement_include_file,
                                                                         conversion_step)

    # 12. Check filter
    def __check_filter(self):
        conversion_step = self.__check_filter_summary_generator()
        conf_dispatcher_d_dir_path = join(self.__dispatcher_config_directory, constants.CONF_DISPATCHER_D)
        filters_dir_path = join(self.__dispatcher_config_directory, constants.CONF_DISPATCHER_D, "filters")
        # Remove any file prefixed ams_.
        ams_files = [f for f in glob(join(filters_dir_path, "**", "*ams_*.any"), recursive=True)]
        for file in ams_files:
            FileOperationsUtility.__delete_file__(file, conversion_step)
        files = FileOperationsUtility.__delete_all_files_not_conforming_to_pattern__(filters_dir_path, "*.any",
                                                                                     conversion_step)
        file_count = len(files)
        # If conf.dispatcher.d/filters now contains a single file
        if file_count == 1 and files[0].endswith("_filters.any"):
            old_file_name = basename(files[0])
            # it should be renamed to filters.any
            renamed_file_path = join(dirname(files[0]), "filters.any")
            FileOperationsUtility.__rename_file__(files[0], renamed_file_path, conversion_step)
            # adapt the $include statements referring to that file in the farm files as well
            FileOperationsUtility.__replace_rule_in_include_statement__(conf_dispatcher_d_dir_path,
                                                                        constants.FARM,
                                                                        constants.INCLUDE_SYNTAX_IN_FARM,
                                                                        old_file_name, '"../filters/filters.any"',
                                                                        conversion_step)
        # If the folder however contains multiple, farm specific files with that pattern,
        elif file_count > 1:
            available_farm_files = self.__get_all_available_farm_files()
            if len(available_farm_files) > 1:
                for file in files:
                    if file.endswith("_filters.any"):
                        content_from_client_header_file = FileOperationsUtility.__get_content_from_file__(file, True)
                        # their contents should be copied to the $include statement referring to them in the farm files.
                        FileOperationsUtility.__replace_include_statement_with_content_of_rule_file__(
                            conf_dispatcher_d_dir_path,
                            constants.FARM, basename(file),
                            content_from_client_header_file,
                            constants.INCLUDE_SYNTAX_IN_FARM,
                            conversion_step)
                        FileOperationsUtility.__delete_file__(file, conversion_step)
            elif len(available_farm_files) == 1:
                # If the folder however contains multiple rule files specific to a single farm file, we should
                # consolidate all the included rule file into a single rule file and include it.
                rule_files = FileOperationsUtility.__get_all_file_names__(files)
                # find all the rule files that are actually included in single the farm file
                rule_files_included = FileOperationsUtility.__get_names_of_rule_files_included__(available_farm_files[0],
                                                                                        rule_files,
                                                                                        constants.INCLUDE_SYNTAX_IN_FARM)
                # delete the rule files not included in the single available farm file, and get the files actually used
                files = self.__filter_and_remove_unused_files(files, rule_files_included, conversion_step)
                # consolidate all rule files into a single filters.any file
                FileOperationsUtility.__consolidate_all_rule_files_into_single_rule_file__(files,
                                                                                           join(
                                                                                               filters_dir_path,
                                                                                               "filters.any"),
                                                                                           conversion_step)
                rule_files = FileOperationsUtility.__get_all_file_names__(files)
                # replace all statements including the files in the filters section with a single include statement
                include_statement_to_replace_with = '$include "../filters/filters.any"'
                FileOperationsUtility.__replace_file_includes_in_section_or_ifmodule__(conf_dispatcher_d_dir_path,
                                                                                       constants.FARM,
                                                                                       constants.FILTERS_SECTION,
                                                                                       rule_files,
                                                                                       include_statement_to_replace_with,
                                                                                       conversion_step)

        self.__copy_default_filter_files_from_sdk(conf_dispatcher_d_dir_path, filters_dir_path, conversion_step)
        self.__conversion_steps.append(conversion_step)

    def __check_filter_summary_generator(self):
        logger.info("AEMDispatcherConverter: Executing Rule : Checking filters folder.")
        return ConversionStep("Check filter",
                              "In directory `conf.dispatcher.d/filters`, remove any file prefixed `ams_`."
                              + linesep +
                              " If `conf.dispatcher.d/filters` now contains a single file it should be "
                              "renamed to `filters.any` and adapt the `$include` statements referring to "
                              "that file in the farm files as well."
                              + linesep +
                              "If the folder however contains multiple, farm specific files with that "
                              "pattern, their contents should be copied to the `$include` statement "
                              "referring to them in the farm files."
                              + linesep +
                              "Copy the file `conf.dispatcher/filters/default_filters.any` from the default "
                              "AEM as a Cloud Service dispatcher configuration to that location."
                              + linesep +
                              "In each farm file, replace any filter include statements that looks as "
                              "follows: `$include \"/etc/httpd/conf.dispatcher.d/filters/ams_publish_filters.any\"`"
                              + linesep +
                              " with the statement: `$include \"../filters/default_filters.any\"`")

    def __copy_default_filter_files_from_sdk(self, conf_dispatcher_d_dir_path, filters_dir_path, conversion_step):
        # Copy the file conf.dispatcher.d/filters/default_filters.any from the default skyline dispatcher configuration
        # to that location.
        default_filters_file_from_sdk = join(self.__sdk_src_path, constants.CONF_DISPATCHER_D, "filters",
                                             "default_filters.any")
        copy(default_filters_file_from_sdk, filters_dir_path)
        logger.info(
            "AEMDispatcherConverter: Copied file 'conf.dispatcher.d/filters/default_filters.any' from the "
            "standard dispatcher configuration to %s.", filters_dir_path)
        conversion_step.__add_operation__(ConversionOperation(constants.ACTION_ADDED, filters_dir_path,
                                                              "Copied file 'conf.dispatcher.d/filters/default_filters.any' "
                                                              "from the standard dispatcher configuration to "
                                                              + filters_dir_path))
        if exists(join(filters_dir_path, "filters.any")):
            # In each farm file, replace any filter include statements that looks as follows:
            #
            # $include "/etc/httpd/conf.dispatcher.d/filters/ams_publish_filters.any"
            # with the statement:
            #
            # $include "../filters/default_filters.any"
            include_pattern_to_replace_with = constants.INCLUDE_SYNTAX_IN_FARM + ' "../filters/default_filters.any"'
            include_pattern_to_replace = constants.INCLUDE_SYNTAX_IN_FARM + ' "/etc/httpd/conf.dispatcher.d/filters/ams'
            FileOperationsUtility.__replace_include_pattern_in_section__(conf_dispatcher_d_dir_path, constants.FARM,
                                                                         constants.FILTERS_SECTION,
                                                                         include_pattern_to_replace,
                                                                         include_pattern_to_replace_with,
                                                                         conversion_step)
        else:
            # Copy the file conf.dispatcher.d/filters/filters.any from the default skyline dispatcher configuration
            # to that location.
            filters_file_from_sdk = join(self.__sdk_src_path, constants.CONF_DISPATCHER_D, "filters",
                                         "filters.any")
            copy(filters_file_from_sdk, filters_dir_path)
            logger.info(
                "AEMDispatcherConverter: Copied file 'conf.dispatcher.d/filters/filters.any' from the "
                "standard dispatcher configuration to %s.", filters_dir_path)
            conversion_step.__add_operation__(ConversionOperation(constants.ACTION_ADDED, filters_dir_path,
                                                                  "Copied file 'conf.dispatcher.d/filters/filters.any`"
                                                                  "'from the standard dispatcher configuration to "
                                                                  + filters_dir_path))
            # In each farm file, replace any filter include statements that looks as follows:
            #
            # $include "/etc/httpd/conf.dispatcher.d/filters/ams_publish_filters.any"
            # with the statement:
            #
            # $include "../filters/filters.any"
            include_pattern_to_replace_with = constants.INCLUDE_SYNTAX_IN_FARM + ' "../filters/filters.any"'
            include_pattern_to_replace = constants.INCLUDE_SYNTAX_IN_FARM + ' "/etc/httpd/conf.dispatcher.d/filters/ams'
            FileOperationsUtility.__replace_include_pattern_in_section__(conf_dispatcher_d_dir_path, constants.FARM,
                                                                         constants.FILTERS_SECTION,
                                                                         include_pattern_to_replace,
                                                                         include_pattern_to_replace_with,
                                                                         conversion_step)

    # 13. Check renders
    def __check_renders(self):
        conversion_step = self.__check_renders_summary_generator()
        conf_dispatcher_d_dir_path = join(self.__dispatcher_config_directory, constants.CONF_DISPATCHER_D)
        renders_dir_path = join(self.__dispatcher_config_directory, constants.CONF_DISPATCHER_D, "renders")
        # Remove all files in that folder.
        files = [f for f in glob(join(renders_dir_path, "**", "*.any"), recursive=True)]
        for file in files:
            FileOperationsUtility.__delete_file__(file, conversion_step)
        # Copy the file conf.dispatcher.d/renders/default_renders.any from the default skyline dispatcher
        # configuration to that location.
        default_filters_file_from_sdk = join(self.__sdk_src_path, constants.CONF_DISPATCHER_D, "renders",
                                             "default_renders.any")
        copy(default_filters_file_from_sdk, renders_dir_path)
        logger.info(
            "AEMDispatcherConverter: Copied file 'conf.dispatcher.d/renders/default_renders.any' from the "
            "standard dispatcher configuration to %s.", renders_dir_path)
        conversion_step.__add_operation__(ConversionOperation(constants.ACTION_ADDED, renders_dir_path,
                                                              "Copied file 'conf.dispatcher.d/renders/default_renders.any`"
                                                              "'from the standard dispatcher configuration to "
                                                              + renders_dir_path))
        # In each farm file, remove any contents in the renders section and replace it with:
        # $include "../renders/default_renders.any"
        include_statement_to_replace_with = '$include "../renders/default_renders.any"'
        FileOperationsUtility.__replace_content_of_section__(conf_dispatcher_d_dir_path, constants.FARM,
                                                             constants.RENDERS_SECTION,
                                                             include_statement_to_replace_with,
                                                             conversion_step)
        self.__conversion_steps.append(conversion_step)

    def __check_renders_summary_generator(self):
        logger.info("AEMDispatcherConverter: Executing Rule : Checking renders folder.")
        return ConversionStep("Check renders",
                              "Remove all files in the directory `conf.dispatcher.d/renders'."
                              "Copy the file `conf.dispatcher.d/renders/default_renders.any` from the "
                              "default AEM as a Cloud Service dispatcher configuration to that location."
                              + linesep +
                              "In each farm file, remove any contents in the renders section and replace "
                              "it with: `$include \"../renders/default_renders.any\"`")

    # 14. Check VirtualHosts
    def __check_virtualhosts(self):
        conversion_step = self.__check_virtualhosts_summary_generator()
        conf_dispatcher_d_dir_path = join(self.__dispatcher_config_directory, constants.CONF_DISPATCHER_D)
        old_virtualhosts_dir_path = join(conf_dispatcher_d_dir_path, "vhosts")
        renamed_virtualhosts_dir_path = join(conf_dispatcher_d_dir_path, "virtualhosts")
        # Rename the directory conf.dispatcher.d/vhosts to conf.dispatcher.d/virtualhosts and enter it.
        FolderOperationsUtility.__rename_folder__(old_virtualhosts_dir_path,
                                                  renamed_virtualhosts_dir_path,
                                                  conversion_step)
        # Remove any file prefixed ams_.
        FileOperationsUtility.__delete_all_files_containing_substring__(renamed_virtualhosts_dir_path,
                                                                        "ams_", conversion_step)
        files = FileOperationsUtility.__delete_all_files_not_conforming_to_pattern__(renamed_virtualhosts_dir_path,
                                                                                     "*.any", conversion_step)
        file_count = len(files)
        # If conf.dispatcher.d/virtualhosts now contains a single file
        if file_count == 1 and files[0].endswith("vhosts.any"):
            old_file_name = basename(files[0])
            # it should be renamed to virtualhosts.any
            renamed_file_path = join(dirname(files[0]), "virtualhosts.any")
            FileOperationsUtility.__rename_file__(files[0], renamed_file_path, conversion_step)
            # adapt the $include statements referring to that file in the farm files as well
            FileOperationsUtility.__replace_rule_in_include_statement__(conf_dispatcher_d_dir_path,
                                                                        constants.FARM,
                                                                        constants.INCLUDE_SYNTAX_IN_FARM,
                                                                        old_file_name, '"../virtualhosts/virtualhosts.any"',
                                                                        conversion_step)
        elif file_count > 1:
            # If the folder however contains multiple, farm specific files with that pattern,
            available_farm_files = self.__get_all_available_farm_files()
            if len(available_farm_files) > 1:
                for file in files:
                    if file.endswith("_vhosts.any"):
                        content_from_vhost_file = FileOperationsUtility.__get_content_from_file__(file, True)
                        # their contents should be copied to the $include statement referring to them in the farm files.
                        FileOperationsUtility.__replace_include_statement_with_content_of_rule_file__(
                            conf_dispatcher_d_dir_path,
                            constants.FARM, basename(file),
                            content_from_vhost_file,
                            constants.INCLUDE_SYNTAX_IN_FARM,
                            conversion_step)
                        FileOperationsUtility.__delete_file__(file, conversion_step)
            elif len(available_farm_files) == 1:
                # If the folder however contains multiple rule files specific to a single farm file, we should
                # consolidate all the included rule file into a single rule file and include it.
                rule_files = FileOperationsUtility.__get_all_file_names__(files)
                # find all the rule files that are actually included in single the farm file
                rule_files_included = FileOperationsUtility.__get_names_of_rule_files_included__(available_farm_files[0],
                                                                                        rule_files,
                                                                                        constants.INCLUDE_SYNTAX_IN_FARM)
                # delete the rule files not included in the single available farm file, and get the files actually used
                files = self.__filter_and_remove_unused_files(files, rule_files_included, conversion_step)
                # consolidate all remaining rule files into a single virtualhosts.any file
                FileOperationsUtility.__consolidate_all_rule_files_into_single_rule_file__(files,
                                                                                           join(
                                                                                               renamed_virtualhosts_dir_path,
                                                                                               "virtualhosts.any"),
                                                                                           conversion_step)
                # replace all statements including the files in the virtualhosts section with a single include statement
                include_statement_to_replace_with = '$include "../virtualhosts/virtualhosts.any"'
                FileOperationsUtility.__replace_file_includes_in_section_or_ifmodule__(conf_dispatcher_d_dir_path,
                                                                                       constants.FARM,
                                                                                       constants.VIRTUALHOSTS_SECTION_IN_FARM,
                                                                                       rule_files,
                                                                                       include_statement_to_replace_with,
                                                                                       conversion_step)
        self.__copy_default_virtualhost_files_from_sdk(conf_dispatcher_d_dir_path,
                                                       renamed_virtualhosts_dir_path,
                                                       conversion_step)
        # remove usage of variables from /virtualhost sections
        FileOperationsUtility.__remove_variable_usage_in_section__(conf_dispatcher_d_dir_path, constants.FARM,
                                                                   constants.VIRTUALHOSTS_SECTION_IN_FARM,
                                                                   conversion_step)
        self.__conversion_steps.append(conversion_step)

    def __check_virtualhosts_summary_generator(self):
        logger.info("AEMDispatcherConverter: Executing Rule : Checking vhosts folder.")
        return ConversionStep("Check VirtualHosts",
                              "Rename the directory `conf.dispatcher.d/vhosts` to "
                              "`conf.dispatcher.d/virtualhosts`. Remove any file prefixed `ams_` ."
                              + linesep +
                              "If `conf.dispatcher.d/virtualhosts` now contains a single file it should "
                              "be renamed to `virtualhosts.any` and adapt the `$include` statements "
                              "referring to that file in the farm files as well."
                              + linesep +
                              "If the folder however contains multiple, farm specific files with that "
                              "pattern, their contents should be copied to the `$include` statement "
                              "referring to them in the farm files."
                              + linesep +
                              "Copy the file `conf.dispatcher/virtualhosts/default_virtualhosts.any` from "
                              "the default AEM as a Cloud Service dispatcher configuration to that location."
                              + linesep +
                              "In each farm file, replace any filter include statement that looks like :"
                              "`$include \"/etc/httpd/conf.dispatcher.d/vhosts/ams_publish_vhosts.any\"`"
                              + linesep +
                              " with the statement: `$include \"../virtualhosts/default_virtualhosts.any\"`")

    def __copy_default_virtualhost_files_from_sdk(self, conf_dispatcher_d_dir_path, dir_of_operation, conversion_step):
        # Copy the file conf.dispatcher.d/virtualhosts/default_virtualhosts.any from the default skyline dispatcher
        # configuration to that location.
        default_virtualhost_file_from_sdk = join(self.__sdk_src_path, constants.CONF_DISPATCHER_D, "virtualhosts",
                                                 "default_virtualhosts.any")
        copy(default_virtualhost_file_from_sdk, dir_of_operation)
        logger.info(
            "AEMDispatcherConverter: Copied file 'conf.dispatcher.d/virtualhosts/default_virtualhosts.any' "
            "from the standard dispatcher configuration to %s.", dir_of_operation)
        conversion_step.__add_operation__(ConversionOperation(constants.ACTION_ADDED, dir_of_operation,
                                                              "Copied file "
                                                              "'conf.dispatcher.d/virtualhosts/default_virtualhosts.any'"
                                                              "'from the standard dispatcher configuration to "
                                                              + dir_of_operation))
        if exists(join(dir_of_operation, "virtualhosts.any")):
            # In each farm file, replace any filter include statements that looks as follows:
            # $include "/etc/httpd/conf.dispatcher.d/vhosts/ams_publish_vhosts.any"
            # with the statement:
            # $include "../virtualhosts/default_virtualhosts.any"
            replacement_include_file = constants.INCLUDE_SYNTAX_IN_FARM + ' "../virtualhosts/default_virtualhosts.any"'
            include_pattern_to_replace = constants.INCLUDE_SYNTAX_IN_FARM + ' "/etc/httpd/conf.dispatcher.d/vhosts/ams_'
            FileOperationsUtility.__replace_include_pattern_in_section__(conf_dispatcher_d_dir_path, constants.FARM,
                                                                         constants.VIRTUALHOSTS_SECTION_IN_FARM,
                                                                         include_pattern_to_replace,
                                                                         replacement_include_file,
                                                                         conversion_step)
        else:
            virtualhost_file_from_sdk = join(self.__sdk_src_path, constants.CONF_DISPATCHER_D, "virtualhosts",
                                             "virtualhosts.any")
            copy(virtualhost_file_from_sdk, dir_of_operation)
            logger.info(
                "AEMDispatcherConverter: Copied file 'conf.dispatcher.d/virtualhosts/virtualhosts.any' "
                "from the standard dispatcher configuration to %s.", dir_of_operation)
            conversion_step.__add_operation__(ConversionOperation(constants.ACTION_ADDED, dir_of_operation,
                                                                  "Copied file "
                                                                  "'conf.dispatcher.d/virtualhosts/virtualhosts.any'"
                                                                  "'from the standard dispatcher configuration to "
                                                                  + dir_of_operation))
            # In each farm file, replace any filter include statements that looks as follows:
            # $include "/etc/httpd/conf.dispatcher.d/vhosts/ams_publish_vhosts.any"
            # with the statement:
            # $include "../virtualhosts/virtualhosts.any"
            replacement_include_file = constants.INCLUDE_SYNTAX_IN_FARM + ' "../virtualhosts/virtualhosts.any"'
            include_pattern_to_replace = constants.INCLUDE_SYNTAX_IN_FARM + ' "/etc/httpd/conf.dispatcher.d/vhosts/ams_'
            FileOperationsUtility.__replace_include_pattern_in_section__(conf_dispatcher_d_dir_path, constants.FARM,
                                                                         constants.VIRTUALHOSTS_SECTION_IN_FARM,
                                                                         include_pattern_to_replace,
                                                                         replacement_include_file,
                                                                         conversion_step)

    # 14. Report and remove usage of non-whitelisted directives
    def __remove_non_whitelisted_directives(self):
        conversion_step = self.__remove_non_whitelisted_directives_summary_generator()
        available_vhosts_dir_path = join(self.__dispatcher_config_directory, constants.CONF_D,
                                         constants.AVAILABLE_VHOSTS)
        # create a set from the list of whitelisted directive
        # (in lowercase, since Directives in the configuration files are case-insensitive)
        whitelisted_directives_set = set(directive.lower() for directive in constants.WHITELISTED_DIRECTIVES_LIST)
        FileOperationsUtility.__remove_non_whitelisted_directives_in_vhost_files__(available_vhosts_dir_path,
                                                                                   whitelisted_directives_set,
                                                                                   conversion_step)
        self.__conversion_steps.append(conversion_step)

    def __remove_non_whitelisted_directives_summary_generator(self):
        logger.info("AEMDispatcherConverter: Checking for usage of non-whitelisted directives.")
        return ConversionStep("Remove usage of non-whitelisted directives",
                              "Checking for usage of non-whitelisted directives and remove them.")

    # 15. Replace variables in farm files
    def __replace_variable_in_farm_files(self):
        conversion_step = self.__replace_variable_in_farm_files_summary_generator()
        # In all farm files rename PUBLISH_DOCROOT to DOCROOT
        conf_dispatcher_d_dir_path = join(self.__dispatcher_config_directory, constants.CONF_DISPATCHER_D)
        FileOperationsUtility.__replace_all_usage_of_old_variable_with_new_variable__(conf_dispatcher_d_dir_path,
                                                                                      constants.FARM,
                                                                                      "PUBLISH_DOCROOT", "DOCROOT",
                                                                                      conversion_step)
        self.__conversion_steps.append(conversion_step)

    def __replace_variable_in_farm_files_summary_generator(self):
        logger.debug("AEMDispatcherConverter: Renaming PUBLISH_DOCROOT to DOCROOT in all farm files.")
        return ConversionStep("Replace variables in farm files",
                              "Rename PUBLISH_DOCROOT to DOCROOT in all farm files.")

    def __get_all_available_vhost_files(self):
        available_vhosts_dir_path = join(self.__dispatcher_config_directory, constants.CONF_D,
                                        constants.AVAILABLE_VHOSTS)
        files = [f for f in glob(join(available_vhosts_dir_path, "**", "*." + constants.VHOST), recursive=True)]
        return files

    def __get_all_available_farm_files(self):
        available_farms_dir_path = join(self.__dispatcher_config_directory, constants.CONF_DISPATCHER_D,
                                        constants.AVAILABLE_FARMS)
        files = [f for f in glob(join(available_farms_dir_path, "**", "*." + constants.FARM), recursive=True)]
        return files

    # delete all the non-included rule files, and return the files (file paths) that are actually included
    def __filter_and_remove_unused_files(self, all_files, used_file_names, conversion_step):
        used_files = set()
        for file in all_files:
            if basename(file) in used_file_names:
                used_files.add(file)
            else:
                FileOperationsUtility.__delete_file__(file, conversion_step)
        return used_files

    # this is a hack to check if files are symlinks
    def __is_symlink_file(self, file):
        file_content = FileOperationsUtility.__get_content_from_file__(file, False)
        return len(file_content) == 2 and file_content[1].startswith("../")
