#!/bin/bash
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


function create_passwordless_ssh()
{
    target_node="$1"
    sed -i "/$target_node/d" ~/.ssh/known_hosts
    ssh-keyscan $target_node 1 >> ~/.ssh/known_hosts
    test -f ~/.ssh/id_rsa.pub || { \
    expect -c "
    set timeout 90
    set env(TERM)
    spawn ssh-keygen -t rsa
    expect \"id_rsa): \"
    send \"\r\"
    expect \"passphrase): \"
    send \"\r\"
    expect \"passphrase again: \"
    send \"\r\"
    expect eof
    "
    }

    expect -c "
    set timeout 90
    set env(TERM)
    spawn ssh-copy-id root@$target_node
    expect \"password: \"
    send \"$password\r\"
    expect eof
    "
}

function main()
{
    ALL_NODES="$NODES $CLIENTS $PEERS $GM_NODES $GS_NODES"
    echo -n "Enter the password of your test machines: "
    stty -echo
    trap 'stty echo' EXIT
    read password
    stty echo
    trap - EXIT
    for node in $ALL_NODES; do
        create_passwordless_ssh $node
    done
}

main"$@"
