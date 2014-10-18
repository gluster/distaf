glusterfs test automation framework
==============================================

This is a glusterfs test automation framework written in python. The framework
is written with portability in mind. It just needs ip addresses or resolvable
hostnames of servers and clients. The servers and clients can be physical machines
of vms or even linux conatiners.

Architecture of the Framework
==============================
An rpc server (server_rpycd) runs as a daemon on each of the *nodes* in the test
cluster and listens in a particular port. *The management node* (The node from which
this test suite is executed) connects to each nodes in the test cluster.

The connection to each node is done at the start of tests and each test case uses
this connection to execute any commands in the servers/clients. The connection is
torn down at the end of tests. A disconnection for any reason will trigger a
reconnection from the management node.


Setup
================
The machines required to run automation can be devided broadly in to two categories.
* Management Node
* Test nodes (Which participates in test)

*Management Node* : This node is responsible for orchestration of test automation. This can be your workstation or Laptop.  
###On management Node

1. Clone this git repo and cd in to it i.e. `cd glusterfs-automation-framework`

2. scp libs/server_rpycd /usr/local/bin to each of your server nodes.

3. scp libs/rcscript_server_rpycd to /etc/init.d/server_rpycd to all
   of your servers/nodes. 

###On the nodes in test cluster
1.  Install *rpyc* Python module i.e. `easy_install rpyc`

2. Start the server using /etc/init.d/server_rpycd start

3. Run the following commands on each of your machines.
   chkconfig server_rpycd --add
   chkconfig server_rpycd on

4. Source the config.sh file which has information about test environment.


How to run
=============

###On the management node
 - To run only a specific test case: `python main.py -t basic_test`

   - To run multiple test cases: `python main.py -t "basic_test0 basic_test1"`

   - To run all tests in a directory: `python main.py -d snapshot`

How to write tests
====================

1. Create a directory inside ./tests_d with your component name.     

   Note: These directories should be importable from other modules, so the name should be a valid Python variable.

2. The test should follow test_<test-name>.py format.

3. For test skeleton and example please look at the
   tests_d/example/test_basic_gluster_tests.py

TODO
=====

* Automating the initial setup part using pexpect or expect
* Better test case selection logic
* Better logging of test cases/results
* Forcing the order of execution if testcases whenever required
* Integrating with nose tests for Jenkins friendly reporting format
* Logs monitoring in each servers
* More and more library functions

Integration Work
=================

We are also working on integrating this project with dockit (https://github.com/humblec/dockit)
This would enable to simulate multinode testing from a single host node. Each of the servers and clients
would be docker containers.
