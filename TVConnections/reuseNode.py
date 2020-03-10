#!/bin/env python
import json,re
import sys,argparse

#[prompt]$ python3 -m json.tool $path/nodes_new.json
#Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)
#=>
#[prompt]$ LANG=C LC_ALL=C sed -e 's/\r$// ; 1 s/^\xef\xbb\xbf//' 

def parse_args(argv):
    parser = argparse.ArgumentParser(
        'reuseNode is a python script that will use '+
        'a nodes_new.json created by launch_dockers script and '+
        'a nodes_saved.json saved by TiledViz web interface '+
        'to put passwords from the first one into the saved json and create an output json.')
    parser.add_argument('-s','--oldsaved', default='./nodes_saved.json',
                        help='nodes_old.json file saved (default: ./nodes_saved.json)')
    parser.add_argument('-n','--newpass', default='./nodes_new.json',
                        help='nodes_new.json whith new passwords (default: ./nodes_new.json)')
    parser.add_argument('-o','--out', default='./nodes_out.json',
                        help='output nodes_out.json whith saved sorting and new passwords (default: ./nodes_out.json)')

    args = parser.parse_args(argv[1:])
    return args

if __name__ == '__main__':
    args = parse_args(sys.argv)
    try:
        new_node_file=open(args.newpass,'r')
    except:
        print("error opening new nodes file.")
        sys.exit(1)
    try:
        saved_file=open(args.oldsaved,'r')
    except:
        print("error opening saved nodes file.")
        sys.exit(1)
    json_saved_node=json.load(saved_file)
    json_new_node=json.load(new_node_file)

    p=re.compile(r'.*port=([0-9]*)&encrypt=0&password=([^&]*).*')
    #p.sub(r'\1',json_saved_node["nodes"][0]["url"])
    #p.sub(r'\2',json_saved_node["nodes"][0]["url"])
    
    for tile in json_saved_node["nodes"]:
        for oldt in json_new_node["nodes"]:
            if ( tile["title"] == oldt["title"] ):
                tile["url"]=tile["url"].replace(r''+p.sub(r'\2',tile["url"]),p.sub(r'\2',oldt["url"]))
                break
 
    node_new_file=open(args.out,'w')
    json.dump(json_saved_node,node_new_file)
    node_new_file.close()

