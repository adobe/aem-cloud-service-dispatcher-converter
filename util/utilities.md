# Utilities

This section lists generic file and folder manipulation utility methods exposed for the usage by configuration Converters.

### FileOperationsUtility

* ***`__check_for_undefined_variables__`***
   Checks vhost files for usage of undefined variables. If found, print warning in terminal and log error.

   **Parameters**
   1. *dir_path (str)*: The directory to be searched under.
   1. *defined_variables_list (List[str])*: The list of variables that are defined.

* ***`__consolidate_all_rule_files_into_single_rule_file__`***
   Consolidate content of all rule files into a single rule file, and delete the given rule files.

   **Parameters**
   1. *rule_files ((List[IO[AnyStr]]))*: The rule files whose content needs to be consolidated into a single rule file.
   1. *consolidated_rule_file_path (str)*: The new rule file path (along with the new rule file name).
   1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.

* ***`__delete_file__`***

   Deletes the provided file.

   **Parameters**
   1. *file_path (str)*: The path to the file to be deleted.
   1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.

* ***`__delete_files_with_extension__`***

   Deletes all files with given extension in a specific directory.
   Does not check sub-directories.

   **Parameters**

   1. *dir_path (str)*: The path to the directory where the deletion is to be performed.
   1. *extension (str)*: The file extension which is to be matched for deletion.
   1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.


* ***`__delete_all_files_containing_substring__`***

    Deletes all files containing given substring in a specific directory.
    Does not check sub-directories.

    **Parameters**

    1. *dir_path (str)*: The path to the directory where the deletion is to be performed.
    1. *substring (str)*: The sub-string in the file name which is to be matched for deletion.
    1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.


* ***`__delete_all_files_with_prefix__`***

   Deletes all files containing given prefix in a specific directory. Does not check sub-directories.

   **Parameters**

   1. *dir_path (str)*: The path to the directory where the deletion is to be performed.
   1. *prefix (str)*: The file name prefix which is to be matched for deletion.
   1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.


* ***`__delete_all_files_not_conforming_to_pattern__`***

   Deletes all the files in a given directory (recursively) on conforming to the given file name pattern (for example, '*.vars'). Returns the files remaining.

    **Parameters**
 
    1. *dir_path (str)*: The path to the directory where the deletion is to be performed.
    1. *pattern (str)*: The file pattern to be persisted.
    1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.

   **Returns**
    a list containing the names of the files in the directory.


* ***`__get_all_file_names__`***

    Get all the file names from the provided list of files.

   **Parameters**
   1. *files (List[IO[AnyStr]])*: The list of files whose names we want to retrieve .

   **Returns**
    List[str]: A list of file names.


* ***`__get_content_from_file__`***

    Returns the content of a given file.
    Also provides the functionality to recursively fetch the content of a symlink files target.

   **Parameters**
   1. *file_path (str)*: The path to file whose content is to be retrieved.
   1. *recursive (bool)*: If true and given file is a symlink file, then recursively fetch the content of the target link if true.

   **Returns**
    String: Content of the file


* ***`__get_names_of_rule_files_included__`***

    From the given list of rule files, get the file names which are actually included/used in the given file.

   **Parameters**
   1. *file_path (str)*: The file in which we need to check for the rule files' inclusion.
   1. *rule_files_to_check (List[str])*: The list of rule files names, whose inclusion we need to check for.
   1. *include_syntax (str)*: The include statement syntax (specific to vhost or farm files).

   **Returns**
    Set[str]: A set of file (from among the given rule files) which are actually included/used.


* ***`__remove_all_usage_of_old_variable__`***

   Replaces usage of specified variable in all files of given file-type in specified directory and sub-directories.

   **Parameters**
   1. *dir_path (str)*: The path to directory whose files are to be processed
   1. *file_extension (str)*: The extension of the type that needs to be processed
   1. *variable_to_remove (str)*: The variable that is to be removed.
   1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.


* ***`__remove_include_statement_for_some_rule__`***

   Removes inclusion of some file from all files os given file-extension in specified directory and sub-directories.

   **Parameters**
   1. *dir_path (str)*: The path to directory whose files are to be processed.
   1. *include_statement_syntax (str)*: The syntax of the include statement to be looked for.
   1. *file_extension (str)*: The extension of the type that needs to be processed.
   1. *rule_file_name_to_remove (str)*: The rule file name (in include statement) that is to be removed.
   1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.


* ***`__replace_file_includes_in_section_or_ifmodule__`***

   In the specified section/module replace all statements including any file from the given list of rule files with new file include within specified section/module of all files (of given file extension) in specified directory and sub-directories.
   Please provide only the replacement filename in case of replacement in vhost files, and complete replacement include statement in case of farm files.

   **Parameters**
   1. *dir_path (str)*: The path to directory whose files are to be processed.
   1. *file_extension (str)*: The extension of the type that needs to be processed.
   1. *section_header (str)*: The section header (within the file), whose content is to be processed.
   1. *rule_files_to_replace (List[IO[AnyStr]])*: Tlist of rule files whose include statements are to be replaced.
   1. *file_to_replace_with (str)*: Include statement or rule filename that is to be replaced with.
   1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.


* ***`__remove_non_matching_files_by_name__`***

   Remove the files in destination directory, not present in source directory (comparison by name).

   **Parameters**
   1. *src_dir (str)*: The source directory's path.
   1. *dest_dir (str)*: The destination directory's path.
   1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.


* ***`__remove_non_whitelisted_directives_in_vhost_files__`***

   Report and remove usage of non-whitelisted directives in configuration files

   **Parameters**
   1. *dir_path (str)*: The path to directory whose files are to be processed.
   1. *whitelisted_directives_set (Set[str])*: The set of whitelisted directives that are allowed (lowercase).
   1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.


* ***`__remove_variable_usage_in_section__`***

   Remove the usage of variables within specified sections of all files (of given file extension) in specified directory and sub-directories.

   **Parameters**
   1. dir_path (str): The path to dir where the vhost files reside
   1. file_extension (str): The extension of the type that needs to be processed
   1. section_header (str): The section header (within the file), whose content is to be processed
   1. conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.


* ***`__remove_virtual_host_sections_not_port_80__`***

   Remove any VirtualHost section not referring to port 80 from all vhost files under specified directory.

   **Parameters**
   1. dir_path (str): The path to dir where the vhost files reside
   1. conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.


* ***`__rename_file__`***

   Renames a file.

   **Parameters**
    
   1. *src_path (str)*: The path to file to be renamed.
   1. *dest_path (str)*: The renamed file path string.
   1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.

* ***`__replace_all_usage_of_old_variable_with_new_variable__`***
 
   Replace usage of a variable with a new variable in all files of given file-type in specified directory and sub-directories.

   **Parameters**
   1. *dir_path (str)*: The path to directory whose files are to be processed.
   1. *file_extension (str)*: The extension of the type that needs to be processed.
   1. *variable_to_replace (str)*: The variable that is to be replaced.
   1. *new_variable (str)*: The variable that is to be replaced with.
   1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.


* ***`__replace_content_of_section__`***
 
   Replace the content of specified section with given file include statement, in all files of specified type in provided directory and sub-directories.

   **Parameters**
   1. *dir_path (str)*: The path to directory whose files are to be processed
   1. *section_header (str)*: The section header (within the file), whose content is to be replaced
   1. *include_statement_to_replace_with (str)*: include statement pattern that is to be replaced with
   1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.


* `__replace_include_pattern_in_section__`

   Replace include statements of certain pattern within specified sections of all files (of given file extension) in specified directory and sub-directories.

   **Parameters**
   1. dir_path (str): The path to directory whose files are to be processed
   1. file_extension (str): The extension of the type that needs to be processed
   1. section_header (str): The section header (within the file), whose content is to be processed
   1. pattern_to_replace (str): include statement pattern that is to be replaced
   1. file_to_replace_with (str): include statement pattern that is to be replaced with
   1. conversion_step (ConversionStep): The conversion step to which the performed actions are to be added.


* `__replace_include_statement_with_content_of_rule_file__`

    Replace file include statements with the content of the included file itself, in all files of given file-type in specified directory and sub-directories.

    **Parameters**

    1. *dir_path (str)*: The path to directory whose files are to be processed.
    1. *file_extension (str)*: The extension of the type that needs to be processed.
    1. *rule_file_to_replace (str)*: include statement pattern that is to be replaced.
    1. *content (str)*: The content of file with which the include statement is to be replaced.
    1. *include_statement_syntax (str)*: The syntax of the include statement to be replaced.
    1. *conversion_step (ConversionStep*): The conversion step to which the performed actions are to be added.


* ***`__replace_file_name_in_include_statement__`***

   Replace the file name (with new file name) in all include statements from all files os given file-extension in specified directory and sub-directories.
   Usage scenario : In all include statements including the file `ams_publish_filters.any` replace it with inclusion of the file `"filters.any"`.

   **Parameters**

   1. *dir_path (str)*: The path to directory whose files are to be processed
   1. *include_statement_syntax (str)*: The syntax of the include statement to be looked for
   1. *file_extension (str)*: The extension of the type that needs to be processed
   1. *file_to_replace (str)*: The rule file name (in include statement) that is to be replaced
   1. *file_to_replace_with (str)*: The complete rule (in include statement) that is to be replaced with
   1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.


* ***`__replace_rule_in_include_statement__`***

   Replace inclusion rule (with new rule) from all files os given file-extension in specified directory and sub-directories.
   Usage scenario : In all include statements including the file `ams_publish_filters.any` replace with the rule `"../filters/filters.any"`

   **Parameters**

   1. *dir_path (str)*: The path to directory whose files are to be processed
   1. *include_statement_syntax (str)*: The syntax of the include statement to be looked for
   1. *file_extension (str)*: The extension of the type that needs to be processed
   1. *file_to_replace (str)*: The file name (in the rule) that is to be replaced
   1. *rule_to_replace_with (str)*: The complete rule (in include statement) that is to be replaced with
   1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.


### FolderOperationsUtility

* ***`__delete_folder__`***

   Deletes the specified folder.

   **Parameters**
   1. *dir_path (str)*: The directory to be deleted.
   1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.


* ***`__rename_folder__`***
  
   Renames the specified folder.

   **Parameters**
   1. *dir_path (str*): The directory to be renamed.
   1. *conversion_step (ConversionStep)*: The conversion step to which the performed actions are to be added.

