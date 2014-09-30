import re
import os
import sys
import rpyc
import logging

class big_bang:

    def __init__(self):
        """
            Initialises the whole environment and establishes connection
        """
        self.mgmt_node = ''
        self.clients = self.nodes = self.peers = self.gm_nodes = []
        self.gm_peers = self.gs_nodes = self.gs_peers = []
        self.number_nodes = self.number_peers = self.number_gm_nodes = 0
        self.number_gm_peers = self.number_gs_nodes = self.number_gs_peers = 0
        self.number_clients = self.number_servers = self.number_masters = 0
        self.number_slaves =0

        if 'MGMT_NODE' in os.environ:
            self.mgmt_node = os.environ['MGMT_NODE']
        if 'NODES' in os.environ:
            self.nodes = os.environ['NODES'].split(' ')
        if 'PEERS' in os.environ:
            self.peers = os.environ['PEERS'].split(' ')
        if 'CLIENTS' in os.environ:
            self.clients = os.environ['CLIENTS'].split(' ')
        if 'GM_NODES' in os.environ:
            self.gm_nodes = os.environ['GM_NODES'].split(' ')
        if 'GM_PEERS' in os.environ:
            self.gm_peers = os.environ['GM_PEERS'].split(' ')
        if 'GS_NODES' in os.environ:
            self.gs_nodes = os.environ['GS_NODES'].split(' ')
        if 'GS_PEERS' in os.environ:
            self.gs_peers = os.environ['GS_PEERS'].split(' ')

        self.number_nodes = len(self.nodes)
        self.number_peers = len(self.peers)
        self.number_clients = len(self.clients)
        self.number_gm_nodes = len(self.gm_nodes)
        self.number_gm_peers = len(self.gm_peers)
        self.number_gs_nodes = len(self.gs_nodes)
        self.number_gs_peers = len(self.gs_peers)


        self.servers = self.nodes + self.peers + self.gm_nodes + self.gm_peers \
                       + self.gs_nodes + self.gs_peers
        self.all_nodes = self.nodes + self.peers + self.clients + self.gm_nodes\
                         + self.gm_peers + self.gs_nodes + self.gs_peers
        self.connection_handles = {}
        for node in self.all_nodes:
            c0 = rpyc.connect(node, 18861)
            async_object = rpyc.async(c0.root.run)
            self.connection_handles[node] = ( c0, async_object)

        self.logger = logging.getLogger('rpyc_client')
        self.lhndlr = logging.FileHandler('/var/log/tests/client_rpyc.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s %(message)s')
        self.lhndlr.setFormatter(formatter)
        self.logger.addHandler(self.lhndlr)
        self.logger.setLevel(logging.DEBUG)

    def run(self, machine, cmd):
        """
            Run the specified command in specified remote node synchronously
        """
        self.logger.info("Executing %s on %s" % (cmd, machine))
        c = self.connection_handles[machine][0]
        try:
            p, pout, perr = c.root.run(cmd)
        except EOFError:
            c = rpyc.connect(machine, 18861)
            casync = rpyc.async(c.root.run)
            self.connection_handles[machine] = (c, casync)
            p, pout, perr = c.root.run(cmd)
        self.logger.info("\"%s\" on %s: RETCODE is %d" % (cmd, machine, p))
        if pout != "":
            self.logger.info("\"%s\" on %s: STDOUT is \n %s" % \
                            (cmd, machine, pout))
        if perr != "":
            self.logger.info("\"%s\" on %s: STDERR is \n %s" % \
                            (cmd, machine, perr))
        return ( p, pout, perr )

    def run_async(self, machine, cmd):
        """
            Run the specified command in specified remote node asynchronously
        """
        self.logger.info("Executing %s on %s in background" % (cmd,machine))
        try:
            p = self.connection_handles[machine][1](cmd)
        except EOFError:
            c = rpyc.connect(machine, 18861)
            casync = rpyc.async(c.root.run)
            self.connection_handles[machine] = (c, casync)
            p = casync(cmd)
        return p

    def run_servers(self, command):
        """
            Run the specified command in each of the server in parallel
        """
        sdict = {}
        out_dict = {}
        ret = True
        self.logger.info("Executing %s on all servers" % command)
        for server in self.servers:
            sdict[server] = self.connection_handles[server][1](command)
        for server in self.servers:
            sdict[server].wait()
            ps, pout, perr = sdict[server].value
            self.logger.debug("%s returned with status %d" % (server, ps ))
            out_dict[server] = ps
            if 0 != ps:
                ret = False
        return (ret, out_dict)


    def refresh_connections(self):
        data = 'Thisismydataandyoudonotworryaboutdecipheriingthisthing' * 10
        for node in self.all_nodes:
            try:
                self.connection_handles[node][0].ping(data, 42)
            except EOFError, PingError:
                self.logger.info("Connection to %s is broken. reestablishing \
                                  the connection" % node)
                self.connection_handles[node][0].close()
                conn = rpyc.connect(node, 18861)
                aconn = rpyc.async(conn.root.run)
                self.connection_handles[node] = (conn, aconn)


    def fini(self):
        for conn in self.connection_handles.keys():
            self.connection_handles[conn][0].close()
