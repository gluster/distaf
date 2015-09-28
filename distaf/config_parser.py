import yaml


def get_config_data():
    """
        Gets all the config data from the distaf_config.yml file

        Returns the parsed output of config in a dictionary format
    """
    configs = yaml.load(open('config.yml', 'r'))
    for vol in configs['volumes']:
        for node in configs['volumes'][vol]['servers']:
            if node not in configs['servers']:
                configs['servers'][node] = {}
        for node in configs['volumes'][vol]['peers']:
            if node not in configs['peers']:
                configs['servers'][node] = {}
    return configs
