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

from util.constants import SUMMARY_REPORT_FILE, TARGET_FOLDER, SUMMARY_REPORT_LINE_SEPARATOR as LINE_SEP
from util.conversion_report.conversion_operation import ConversionOperation
from util.conversion_report.conversion_step import ConversionStep

from os import getcwd, path, linesep
from shutil import copy
from typing import List


class SummaryReportWriter:
    """
    A utility class that provides functionality for creation of summary report for the dispatcher converter
    """

    @staticmethod
    def __write_summary_report__(conversion_steps: List[ConversionStep]):
        """
        Create a summary report which contains the step followed (and operations performed) during the conversion

        Parameters:
            conversion_steps(List[ConversionStep]): List of steps performed that are to be added to the summary report
        """
        # create a copy of the summary report template file in the target folder
        copy(path.join(getcwd(), "util", "conversion_report", "conversion-report.md"), TARGET_FOLDER)

        with open(SUMMARY_REPORT_FILE, "a") as file:
            for conversion_step in conversion_steps:
                if isinstance(conversion_step, ConversionStep):
                    # only if some operation is actually performed under the step
                    if conversion_step.__is_performed__():
                        file.write(LINE_SEP)
                        file.write("##### " + conversion_step.__get_rule__())
                        file.write(LINE_SEP)
                        file.write(conversion_step.__get_description__())
                        file.write(LINE_SEP)
                        SummaryReportWriter.__append_table_header(file)
                        SummaryReportWriter.__append_operation(file, conversion_step.__get_operations__())

    @staticmethod
    def __append_table_header(file):
        file.write(linesep)
        file.write("| ")
        file.write("Action Type")
        file.write(" | ")
        file.write("Location")
        file.write(" | ")
        file.write("Action")
        file.write(" |")
        file.write(LINE_SEP)
        file.write("| ----------- | -------- | ------ |")
        file.write(LINE_SEP)

    @staticmethod
    def __append_operation(file, conversion_operations):
        for conversion_operation in conversion_operations:
            if isinstance(conversion_operation, ConversionOperation):
                file.write("|")
                file.write(" " + conversion_operation.__get_operation_type__() + " ")
                file.write("|")
                file.write(" " + conversion_operation.__get_operation_location__() + " ")
                file.write("|")
                file.write(" " + conversion_operation.__get_operation_action__() + " ")
                file.write("|")
                file.write(LINE_SEP)
