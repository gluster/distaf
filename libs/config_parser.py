import os

def get_config_data():
    """
        Gets all the config data from the environmental variables

        Returns the value of requested parameter
        If nothing is requested the whole dict is sent
        If the requested parameter does not exist, the False is returned
    """
    volume_config_dict = {
        'VOLNAME'         : 'testvol',
        'DIST_COUNT'      : 2,
        'REP_COUNT'       : 2,
        'STRIPE'          : 1,
        'TRANS_TYPE'      : 'tcp',
        'MOUNT_TYPE'      : 'glusterfs',
        'MOUNTPOINT'      : '/mnt/glusterfs',
        'LOG_LEVEL'       : 'DEBUG',
        'GEO_USER'        : 'root',
        'FILE_TYPE'       : 'text',
        'DIR_STRUCT'      : 'multi',
        'NUM_FILES_MULTI' : 5,
        'NUM_FILES_SING'  : 1000,
        'NUM_THREADS'     : 5,
        'DIRS_BREADTH'    : 5,
        'DIRS_DEPTH'      : 5,
        'SIZE_MIN'        : '5k',
        'SIZE_MAX'        : '10k',
        'LOG_FILE'        : '/var/log/tests/distaf_tests.log' }
    for conf in volume_config_dict.keys():
        if conf in os.environ:
            volume_config_dict[conf] = os.environ[conf]
    setup_config_dict = {
        'MGMT_NODE' : [],
        'NODES' : [],
        'PEERS' : [],
        'CLIENTS' : [],
        'GM_NODES' : [],
        'GS_NODES' : [],
        'GM_PEERS' : [],
        'GS_PEERS' : [] }
    for conf in setup_config_dict.keys():
        if conf in os.environ:
                setup_config_dict[conf] = os.environ[conf].split(' ')
    return dict(volume_config_dict.items() + setup_config_dict.items())
