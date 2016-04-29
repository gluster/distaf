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


from distaf.util import tc, testcase
from distaf.distaf_base_class import DistafTestClass


@testcase("exercise_remote_commands")
class ExerciseRemoteConnections(DistafTestClass):
    """Run some commands against remote servers to
    test connectivity and speed.

    To test speed differences, set combinations of...
        connection_engine : ssh_controlpersist (default)
        connection_engine : rpyc
        connection_engine : ssh

        skip_log_inject : True|False

    Run with...
        time python main.py -d examples -t exercise_remote_commands
    """
    def setup(self):
        return True

    def run(self):
        retstat = 0
        for i in range(1, 10):
            for node in tc.all_nodes:
                tc.logger.info("Connection %s %i" % (node, i))
                rcode, _, _ = tc.run(node, "ls -dl /etc")
                if rcode != 0:
                    retstat = retstat | rcode

                rcode, _, _ = tc.run(node, "ls -dl /etc >&2")
                if rcode != 0:
                    retstat = retstat | rcode

        if retstat == 0:
            return True

        return False

    def cleanup(self):
        return True

    def teardown(self):
        return True
