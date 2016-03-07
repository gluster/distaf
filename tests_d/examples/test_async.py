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


@testcase("run_async")
class RunAsync(DistafTestClass):
    """Run a command against all servers via run_async()

    Run with...
        time python main.py -d examples -t run_async
    """
    def setup(self):
        return True

    def run(self):
        retstat = 0
        tc.logger.info("Run command on all servers via run_async()")

        rasyncs = {}
        results = {}
        command = 'ls -ail; hostname'
        for node in tc.nodes:
            rasyncs[node] = tc.run_async(node, command)
            if not rasyncs[node]:
                retstat = retstat | rcode

        for node, proc in rasyncs.items():
            rcode, rout, rerr = proc.value()
            retstat = retstat | rcode

        if retstat == 0:
            return True

        return False

    def cleanup(self):
        return True

    def teardown(self):
        return True
