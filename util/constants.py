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

from os.path import join

TARGET_FOLDER = "./target"

TARGET_DISPATCHER_SRC_FOLDER = join(TARGET_FOLDER, "src")

LOG_FILE = "./result.log"

SUMMARY_REPORT_FILE = join(TARGET_FOLDER, "conversion-report.md")

SUMMARY_REPORT_LINE_SEPARATOR = "\n"

ACTION_ADDED = "Added"

ACTION_DELETED = "Deleted"

ACTION_REMOVED = "Removed"

ACTION_RENAMED = "Renamed"

ACTION_REPLACED = "Replaced"

CONF = "conf"

CONF_DISPATCHER_D = "conf.dispatcher.d"

CONF_D = "conf.d"

CONF_MODULES_D = "conf.modules.d"

VHOST = "vhost"

ANY = "any"

FARM = "farm"

ENABLED_FARMS = "enabled_farms"

ENABLED_VHOSTS = "enabled_vhosts"

AVAILABLE_VHOSTS = "available_vhosts"

AVAILABLE_FARMS = "available_farms"

COMMENT_ANNOTATION = "#"

VIRTUAL_HOST_SECTION_START = "<VirtualHost"

VIRTUAL_HOST_SECTION_END = "</VirtualHost>"

VIRTUAL_HOST_SECTION_START_PORT_80 = ":80>"

INCLUDE_SYNTAX_IN_VHOST = "Include"

INCLUDE_SYNTAX_IN_FARM = "$include"

RENDERS_SECTION = "/renders"

VIRTUALHOSTS_SECTION_IN_FARM = "/virtualhosts"

ALLOWED_CLIENTS_SECTION = "/allowedClients"

CLIENT_HEADER_SECTION = "/clientheader"

RULES_SECTION = "/rules"

FILTERS_SECTION = "/filter"

IF_BLOCK_START = "<If"

IF_BLOCK_END = "</If>"

BLOCK_START = "block_start"

BLOCK_END = "block_end"

# whitelisted directives (in lower case for ease of comparision; directives can be case-insensitive)
WHITELISTED_DIRECTIVES_LIST = [
    '<directory>',
    '<files>',
    '<filesmatch>',
    '<if>',
    '<ifdefine>',
    '<ifmodule>',
    '<location>',
    '<locationmatch>',
    '<proxy>',
    '<requireall>',
    '<requireany>',
    '<virtualhost>',
    'addcharset',
    'addencoding',
    'addhandler',
    'addoutputfilter',
    'addoutputfilterbytype',
    'addtype',
    'alias',
    'allow',
    'allowencodedslashes',
    'allowmethods',
    'allowoverride',
    'authbasicprovider',
    'authgroupfile',
    'authname',
    'authtype',
    'authuserfile',
    'browsermatch',
    'browsermatchnocase',
    'define',
    'deflatecompressionlevel',
    'deflatefilternote',
    'deflatememlevel',
    'deflatewindowsize',
    'deny',
    'directoryslash',
    'dispatcherdeclineroot',
    'dispatcherpasserror',
    'dispatcheruseprocessedurl',
    'documentroot',
    'errordocument',
    'fileetag',
    'filterchain',
    'filterdeclare',
    'filterprovider',
    'forcetype',
    'header',
    'include',
    'includeoptional',
    'keepalive',
    'limitrequestfieldsize',
    'modmimeusepathinfo',
    'options',
    'order',
    'passenv',
    'redirect',
    'redirectmatch',
    'remoteipheader',
    'remoteiptrustedproxylist',
    'requestheader',
    'requestreadtimeout',
    'require',
    'rewritecond',
    'rewriteengine',
    'rewritemap',
    'rewriteoptions',
    'rewriterule',
    'satisfy',
    'scriptalias',
    'secrequestbodyaccess',
    'secruleengine',
    'serveralias',
    'servername',
    'serversignature',
    'setenvif',
    'setenvifnocase',
    'sethandler',
    'setoutputfilter',
    'substitute',
    'traceenable',
    'undefine',
    'userdir']
