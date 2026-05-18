#!/usr/bin/env python3
import sys,os,stat
import argparse
import re

import nftables

def parse_args(argv):
    parser = argparse.ArgumentParser("Use as root to destroy TiledViz connectiondock nft rules during debug.")
    parser.add_argument('--all', action='store_true',
                        help='Destroy all TiledViz chains.',default=False)
    parser.add_argument('-n', '--connectionnumber',
                        help='Docker connectiondock number to be closed.')
    args = parser.parse_args(argv[1:])
    return args

args = parse_args(sys.argv)

nft = nftables.Nftables()

if (args.all):
    print("destroy chain ip filter TILEDVIZ")
    nft.cmd("destroy chain ip filter TILEDVIZ")

    rc, output, error = nft.cmd("list table ip filter")
    #print(f"{rc}\n\n {output}\n\n {error}\n\n")
    matches = re.findall(r'connectiondock[0-9]+',output)
    print(matches)
    for i in matches :
        destroychain=f"destroy chain ip filter {i}"
        print(destroychain)
        nft.cmd(destroychain)
else:
    id=int(args.connectionnumber)
    ConnectName=f"connectiondock{id}"

    print(f"remove jump connectiondock {ConnectName} rule in TILEDVIZ chain")
    nft.set_handle_output("True")
    rc, output, error = nft.cmd("list table ip filter")
    #print(f"{rc}\n\n {output}\n\n {error}\n\n")
    matches = re.findall("jump " + ConnectName + " # handle [0-9]+",output)
    print(f"{matches}")
    if (len(matches) > 0):
        handle_num = re.sub("jump " + ConnectName + " # handle ","", matches[0])
        strdelete=f"delete rule ip filter TILEDVIZ handle {handle_num}"
        print(strdelete)
        nft.cmd(strdelete)
    else:
        print(f"connection {ConnectName} not detected!")
            
    strdestroy=f"destroy chain ip filter {ConnectName}"
    print(strdestroy)
    nft.cmd(strdestroy)
            
