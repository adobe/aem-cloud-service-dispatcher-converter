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

from converter.aem_dispatcher_converter import AEMDispatcherConverter
from util import constants

from argparse import ArgumentParser
from shutil import copytree, rmtree
from os.path import exists

parser = ArgumentParser()
parser.add_argument('--sdk_src', help='Absolute path to the src folder of the dispatcher sdk')
parser.add_argument('--cfg', help='Absolute path to dispatcher config folder')
args = parser.parse_args()

# if `target` folder already exists, delete it
if exists(constants.TARGET_FOLDER):
    rmtree(constants.TARGET_FOLDER)
copytree(args.cfg, constants.TARGET_DISPATCHER_SRC_FOLDER, True)
converter = AEMDispatcherConverter(args.sdk_src, constants.TARGET_DISPATCHER_SRC_FOLDER)
converter.__transform__()
print("\nTransformation Complete!\n")
print("Please check", constants.TARGET_DISPATCHER_SRC_FOLDER, "folder for transformed configuration files.")
print("Please check", constants.SUMMARY_REPORT_FILE, "for summary report.")
print("Please check", constants.LOG_FILE, "for logs.")
