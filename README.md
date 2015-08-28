DiSTAF - Di'stributed Systems Test Automation Framework
========================================================

DiSTAF is a test automation framework for distributed systems. Although the
framework is written with glusterfs in mind, this can be used for test automation
of many distributed systems. And this framework is written with portability in
mind. It just needs ip addresses or resolvable hostnames of servers and clients.
The servers and clients can be physical machines or vms or even linux conatiners.

**About the name:**
DiSTAF (or distaf) is short for Di'stributed Systems Test Automation Framework.
Also distaff is a tool used in spinning, which is designed to hold unspun fibres
together keeping them untangled and thus easing the process of spinning. This
frameowrk is trying to do just that, keeping the machines untangled and and easing
the process of writing and executing the test cases. Hence the name DiSTAF (distaf)

Architecture of the Framework
==============================
**Terminologies used:**
* *Management node* or *rpyc client* - The node from which this test suite is executed. This node is responsible for orchestration of test automation.
* *Test machines* - These include all the machines/nodes/servers participating in tests.

By default, all *test machines* run sshd. *Management node* connects to *test machines*
using rpyc zero-deploy, which internally makes use of ssh tunnelling protocol for
establishing and maintaining the secure connections. The connection is kept open for
the entire duration of the tests. All the synchronous commands run by the test cases,
uses this connection to run them. For asynchronous calls, a new connection is opened.
This connection will be closed when async command returns.

And python unittest is used for running tests and generating the results results.

How to Setup
================
1. Clone this git repo and cd in to it i.e. `cd distaf` on the *Management Node*.
2. Populate the config.sh with your environment details. And then source the config.sh  
   `. config.sh`
2. Establish a passwordless ssh between *Management Node* to all *test machines*.  
   `./libs/create_passwdless_ssh.sh`.  
    This will ask for the password of all your test machines.

How to run
=============

###On the management node
 - Source the config.sh file which has information about test environment.

 - To run all test cases: `python main.py` or `./main.py`

 - To run only a specific test case: `python main.py -t basic_test`

 - To run multiple test cases: `python main.py -t "basic_test0 basic_test1"`

 - To run all tests in a directory: `python main.py -d snapshot`  

 - To run specific tests in a specific directory: `python main.py -d snapshot -t "snaptest0 snaptest1"`
####Note:
     * Automation test logs are at /var/log/tests/ by default in management node. This can be changed by exporting LOG_FILE="/new/path/"

 - To create junit output in directory /tmp/test_results: `python main.py -j /tmp/test_results`

How to write tests
====================

1. Create a directory inside ./tests_d with your component name.     

   Note: These directories should be importable from other modules, so the name should be a valid Python variable.

2. The test should follow test_*test name*.py format.

3. For test skeleton and example please look at the
   tests_d/example/test_basic_gluster_tests.py

TODO
=====

* Better test case selection logic
* Better logging of test cases/results
* Integrating with nose tests for Jenkins friendly reporting format
* Glusterfs health monitoring in each servers
* setup_fs to create the initial xfs/ext4 partition before running the tests

Integration Work
=================

We are also working on integrating this project with dockit (https://github.com/humblec/dockit)
This would enable to simulate multinode testing from a single host node. Each of the servers and clients
would be docker containers.
