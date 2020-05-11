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


class ConversionStep:
    """
    ConversionStep describes a single step (or rule) that has been performed with the objective of generating a
    dispatcher configuration compatible for AEM as a Cloud Service.
    Each step (or rule) can have multiple ConversionOperation performed as part of it.

    Attributes:
    __rule (str): The rule that is being executed/followed.
    __description (str): The details of the rule that is being followed for conversion.
    __operations_performed (List[ConversionOperation]): The list of operations performed while executing the step.

    """
    __rule = None
    __description = None
    __operations_performed = None

    def __init__(self, rule, description):
        """
        Parameters:
            rule (str): The rule that is being executed/followed
            description (str): The details of the rule that is being followed for conversion
        """
        self.__rule = rule
        self.__description = description
        self.__operations_performed = []

    def __add_operation__(self, operation):
        """
        Add an operation to the list of operations performed while executing the step
        """
        self.__operations_performed.append(operation)

    def __get_rule__(self):
        """
        Get the rule that is being executed/followed.
        """
        return self.__rule

    def __get_description__(self):
        """
        Get the details of the rule that is being followed for conversion.
        """
        return self.__description

    def __get_operations__(self):
        """
        Get the list of operations performed while executing the step

        Return:
            List[ConversionOperation]
        """
        return self.__operations_performed

    def __is_performed__(self):
        """
        Find whether some operation (under the given step) has been performed on target dispatcher configurations

        Return:
            bool: `true` if at least one operation has been performed, else `false`
        """
        return len(self.__operations_performed) > 0
