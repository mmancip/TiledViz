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
        'Compare two nodes.json databases for TiledViz.\n'+
        'example : \n'+\
        './compare_json.py -n "AstroIAlastFiles.json" "AstroIA_mean_newtags.json"')
    #parser.add_argument('-c', '--oldcasefile', default=oldcasefile,
    #                    help='Old case_config_machine path (default: ANATOMIST Mandelbrot).')
    parser.add_argument('-n', '--file-names', nargs=2, required=True)
    parser.add_argument('-o', '--out', action='store_true')
    args = parser.parse_args(argv[1:])
    return args

if __name__ == '__main__':
    args = parse_args(sys.argv)

    with open(args.file_names[0],'r') as fnode1:
        nodes1=json.load(fnode1)
    with open(args.file_names[1],'r') as fnode2:
        nodes2=json.load(fnode2)

    nodes1_s=sorted(nodes1["nodes"], key=lambda x: x['name'])
    ind_nodes1_s=sorted(range(len(nodes1["nodes"])), key=lambda k: nodes1["nodes"][k]['name'])
    nodes2_s=sorted(nodes2["nodes"], key=lambda x: x['name'])
    ind_nodes2_s=sorted(range(len(nodes2["nodes"])), key=lambda k: nodes2["nodes"][k]['name'])
    print("len nodes1,nodes2 : %d,%d " % (len(nodes1_s),len(nodes2_s)))
    if (args.out):
        file1o=os.path.join(os.path.dirname(args.file_names[0]),"sorted_"+os.path.basename(args.file_names[0]))
        file2o=os.path.join(os.path.dirname(args.file_names[1]),"sorted_"+os.path.basename(args.file_names[1]))
        print(file1o,"\n",file2o)
        o_nodes1={"nodes":nodes1_s,"order":ind_nodes1_s}
        with open(file1o,'w+') as fnode1:
            json.dump(o_nodes1,fnode1)
        o_nodes2={"nodes":nodes2_s,"order":ind_nodes2_s}
        with open(file2o,'w+') as fnode2:
            json.dump(o_nodes2,fnode2)
    nbsame=0
    difftile=[]
    i1=0
    i2=0
    #import ipdb; ipdb.set_trace()
    while i1 < len(nodes1_s):
        tile1=nodes1_s[i1]
        # title1=tile1['title']
        # url1=tile1['url']
        # if ("comment" in tile1):
        #     comment1=tile1['comment']
        # else:
        #     comment1=""
        tags1=tile1['tags']
        name1=tile1['name']
        # db1=tile1['dbid']
        #pass=1
        while i2 < len(nodes2_s):
            tile2=nodes2_s[i2]
            # print(tile1==tile2)
            tile1_keys = set(tile1.keys())
            tile2_keys = set(tile2.keys())
            shared_keys = tile1_keys.intersection(tile2_keys)
            shared_keys.remove("IdLocation")
            # added = tile1_keys - tile2_keys
            # removed = tile2_keys - tile1_keys
            modified = {o : (tile1[o], tile2[o]) for o in shared_keys if str(tile1[o]) != str(tile2[o])}
            same = set(o for o in shared_keys if str(tile1[o]) == str(tile2[o]))
            allsame=len(modified)==0
            if (allsame):
                nbsame=nbsame+1
                i2=i2+1
                break
            # title2=tile2['title']
            # url2=tile2['url']
            # if ("comment" in tile2):
            #     comment2=tile2['comment']
            # else:
            #     comment2=""
            tags2=tile2['tags']
            name2=tile2['name']
            # db2=tile2['dbid']
            if( name1 == name2 ):
                if ("tags" in modified):
                    modified["tags"] = (list(set(tags1) - set(tags2)),list(set(tags2) - set(tags1)))
                t1=ind_nodes1_s[i1]; t2=ind_nodes2_s[i2]
                difftile.append({"t1":t1, "t2":t2, "i1":i1, "i2":i2, **modified})
                i2=i2+1
                break
            i2=i2+1
        #import pdb; pdb.set_trace()
        i1=i1+1

    print("Nb same %d" % (nbsame)) 
    print("All diff : %d " % (len(difftile)))
    [ print(difft,"\n") for difft in difftile ]
    # print(i1,' ',i2,"\n", \
    #       ' ',title1," ",title2, "\n", \
    #       ' ',url1,"\n ",url2, '\n',\
    #       ' ',comment1,'\n ',comment2, '\n', \
    #       ' ',tags1,'\n ',tags2, '\n',\
    #       ' ',name1,' ',name2, '\n',\
    #       db1,' ',db2)
            
