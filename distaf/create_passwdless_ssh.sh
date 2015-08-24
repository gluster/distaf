#!/bin/bash

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
