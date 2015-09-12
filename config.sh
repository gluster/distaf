# This file contains the details of nodes in the test cluster.
# Each of the variable is explained below
#
# MGMT_NODE: The node from which this test suite is executed.
#            This is optional if not used in test case.
# NODES: The gluster servers. There should be at least one server.
# PEERS: The peer are also gluster servers which will be peer probed
#        later during the tests for add-brick and rebalance tests.
#        This is optional if not used in test case.
# CLIENTS: gluster clients where volume is mounted. Optional if not used.
# GM_NODES: Only applicable for geo-rep. geo-rep master nodes.
# GS_NODES: Only applicable for geo-rep. geo-rep slave nodes.


export NODES="mustang harrier typhoon falcon"
export CLIENTS="interceptor"
