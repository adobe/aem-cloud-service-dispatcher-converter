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


class ConversionOperation:
    """
    ConversionOperation describes a single operation (can be add/remove/rename/replace/delete operation) which has been
    performed on the target dispatcher configuration as part of some conversion step.

    Attributes:
    __type (str): The type of operation performed.
    __location (str): The location at which the operation has been performed.
    _action (str): The gist of the operation performed.

    """
    __type = None
    __location = None
    __action = None

    def __init__(self, operation_type, operation_location, operation_action):
        """
        Parameters:
            operation_type (str): The type of operation performed
            operation_location (str): The location at which the operation has been performed
            operation_action (str): The gist of the operation performed
        """
        self.__action = operation_action
        self.__location = operation_location
        self.__type = operation_type

    def __get_operation_type__(self):
        """
        Get the type of operation performed
        """
        return self.__type

    def __get_operation_location__(self):
        """
        Get the location at which the operation has been performed
        """
        return self.__location

    def __get_operation_action__(self):
        """
        Get the gist of the operation performed
        """
        return self.__action
