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
        'REP_COUNT'       : 1,
        'DISPERSE'        : 1,
        'REDUNDANCY'      : 1,
        'STRIPE'          : 1,
        'TRANS_TYPE'      : 'tcp',
        'MASTERVOL'       : 'master',
        'SLAVEVOL'        : 'slave',
        'MOUNT_TYPE'      : 'glusterfs',
        'MOUNTPOINT'      : '/mnt/glusterfs',
        'REMOTE_USER'     : 'root',
        'MOUNTBROKER'     : 'False',
        'ENABLE_USS'      : 'False',
        'ENABLE_QUOTA'    : 'False',
        'GEO_USER'        : 'root',
        'GEO_GROUP'       : 'geogroup',
        'GEO_SYNC_MODE'   : 'rsync',
        'FILE_TYPE'       : 'text',
        'DIR_STRUCT'      : 'multi',
        'FILES_PER_DIR'   : 5,
        'NUM_FILES_MULTI' : 5,
        'NUM_FILES_SING'  : 1000,
        'NUM_THREADS'     : 5,
        'DIRS_BREADTH'    : 5,
        'DIRS_DEPTH'      : 5,
        'SIZE_MIN'        : '5k',
        'SIZE_MAX'        : '10k' }
    for conf in volume_config_dict.keys():
        if conf in os.environ:
            volume_config_dict[conf] = os.environ[conf]
    config_dict = {
        'LOG_FILE'        : '/var/log/tests/distaf_tests.log',
        'LOG_LEVEL'       : 'INFO' }
    for conf in config_dict.keys():
        if conf in os.environ:
            config_dict[conf] = os.environ[conf]
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
    ret = dict(volume_config_dict.items() + config_dict.items() + \
            setup_config_dict.items())
    return ret
