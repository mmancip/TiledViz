#!/bin/env python3

import sys,os
import argparse
import re
import json
import datetime
import traceback

errors=sys.stderr
def parse_args(argv):
    parser = argparse.ArgumentParser(
        'Sorte with key name a nodes.json databases for TiledViz.\n'+
        'This example will give a "./sorted_AstroIAlastFiles.json" file : \n'+\
        './sort_json.py -n "./AstroIAlastFiles.json""')
    parser.add_argument('-n', '--file-name', nargs=1, required=True)
    args = parser.parse_args(argv[1:])
    return args

if __name__ == '__main__':
    args = parse_args(sys.argv)

    with open(args.file_name[0],'r') as fnode1:
        nodes1=json.load(fnode1)

    nodes1_s=sorted(nodes1["nodes"], key=lambda x: x['name'])
    ind_nodes1_s=sorted(range(len(nodes1["nodes"])), key=lambda k: nodes1["nodes"][k]['name'])
    print("len nodes1 : %d " % (len(nodes1_s)))

    file1o=os.path.join(os.path.dirname(args.file_name[0]),"sorted_"+os.path.basename(args.file_name[0]))
    print(file1o)
    o_nodes1={"nodes":nodes1_s,"order":ind_nodes1_s}
    with open(file1o,'w+') as fnode1:
        json.dump(o_nodes1,fnode1)
            
