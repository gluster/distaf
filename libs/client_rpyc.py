import os
import time
import logging
from libs.config_parser import get_config_data
from plumbum import SshMachine
from rpyc.utils.zerodeploy import DeployedServer

class big_bang:

    def __init__(self):
        """
            Initialises the whole environment and establishes connection
        """
        self.config_dict = get_config_data()

        self.nodes = self.config_dict['NODES']
        self.peers = self.config_dict['PEERS']
        self.clients = self.config_dict['CLIENTS']
        self.gm_nodes = self.config_dict['GM_NODES']
        self.gm_peers = self.config_dict['GM_PEERS']
        self.gs_nodes = self.config_dict['GS_NODES']
        self.gs_peers = self.config_dict['GS_PEERS']
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

        client_logfile = self.config_dict['LOG_FILE']
        loglevel = getattr(logging, self.config_dict['LOG_LEVEL'].upper())
        client_logdir = os.path.dirname(client_logfile)
        if not os.path.exists(client_logdir):
            os.makedirs(client_logdir)
        self.logger = logging.getLogger('client_rpyc')
        self.lhndlr = logging.FileHandler(client_logfile)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s %(message)s')
        self.lhndlr.setFormatter(formatter)
        self.logger.addHandler(self.lhndlr)
        self.logger.setLevel(loglevel)

        self.connection_handles = {}
        self.subp_conn = {}
        for node in self.all_nodes:
            self.logger.debug("Connecting to node: %s" % node)
            dep = DeployedServer(SshMachine(node, user="root"))
            c = dep.classic_connect()
            self.connection_handles[node] = (dep, c)
            self.subp_conn[node] = c.modules.subprocess


    def refresh_connections(self, node, timeout=210):
        self.logger.info("Closing the connection to %s" % node)
        self.connection_handles[node][1].close()
        self.logger.info("reconnecting to %s" % node)
        while timeout >= 0:
            try:
                dep = DeployedServer(SshMachine(node, user='root'))
                c = dep.classic_connect()
                self.connection_handles[node] = (dep, c)
                break
            except:
                self.logger.debug("Couldn't connect to %s. Retrying in 42 secs" \
                % node)
                time.sleep(42)
                timeout = timeout - 42
        if timeout < 0:
            self.logger.critical("Unable to connect to %s" % node)
            return False
        else:
            self.logger.debug("Connection re-established to %s" % node)
            return True

    def run(self, node, cmd):
        """
            Run the specified command in specified remote machine

            Returns a tuple of (retcode, stdout, stderr) of the command
            in remote machine
        """
        self.logger.info("Executing %s on %s" % (cmd, node))
        subp = self.subp_conn[node]
        try:
            p = subp.Popen(cmd, shell=True, stdout=subp.PIPE, stderr=subp.PIPE)
        except:
            ret = self.refresh_connections(node)
            if not ret:
                self.logger.critical("Connection to %s couldn't be established"\
                % node)
                return (-1, -1, -1)
            c = self.connection_handles[node][1]
            subp = c.modules.subprocess
            self.subp_conn[node] = subp
            p = subp.Popen(cmd, shell=True, stdout=subp.PIPE, stderr=subp.PIPE)
        pout, perr = p.communicate()
        ret = p.returncode
        self.logger.info("\"%s\" on %s: RETCODE is %d" % (cmd, node, ret))
        if pout != "":
            self.logger.info("\"%s\" on %s: STDOUT is \n %s" % \
                            (cmd, node, pout))
        if perr != "":
            self.logger.info("\"%s\" on %s: STDERR is \n %s" % \
                            (cmd, node, perr))
        return ( ret, pout, perr )

    def run_async(self, node, cmd):
        """
            Run the specified command in specified remote node asynchronously
        """
        try:
            c = self.connection_handles[node][0].classic_connect()
        except:
            ret = self.refresh_connections(node)
            if not ret:
                self.logger.critical("Couldn't connect to %s" % node)
                return None
            c = self.connection_handles[node][0].classic_connect()
        self.logger.info("Executing %s on %s asynchronously" % (cmd, node))
        p = c.modules.subprocess.Popen(cmd, shell=True, \
            stdout=c.modules.subprocess.PIPE, stderr=c.modules.subprocess.PIPE)
        def value():
            pout, perr = p.communicate()
            retc = p.returncode
            c.close()
            self.logger.info("\"%s\" on \"%s\": RETCODE is %d" % \
            (cmd, node, retc))
            if pout != "":
                self.logger.debug("\"%s\" on \"%s\": STDOUT is \n %s" % \
                (cmd, node, pout))
            if perr != "":
                # Log the perr at both debug and error level
                # This is done to make sure that error is logged when log level
                # is not DEBUG. Also to make sure to print the perr as ERROR
                # in the log file. Helps in reading/debugging
                self.logger.debug("\"%s\" on \"%s\": STDERR is \n %s" % \
                (cmd, node, perr))
                self.logger.error("\"%s\" on \"%s\": STDERR is \n %s" % \
                (cmd, node, perr))
            return (retc, pout, perr)
        p.value = value
        p.close = lambda: c.close()
        return p

    def run_servers(self, command):
        """
            Run the specified command in each of the server in parallel
        """
        sdict = {}
        out_dict = {}
        ret = True
        for server in self.servers:
            sdict[server] = self.run_async(server, command)
        for server in self.servers:
            sdict[server].wait()
            ps, pout, perr = sdict[server].value()
            out_dict[server] = ps
            if 0 != ps:
                ret = False
        return (ret, out_dict)

    def fini(self):
        for conn in self.connection_handles.keys():
            self.connection_handles[conn][1].close()
            self.connection_handles[conn][0].close()
