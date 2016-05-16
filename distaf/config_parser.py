#  This file is part of DiSTAF
#  Copyright (C) 2015-2016  Red Hat, Inc. <http://www.redhat.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import yaml


def get_global_config(config_files):
    """
        Gets all the config data from the distaf_config.yml file

        Returns the parsed output of config in a dictionary format
    """
    configs = {}
    for config_file in config_files:
        configs.update(yaml.load(open(config_file, 'r')))

    return configs


def get_testcase_config(doc_string):
    """
    Parses the config yaml structure from the
        doc string passed to the function

    @params: doc string with yaml structure
    @returns: python dict with config values on Success
              Upon failure python dict with defaults
    """
    if not doc_string:
        config_dict = {}
        config_dict['runs_on_volumes'] = 'ALL'
        config_dict['runs_on_protocol'] = 'ALL'
        config_dict['reuse_setup'] = True
    else:
        if "---\n" in doc_string:
            config_string = doc_string.split("---\n")[1]
        else:
            config_string = doc_string

        try:
            config_dict = yaml.load(config_string)
            if isinstance(config_dict, str):
                config_dict = {}
        except yaml.YAMLError:
            config_dict = {}
            config_dict['runs_on_volumes'] = 'ALL'
            config_dict['runs_on_protocol'] = 'ALL'
            config_dict['reuse_setup'] = True
    if 'runs_on_volumes' not in config_dict:
        config_dict['runs_on_volumes'] = 'ALL'
    if config_dict['runs_on_volumes'] == 'ALL':
        config_dict['runs_on_volumes'] = ['distribute', 'replicate', \
                'dist_rep', 'disperse', 'dist_disperse']
    if 'runs_on_protocol' not in config_dict:
        config_dict['runs_on_protocol'] = 'ALL'
    if config_dict['runs_on_protocol'] == 'ALL':
        config_dict['runs_on_protocol'] = ['glusterfs', 'nfs']
    if 'reuse_setup' not in config_dict:
        config_dict['reuse_setup'] = True
    return config_dict
