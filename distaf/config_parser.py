import yaml


def get_global_config(config_file):
    """
        Gets all the config data from the distaf_config.yml file

        Returns the parsed output of config in a dictionary format
    """
    configs = yaml.load(open(config_file, 'r'))
    for vol in configs['volumes']:
        for node in configs['volumes'][vol]['nodes']:
            if node not in configs['nodes']:
                configs['nodes'][node] = {}
        if configs['volumes'][vol]['peers'] is not None:
            for node in configs['volumes'][vol]['peers']:
                if node not in configs['peers']:
                    configs['nodes'][node] = {}
    return configs


def get_testcase_config(config_string):
    """
        Parses the yaml structure config string passed to the function

        @params: config string of yaml structure
        @returns: python dict with config values on Success
                  Upon failure None
    """
    if config_string == '':
        return None
    try:
        config_dict = yaml.load(config_string)
    except yaml.YAMLError:
        return None
    if 'runs_on_volumes' not in config_dict:
        config_dict['runs_on_volumes'] = 'ALL'
    if config_dict['runs_on_volumes'] == 'ALL':
        config_dict['runs_on_volumes'] = ['distribute', 'replicate', \
                'dist_rep', 'disperse', 'dist_disperse' ]
    if 'runs_on_protocol' not in config_dict:
        config_dict['runs_on_protocol'] = 'ALL'
    if config_dict['runs_on_protocol'] == 'ALL':
        config_dict['runs_on_protocol'] = ['glusterfs', 'nfs' ]
    if 'reuse_setup' not in config_dict:
        config_dict['reuse_setup'] = True
    return config_dict
