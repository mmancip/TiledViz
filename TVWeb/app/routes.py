# -*- coding: utf-8 -*-

# routes are defined here, then imported in __init__.py

from flask import render_template, flash, Markup, redirect, session, request, jsonify, make_response, url_for, Response
import sqlalchemy
from sqlalchemy.orm.session import make_transient
from sqlalchemy.orm.attributes import flag_modified
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import requests

from app import app, socketio, db

from app.forms import RegisterForm, BuildLoginForm, BuildNewProjectForm, BuildAllProjectSessionForm, BuildOldProjectForm, BuildNewSessionForm, BuildTilesSetForm, BuildEditsessionform, BuildOldTileSetForm, BuildConfigSessionForm, BuildConnectionsForm, BuildRetreiveSessionForm


import app.models as models # DB management
import json, os, pprint
# import gzip,base64
import socket

import logging
import code

from flask_socketio import emit, join_room, rooms

#import werkzeug.exceptions
from werkzeug.utils import secure_filename

import sys,re,traceback
import datetime,time
import random

import tempfile, filecmp
import tarfile

sys.path.append(os.path.abspath('../TVDatabase'))
from TVDb import tvdb
tvdb.session=db.session

timeAlive=5

# Logging
logFormatter = logging.Formatter("%(asctime)s - %(threadName)s - %(levelname)s: %(message)s ")
outHandler = logging.StreamHandler(sys.stdout)
outHandler.setLevel(logging.WARNING)
# outHandler.setLevel(logging.DEBUG)
outHandler.setFormatter(logFormatter)

def myflush():
    outHandler.flush()
    sys.stdout.flush()

# Shared variables for threads in server
clients = [] # Array to store clients
room_dict = {} # Dict to store rooms (and sub-arrays for clients in each room)
cookie_persistence = False # Opt-in (TODO: better in config?)
config = {}

tiles_data={}
tiles_data["nodes"]=[]

jsontransfert={}

# Global functions : creation and copy DB elements

# Test login user :
def get_user_id(fun,username):
    try:
        user=db.session.query(models.User.id).filter_by(name=session["username"]).one()
    except:
        flash(fun+" requested : User must login !")
        return redirect(url_for("login"))
    return user[0]

# copy users in Session
def copy_users_session(newsession,oldusers):
    if ( len(oldusers) > 0 ):
        # register only known oldusers
        for newuser in oldusers:
            thisuserq=db.session.query(models.User).filter_by(name=newuser.data)
            if db.session.query(thisuserq.exists()).scalar():
                user=thisuserq.one()
                # don't register a user two times
                if (user not in newsession.users):
                    newsession.users.append(user)
                    db.session.commit()

# Define new session
def create_newsession(sessionname, description, projectid, oldusers):
    creation_date=datetime.datetime.now()
    newsession = models.Session(name=str(sessionname),
                                description=str(description),
                                id_projects=projectid,
                                creation_date=creation_date)

    exist=db.session.query(models.Session.id).filter_by(name=sessionname).scalar() is not None

    if (not exist):
        lastsession=db.session.query(models.Session.id).order_by(models.Session.id.desc()).first()
        if ( lastsession ):
            newsession.id=lastsession.id+1
        else:
            newsession.id=1
        db.session.commit()
        copy_users_session(newsession,oldusers)
        db.session.commit()
    else:
        newsession=db.session.query(models.Session).filter_by(name=sessionname).one()
        
    session["sessionname"]=str(sessionname)
            
    return newsession,exist
    
# Define new TileSet
def create_newtileset(tilesetname, thesession, type_of_tiles, datapath, creation_date):
    newtileset = models.TileSet(name=tilesetname,
                                type_of_tiles = type_of_tiles,
                                Dataset_path = datapath,
                                creation_date=creation_date)
    
    exist=db.session.query(models.TileSet.id).filter_by(name=tilesetname).scalar() is not None

    if (not exist):
        # Last TileSet id +1
        lasttileset=db.session.query(models.TileSet.id).order_by(models.TileSet.id.desc()).first()
        if ( lasttileset ):
            newtileset.id=lasttileset.id+1
        else:
            newtileset.id=1
        db.session.commit()
        thesession.tile_sets.append(newtileset)
        db.session.commit()
    else:
        newtileset=db.session.query(models.TileSet).filter_by(name=tilesetname).one()
    return newtileset,exist

# Convert Tile fron json file structure to database object
def convertTile(Mynode,tilesetname,connectionbool,urlbool,datapath):
    url=Mynode["url"]

    ConnectionPort=0
    if (urlbool and len(datapath) > 0):
        # Detect if path is already in tiles source url
        searchPath=re.search(r''+datapath,url)
        # if no add Dataset_path in url
        if (not searchPath):
            url=datapath+Mynode["url"]
    elif (connectionbool):
        searchPort=re.search(r'port=\d+',url)
        if (searchPort):
            ConnectionPort=int(searchPort.group().replace('port=',''))
    try:
        title=Mynode["title"]
    except :
        title=Mynode["name"]
    try:
        name=Mynode["name"]
    except:
        name=Mynode["title"]

    comment=""
    try:
        comment=Mynode["comment"]
    except:
        pass
    
    tags=[]
    try:
        searchtsn=re.search(r''+tilesetname,str(Mynode["tags"]))
        if (not searchtsn):
            if (type(Mynode["tags"]) == 'str'):
                tags=[tilesetname,Mynode["tags"]]
            else:
                tags=[tilesetname]+Mynode["tags"]
        else :
            tags=Mynode["tags"]
    except:
        #traceback.print_exc(file=sys.stderr)
        tags=[tilesetname]
        pass

    variable=""
    try:
        variable=Mynode["variable"]
    except:
        pass
    
    pos_px_x=-1
    pos_px_y=-1
    try:
        pos_px_x=Mynode["pos_px_x"]
        pos_px_y=Mynode["pos_px_y"]
    except:
        pass

    IdLocation=-1
    try:
        IdLocation=Mynode["IdLocation"]
    except:
        pass
    
    return title,name,comment,tags,variable,pos_px_x,pos_px_y,IdLocation,url,ConnectionPort

# Copy a connection when copy a TileSet
# => copy connection + config files +     vnctransfert=json.loads(session["connection"+str(idconnection)]) + session["connection"+str(idconnection)]
# TODO message to connection user owner grid : "Are you OK to copy your connection for tileset.name ?"
def copy_connection(oldtileset,newtileset,newsessionname):
    oldconnection=oldtileset.connection        
    user_id=get_user_id("copy_connection",session["username"])

    message = '{"oldtilesetid":'+str(newtileset.id)+',"oldsessionname":"'+session["sessionname"]+'"}'

    #TODO : session from/to right user for connection
    if (oldconnection.id == None ):
        return
    else:
        idconnection=oldconnection.id
    if ( not "connection"+str(idconnection) in session):
        flash("You don't have connection information in your personal cookie for this connection.")
        logging.error("You (user "+str(user_id)+") don't have connection information in your personal cookie for this connection : "+str(idconnection))
        return

    #TODO : vncpassword from/to right user for connection
    if  (user_id != oldconnection.id_users) :
        flash("You can not access to this connection. You are not its owner.")
        owner=db.session.query(models.User).filter_by(id=oldconnection.id_users).name
        you=db.session.query(models.User).filter_by(id=user_id).name
        logging.error("You (user "+you+") can not access to this connection owned by user "+owner)
        return redirect(url_for(".edittileset",message=message))

    creation_date=datetime.datetime.now()
    newconnection = models.Connection(host_address=oldconnection.host_address,
                                      auth_type=oldconnection.auth_type,
                                      container=oldconnection.container,
                                      scheduler=oldconnection.scheduler,
                                      scheduler_file=oldconnection.scheduler_file,
                                      id_users=user_id,
                                      creation_date= creation_date)
    
    lastconnection=db.session.query(models.Connection.id).order_by(models.Connection.id.desc()).first()
    if ( lastconnection ):
        newconnection.id=lastconnection.id+1
    else:
        newconnection.id=1
    db.session.add(newconnection)
    db.session.commit()

    user_path=os.path.join("/TiledViz/TVFiles",str(user_id))
    olddir=os.path.join(user_path,str(idconnection))
    newdir=os.path.join(user_path,str(newconnection.id))
    os.system("mkdir "+newdir)
    
    config_files={}
    for key in oldconnection.config_files:
        filetmp=oldconnection.config_files[key]
        newtmp=filetmp.replace(olddir,newdir)
        os.system("cp "+filetmp+" "+newtmp)
        config_files[key]=newtmp

    newconnection.config_files=config_files
    flag_modified(newconnection,"config_files")
    newconnection.scheduler_file=oldconnection.scheduler_file
    newtileset.id_connections=newconnection.id
    db.session.commit()
    
    vnctransfert=json.loads(session["connection"+str(idconnection)])
    vncpassword=vnctransfert["vncpassword"]
    session["connection"+str(newconnection.id)]=' {"callfunction":"edittileset",'+'"args":{"oldsessionname":"'+newsessionname+'","oldtilesetid":"'+str(newtileset.id)+'"}, "vncpassword":"'+vncpassword+'"}'

    return

# Copy a mirror connection and tileset files
def copy_tileset_connection(tileset,tileset1,sessionname ):
    oldconnection=tileset.connection
    if (oldconnection):
        copy_connection(tileset,tileset1,sessionname)
    user_id=get_user_id("copy_tileset_connection",session["username"])
    user_path=os.path.join("/TiledViz/TVFiles",str(user_id))
    olddir=os.path.join(user_path,str(tileset.id_connections))
    newdir=os.path.join(user_path,str(tileset1.id_connections))

    config_files={}
    for key in tileset.config_files:
        filetmp=tileset.config_files[key]
        newtmp=filetmp.replace(olddir,newdir)
        os.system("cp "+filetmp+" "+newtmp)
        config_files[key]=newtmp

    tileset1.config_files=config_files
    tileset1.launch_file=tileset.launch_file


# Function to launch connection page
def launch_connection(theTS, theConnect, myhost_address, myauth_type, mycontainer, myscheduler):
    try:
        logging.warning("editconnection: "
                        +str(session["username"])+" ; "
                        +str(myhost_address)+" ; "
                        +str(myauth_type)+" ; "
                        +str(mycontainer)+" ; "
                        +str(myscheduler)+" ; "
                        +str(theTS.id)+" ; "
                        +str(theConnect.id))
        myflush()

        #  Wait NbTimeAlive for TVSecure to get VNC view to give connection again.
        NbTimeAlive = 20
        passpath="/home/connect"+str(theConnect.id)+"/vncpassword"
        logging.warning("Go to vnc with path "+passpath)
        
        count=0
        while(True):
            if (count > NbTimeAlive):
                strerror="Connection has never been reach. Go back to TileSet."
                logging.error(strerror)
                flash(strerror)
                message = '{"oldtilesetid": "'+str(theTS.id)+'"}'
                logging.warning(strerror+" message "+message)
                return redirect(url_for(".edittileset",message=message))
            count=count+1
            logging.debug("count = "+str(count))
            # GET VNC password in 
            # security problem here if server is attacked ?
            time.sleep(timeAlive)
            #os.system("ls -la "+passpath)
            if (os.path.isfile(passpath)):
                with open(passpath,'r') as f:
                    vncpassword=re.sub(r'\n',r'',f.read())
                f.close()
                logging.warning("and password : "+vncpassword)
            else:
                logging.error("File not found in connection container "+passpath)
                vncpassword=""
            
            message = '{"oldtilesetid":'+str(theTS.id)+',"connectionid":'+str(theConnect.id)+',"sessionname":"'+session["sessionname"]+'"}'
            session["connection"+str(theConnect.id)]=' {"callfunction":"edittileset",'+'"args":{"oldsessionname":"'+str(session["sessionname"])+'","oldtilesetid":"'+str(theTS.id)+'"}, "vncpassword":"'+vncpassword+'"}'

            logging.warning("editconnection in session : "+str(session["connection"+str(theConnect.id)])+" message :"+str(message))
            #TODO logging.debug
            myflush()
            return message
    except Exception:
        traceback.print_exc(file=sys.stderr)


# Define new session
def save_session(oldsessionname, newsuffix, newdescription, alltiles):
    creation_date=datetime.datetime.now()
    oldsession=db.session.query(models.Session).filter_by(name=oldsessionname).one()
    projectid=oldsession.id_projects
    # TODO : max length of Session.name (=80) ?
    # mais parent with date may be too long
    #=> notion of heritage for session and tilsets in DB    
    newsessionname=session["sessionname"]+'_'+newsuffix
    newsession = models.Session(name=newsessionname,
                                description=newdescription,
                                id_projects=projectid,
                                creation_date=creation_date)
    lastsession=db.session.query(models.Session.id).order_by(models.Session.id.desc()).first()
    if ( lastsession ):
        newsession.id=lastsession.id+1
    else:
        newsession.id=1
    db.session.commit()

    oldusers=oldsession.users
    for user in oldusers:
        newsession.users.append(user)
        db.session.commit()

    newsession.config = oldsession.config
    flag_modified(newsession,"config")
    db.session.commit()

    logging.warning("All tilesets :"+str([ ts.name for ts in oldsession.tile_sets]))

    alltilesjson = alltiles["nodes"]
    for tileset in oldsession.tile_sets:
        # copy tilesets
        tilesetname=tileset.name
        logging.debug("copy tileset from :"+tileset.name)

        urlbool=False
        connectionbool=False        
        if (tileset.type_of_tiles == "URL"):
            urlbool=True
        elif(tileset.type_of_tiles == "CONNECTION"):
            # Creation of the tiles and launch connection to remote machine.
            connectionbool=True
            
        datapath=tileset.Dataset_path
        tileset1,exist=create_newtileset(tilesetname+'_'+newsuffix, newsession,
                                   tileset.type_of_tiles, datapath, creation_date)

        if (connectionbool):
            # Copy a mirror connection
            logging.error("copy config data :"+tileset.launch_file+"  "+str(tileset.config_files))

            copy_tileset_connection(tileset,tileset1,newsession.name)
            if (tileset1.connection):
                logging.error("copy id connection :  "+str(tileset1.id_connections))

            logging.error("copy config data 1 :"+tileset1.launch_file+"  "+str(tileset1.config_files))
            
            
        if (not exist):
            try:
                db.session.add(tileset1)
                db.session.commit()
            except Exception:
                traceback.print_exc(file=sys.stderr)
        logging.warning("add tileset1 :"+tileset1.name)
        
        for tile in tileset.tiles:
            try :
                i=next(i for i, item in enumerate(alltilesjson) if (item["title"] == tile.title))
            except StopIteration:
                i=-1
            logging.debug("new tile :"+tile.title+" i "+str(i))
            if (i > -1):
                Mynode=alltilesjson[i]
                #print("Mynode :",str(Mynode)," type ",str(type(Mynode))," type tags ",str(type(Mynode["tags"])))
                title,name,comment,tags,variable,pos_px_x,pos_px_y,IdLocation,url,ConnectionPort = \
                    convertTile(Mynode,tilesetname,connectionbool,urlbool,datapath)
                tile.tags=tags
                tile.source= {"name" : name,
                              "connection" : ConnectionPort,
                              "url" : url,
                              "variable": variable}
                flag_modified(tile,"source")
                tile.pos_px_x= pos_px_x
                tile.pos_px_y= pos_px_y
                tile.IdLocation=IdLocation
                tileset1.tiles.append(tile)
                db.session.commit()
            else:
                pass # do nothing if tile is not found in oldtileset ?

    newsession.config = oldsession.config
    db.session.commit()
    return newsession
    
def remove_this_connection(oldtileset,idconnection,user_id):
    oldconnection=oldtileset.connection
    oldtilesetid=oldtileset.id
    logging.warning("Remove connection of tileset %d" % (oldtilesetid))

    if (oldconnection.id != idconnection):
        logging.error("id %d to be removed is not this tileset %d id %d." % (idconnection, oldtilesetid, oldconnection.id))
        return
    # Build connection path
    user_path=os.path.join("/TiledViz/TVFiles",str(user_id))
    connectionpath=os.path.join(user_path,str(idconnection))

    for (dirpath, dirname, filelist) in os.walk(connectionpath):
        for filename in filelist:
            strrm="rm -f "+os.path.join(dirpath,filename)
            os.system(strrm)
            logging.warning("Remove file for tileset "+oldtileset.name+" : "+os.path.join(dirpath,filename))
        os.rmdir(dirpath)
        logging.warning("Remove dir for tileset "+oldtileset.name+" : "+dirpath)
    
    oldtileset.id_connections=None
    #oldtileset.type_of_tiles == None
    oldtileset.config_files=""
    flag_modified(oldtileset,"config_files")
    oldconnection.config_files=""
    flag_modified(oldconnection,"config_files")
    logging.warning("removeconnection: "
                    +str(session["username"])+" ; "
                    +str(oldtilesetid)+" ; "
                    +str(idconnection))
    db.session.commit()
    myflush()

    session["connection"+str(idconnection)]=""
    del(session["connection"+str(idconnection)])

# @app.route('/upload', methods=['GET', 'POST'])
# async def upload(request):
#     form = TestForm(request)
#     if form.validate_on_submit():
#         return response.text(form.upload.data.name)
#     content = render_form(form)
#     return response.html(content)


# ====================================================================
# Index/home page
@app.route('/', methods=['GET', 'POST']) # decorators for routes ; all these ones will lead to index
@app.route('/index', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def index():
    try: 
        #logging.warning(str(session))
        try:
            user = {"username" : session["username"] } # Test for cookie?
        except:
            user = {"username" : "Anonymous"}
            session["username"]="Anonymous"
        if (session["username"] != "Anonymous"):
            session["is_client_active"]=True
        if ( "projectname" in session ):
            project = session["projectname"]
        else:
            project = ""
        if ("sessionname" in session ):
            psession = session["sessionname"]
        else:
            psession=""
    except KeyError as e: # If session["username"] does not exist (no cookie yet)
        logging.error("Home error : "+e)
        # If the cookie is not present
        project = "test"
        psession = "testsession"
        session["username"]="Anonymous"
        user = {"username" : session["username"] }
        session["projectname"]=project
        session["sessionname"]=psession
        session["is_client_active"]=False

    return render_template("main_template.html", title="TiledViz home", user=user, project=project, session=psession)

# ====================================================================
# Register
@app.route('/register', methods=["GET", "POST"])
def register():
    showlogin=False
    showexist=False
    showknown=False
    myform = RegisterForm()
    if myform.validate_on_submit():
        logging.info("Register new user.")
        session["username"] = myform.username.data
        # if (showlogin):
        #     flash("Login requested for user {} in project {}, remember_me={}".format(myform.username.data, myform.projectname.data, myform.remember_me.data))
        #     showlogin=False
        #     return render_template("main_login.html", title="TiledViz register", form=myform)
        try:
            exists = db.session.query(models.User.id).filter_by(name=session["username"]).scalar() is not None
        except Exception:
            exists=False
        if exists:
            if (showexist):
                flash("Known user {}, remember_me={}".format(myform.username.data, myform.remember_me.data))
                showexist=False
                return render_template("main_login.html", title="TiledViz register", form=myform)
            logging.warning("username already exists.")
            hashPassword,hashSalt=db.session.query(models.User.password,models.User.salt).filter_by(name=session["username"]).scalar()
            testP=tvdb.testpassprotected(models.User,session["username"],myform.password.data,hashPassword,hashSalt)
            if (testP):
                logging.info("Correct password !")
                if (showknown):
                    flash(Markup("Correct Login for user {} remember_me={}".format(myform.username.data, myform.remember_me.data)))
                    showknown=False
                    return render_template("main_login.html", title="TiledViz register", form=myform)
                user = {"username" : session["username"] }
                session["is_client_active"]=True
            else:
                if (showknown):
                    flash("You have entered an already existing username, but wrong password for user {}".format(myform.username.data))
                    showknown=False
                    return render_template("main_login.html", title="TiledViz register", form=myform)
                # TODO :
                # We have entered an already existing username, but wrong password
                # 1. we try again with password (and all the form ?)
                # -> 2. we are redirected to login only ?
                flash("This username {} already exists and passwd is incorrect : ".format(session["username"]))
                return render_template("main_login.html", 
                    title="TiledViz register", 
                    form=myform)
        else:
            hashpass, salt=tvdb.passprotected(myform.password.data)
            
            creation_date=datetime.datetime.now()
            user = models.User(name=str(session["username"]),
                               creation_date=str(creation_date),
                               mail=str(myform.email.data),
                               compagny=str(myform.compagny.data),
                               manager=str(myform.manager.data),
                               salt=salt,
                               password=hashpass,
                               dateverified=str(creation_date)) # DANGEROUS: TODO: clean string
            db.session.add(user)
            db.session.commit()
            logging.info("Commit new user.")
            session["is_client_active"]=True

        cookie_persistence = myform.remember_me.data
        logging.warning("[!] Cookie persistence set to %s"+str(cookie_persistence))

        logging.debug("Project Choice :"+myform.choice_project.data)
        if(myform.choice_project.data == "create"):
            logging.info("Go to create new project for user "+session["username"]+".")
            return redirect("/project")
        else:
            # use an old project
            if exists:
                #User already exists => go to session
                # user=db.session.query(models.User.id).filter_by(name=session["username"]).one()

                # if (len(projects) == 1):
                #     logging.info("New user "+session["username"]+" : has been already invited in session .")
                return redirect("/allsessions")
            else:
                # or Request an invite link from another connected user and use it !
                logging.info("New user "+session["username"]+" : create a new project or ask for invite_link.")
                flash("New user {} registred : please create a new project or ask another user for an invite_link.".format(session["username"]))
                return render_template("main_login.html", 
                    title="TiledViz register", 
                    form=myform)
    return render_template("main_login.html", title="TiledViz register", form=myform)

# OR Login
@app.route('/login', methods=["GET", "POST"])
def login():
    try:
        myform = BuildLoginForm(session)()
    except:
        session["username"]="Anonymous"
        myform = BuildLoginForm(session)()
        
    if myform.validate_on_submit():
        logging.debug("Login : session = "+str(session))
        # flash(Markup("Login requested for user {} remember_me={}".
        #              format(myform.username.data, myform.remember_me.data)))
        if ( myform.newuser.data ):
            # Ask for new user finally
            return redirect("/register")
        try:
            User=db.session.query(models.User).filter_by(name=myform.username.data).one()
            session["username"] = myform.username.data
        except:
            flash("Login rejected : '{}' for username does not exist.".format(session["username"]))
            return redirect("/login")
        exists = User.id is not None
        
        if exists:
            hashPassword=User.password
            hashSalt=User.salt
            testP=tvdb.testpassprotected(models.User,session["username"],myform.password.data,hashPassword,hashSalt)
            if (testP):
                logging.warning('Correct password.')
                session["is_client_active"]=True
                if(myform.choice_project.data == "create"):
                    # Go to project page now
                    return redirect("/project")
                elif (myform.choice_project.data == "modify"):
                    return redirect("/oldsessions")
                else:
                    logging.error("Before leave login page choice_project : " + myform.choice_project.data)
                    # Want to use a project now :
                    # 1. list (user/ ?) (own ?) projects/session for user
                    # 2. ask a invite links from another user ?

                    # ==> list users'project and all (active ?) session with user connected
                    return redirect("/allsessions")
            else:
                flash("Invalid Password user {}".format(myform.username.data))
                return render_template("main_login.html", title="Invalid Password : Login TiledViz", form=myform)
        else:
            flash("Unknown user {}".format(myform.username.data))
            return render_template("main_login.html", title="Unknown user : Login TiledViz", form=myform)
    return render_template("main_login.html", title="Login TiledViz", form=myform)        

@app.route('/logout')
def logout():
    # remove the username from the session if it is there
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/savesession', methods=['GET', 'POST'])
def savesession():

    if ("username" in session):
        user_id=get_user_id("Savession",session["username"])
    else:
        flash("You are not connected. You must login before saving a session.")
        return redirect("/login")

    all_session={"username":session['username'],"is_client_active":session["is_client_active"],
                 "projectname":session["projectname"],"sessionname":session["sessionname"]}
    # logging.error("basic all_session : "+str(all_session))
    for item in session:
        logging.info("item all_session : "+str(item))
        if item in all_session:
            pass
        elif (item == 'csrf_token'):
            pass
        else:
            all_session[item]=session[item]
            
    logging.info("complete all_session : "+str(all_session))
    
    #all_connections=
    # session["connection"+str(idconnection)])
    # session["connection"+str(newconnection.id)]
    json_all_session=json.JSONEncoder().encode(all_session)

    if ( request.method == 'POST'):
        flash("Session cookie saved.")
        return redirect("/index")
        #return redirect(url_for('index'))
    
    return render_template("savesession.html",
                           all_session=json_all_session)

@app.route('/retreivesession', methods=["GET", "POST"])
def retreivesession():

    if ("username" in session):
        user_id=get_user_id("retreivesession",session["username"])
    else:
        flash("You are not connected. You must login before retreive a session.")
        return redirect("/login")

    # if ( session["sessionname"] in  jsontransfert):
    #     if ( "TheJson" in  jsontransfert[session["sessionname"]]):

    myform = BuildRetreiveSessionForm()()

    if myform.validate_on_submit():
        logging.info("in tileset editor")

        if(myform.goback.data):
            logging.warning("go back to home without session.")
            return redirect(url_for(".index"))
        
        if (myform.session_file.data) :
            session_file = myform.session_file.data
            logging.warning("Read session_file :"+myform.session_file.data.filename)
            session_data = json.loads(json.loads(session_file.read().decode('utf-8')))
            logging.warning("Session_data :"+str(session_data))
            logging.warning("Session_data type :"+str(type(session_data)))
            logging.warning("Session_data user :"+str(session_data['username']))
            
            session["username"]=session_data['username']
            session["is_client_active"]=session_data["is_client_active"]
            session["projectname"]=session_data["projectname"]
            session["sessionname"]=session_data["sessionname"]
            all_session={"username":session['username'],"is_client_active":session["is_client_active"],
                 "projectname":session["projectname"],"sessionname":session["sessionname"]}
            
            logging.info("basic all_session : "+str(all_session))
            for item in session_data:
                if item in all_session:
                    pass
                else:
                    session[item]=session_data[item]

            flash("Session cookie restored.")
            return redirect("/index")

        # if myform.editjson.data:
        #     # jsontransfert[session["sessionname"]]={"callfunction": '{"function":"edittileset",'+'"args":{"oldtilesetid":"'+str(oldtilesetid)+'"}}',
        #     #                                        "TheJson":json_tiles}
        #     pass
        
    #    return render_template("retreivesession.html")
    return render_template("main_login.html", title="Retreive saved session for TiledViz", form=myform)


# For display in form list, specify length of elements
sessionl=str(80)
tilesetl=str(80)
projectl=str(15)
datel=str(19)
descrl=str(62)    

# Create new project
@app.route('/project', methods=["GET", "POST"])
def project():
    flash("Create new or use an old project for user {}".format(session["username"]))
    user_id=get_user_id("Project",session["username"])

    # All projects own by user
    printstr="{0:\xa0<"+projectl+"."+projectl+"}|\xa0{2:\xa0<"+datel+"."+datel+"}\xa0|\xa0{1:\xa0<"+descrl+"."+descrl+"}|\xa0{3:\xa0<"+descrl+"}"
    
    projects = db.session.query(models.Project).filter_by(id_users=user_id)
    myprojects=[]
    myprojects.append(('NoChoice',printstr.format("Project name","Description","Date and Time","All sessions")))

    try:
        for theproject in projects:
            ListsessionsTheproject=db.session.query(models.Session.name).filter_by(id_projects=theproject.id)
            allsessionsname=[ asessionTheproject.name for asessionTheproject in ListsessionsTheproject ]
            thedate=theproject.creation_date.isoformat().replace("T"," ")
            
            myprojects.append((str(theproject.id),
                               printstr.format(
                                     theproject.name,
                                     theproject.description,
                                     thedate,
                                     str(allsessionsname))
                               ))
    except:
        pass
    
    myform = BuildNewProjectForm(myprojects)()
    if myform.validate_on_submit():
        logging.info("in project")
        
        # TODO : Add test if the user is authorized to use this project ? ==> NO only own project
        if (myform.chosen_project.data=="NoChoice"):
            if (myform.projectname.data != ""):
                project_id = db.session.query(models.Project.id).filter_by(name=myform.projectname.data).scalar()
            else:
                # Impossible to be here ?
                logging.warning("You must create a new project or choose an old one.")
                flash("You must create a new project or choose an old one.")
                return redirect("/project")
            
        else:
            project_id = int(myform.chosen_project.data)
        exists = project_id is not None
        logging.debug("Project exists "+str(exists)+" id : "+str(project_id))
        if exists:
            if (myform.chosen_project.data == "NoChoice"):
                session["projectname"]=myform.projectname.data
            else:
                session["projectname"]=db.session.query(models.Project.name).filter_by(id=project_id).scalar()
            # test if the user is authorized to use this project ? ==> NO only own project ! or session with the user already invited
            logging.debug("Chosen project : "+str(session["projectname"]))
            if(myform.action_sessions.data == "create"):
                logging.debug("Create new session ")
                return redirect("/newsession")
            else:
                logging.debug("Use old sessions ")
                return redirect("/oldsessions")
        elif (myform.chosen_project.data=="NoChoice"):
            creation_date=datetime.datetime.now()
            screation_date=str(creation_date)
            logging.error("create project date "+screation_date)
            project = models.Project(name=str(myform.projectname.data),
                                     creation_date=screation_date,
                                     id_users=user_id,
                                     description=myform.description.data) # DANGEROUS: TODO: clean string
            db.session.add(project)
            db.session.commit()
            session["projectname"]=myform.projectname.data
            logging.debug("Project created : create new session ")
            return redirect("/newsession")
        else:
            logging.error("Error for chosen project.")
            return redirect("/project")            
        
    return render_template("main_login.html", title="New project TiledViz", form=myform)

# List all my old projects and after all sessions I am in
@app.route('/allsessions', methods=["GET", "POST"])
def allmysessions():
    if ("username" in session):
        if (session["username"] == "Anonymous"):
            return redirect("/login")

        flash("All projects and sessions for user {}".format(session["username"]))
        logging.warning("All projects and sessions for user {}".format(session["username"]))
        user_id=get_user_id("allsavessions",session["username"])
        logging.warning("User id {}".format(user_id))
    elif (not 'is_client_active' in session):
        flash("You are not connected. You must login before using a grid.")
        return redirect("/login")
    else:
        flash("All projects and sessions : User must login !")
        return redirect("/login")


    message='{"username": '+session["username"]+'}'
    logging.info("in allsessions")

    # All projects own by user
    projects = db.session.query(models.Project).filter_by(id_users=user_id)
    logging.debug("My projects :"+str([ theproject.name for theproject in projects]))
    
    # All sessions own of those projects
    mysessions=[]
    try:
        for theproject in projects:
            ListsessionsTheproject=db.session.query(models.Session.name).filter_by(id_projects=theproject.id)
            [ mysessions.append((theproject.name,ListsessionTheproject)) for ListsessionTheproject in ListsessionsTheproject ]
    except:
        pass
    logging.debug("My sessions :"+str(mysessions))
    
    printstr="{1:\xa0<"+sessionl+"."+sessionl+"}|{0:\xa0<"+projectl+"."+projectl+"}|\xa0{2:\xa0<"+datel+"."+datel+"}\xa0|\xa0{3:\xa0<"+descrl+"."+descrl+"}"
    listmyprojectssession=[]
    listmyprojectssession.append(('NoChoice',printstr.format("Project name","Session name","Date and Time","Description")))
    listmysession=[]
    for thissessions in mysessions:
            
        for thissession in thissessions[1]:
            listmysession.append(thissession)
            thedate="1970-01-01"
            try:
                thedate=db.session.query(models.Session.creation_date).filter_by(name=str(thissession)).scalar().isoformat().replace("T"," ")
            except:
                pass
            SessDesc=db.session.query(models.Session).filter_by(name=thissession).scalar().description
            listmyprojectssession.append(
                (str(thissession),printstr.
                 format(str(thissessions[0]),
                        str(thissession),
                        thedate,SessDesc)
                )
            )
    
    # All sessions this user has been invited to
    listsessions=[]

    invite_sessions = db.session.query(models.Session.name).filter(models.Session.users.any(id=user_id)).all()
    printstr="{0:\xa0<"+sessionl+"."+sessionl+"}|\xa0{1:\xa0<"+datel+"."+datel+"}\xa0|\xa0{2:\xa0<"+descrl+"."+descrl+"}"        
    listsessions.append(('NoChoice',printstr.format("Session name","Date and Time","Description")))
    for thissession in invite_sessions:
        logging.debug("Build listsessions for invite_session "+str(thissession.name))
        if (thissession.name not in listmysession):
            thedate="1970-01-01"
            try:
                thedate=db.session.query(models.Session.creation_date).filter_by(name=thissession.name).scalar().isoformat().replace("T"," ")
            except:
                pass
            SessDesc=db.session.query(models.Session).filter_by(name=thissession.name).scalar().description
            listsessions.append(
                (str(thissession.name),printstr.
                 format(str(thissession.name),
                        thedate, SessDesc)
                )
            )
        
    logging.debug("My project sessions :"+str(listmyprojectssession))
    logging.debug("My invited sessions :"+str(listsessions))
    myform = BuildAllProjectSessionForm(listmyprojectssession,listsessions)()
    if myform.validate_on_submit():
        if (myform.chosen_project_session.data != "NoChoice"):
            logging.debug("Chosen project session "+str(myform.chosen_project_session.data))
            session["sessionname"]=myform.chosen_project_session.data
        elif (myform.chosen_session_invited.data != "NoChoice"):
            logging.debug("Chosen session invited "+str(myform.chosen_session_invited.data))
            session["sessionname"]=myform.chosen_session_invited.data
        else:
            logging.warning("You must choose a session")
            flash("You didn't select a session or click 'Go' button on search bar.\n"+
                  "You must choose a session in your projects or one you were invited on.")
            return redirect("/allsessions")
            
        logging.debug("Which is session "+str(db.session.query(models.Session.id).filter_by(name=session["sessionname"]).scalar()))
        its_project_id=db.session.query(models.Session).filter_by(name=session["sessionname"]).scalar().id_projects
        session["projectname"]=db.session.query(models.Project).filter_by(id=its_project_id).scalar().name
        logging.debug("And have project id "+str(its_project_id)+" which is "+str(session["projectname"]))
        session["is_client_active"]=True
        if(myform.edit.data):
            logging.debug("go to edit old session : "+session["sessionname"])
            message = '{"oldsessionname":"'+session["sessionname"]+'"}'
            return redirect(url_for(".editsession",message=message))
        return redirect("/grid")
        
    return render_template("main_login.html", title="All projects/sessions TiledViz", form=myform, message=message)

    
# List all old sessions for the projectname I am in
@app.route('/oldsessions', methods=["GET", "POST"])
def oldsessions():
# Old Session page
    Project = db.session.query(models.Project).filter_by(name=session["projectname"]).scalar()
    project_id=Project.id
    project_desc=Project.description
    querysessions = db.session.query(models.Session.name).filter_by(id_projects=project_id)
    listsessions=[]
    for thissession in querysessions:
        logging.debug("Build listsessions "+str(thissession[0]))
        listsessions.append((str(thissession[0]),str(thissession[0])))
    oldproject={"name":session["projectname"],
                "description":project_desc}
    logging.debug("Old project : "+str(oldproject["name"])+" list old sessions :"+str(listsessions))
    myform = BuildOldProjectForm(oldproject, listsessions)()
    if myform.validate_on_submit():
        if(myform.from_session.data=="use"):
            logging.debug("reuse old session : "+myform.chosen_session.data)
            session["sessionname"]=myform.chosen_session.data
            session["is_client_active"]=True
            return redirect("/grid")
        elif(myform.from_session.data=="edit"):
            logging.debug("go to edit old session : "+myform.chosen_session.data)
            message = '{"oldsessionname":"'+myform.chosen_session.data+'"}'
            return redirect(url_for(".editsession",message=message))
        elif(myform.from_session.data=="copy"):
            logging.debug("go to copy old session : "+myform.chosen_session.data)
            message = '{"oldsessionname":"'+myform.chosen_session.data+'"}'
            return redirect(url_for(".copysession",message=message))

    return render_template("main_login.html", title="Old projects TiledViz", form=myform)

# ==> invite an existing user (and connected) with invite_link
# Create new session
@app.route('/newsession', methods=["GET", "POST"])
def newsession():
    # New or session manager (copy, invite_link a list of connected users ?)
    myform = BuildNewSessionForm()() 
    if myform.validate_on_submit():
        if myform.add_users.data:
            myform.users.append_entry()
            flash("New user for user {} in session {}".format(session["username"], myform.sessionname.data))
            return render_template("main_login.html", title="New session TiledViz", form=myform)
        logging.info("in session")
        id_projects=db.session.query(models.Project.id).filter_by(name=session["projectname"])
        sessionname=myform.sessionname.data
        newsession,exist=create_newsession(sessionname, myform.description.data, id_projects, myform.users)
        if (not exist):
            try:
                db.session.add(newsession)
                db.session.commit()
            except Exception:
                traceback.print_exc(file=sys.stderr)
            
                flash("Session with name {} creation problem.".format(sessionname))    
                return render_template("main_login.html", title="New Session TiledViz", form=myform, message=message)
        else:
            flash("Session with name {} already exists".format(sessionname))
            return render_template("main_login.html", title="New Session TiledViz", form=myform)

        # Create default config for new session 
        config_default_file=open("app/static/js/config_default.json",'r')
        json_configs=json.load(config_default_file)
        config_default_file.close()
        newsession.config=json_configs
        db.session.commit()

        if myform.Session_config.data:
            message = '{"sessionname":"'+newsession.name+'"}'
            return redirect(url_for(".configsession",message=message))
        else:
            message='{"username":"'+session["username"]+'","sessionname":"'+session["sessionname"]+'"}'
            return redirect(url_for(".addtileset",message=message))
    return render_template("main_login.html", title="New session TiledViz", form=myform)        

# Copy an old session and edit tilesets
@app.route('/copysession', methods=["GET", "POST"])
def copysession():
    message=json.loads(request.args["message"])
    oldsessionname=message["oldsessionname"]
    oldsession = db.session.query(models.Session).filter_by(name=oldsessionname).scalar()    
    myform = BuildEditsessionform(oldsession,edit=False)()
    if myform.validate_on_submit():
        logging.debug("copySessionForm : ")
        if myform.add_users.data:
            myform.users.append_entry()
            message = '{"oldsessionname":"'+session["sessionname"]+'"}'
            flash("New user avaible for user {} in session {}".format(session["username"], myform.sessionname.data))
            # TODO !! => send invitation to new users ?
            return render_template("main_login.html", title="Copy session TiledViz", form=myform)

        newsession,exist=create_newsession(myform.sessionname.data, myform.description.data, oldsession.id_projects, myform.users)

        if (not exist):
            nbts=len(oldsession.tile_sets)
            for i in range(nbts):
                newsession.tile_sets.append(oldsession.tile_sets[i])
                
            try:
                # if user has not change session.name, it can't be created.
                db.session.add(newsession)
                db.session.commit()
            except Exception:
                traceback.print_exc(file=sys.stderr)
            
                message = '{"oldsessionname":"'+oldsessionname+'"}'
                flash("Session with name {} creation problem.".format(myform.sessionname.data))
                return render_template("main_login.html", title="Copy session TiledViz", form=myform, message=message)
        else:
            flash("You must change session name {} for new session.".format(sessionname))
            return render_template("main_login.html", title="Copy Session TiledViz", form=myform)

        theaction=myform.tilesetaction.data
        
        # try:    
        #     oldtilesetid=int(myform.tilesetchoice.data)
        #     message = '{"oldtilesetid":'+str(tilesetid)+'}'
        # except :
        #     traceback.print_exc(file=sys.stderr)
        #     if ( theaction != "search" and theaction != "copy" ): #and theaction != "useold"
        #             logging.error("You must check a tileset for this action {}".format(theaction))
        #             flash("You must check a tileset for this action {}".format(theaction))
        #             message = '{"oldsessionname":'+newsession.name+'}'
        #             return redirect(url_for(".editsession",message=message))

        logging.debug("Action tileset : "+str(message)+" "+theaction)
        if(theaction == "useold"):
            session["is_client_active"]=True
            return redirect("/grid")
        elif myform.Session_config.data:
            message = '{"sessionname":"'+newsession.name+'"}'
            return redirect(url_for(".configsession",message=message))
        elif(theaction == "copy"):
            message = '{"oldtilesetid":"'+str(oldtilesetid)+'"}'
            return redirect(url_for(".copytileset",message=message))
        elif (theaction == "search"):
            message = '{"oldsessionname":"'+newsession.name+'"}'
            return redirect(url_for(".searchtileset",message=message))
    return render_template("main_login.html", title="Copy session TiledViz", form=myform, message=message)


# Edit old session
@app.route('/editsession', methods=["GET", "POST"])
def editsession():
    message=json.loads(request.args["message"])
    oldsessionname=message["oldsessionname"]
    oldsession = db.session.query(models.Session).filter_by(name=oldsessionname).scalar()    
    myform = BuildEditsessionform(oldsession,edit=True)()
    if myform.validate_on_submit():
        logging.debug("editSessionForm : ")
        if myform.add_users.data:
            myform.users.append_entry()
            message = '{"oldsessionname":"'+oldsessionname+'"}'
            flash("New user avaible for user {} in session {}".format(session["username"], myform.sessionname.data))
            # TODO !! => send invitation to new users ?
            return render_template("main_login.html", title="Edit session TiledViz", form=myform)

        if (myform.sessionname.data != oldsessionname):
            message = '{"oldsessionname":"'+session["sessionname"]+'"}'
            flash("You must NOT change session name to edit session {}".format(oldsessionname))
            return render_template("main_login.html", title="Edit session TiledViz", form=myform, message=message)

        oldsession.description=str(myform.description.data)
        creation_date=datetime.datetime.now()
        oldsession.creation_date=str(creation_date)
        db.session.commit()
        session["sessionname"]=oldsessionname

        copy_users_session(oldsession,myform.users)
        db.session.commit()

        if myform.Session_config.data:
            message = '{"sessionname":"'+oldsessionname+'"}'
            return redirect(url_for(".configsession",message=message))

        theaction=myform.tilesetaction.data

        ListAllTileSet_ThisSession=[ (str(thistileset.id), thistileset.name) for thistileset in oldsession.tile_sets]
        if (len(ListAllTileSet_ThisSession) > 0):
            try:    
                tilesetid=int(myform.tilesetchoice.data)
                message = '{"oldtilesetid":'+str(tilesetid)+'}'
            except :
                #traceback.print_exc(file=sys.stderr)
                if ( theaction != "search" and theaction != "copy" and theaction != "create" and theaction != "useold" and not myform.edit.data):
                    logging.debug("You must check a tileset for this action {}".format(theaction))
                    flash("You must check a tileset for this action {}".format(theaction))
                    message = '{"oldsessionname":'+oldsessionname+'}'
                    return redirect(url_for(".editsession",message=message))
            if(myform.edit.data):
                logging.debug("message before edittileset "+str(message))
                return redirect(url_for(".edittileset",message=message))
        
        logging.debug("Action tileset : "+str(message)+" "+theaction)
        if(theaction == "useold"):
            session["is_client_active"]=True
            return redirect("/grid")
        elif (theaction == "create"):
            flash("Tileset requested for user {} in session {}".format(session["username"],session["sessionname"]))
            message='{"username":"'+session["username"]+'","sessionname":"'+session["sessionname"]+'"}'
            return redirect(url_for(".addtileset",message=message))
        elif(theaction == "copy"):
            return redirect(url_for(".copytileset",message=message))
        elif(theaction == "search"):
            message = '{"oldsessionname":"'+session["sessionname"]+'"}'
            return redirect(url_for(".searchtileset",message=message))
        elif(theaction == "remove"):
            try:
                thistileset=db.session.query(models.TileSet).filter_by(id=tilesetid).scalar()
                logging.debug("TileSet for remove : "+str(thistileset))
                oldsession.tile_sets.remove(thistileset)
                db.session.commit()
            except Exception:
                traceback.print_exc(file=sys.stderr)
                
                flash("Error remove tileset {}".format(db.session.query(models.TileSet).filter_by(id=tilesetid).scalar().name))
            message = '{"oldsessionname":"'+oldsessionname+'"}'
            return redirect(url_for(".editsession",message=message))
    return render_template("main_login.html", title="Edit session TiledViz", form=myform, message=message)

# List all old tilesets I am in
@app.route('/searchtileset', methods=["GET", "POST"])
def searchtileset():
# Old Tileset page
    try:
        message=json.loads(request.args["message"])
    except json.decoder.JSONDecodeError as e:
        logging.error("message error ! "+str(e))
        logging.error("message : "+str(request.args["message"]))
        traceback.print_exc(file=sys.stderr)
        message=json.loads(request.args["message"].replace("'", '"'))

    oldsessionname=message["oldsessionname"]
    oldsession = db.session.query(models.Session).filter_by(name=oldsessionname).scalar()    

    querysessions= models.Session.query.filter(models.Session.users.any(name=session["username"])).all()

    printstr="{0:\xa0<"+tilesetl+"."+tilesetl+"}|\xa0{1:\xa0<"+datel+"."+datel+"}\xa0|\xa0{2:\xa0<"+descrl+"."+descrl+"}"

    listtilesets=[]
    listtilesets.append(('NoChoice',printstr.format("Tileset name","Date and Time","Data Path")))
    for thissession in querysessions:
        #thissession=db.session.query(model.Session).filter_by(id=thissessionid[0])
        for tileset in thissession.tile_sets:
            if ( tileset.name not in listtilesets ):
                thedate=db.session.query(models.TileSet.creation_date).filter_by(name=tileset.name).scalar().isoformat().replace("T"," ")
                logging.error("Compare thedate : %s %s" % (thedate, tileset.creation_date.isoformat().replace("T"," ")))
                listtilesets.append((str(tileset.id),
                                     printstr.format(
                                         str(tileset.name),
                                         thedate,
                                         tileset.Dataset_path)))
    # logging.warning("For user : "+session["username"]+" list old tilesets :"+str(listtilesets).replace("\xa0"," ").replace("('","\n('"))

    myform = BuildOldTileSetForm(session["username"], listtilesets)()
    if myform.validate_on_submit():
        if (myform.chosen_tileset.data=="NoChoice"):
            flash("Error : no TileSet Selected.")
            return redirect(url_for(".searchtileset",message=message))
        else:
            logging.warning("Out of forms, add tilesets :"+str(myform.chosen_tileset.data))
            thisTS=db.session.query(models.TileSet).filter_by(id=myform.chosen_tileset.data).scalar()
            logging.warning("For user : "+session["username"]+", add tilesets :"+str(thisTS.name))
            oldsession.tile_sets.append(thisTS)
            db.session.commit()
            message = '{"oldsessionname":"'+oldsessionname+'"}'
            flash("Add tileSet {}.".format(thisTS.name))
            return redirect(url_for(".editsession",message=message))

    return render_template("main_login.html", title="Old projects TiledViz", form=myform)

# Config Session : give the json (depend of static/js/config_default.json)
@app.route('/configsession', methods=["GET", "POST"])
def configsession():
    message=json.loads(request.args["message"])

    sessionname=message["sessionname"]
    thesession = db.session.query(models.Session).filter_by(name=sessionname).scalar()

    # Detect how the data of config has been inserted :        
    if ( session["sessionname"] in  jsontransfert):
        if ( "TheJson" in  jsontransfert[session["sessionname"]]):
            # if TheJson is already define in message, it has been edited by jsoneditor (call beside)
            json_configs=jsontransfert[session["sessionname"]]["TheJson"]
            jsontransfert[session["sessionname"]].pop("TheJson")
            logging.debug("configsession : come back from jsoneditor") 
            # json_gziped=message["TheJson"].replace("b'","").replace("'","")
            # json_unziped=gzip.decompress(base64.b64decode(json_gziped)).decode('utf-8')
            # #print("configsession json_unziped", json_unziped)
            # json_configs=json.loads(json_unziped)
            #print("configsession json_configs", json_configs)
        else:
            logging.debug("configsession : we can't be here !") 
            if ( thesession.config == None ):
                logging.debug("configsession : using config_default.json") 
                config_default_file=open("app/static/js/config_default.json",'r')
                json_configs=json.load(config_default_file)
                config_default_file.close()
            else:
                logging.debug("configsession : old session config.") 
                json_configs=thesession.config
    else:
        if ( thesession.config == None ):
            logging.debug("configsession : using config_default.json") 
            config_default_file=open("app/static/js/config_default.json",'r')
            json_configs=json.load(config_default_file)
            config_default_file.close()
        else:
            logging.debug("configsession : old session config.") 
            json_configs=thesession.config

    json_configs_text=json.JSONEncoder().encode(json_configs)
    #logging.debug("json_configs_text : "+json_configs_text)
    myform = BuildConfigSessionForm(json_configs,json_configs_text)()

    if myform.validate_on_submit():
        # if json structure is inserted with text area
        json_configs = myform.json_config_text.data

        if myform.editjson.data:
            # json_gziped=base64.b64encode(gzip.compress(json_configs.encode('utf-8')))
            # callfunction = '{"function":"configsession",'+'"args":{"sessionname":"'+sessionname+'"}}'
            jsontransfert[session["sessionname"]]={"callfunction": '{"function":"configsession",'+'"args":{"sessionname":"'+sessionname+'"}}',
                                                   "TheJson":json_configs}
            # return redirect(url_for(".jsoneditor",callfunction=callfunction,TheJson=json_gziped))
            return redirect(url_for(".jsoneditor"))

        # Translate json text in structure
        jsonConfigs = json.loads(json_configs)
        #logging.debug("json_configs modify : "+str(jsonConfigs))
        
        # json_configs_file = FileField("File json object for tileset ")
        # json_file = open(json_file_name).read()

        thesession.config=jsonConfigs
        db.session.commit()

        message = '{"oldsessionname":"'+sessionname+'"}'
        return redirect(url_for(".editsession",message=message))
        
    return render_template("main_login.html", title="Config session", form=myform, message=message)


# New TileSet : always create tile even if another (title/comment) exists
@app.route('/addtileset', methods=["GET", "POST"])
def addtileset():
    myform = BuildTilesSetForm()()
    #print('message=',str(request.args["message"]))
    message=json.loads(request.args["message"])
    if myform.validate_on_submit():
        logging.info("in addtileset")

        json_tiles=None;
        # Detect how the data of tiles has been inserted :
        if (myform.json_tiles_file.data) :
            json_tiles_file = myform.json_tiles_file.data
            json_tiles = json_tiles_file.read()
        elif (myform.json_tiles_text.data):
            # if json structure is inserted with text area
            json_tiles = myform.json_tiles_text.data

        if (json_tiles):
            # Translate json text in structure
            try:
                jsonTileSet = json.loads(json_tiles)
            except json.decoder.JSONDecodeError as e:
                logging.error("Addtileset : json TileSet error ! "+str(e))
                logging.error("Data : "+str(json_tiles))
                traceback.print_exc(file=sys.stderr)
                json_tiles=json.loads(json_tiles.replace("'", '"'))
                try:
                    jsonTileSet = json.loads(json_tiles)
                except json.decoder.JSONDecodeError as e:
                    logging.error("Addtileset : correction with double quotes not efficient ! "+str(e))
                    flash("Please look on data for TileSet json compliance")
                    return redirect(url_for(".addtileset",message=message))
                    
            nbr_of_tiles = len(jsonTileSet["nodes"])
            logging.info("Number of tiles "+str(nbr_of_tiles))
            
        # openports_between_tiles = FieldList(IntegerField("port :",validators=[Optional()]),description="Open port in visualisation network",min_entries=2,max_entries=5) 

        urlbool=False
        connectionbool=False
        if (myform.type_of_tiles.data == "URL"):
            urlbool=True
        elif(myform.type_of_tiles.data == "CONNECTION"):
            launch_file=myform.script_launch_file.data
            if (not launch_file):
                flash("TileSet with connection must have at least a script to launch your tiles.\n You must add launch_file script.")    
                return render_template("main_login.html", title="New TileSet TiledViz", form=myform, message=message) 
            connectionbool=True

        #print(session["sessionname"])
        conn_session=db.session.query(models.Session).filter_by(name=session["sessionname"]).scalar()
        creation_date=datetime.datetime.now()
        tilesetname=myform.name.data
        if ( myform.dataset_path.data ):
            datapath=str(myform.dataset_path.data)
        else:
            if (urlbool):
                datapath="http"
            else:
                datapath=""
                
        newtileset,exist=create_newtileset(tilesetname, conn_session, myform.type_of_tiles.data, datapath, creation_date)
        if (not exist):
            try:
                db.session.add(newtileset)
                db.session.commit()
            except Exception:
                traceback.print_exc(file=sys.stderr)
                
                flash("TileSet with name {} creation problem :".format(tilesetname))    
                return render_template("main_login.html", title="New TileSet TiledViz", form=myform, message=message)
        else:
            flash("TileSet with name {} already exists : Please give another name ".format(tilesetname))
            return render_template("main_login.html", title="New TileSet TiledViz", form=myform, message=message)
        
        # Register config files in jsontransfert to write them in connection path
        if (connectionbool):
            TStmpName="tileset_"+str(newtileset.id)
            if ( not TStmpName in  jsontransfert):
                jsontransfert[TStmpName]={}
            if (myform.configfiles.data):
                for FileS in myform.configfiles.data:
                    jsontransfert[TStmpName][FileS.filename]=FileS.read()

            # Python file to launch case
            jsontransfert["tileset_"+str(newtileset.id)][launch_file.filename]=launch_file.read()
            newtileset.launch_file=launch_file.filename
            db.session.commit()
        
        if (json_tiles):
            # Insert tiles into DB :
            tiles=[]

            for i in range(nbr_of_tiles):
                Mynode=jsonTileSet["nodes"][i]

                title,name,comment,tags,variable,pos_px_x,pos_px_y,IdLocation,url,ConnectionPort = \
                    convertTile(Mynode,tilesetname,connectionbool,urlbool,datapath)
            
                newtile = models.Tile(title=title,
                                      comment=comment,
                                      tags=tags,
                                      source= {"name" : name,
                                               "connection" : ConnectionPort,
                                               "url" : url,
                                               "variable": variable
                                      },
                                      pos_px_x= pos_px_x,
                                      pos_px_y= pos_px_y,
                                      IdLocation=IdLocation,
                                      creation_date= creation_date)
                lasttile=db.session.query(models.Tile.id).order_by(models.Tile.id.desc()).first()
                if (lasttile):
                    newtile.id=lasttile.id+1
                else:
                    newtile.id=1
            
                db.session.add(newtile)
                db.session.commit()
                logging.warning(str(i)+" add tile "+str(newtile.id)+" "+str(newtile.title))
            
                newtileset.tiles.append(newtile)
                db.session.commit()


        session["is_client_active"]=True

        if (connectionbool):
            message = '{"oldtilesetid":'+str(newtileset.id)+',"oldsessionname":"'+session["sessionname"]+'"}'
            return redirect(url_for(".addconnection",message=message))
        else:        
            message = '{"oldsessionname":"'+session["sessionname"]+'"}'
            return redirect(url_for(".editsession",message=message))
    
    return render_template("edittileset.html", title="New TileSet TiledViz", form=myform, message=message)


# Copy an old TileSet
# Only copy old tiles in DB
@app.route('/copytileset', methods=["GET", "POST"])
def copytileset():
    message=json.loads(request.args["message"])
    logging.warning("copytileset : "+str(message))
    oldtilesetid=message["oldtilesetid"]
    oldtileset=db.session.query(models.TileSet).filter_by(id=oldtilesetid).scalar()

    myform = BuildTilesSetForm(oldtileset,onlycopy=True)()

    flash("Tileset {} copy for user {} in session {}".format(oldtileset.name,session["username"],session["sessionname"]))
    if myform.validate_on_submit():
        logging.info("in copy tileset")
        
        if (myform.name.data == oldtileset.name):
            message = '{"oldtilsetid":"'+str(oldtilesetid)+'"}'
            flash("You must change tilsetname to copy tileset {}".format(oldtileset.name))
            #return redirect(url_for(".copytileset",message=message))
            return render_template("main_login.html", title="Copy tileset TiledViz", form=myform, message=message)

        nbr_of_tiles = len(oldtileset.tiles)
        
        sessioncopy=db.session.query(models.Session).filter_by(name=session["sessionname"]).scalar()
        creation_date=datetime.datetime.now()
        tilesetname=myform.name.data
        newtileset, exist=create_newtileset(myform.name.data, sessioncopy, oldtileset.type_of_tiles, oldtileset.Dataset_path, creation_date)
        if (not exist):
            try:
                db.session.add(newtileset)
                db.session.commit()
            except Exception:
                traceback.print_exc(file=sys.stderr)

                flash("TileSet creation with name {} already exist :".format(tilesetname))    
                return render_template("main_login.html", title="New TileSet TiledViz", form=myform, message=message)


        newtileset.tiles=[]
        for i in range(nbr_of_tiles):
            oldtile=oldtileset.tiles[i]
            newtileset.tiles.append(oldtile)
            db.session.commit()

        session["is_client_active"]=True

        # TODO : get back old connection if exists
        urlbool=False
        connectionbool=False
        if (oldtileset.type_of_tiles == "URL"):
            urlbool=True
        elif(oldtileset.type_of_tiles == "CONNECTION"):
            connectionbool=True

        if (connectionbool):
            # Copy a mirror connection
            copy_tileset_connection(oldtileset,newtileset,session["sessionname"])
            logging.error("copy id connection :  "+str(newtileset.id_connections))

            flag_modified(newtileset,"config_files")
            db.session.commit()
            
            message = '{"oldtilesetid":'+str(newtileset.id)+',"oldsessionname":"'+session["sessionname"]+'"}'
            return redirect(url_for(".edittileset",message=message))
        else:
            message = '{"oldsessionname":"'+session["sessionname"]+'"}'
            return redirect(url_for(".editsession",message=message))
            
    return render_template("edittileset.html", title="Copy TileSet TiledViz", form=myform, message=message)

# Edit old new TileSet
@app.route('/edittileset', methods=["GET", "POST"])
def edittileset():
    try:
        message=json.loads(request.args["message"])
    except json.decoder.JSONDecodeError as e:
        logging.error("message error ! "+str(e))
        logging.error("message : "+str(request.args["message"]))
        traceback.print_exc(file=sys.stderr)
        message=json.loads(request.args["message"].replace("'", '"'))
        
    logging.warning("edittileset : "+str(message))

    oldtilesetid=message["oldtilesetid"]
    oldtileset=db.session.query(models.TileSet).filter_by(id=oldtilesetid).one()

    # TODO : test if user is in a session with this tileset
    
    # Detect how the data of tileset has been inserted :
    buildargs={}
    buildargs["oldtileset"]=oldtileset

    if ( session["sessionname"] in  jsontransfert):
        if ( "TheJson" in  jsontransfert[session["sessionname"]]):
            # if TheJson is already define in message, it has been edited by jsoneditor (call beside)
            logging.debug("TheJson is already define in message")
            TheJson=jsontransfert[session["sessionname"]]["TheJson"]
            jsontransfert[session["sessionname"]].pop("TheJson")
            try:
                json_tiles_text=json.JSONEncoder().encode(TheJson)
                #print("edittileset json_tiles_text) ",json_tiles_text)
                buildargs["json_tiles_text"]=json_tiles_text
            except:
                traceback.print_exc(file=sys.stderr)
                flash("Error from json editor. Please try again.")
                return redirect(url_for(".edittileset",message=message))

    connectionbool=False            
    if(oldtileset.type_of_tiles == "CONNECTION"):
        # Try to get the old connection
        oldConnection_id=-1
        try:
            oldconnection=db.session.query(models.Connection).filter_by(id=oldtileset.id_connections).one()
            oldConnection_id=oldtileset.id_connections
            buildargs["editconnection"]=True
        
        except sqlalchemy.orm.exc.NoResultFound:
            flash("Tileset {} edit for user {} : no connection found ! ".format(oldtileset.name,session["username"]))
            oldConnection_id = 0
            buildargs["editconnection"]=True
        except AttributeError as err:
            #message = '{"oldtilesetid":'+str(oldtileset.id)+',"oldsessionname":"'+session["sessionname"]+'"}'
            #return redirect(url_for(".addconnection",message=message))
            traceback.print_exc(file=sys.stderr)
            logging.error("Error get old connection for tileset %s : %s" % ( oldtileset.name, err ))
            flash("Tileset {} edit for user {} : AttributeError ! ".format(oldtileset.name,session["username"]))

        except Exception as err:
            traceback.print_exc(file=sys.stderr)
            logging.error("Error get old connection for tileset %s : %s" % ( oldtileset.name, err ))
            flash("Error get old connection for tileset %s : %s" % ( oldtileset.name, err ))

        if ( oldConnection_id < 0):
            message = '{"oldsessionname":"'+session["sessionname"]+'"}'
            return redirect(url_for(".editsession",message=message))
        connectionbool=True
    
    myform = BuildTilesSetForm(**buildargs)()

    if ("username" in session):
        flash("Tileset {} edit for user {} in session {}".format(oldtileset.name,session["username"],session["sessionname"]))
    else:
        flash("You are not connected. You must login before using a connection.")
        return redirect("/login")
        
    if myform.validate_on_submit():
        logging.info("in tileset editor")
        
        if(connectionbool):
            if (myform.editconnection.data):
                message = '{"oldtilesetid":'+str(oldtileset.id)+',"oldsessionname":"'+session["sessionname"]+'"}'
                return redirect(url_for(".editconnection",message=message))
            if (myform.shellconnection.data):
                message = '{"direct":1,"oldtilesetid":'+str(oldtileset.id)+',"oldsessionname":"'+session["sessionname"]+'"}'
                return redirect(url_for(".editconnection",message=message))
            
        if(myform.goback.data):
            logging.debug("go back to edit old session : "+session["sessionname"])
            message = '{"oldsessionname":"'+session["sessionname"]+'"}'
            return redirect(url_for(".editsession",message=message))

        # Detect how the data of tiles has been inserted :
        if (myform.json_tiles_file.data) :
            json_tiles_file = myform.json_tiles_file.data
            logging.warning("Read json_tiles_file :"+myform.json_tiles_file.data.filename)
            json_tiles = json_tiles_file.read()
        else:
            # if json structure is inserted with text area
            json_tiles = myform.json_tiles_text.data

        try:    
            if myform.editjson.data:
                jsontransfert[session["sessionname"]]={"callfunction": '{"function":"edittileset",'+'"args":{"oldtilesetid":"'+str(oldtilesetid)+'"}}',
                                                   "TheJson":json_tiles}
                # json_gziped=base64.b64encode(gzip.compress(json_tiles.encode('utf-8')))
                #return redirect(url_for(".jsoneditor",callfunction=callfunction,TheJson=json_gziped))
                return redirect(url_for(".jsoneditor"))
        except Exception as err:
            traceback.print_exc(file=sys.stderr)
            logging.error("Error editjson %s : %s" % ( str(myform.editjson), err ))

        if(oldtileset.type_of_tiles == "CONNECTION" and myform.manage_connection.data != "reNew"):
            user_id=get_user_id("edittileset",session["username"])
            if ( not "connection"+str(oldConnection_id) in session):
                flash("You don't have connection information in your personal cookie for this connection.")
                logging.error("You (user "+str(user_id)+") don't have connection information in your personal cookie for this connection : "+str(oldConnection_id))
                message=request.args["message"]
                return redirect(url_for(".edittileset",message=message))
        
            # Build connection path            
            user_path=os.path.join("/TiledViz/TVFiles",str(user_id))
            connectionpath=os.path.join(user_path,str(oldConnection_id))

            # Diff config files to write them if needed in connection path
            oldtileset_config_files=oldtileset.config_files
            if (myform.configfiles.data):
                for FileS in myform.configfiles.data:
                    # data from form
                    tf = tempfile.NamedTemporaryFile(mode="w+b",dir=connectionpath,prefix="",delete=False)
                    tf.write(FileS.read())
                    newfilename=tf.name
                    tf.close()
                    if (os.stat(tf.name).st_size > 0):
                        if (FileS.filename in oldtileset_config_files):
                            # Test file modified with same name
                            boolDiff=filecmp.cmp(f1=oldtileset_config_files[FileS.filename],f2=newfilename)
                            logging.warning("Diff with modified config file : "+str(boolDiff))
                            if (not boolDiff):
                                # rm old config files
                                strrm="rm -f "+oldtileset_config_files[FileS.filename]
                                logging.warning("Update old config file "+FileS.filename+" in edittileset.")
                                os.system(strrm)
                                oldtileset.config_files[FileS.filename]=newfilename
                                flag_modified(oldtileset,"config_files")
                                db.session.commit()
                            else:
                                # rm unused config files
                                strrm="rm -f "+newfilename
                                os.system(strrm)
                        else:
                            # new config file
                            oldtileset.config_files[FileS.filename]=newfilename
                            logging.warning("Add new config file "+FileS.filename+" in edittileset.")
                            flag_modified(oldtileset,"config_files")
                            db.session.commit()
                    else:
                        # rm unused config files
                        strrm="rm -f "+newfilename
                        os.system(strrm)
            
            # Python file to launch case
            launch_file=myform.script_launch_file.data
            
            oldtileset_launch_file=oldtileset.launch_file
            FileS=myform.script_launch_file.data
            tf = tempfile.NamedTemporaryFile(mode="w+b",dir=connectionpath,prefix="",delete=False)
            tf.write(FileS.read())
            newfilename=tf.name
            tf.close()
            if (os.stat(tf.name).st_size > 0):
                if (FileS.filename in oldtileset_config_files):
                    # Test launch_file modified with same name
                    boolDiff=filecmp.cmp(f1=oldtileset_config_files[FileS.filename],f2=newfilename)
                    logging.warning("Diff with modified launch case file : "+str(boolDiff))
                    if (not boolDiff):
                        # rm old config files
                        strrm="rm -f "+oldtileset_config_files[FileS.filename]
                        logging.warning("Update old launch file "+FileS.filename+" in edittileset.")
                        os.system(strrm)
                        oldtileset.config_files[FileS.filename]=newfilename
                        flag_modified(oldtileset,"config_files")
                        db.session.commit()
                    else :
                        # rm unused config files
                        strrm="rm -f "+newfilename
                        os.system(strrm)
                else :
                    # New launch_file filename
                    # rm old config files
                    strrm="rm -f "+oldtileset_config_files[oldtileset_launch_file]
                    del(oldtileset_config_files[oldtileset_launch_file])
                    logging.warning("Rename launch file from "+oldtileset_launch_file
                                        +" to "+FileS.filename+" in edittileset.")
                    os.system(strrm)
                    oldtileset.launch_file=FileS.filename
                    oldtileset.config_files[FileS.filename]=newfilename
                    flag_modified(oldtileset,"config_files")
                    db.session.commit()
            else :
                # rm unused config files
                strrm="rm -f "+newfilename
                os.system(strrm)
        
        elif(oldtileset.type_of_tiles == "CONNECTION" and myform.manage_connection.data == "reNew"):
            launch_file=myform.script_launch_file.data
            if (not launch_file):
                flash("TileSet with connection must have at least a script to launch your tiles.\n You must add launch_file script.")    
                return render_template("main_login.html", title="Edit TileSet TiledViz", form=myform, message=message)
            # Register config files in jsontransfert to write them in connection path
            TStmpName="tileset_"+str(oldtileset.id)
            if ( not TStmpName in  jsontransfert):
                jsontransfert[TStmpName]={}
            if (myform.configfiles.data):
                for FileS in myform.configfiles.data:
                    jsontransfert[TStmpName][FileS.filename]=FileS.read()

            # Python file to launch case
            jsontransfert["tileset_"+str(oldtileset.id)][launch_file.filename]=launch_file.read()
            oldtileset.launch_file=launch_file.filename
            db.session.commit()
            

        # Translate json text in structure
        if (len(json_tiles) > 0):
            jsonTileSet = json.loads(json_tiles)
        else:
            jsonTileSet = {"nodes":[]}
        # else:
        #     json_file_name=secure_filename(myform.json_tiles_file.data)
        #     print("instance_path :",app.instance_path)
        #     myform.save(os.path.join(app.instance_path, filename))
        #     req, resp = app.test_client.post(
        #          '/upload', data={'upload': open(__file__, 'rb')})
        #     assert resp.status == 200
        #     assert resp.text == os.path.basename(__file__)
        #     #json_file = json_file_name.data.read()
        #     print("Read the file ",json_file_name," contains ",json_file)
        #     # get call message and put new json from file
        #     OutJson=json.dumps(json.loads(json_file)).replace("'", '"')
        #     message["TheJson"]=str(base64.b64encode(gzip.compress(OutJson.encode('utf-8'))))
        #     message=json.dumps(message) #.replace("'", '"')
        #     print("Relaunch whith file ",message)
        #     return redirect(url_for(".edittileset",message=message))
        
        nbr_of_tiles = len(jsonTileSet["nodes"])
        logging.info("Number of tiles "+str(nbr_of_tiles))

        # TODO:
        # openports_between_tiles = FieldList(IntegerField("port :",validators=[Optional()]),description="Open port in visualisation network",min_entries=2,max_entries=5) 

        # TODO
        # TilesSetForm.script_launch_file


        # Insert and create NEW tiles into TileSet or delete OLD tiles from TileSet.tiles list ?
        old_nbr_of_tiles=len(oldtileset.tiles)
        if (nbr_of_tiles > old_nbr_of_tiles):
            insertnewtiles=True
        elif (nbr_of_tiles < old_nbr_of_tiles):
            deletesometiles=True
            

        urlbool=False
        if (myform.type_of_tiles.data == "URL"):
            urlbool=True

        tilesetname=oldtileset.name
        
        creation_date=datetime.datetime.now()
        if (myform.dataset_path.data):
            datapath=str(myform.dataset_path.data)
        else:
            if (urlbool):
                datapath="http"
            else:
                datapath=""          
        oldtileset.datapath=datapath
        oldtileset.creation_date=creation_date
        db.session.commit()

        

        oldtileset.tiles=[]

        for i in range(nbr_of_tiles):
            Mynode=jsonTileSet["nodes"][i]
            #print (str(i)+" "+str(Mynode))

            title,name,comment,tags,variable,pos_px_x,pos_px_y,IdLocation,url,ConnectionPort = \
                convertTile(Mynode,tilesetname,connectionbool,urlbool,datapath)
            
            # Insert and create only NEW tiles into TileSet or
            # TODO: edit OLD tiles from TileSet.tiles list ? (add a suppress old tiles button in form).
            # search if Tile already exists :
            try:
                # unicity for (title, comment, tags) (url ?)
                oldtile=db.session.query(models.Tile).filter_by(title=title,comment=comment).order_by(models.Tile.id.desc()).first()

                # if (type(oldtile) == type(None)):
                #     logging.warning(str(i)+" tile type "+str(type(oldtile)))
                #     # search with url ? (if comment has changed)
                #     try:
                #         oldtile=db.session.query(models.Tile).filter_by(title=title,source={"name":name,"url":url,"connection":ConnectionPort,"variable":variable}).order_by(models.Tile.id.desc()).first()
                # => sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedFunction) operator does not exist: json = unknown
                # LINE 3: WHERE tiles.title = '001 ' AND tiles.source = '{"name": "001...
                #                                                     ^
                # HINT:  No operator matches the given name and argument types. You might need to add explicit type casts.
                #         oldtile=db.session.query(models.Tile).filter_by(title=title,source=jsonify(name=name,url=url,connection=ConnectionPort,variable=variable)).order_by(models.Tile.id.desc()).first()
                # TypeError: Object of type Response is not JSON serializable
                #     except :
                #         raise AttributeError
                
                logging.debug(str(i)+" tile type "+str(type(oldtile)))
                oldtileid=oldtile.id
                logging.warning(str(i)+" update old tile "+str(oldtileid))
                oldtile.tags=tags
                oldtile.source= {"name" : name,
                                 "connection" : ConnectionPort,
                                 "url" : url,
                                 "variable": variable}
                flag_modified(oldtile,"source")
                oldtile.pos_px_x= pos_px_x
                oldtile.pos_px_y= pos_px_y
                oldtile.IdLocation=IdLocation
                oldtileset.tiles.append(oldtile)
                db.session.commit()
            except AttributeError:
                # if not : insert at end of oldtileset.tiles ?
                newtile = models.Tile(title=title,
                                      comment=comment,
                                      tags=tags,
                                      source= {"name" : name,
                                               "connection" : ConnectionPort,
                                               "url" : url,
                                               "variable": variable
                                      },
                                      pos_px_x= pos_px_x,
                                      pos_px_y= pos_px_y,
                                      IdLocation=IdLocation,
                                      creation_date= creation_date)
                lasttile=db.session.query(models.Tile.id).order_by(models.Tile.id.desc()).first()
                if ( lasttile ):
                    newtile.id=lasttile.id+1
                else:
                    newtile.id=1
                db.session.add(newtile)
                db.session.commit()
                oldtileset.tiles.append(newtile)
                logging.warning(str(i)+" add tile "+str(newtile.id))
                db.session.commit()
            except Exception:
                logging.warning(str(i)+" Error tile ")
                traceback.print_exc(file=sys.stderr)
                
        
        session["is_client_active"]=True

        # Get back old connection if exists
        if (connectionbool and myform.manage_connection.data):
            message = '{"oldtilesetid":'+str(oldtileset.id)+',"oldsessionname":"'+session["sessionname"]+'"}'

            if (myform.manage_connection.data == "reNew"):
                return redirect(url_for(".addconnection",message=message))
            # elif (myform.manage_connection.data == "Edit"):
            #     return redirect(url_for(".editconnection",message=message))
            elif (myform.manage_connection.data == "Quit"):
                return redirect(url_for(".removeconnection",message=message))
            else:
                return redirect(url_for(".editsession",message=message))
            #TODO:
            # ("New","Create a new one."),
            # ("Save","Save the connection for reuse."),
            # ("Reload","Reload saved connection."),
        else:        
            message = '{"oldsessionname":"'+session["sessionname"]+'"}'
            return redirect(url_for(".editsession",message=message))
    
    return render_template("edittileset.html", title="Edit TileSet TiledViz", form=myform, message=message)

# # 
# def linkrandom(nbchar):
#     ALPHABET = "B6P8VbhZoGp9JYd0.uLCsAT4DX%F1xqIUSyQMniNgje5_~3crvlHR-7W2f!=kEtmazwKO$"
#     mystring=''.join(random.choice(ALPHABET) for i in range(nbchar)).encode('utf-8')
#     return mystring

# Build iframe with noVNC (in template/noVNC ?) inside a comeback html script to be abble to go back with new message
# Then kill connection link
@app.route('/vncconnection', methods=['GET', 'POST'])
def vncconnection():
    logging.warning("Enter in connection.")
    myflush()
    
    try:
        message=json.loads(request.args["message"])
    except json.decoder.JSONDecodeError as e:
        logging.error("message error ! "+str(e))
        logging.error("message : "+str(request.args["message"]))
        traceback.print_exc(file=sys.stderr)
        message=json.loads(request.args["message"].replace("'", '"'))

    idconnection=message["connectionid"]
    idtileset=message["oldtilesetid"]
    try:
        oldconnection=db.session.query(models.Connection).filter_by(id=idconnection).first()
    except:
        flash("This connection doesn't exist.")
        logging.error("This connection doesn't exist.")
        message=request.args["message"]
        return redirect(url_for(".edittileset",message=message))

    if ("username" in session):
        user_id=get_user_id("vncconnection",session["username"])
    else:
        flash("You are not connected. You must login before using a connection.")
        return redirect("/login")
    if ( not "connection"+str(idconnection) in session):
        flash("You don't have connection information in your personal cookie for this connection.")
        logging.error("You (user "+str(user_id)+") don't have connection information in your personal cookie for this connection : "+str(idconnection))
        message=request.args["message"]
        return redirect(url_for(".edittileset",message=message))
        
    vnctransfert=json.loads(session["connection"+str(idconnection)])
    logging.debug("With infos :"+str(vnctransfert))

    flaskaddr=os.getenv("flaskhost")
    logging.debug("Detected flask address :"+str(flaskaddr))
    
    callfunction=vnctransfert["callfunction"]
    if (oldconnection):
        if  (user_id != oldconnection.id_users) :
            flash("You can not access to this connection. You are not its owner.")
            owner=db.session.query(models.User).filter_by(id=oldconnection.id_users).name
            you=db.session.query(models.User).filter_by(id=user_id).name
            logging.error("You (user "+you+") can not access to this connection owned by user "+owner)
            message=request.args["message"]
            return redirect(url_for(".edittileset",message=message))

    # TODO : wait for connection PORT instead of 3s ?
    time.sleep(3)

    # Wait from TVSecure for connection PORT in DB
    db.session.refresh(oldconnection)
    connection_vnc=oldconnection.connection_vnc
    logging.warning("PORT VNC :"+str(connection_vnc)) 
    if (connection_vnc == 0):
        flash_msg="Error reading PORT VNC :"+str(connection_vnc)
        logging.error(flash_msg)
        flash(flash_msg)
        message=request.args["message"]
        return redirect(url_for(".edittileset",message=message))
    connection_vnc=connection_vnc+32768
    
    if ( request.method == 'POST'):
        message=json.JSONEncoder().encode(vnctransfert["args"])
        
        logging.warning("killconnection: "
                        +str(session["username"])+" ; "
                        +str(idtileset)+" ; "
                        +str(idconnection))
        myflush()
        
        out_nodes_json = os.path.join("/TiledViz/TVFiles", str(user_id), str(idconnection),"nodes.json")
        logging.warning("out_nodes_json after vncconnection.html :"+out_nodes_json)

        # Wait NbTimeAlive to get files from connection
        NbTimeAlive=20

        if ( not session["sessionname"] in  jsontransfert):
            jsontransfert[session["sessionname"]]={}
            
        count=0
        while True:
            time.sleep(timeAlive)
            if (count > NbTimeAlive):
                if ("TheJson" in jsontransfert[session["sessionname"]]):
                    del(jsontransfert[session["sessionname"]]["TheJson"])
                return redirect(url_for("."+callfunction,message=message))
            if ( os.path.exists( out_nodes_json ) ):
                try:
                    json_tiles_file=open(out_nodes_json)
                    jsontransfert[session["sessionname"]]["TheJson"]=json.loads(json_tiles_file.read())
                    json_tiles_file.close()
                    logging.warning("nodes.json read and OK "+out_nodes_json)
                    return redirect(url_for("."+callfunction,message=message))
                except Exception as err:
                    traceback.print_exc(file=sys.stderr)
                    strerror="Error from json "+out_nodes_json+" file from connection : "+str(err)
                    logging.error(strerror)
            else:
                logging.warning("Wait for "+out_nodes_json)
            count=count+1
                
    return render_template("vncconnection.html",
                           port=connection_vnc,
                           id=idconnection,
                           tsid=idtileset,
                           vncpassword=vnctransfert["vncpassword"],
                           session=session["sessionname"],
                           flaskaddr=flaskaddr)
    
@app.route('/addconnection', methods=["GET", "POST"])
def addconnection():
    
    myform = BuildConnectionsForm()()
    print('message=',str(request.args["message"]))
    message=json.loads(request.args["message"])
    logging.debug("ConnectionForm built."+str(message))
    
    if myform.validate_on_submit():
        logging.info("in addconnection")

        logging.info(str(session["username"])+" "+str(myform.host_address.data)+"  "+str(myform.auth_type.data)+"  "+str(myform.container.data))

        creation_date=datetime.datetime.now()
        user_id=get_user_id("addconnection",session["username"])

        # Test if a connection is already attached few seconds ago for the tileset :
        newtileset=db.session.query(models.TileSet).filter_by(id=message["oldtilesetid"]).one()

        if (type(newtileset.id_connections) != type(None)):
            logging.warning("New connection created :"+str(newtileset.id_connections))
            try:
                oldConnection=db.session.query(models.Connection).filter_by(id=newtileset.id_connections).one()
                olddate=oldConnection.creation_date
                if ((creation_date-olddate).seconds < 3):
                    return
            except:
                return
        
        if (myform.scheduler_file.data):
            scheduler_filename=myform.scheduler_file.data.filename
        else:
            scheduler_filename=""

        newConnection = models.Connection(host_address=myform.host_address.data,
                                          auth_type=myform.auth_type.data,
                                          container=myform.container.data,
                                          scheduler=myform.scheduler.data,
                                          scheduler_file=scheduler_filename,
                                          id_users=user_id,
                                          creation_date= creation_date)

        lastconnection=db.session.query(models.Connection.id).order_by(models.Connection.id.desc()).first()
        if ( lastconnection ):
            newConnection.id=lastconnection.id+1
        else:
            newConnection.id=1
        db.session.add(newConnection)
        db.session.commit()

        # We must add connection id in the tile_set
        newtileset.id_connections=newConnection.id
        db.session.commit()

        # TODO : Add subdir specific ?
        TSConfigjson={}
        ConnConfigjson={}
        # Build connection path
        user_path=os.path.join("/TiledViz/TVFiles",str(user_id))
        connectionpath=os.path.join(user_path,str(newConnection.id))
        # Create connection dir
        try:
            os.mkdir(user_path)
            logging.warning("Creation of connection path for config files : "+user_path)
        except FileExistsError:
            pass
        try:
            os.mkdir(connectionpath)
            logging.warning("Creation of connection path for config files : "+connectionpath)
        except FileExistsError:
            pass

        # Save config files from TileSet (placed in jsontransfer) and connection in this connectionpath
        TStmpName="tileset_"+str(newtileset.id)
        if ( TStmpName in jsontransfert):
            for FileS in jsontransfert[TStmpName]:
                tf = tempfile.NamedTemporaryFile(mode="w+b",dir=connectionpath,prefix="",delete=False)
                tf.write(jsontransfert[TStmpName][FileS])
                # TODO : Add dir ? 
                TSConfigjson[FileS]=tf.name
                tf.close()
            # for FileS in jsontransfert[TStmpName]:
            #     jsontransfert[TStmpName].pop(FileS)
            jsontransfert.pop(TStmpName)

        # Write config files for connection
        if (myform.configfiles.data):
            for FileS in myform.configfiles.data:
                tf = tempfile.NamedTemporaryFile(mode="w+b",dir=connectionpath,prefix="",delete=False)
                tf.write(FileS.read())
                # TODO : Add dir (in JOBPath on HPC machine) info for files ? 
                ConnConfigjson[FileS.filename]=tf.name
                tf.close() 

        # if (myform.configfiles.data):
        #     for FileS in myform.configfiles.data:
        #         logging.error("Config type file : %s " % (str(type(FileS))))
        #         outHandler.flush()
        #         if ( type(FileS) != type("AA") ):
        #             logging.error("Config file : %s " % (FileS))
        #             tf = tempfile.NamedTemporaryFile(mode="w+b",dir=connectionpath,prefix="",delete=False)
        #             tf.write(myform.configfiles.data[FileS].read())
        #             # TODO : Add dir (in JOBPath on HPC machine) info for files ? 
        #             ConnConfigjson[FileS]=tf.name
        #             tf.close()
        #         else:
        #             logging.warning("Config file : %s " % (FileS))
        #             outHandler.flush()

        # Save scheduler_file in connectionpath and tmp filename in ConnConfigjson
        if (myform.scheduler_file.data):
            logging.warning("Scheduler file : %s " % (str(myform.scheduler_file.data)))
            scheduler_file=myform.scheduler_file.data
            if ( scheduler_file != "" ):
                tf = tempfile.NamedTemporaryFile(mode="w+b",dir=connectionpath,prefix="",delete=False)
                tf.write(scheduler_file.read())
                ConnConfigjson[scheduler_file.filename]=tf.name
                tf.close()

        sTSConfigjson=str(TSConfigjson).replace("'", '"')
        logging.warning("Configuration files for TileSet %s : %s " % (newtileset.name,sTSConfigjson) )
        newtileset.config_files=json.loads(sTSConfigjson)

        sConnConfigjson=str(ConnConfigjson).replace("'", '"')
        logging.warning("Configuration files for connection %d : %s " % (newConnection.id,sConnConfigjson) )
        newConnection.config_files=json.loads(sConnConfigjson)
        db.session.commit()

        deb=(myform.debug.data & 1 | 0)
        
        passpath="/home/connect"+str(newConnection.id)+"/vncpassword"
        logging.warning("Go to vnc with path "+passpath)

        logging.warning("addconnection: "
                        +str(session["username"])+" ; "
                        +str(myform.host_address.data)+" ; "
                        +str(myform.auth_type.data)+" ; "
                        +str(myform.container.data)+" ; "
                        +str(myform.scheduler.data)+" ; "
                        +str(newtileset.id)+" ; "
                        +str(newConnection.id)+" ; "
                        +str(deb))
        myflush()

        #  Wait NbTimeAlive for TVSecure to get VNC view to put connection datas.
        NbTimeAlive = 40
        count=0
        while(True):
            if (count > NbTimeAlive):
                strerror="Connection has never been reach. Go back to TileSet."
                logging.error(strerror)
                flash(strerror)
                message = '{"oldtilesetid": "'+str(newtileset.id)+'"}'
                return redirect(url_for(".edittileset",message=message))
            count=count+1
            #logging.warning("addconnection count : "+str(count))
            
            # GET VNC password in 
            # security problem here if server is attacked ?
            time.sleep(timeAlive)
            #os.system("ls -la "+passpath)
            #sys.stdout.flush()
            if (os.path.isfile(passpath)):
                with open(passpath,'r') as f:
                    vncpassword=re.sub(r'\n',r'',f.read())
                f.close()
                logging.debug("and password : "+vncpassword)

                message = '{"oldtilesetid":'+str(newtileset.id)+',"connectionid":'+str(newConnection.id)+',"sessionname":"'+session["sessionname"]+'"}'
                session["connection"+str(newConnection.id)]=' {"callfunction":"edittileset",'+'"args":{"oldsessionname":"'+str(session["sessionname"])+'","oldtilesetid":"'+str(newtileset.id)+'"}, "vncpassword":"'+vncpassword+'"}'

                logging.warning("addconnection in session : "+str(session["connection"+str(newConnection.id)]))
                #TODO logging.debug
                myflush()
                return redirect(url_for(".vncconnection",message=message))
        
    return render_template("main_login.html", title="Add new Connection TiledViz", form=myform, message=message)

# Edit old Connection related to a tileset
@app.route('/editconnection', methods=["GET", "POST"])
def editconnection():
    logging.warning('editconnection message='+str(request.args["message"]))
    
    try:
        message=json.loads(request.args["message"])
    except json.decoder.JSONDecodeError as e:
        logging.error("message error ! "+str(e))
        logging.error("message : "+str(request.args["message"]))
        traceback.print_exc(file=sys.stderr)
        message=json.loads(request.args["message"].replace("'", '"'))
    
    oldtilesetid=message["oldtilesetid"]
    oldtileset=db.session.query(models.TileSet).filter_by(id=oldtilesetid).one()

    oldconnection=oldtileset.connection
    try:
        idconnection=oldconnection.id
    except:
        flash("This connection doesn't exist.")
        logging.error("This connection doesn't exist.")
        message=request.args["message"]
        return redirect(url_for(".edittileset",message=message))
        
    user_id=get_user_id("editconnection",session["username"])
    # Build connection path
    user_path=os.path.join("/TiledViz/TVFiles",str(user_id))
    connectionpath=os.path.join(user_path,str(oldconnection.id))


    if ( not "connection"+str(idconnection) in session):
        flash("You don't have connection information in your personal cookie for this connection.")
        logging.error("You (user "+str(user_id)+") don't have connection information in your personal cookie for this connection : "+str(idconnection))
        message=request.args["message"]
        return redirect(url_for(".edittileset",message=message))
          
    if ("direct" in message):
        del message["direct"]
        message=launch_connection(oldtileset,oldconnection,
                          oldconnection.host_address,
                          oldconnection.auth_type,
                          oldconnection.container,
                          oldconnection.scheduler)
        return redirect(url_for(".vncconnection",message=message))
        flash("Error direct connection to shell.")

        
    myform = BuildConnectionsForm(oldconnection)()
    logging.debug("ConnectionForm edit."+str(message))
    if myform.validate_on_submit():
        logging.info("in editconnection")
        
        logging.info(str(myform.host_address.data)+"  "+str(myform.auth_type.data)+"  "+str(myform.container.data))
        
        TSConfigjson={}
        
        # TODO :
        #  Test connection type in launch a form dedicated.

        # TODO : 
        #        rm old config files not overwitten if exists ?

        # detect/diff/update config files
        oldconnection_config_files=oldconnection.config_files

        if (myform.configfiles.data):
            for FileS in myform.configfiles.data:
                # data from form
                tf = tempfile.NamedTemporaryFile(mode="w+b",dir=connectionpath,prefix="",delete=False)
                tf.write(FileS.read())
                newfilename=tf.name
                tf.close()
                if (os.stat(tf.name).st_size > 0):
                    if (FileS.filename in oldconnection_config_files):
                        # Test file modified with same name
                        boolDiff=filecmp.cmp(f1=oldconnection_config_files[FileS.filename],f2=newfilename)
                        logging.warning("Diff with modified config file : "+str(boolDiff))
                        if (not boolDiff):
                            # rm old config files
                            strrm="rm -f "+oldconnection_config_files[FileS.filename]
                            logging.warning("Update old config file "+FileS.filename+" in editconnection.")
                            os.system(strrm)
                            oldconnection.config_files[FileS.filename]=newfilename
                            flag_modified(oldconnection,"config_files")
                            db.session.commit()
                        else :
                            # rm unused config files
                            strrm="rm -f "+newfilename
                            os.system(strrm)
                    else:
                        # new config file
                        oldconnection.config_files[FileS.filename]=newfilename
                        logging.warning("Add new config file "+FileS.filename+" in editconnection.")
                        flag_modified(oldconnection,"config_files")
                        db.session.commit()
                else :
                    # rm unused config files
                    strrm="rm -f "+newfilename
                    os.system(strrm)

        # detect/diff/update scheduler file
        if (myform.scheduler_file.data):
            oldconnection_scheduler_file=oldconnection.scheduler_file
            FileS=myform.scheduler_file.data
            tf = tempfile.NamedTemporaryFile(mode="w+b",dir=connectionpath,prefix="",delete=False)
            tf.write(FileS.read())
            newfilename=tf.name
            tf.close()
            if (os.stat(tf.name).st_size > 0):
                if (FileS.filename in oldconnection_config_files):
                    # Test scheduler_file modified with same name
                    boolDiff=filecmp.cmp(f1=oldconnection_config_files[FileS.filename],f2=newfilename)
                    logging.warning("Diff with modified scheduler file : "+str(boolDiff))
                    if (not boolDiff):
                        # rm old config files
                        strrm="rm -f "+oldconnection_config_files[FileS.filename]
                        logging.warning("Update old scheduler file "+FileS.filename+" in editconnection.")
                        os.system(strrm)
                        oldconnection.config_files[FileS.filename]=newfilename
                        flag_modified(oldconnection,"config_files")
                        db.session.commit()
                    else :
                        # rm unused config files
                        strrm="rm -f "+newfilename
                        os.system(strrm)
                else:
                    if (oldconnection_scheduler_file):
                        # rm old config files
                        strrm="rm -f "+oldconnection_config_files[oldconnection_scheduler_file]
                        logging.warning("Rename scheduler file from "+oldconnection_scheduler_file
                                        +" to "+FileS.filename+" in editconnection.")
                        os.system(strrm)
                    else:
                        logging.warning("Add scheduler file "+FileS.filename+" in editconnection.")
                    oldconnection.scheduler_file=FileS.filename
                    oldconnection.config_files[FileS.filename]=newfilename
                    flag_modified(oldconnection,"config_files")
                    db.session.commit()
            else :
                # rm unused config files
                strrm="rm -f "+newfilename
                os.system(strrm)

        message=launch_connection(oldtileset,oldconnection,
                                  myform.host_address.data,
                                  myform.auth_type.data,
                                  myform.container.data,
                                  myform.scheduler.data)
        return redirect(url_for(".vncconnection",message=message))

    return render_template("main_login.html", title="Edit Connection TiledViz", form=myform, message=message)


# Remove old Connection related to a tileset
@app.route('/removeconnection', methods=["GET", "POST"])
def removeconnection():
    logging.warning('removeconnection message='+str(request.args["message"]))
    
    try:
        message=json.loads(request.args["message"])
    except json.decoder.JSONDecodeError as e:
        logging.error("message error ! "+str(e))
        logging.error("message : "+str(request.args["message"]))
        traceback.print_exc(file=sys.stderr)
        message=json.loads(request.args["message"].replace("'", '"'))

    oldtilesetid=message["oldtilesetid"]
    oldtileset=db.session.query(models.TileSet).filter_by(id=oldtilesetid).one()

    oldconnection=oldtileset.connection
    try:
        idconnection=oldconnection.id
    except:
        flash("This connection doesn't exist.")
        logging.error("This connection doesn't exist.")
        message=request.args["message"]
        return redirect(url_for(".edittileset",message=message))
        
    user_id=get_user_id("removeconnection",session["username"])
    if ( not "connection"+str(idconnection) in session):
        flash("You don't have connection information in your personal cookie for this connection.")
        logging.error("You (user "+str(user_id)+") don't have connection information in your personal cookie for this connection : "+str(idconnection))
        message=request.args["message"]
        return redirect(url_for(".edittileset",message=message))

    remove_this_connection(oldtileset,idconnection,user_id)
    
    flash("Connection "+str(idconnection)+" for tileset "+oldtileset.name+" has been removed.")
    message=request.args["message"]
    return redirect(url_for(".edittileset",message=message))


# Call json editor on a structure           
# TODO : no more GET method to test ?
@app.route('/jsoneditor', methods=['GET', 'POST'])
def jsoneditor():
    #print("jsoneditor args : ",request.args)
    #     json_gziped=request.args["TheJson"]                            
    #     #print("type json_gziped :",type(json_gziped))
    #     TheJson=gzip.decompress(base64.b64decode(json_gziped)).decode('utf-8')
    #     callfunction=json.loads(request.args["callfunction"])
    TheJson=jsontransfert[session["sessionname"]]["TheJson"]
    callfunction=json.loads(jsontransfert[session["sessionname"]]["callfunction"])
    
    logging.debug("jsoneditor : "+str(callfunction))
    if ( request.method == 'POST'):
        message=callfunction["args"]
        TheJson=json.loads(request.form.get("submit"))
        OutJson=json.dumps(TheJson).replace("'", '"')
        #logging.debug("jsoneditor OutJson :"+OutJson)
        jsontransfert[session["sessionname"]]={"TheJson":TheJson}
        # message["TheJson"]=str(base64.b64encode(gzip.compress(OutJson.encode('utf-8'))))
        message=json.dumps(message) #.replace("'", '"')
        #logging.debug("jsoneditor message :"+str(message))

        return redirect(url_for("."+callfunction["function"],message=message))
    return render_template("jsoneditor.html",TheJson=TheJson)

# ====================================================================
# Grid/main page
@app.route('/grid', methods=['GET', 'POST'])
def show_grid():

    #logging.debug("Enter in show_grid: with session "+str(session))
    if (not 'is_client_active' in session):
        flash("You are not connected. You must login before using a grid.")
        return redirect("/login")
        
    if request.method == 'POST' and "new room" in request.form :
        psession = request.form['new room']
        # TODO: properly close the old socket, or remove it from the room 
        # (usefulness? it's only a testing tool at this point')
        logging.info("[!] Change session room to " + psession)
        session["sessionname"]=psession
        thesession = db.session.query(models.Session).filter_by(name=psession).scalar()
        project = session["projectname"]=thesession.project.name
    else: # GET
        if (session["is_client_active"]):
            try:
                cookieuser = {"username" : session["username"] }
            except:
                return redirect("/login")


        if (not "sessionname" in session or
            not "projectname" in session):
            flash("No project or session defined yet. Please chose one.")
            return redirect("/allsessions")

        psession = session["sessionname"]
        project = session["projectname"]
        logging.info("Into '/grid' with GET for session room to " + psession)

    try:
        part_nbr = str(len(room_dict[psession]))
        logging.debug(str(room_dict[psession]))
    except KeyError as e: # If the grid is the first to join the room, the "room_dict[session]" doesn't exist yet
        part_nbr = 0
        logging.info("first to join the room "+session["username"])
    
    try:
        logging.debug("Grid with session :"+str(session["projectname"])+" "+str(session["sessionname"])+" "+str(session["username"]))
    except :
        pass

    # Build Session
    ThisSession=db.session.query(models.Session).filter(models.Session.name == session["sessionname"]).first()
    
    # session["tilesetnames"]=[]
    # if (db.session.query(func.count(ThisSession.tile_sets)).scalar() > 0):
    ListAllTileSet_ThisSession=ThisSession.tile_sets
    session["tilesetnames"]=[ thistileset.name for thistileset in ListAllTileSet_ThisSession ]
    logging.warning("All TileSet for session "+str(session["sessionname"])+" : "+str(session["tilesetnames"]))

    # JsonSession={"info": {"SessionName" : sessionNAME,
    #               "ProjectName" : ThisSession.project.name,
    #               "Users" : list(set([ThisSession.project.user.name]+
    #                                   [SessionUser.name for SessionUser in ThisSession.users]))},
    #              "tilesets": [ {"name":thistileset.name,
    #                     "Dataset_path":thistileset.Dataset_path,
    #                     "tiles": [ {"id" : tile.id,
    #                                 "title" : tile.title,
    #                                 "comment": tile.comment,
    #                                 "source": tile.source,
    #                                 "tags": tile.tags
    #                     } for tile in thistileset.tiles ] }
    #                    for thistileset in ListAllTileSet_ThisSession ]
    # }
    # Need for saving session in a file ?
    # textSession=json.JSONEncoder().encode(JsonSession)    
    #logging.debug(textSession)
    
    # Main loop to build the grid :
    nbr_of_tiles=0

    # If connection ? Test tileset connection ok ??

    # (Temporary ?) build all tiles data vector
    global tiles_data
    tiles_data={}
    tiles_data["nodes"]=[]
    ts=0
    lts=len(ThisSession.tile_sets)
    while (ts < lts):
        thistileset=ThisSession.tile_sets[ts]
        nbtiles=len(thistileset.tiles)
        nbr_of_tiles = nbr_of_tiles + nbtiles
        tiledata=tvdb.encode_tileset(thistileset)
        tiles_data["nodes"]=tiles_data["nodes"]+tiledata
        ts=ts+1
        
    #logging.debug(str(tiles_data))    
    session["nbr_of_tiles"]=nbr_of_tiles
    logging.info("nbr_of_tiles="+str(session["nbr_of_tiles"]))    
    
    config["nbr_of_tiles"] = nbr_of_tiles

    tiles_data["config"] = config
    psgeom={}
    if (not session["is_client_active"]):
        try:
            psgeom=json.loads(session["geometry"])
            logging.warning("geom for passive client :"+str(psgeom)+" "+str(type(psgeom)))
        except:
            traceback.print_exc(file=sys.stderr)

    TheConfig=ThisSession.config;
    if (ThisSession.config is None):
        flash("Session {} does not have a valid configuration for grid.".format(session["sessionname"]))
        message = '{"sessionname":"'+session["sessionname"]+'"}'
        return redirect(url_for(".configsession",message=message))
    # if (TheConfig==""):
    #     config_default_file=open("app/static/js/config_default.json",'r')
    #     json_configs=json.load(config_default_file)
    #     config_default_file.close()
    #     TheConfig=json.JSONEncoder().encode(json_configs)
    logging.debug("config : "+str(TheConfig))

    try:
        lang=TheConfig["language"];
    except:
        lang="EN";

    #get actions files for each TS/connection
    lts=len(ThisSession.tile_sets)
    tiles_actions={}
    ts=0
    while (ts < lts):
 
        thistileset=ThisSession.tile_sets[ts]
        # Connection for this TS
        tsconnection=thistileset.connection

        if (type(tsconnection) != type(None) and
            len(thistileset.config_files) > 0):
            if ("connection"+str(tsconnection.id) in session):
                asaction=False
                if ( "config.tar" in thistileset.config_files ):
                    tar_config_file=tarfile.TarFile(name=thistileset.config_files["config.tar"],mode='r')
                    tar_config_file.list()
                    try:
                        actions_file=tar_config_file.extractfile("actions.json")
                        tiles_actions[thistileset.name]=json.loads(actions_file.read().decode('utf-8'))
                        asaction=True
                    except:
                        pass
                
                if ( "actions.json" in thistileset.config_files ):
                    actions_file=open(thistileset.config_files["actions.json"],'r')
                    tiles_actions[thistileset.name]=json.load(actions_file)
                    asaction=True
                if (asaction):
                    tiles_actions[thistileset.name]["action0"]=["get_new_nodes","system_update_alt"]
                    # Search kill_all_containers action to register it in session cookie for this connection:
                    if (session["is_client_active"]):
                        rekillid=re.compile(r'"killid"')
                        for actionid in tiles_actions[thistileset.name]:
                            if (tiles_actions[thistileset.name][actionid][0] == "kill_all_containers" and
                                not re.search(rekillid,session["connection"+str(tsconnection.id)])):
                                session["connection"+str(tsconnection.id)]=session["connection"+str(tsconnection.id)].replace(', "vncpassword"',', "killid":"'+actionid.replace("action","")+'", "vncpassword"')
                else:
                    tiles_actions[thistileset.name]={}
        else:
            tiles_actions[thistileset.name]={}
        ts=ts+1

    logging.warning("Global tile actions : "+str(tiles_actions))

    if ("colorTheme" in TheConfig["colors"]):
        colorTheme=TheConfig["colors"]["colorTheme"]
        logging.info("Color : "+str(colorTheme))
    else:
        colorTheme="dark"
        logging.info("Color always "+str(colorTheme))
    help_path="doc/user_doc_" + lang + "_" + colorTheme + ".html";
    logging.info("helpPath ="+str(help_path))

    return render_template("grid_template.html",
                           user=session["username"],
                           title="TiledViz on "+project,
                           project=project, 
                           session=psession,
                           description=str(ThisSession.description),
                           json_geom=psgeom,
                           participants=part_nbr,
                           is_client_active=session["is_client_active"],
                           json_data=tiles_data,
                           json_actions=tiles_actions,
                           json_config=TheConfig,
                           helpPath = help_path)

@socketio.on("save_Session")
def saveSession(cdata):
    croom=cdata["room"]
    logging.warning("[->] saveSession \"" + str(cdata["NewSuffix"]) + "\" with description \"" + str(cdata["NewDescription"]) + "\" in room " + str(croom))
    alltilesjson=json.loads(cdata["Session"].replace("'", '"'));
    save_session(str(session["sessionname"]),str(cdata["NewSuffix"]),str(cdata["NewDescription"]),alltilesjson)

@socketio.on("share_Selection")
def shareSelection(cdata):
    croom=cdata["room"]
    listSelectionIds=json.loads(cdata["Selection"]);
    logging.warning("[->] shareSelection " + str(len(listSelectionIds)) + " nodes in room " + str(croom))
    sdata = {"Selection":cdata["Selection"]}
    socketio.emit('receive_deploy_Selection', sdata,room=croom)

@socketio.on("deploy_Session")
def deploySession(cdata):
    croom=cdata["room"] # room is old session
    logging.warning("[->] deploySession NEW ROOM : '" + str(cdata["NewRoom"]) + "' from room " + str(croom))
    sdata = {"NewRoom":cdata["NewRoom"]}
    session["sessionname"]=cdata["NewRoom"];
    socketio.emit('receive_deploy_Session', sdata,room=croom) # change room for new session ?

@socketio.on("share_Config")
def shareConfig(cdata):
    croom=cdata["room"]
    logging.warning("[->] shareConfig in room " + str(croom))
    configJson=json.loads(cdata["Config"].replace("'", '"'));
    sdata = {"Config":configJson};
    socketio.emit('receive_deploy_Config', sdata,room=croom)
    
@socketio.on('move_tile')
def handle_click_event(cdata):
    global tiles_data
    croom = cdata["room"]
    logging.warning("[->] Click on tile " + str(cdata["id"]) + " in room " + str(croom))
    logging.info("[+] Position: (" + str(cdata["posX"]) + ", " + str(cdata["posY"])+ ")")

    session_id = request.sid
    sdata = {"id":cdata["id"],"posX":cdata["posX"], "posY":cdata["posY"], "session_id":session_id}

    socketio.emit('receive_move', sdata, room=croom )
    tileid=tiles_data["nodes"][int(cdata["id"])]["dbid"]
    logging.debug("move id = "+cdata["id"]+" db id = "+str(tileid))
    tile=db.session.query(models.Tile).filter_by(id=tileid).one()
    logging.debug("title = "+tile.title)
    logging.debug("old pos  = (%d,%d)" % (int(tile.pos_px_x),int(tile.pos_px_y)))
    tile.pos_px_x=int(cdata["posX"])
    tile.pos_px_y=int(cdata["posY"])
    logging.debug("new pos  = (%d,%d)" % (int(tile.pos_px_x),int(tile.pos_px_y)))
    db.session.commit()
    
    logging.info("[+] New position for tile " + cdata["id"] + " transmitted to " + str(len(room_dict[croom])) + " sockets")
    return [cdata["id"], 2, croom]


@socketio.on("click_Menu")
def MenuShare(cdata):
    croom=cdata["room"]
    logging.info("MenuShare :"+str(cdata))
    logging.warning("[->] Click on menu " + str(cdata["Menu"]) + " option icon " + str(cdata["optionButton"]) + " in room " + str(croom))

    sdata = {"Menu":cdata["Menu"], "optionNumber":cdata["optionNumber"], "optionButton":cdata["optionButton"]}
    socketio.emit('receive_Menu_click', sdata,room=croom)

@socketio.on("click")
def ClickShare(cdata):
    croom=cdata["room"]
    action=cdata["action"]
    logging.info(action+"Share :"+str(cdata))
    logging.warning("[->] Click on "+action+ " "+ str(cdata["id"]) + " in room " + str(croom))
    sdata = {"action":action,"id":cdata["id"]}
    socketio.emit('receive_click', sdata,room=croom)

@socketio.on("click_val")
def ClickShareVal(cdata):
    croom=cdata["room"]
    action=cdata["action"]
    logging.info(action+"Share with val :"+str(cdata))
    logging.warning("[->] Click on "+action+ " "+ str(cdata["id"]) + " with val " + str(cdata["val"]) + " in room " + str(croom))
    sdata = {"action":action,"id":cdata["id"],"val":cdata["val"]}
    socketio.emit('receive_click_val', sdata,room=croom)

@socketio.on("change_Opacity")
def changeOpacityShare(cdata):
    croom=cdata["room"]
    logging.info("changeOpacityShare :"+str(cdata))
    logging.warning("[->] Click on an opacity slider " + str(cdata["Id"]) + " in room " + str(croom))

    sdata = {"Id":cdata["Id"],"Opacity":cdata["Opacity"]}
    socketio.emit('receive_Force_Opacity', sdata,room=croom)

@socketio.on("add_Tag")
def addNewTagShare(cdata):
    croom=cdata["room"]
    logging.info("addNewTagShare :"+str(cdata))
    logging.warning("[->] Add a new tag " + str(cdata["NewTag"]) + " in room " + str(croom))

    sdata = {"NewTag":cdata["NewTag"]}
    socketio.emit('receive_Add_Tag', sdata,room=croom)

@socketio.on("color_Tag")
def addNewTagShare(cdata):
    croom=cdata["room"]
    logging.info("changeColorTagShare :"+str(cdata))
    logging.warning("[->] Change color for the tag " + str(cdata["OldTag"]) + " for " + str(cdata["TagColor"]) +" in room " + str(croom))

    sdata = {"OldTag":cdata["OldTag"],"TagColor":cdata["TagColor"]}
    socketio.emit('receive_Color_Tag', sdata,room=croom)

@socketio.on("action_click")
def ClickAction(cdata):
    if (session["is_client_active"]):
        croom=cdata["room"]
        action=cdata["action"]
        TS=cdata["TileSet"]
        selections=cdata["selections"]
        logging.info(action+" for TileSet "+TS)
        logging.warning("[->] Click on action "+action+ " "+ str(cdata["id"]) + " in room " + str(croom) + " for selection "+ str(selections))

        actionid=int(action.replace("action", ""))
        command=str(actionid)+","+selections
        
        oldtileset=db.session.query(models.TileSet).filter_by(name=TS).one()
        oldconnection=oldtileset.connection
        user_id=get_user_id("action_click",session["username"])

        if (not oldconnection):
            logging.error("[->] NO Connection : "+str(oldconnection)+" on tileset "+str(oldtileset)+" for user "+str(user_id))
            return
        
        if  (user_id != oldconnection.id_users or not session["is_client_active"]):
            logging.error("[->] Connection id : "+str(oldconnection.id_users)+" for user "+str(user_id)+"  and session active "+str(session["is_client_active"]))
            myflush()
            return
        
        logging.warning("actionid %d" % (actionid))
        myflush()
        if (actionid == 0):
            ThisSession=db.session.query(models.Session).filter(models.Session.name == session["sessionname"]).first()
            # save old nodes.json before get new
            out_nodes_json = os.path.join("/TiledViz/TVFiles", str(oldconnection.id_users), str(oldconnection.id),"nodes.json")
            mvDATE=datetime.datetime.now().isoformat().replace(":","-")
            save_nodes_json=out_nodes_json+"_"+mvDATE
            logging.warning("action 0 : Save old nodes.json in %s" % (save_nodes_json))
            myflush()
            os.system("mv "+out_nodes_json+" "+save_nodes_json)
            # selection must be all tileset
            command=str(actionid)+","+","
        logging.warning("action command %s" % (command))
        myflush()

        searchKillid=re.search(r'"killid":"\d+"',session["connection"+str(oldconnection.id)])
        killid=-1
        if (searchKillid):
            killid=int(searchKillid.group().replace('"killid":','').replace('"',''))
            if (actionid==killid):
                logging.warning("action %d : Find kill_all_containers action." % (actionid))
                command=str(actionid)+","+","
                
        logging.warning("action: "
                        +str(session["username"])+" ; "
                        +str(oldtileset.id)+" ; "
                        +str(oldconnection.id)+" ; "
                        +str(command))
        myflush()
        
        if (searchKillid):
            if (actionid==killid):
                time.sleep(timeAlive)                        
                logging.warning("action %d : Remove connection %d ." % (actionid,oldconnection.id))
                remove_this_connection(oldtileset,oldconnection.id,user_id)
            
        if (actionid == 0):
            try:
                logging.warning("Update nodes for session %s" % (session["sessionname"]))
                myflush()
                ThisSession=db.session.query(models.Session).filter(models.Session.name == session["sessionname"]).first()
                # action0 == get new nodes.json file
                time.sleep(timeAlive)
                
                # copy old nodes.json
                out_nodes_json = os.path.join("/TiledViz/TVFiles", str(oldconnection.id_users), str(oldconnection.id),"nodes.json") 
                #diff save_nodes_json out_nodes_json ?
                
                # Old tile set data
                with open(save_nodes_json) as save_json_tiles_file:
                    tiledata1=json.loads(save_json_tiles_file.read())
                    save_json_tiles_file.close()

                # Add old index => For oldtiledset.tiles ??
                itiledata1={"nodes":[]}; 
                for idx, tile in enumerate(tiledata1["nodes"]):
                    itiledata1["nodes"].append({"i":idx, "title":tile["title"]})

                # New tile set data
                count_exist_new_nodes=0
                not_loaded=True
                while(not_loaded):
                    try:
                        time.sleep(timeAlive)
                        with open(out_nodes_json) as json_tiles_file:
                            tiledata2=json.loads(json_tiles_file.read())
                            json_tiles_file.close()
                        not_loaded=False
                    except Exception as err:
                        count_exist_new_nodes=count_exist_new_nodes+1
                        NbIter=10
                        if ( count_exist_new_nodes > NbIter):
                            traceback.print_exc(file=sys.stderr)
                            strerror=str(err)
                            logging.error("After %d x %d s we still have this error :\n %s" % (NbIter, timeAlive,strerror))
                            return 
                        
                # sort Tiles data for old and new version of tileset
                sortdata1 = sorted(tiledata1["nodes"], key=lambda v: v["title"])
                isortdata1 = sorted(itiledata1["nodes"], key=lambda v: v["title"])
                sortdata2 = sorted(tiledata2["nodes"], key=lambda v: v["title"])

                connectionbool=True
                urlbool=False
                datapath=""
                creation_date=datetime.datetime.now()
                
                # DIFF sorted tiledata1 and tildedata2 and modify them in oldtiledset.tiles
                logging.warning("DIFF sorted tiledata1 and tildedata2 ")
                myflush()
                modtiles_data=[]
                for idx1, tile1 in enumerate(sortdata1):
                    found=False
                    for idx2, tile2 in enumerate(sortdata2):
                        if (tile1 == tile2):
                            del sortdata2[idx2]
                            logging.debug("OK equal tiles %d %d " % (idx1, idx2))
                            found=True
                            break
                        elif (tile1["url"] == tile2["url"]):
                            logging.debug("equal url modify tiles %d %d " % (idx1, idx2))
                            i=isortdata1[idx1]["i"]

                            title,name,comment,tags,variable,pos_px_x,pos_px_y,IdLocation,url,ConnectionPort = \
                                convertTile(tile2,oldtileset.name,connectionbool,urlbool,datapath)
                                
                            oldtileset.tiles[i].tags=tags
                            oldtileset.tiles[i].source= {"name" : name,
                                                         "connection" : ConnectionPort,
                                                         "url" : url,
                                                         "variable": variable}
                            flag_modified(oldtileset.tiles[i],"source")
                            
                            oldtileset.tiles[i].pos_px_x= pos_px_x
                            oldtileset.tiles[i].pos_px_y= pos_px_y
                            oldtileset.tiles[i].IdLocation=IdLocation
                            db.session.commit()
                            logging.debug("OK equal url modify tile")
                            
                            modtiles_data.append((i,tile2))
                            
                            del sortdata2[idx2]
                            found=True
                            break
                
                # emit receive_deploy_nodes
                sdata = {"id":cdata["id"], "modtiles_data":modtiles_data}
                logging.warning("receive_deploy_nodes data : "+str(sdata))
                myflush()

                socketio.emit('receive_deploy_nodes', sdata,room=croom)
            except Exception as err:
                traceback.print_exc(file=sys.stderr)
                strerror=str(err)
                logging.error(strerror)
                        
# Draw    
sidDraw=""
@socketio.on("drawBlob")
def drawBlobShare(cdata):
    sidDraw = request.sid
    croom=cdata["room"]
    logging.info("drawBlobShare :"+str(cdata))
    logging.warning("[->] Share image from draws with blob " + str(cdata["nodeId"]) + " in room " + str(croom))
    nbsend=cdata["nbsend"]
    # start send draw to all clients
    for csid in room_dict[croom]:
        if ( not csid == sidDraw ):
            socketio.emit('receive_draw_img', cdata,room=croom+str(csid))
            logging.info("Send draw_img signal to client "+croom+str(csid))

@socketio.on("uploadDraw")
def uploadDraw(cdata):
    croom=cdata["room"]
    #logging.info("Receive updloadDraw from client "+str(request.sid))
    for csid in room_dict[croom]:
        if ( not csid == sidDraw ):
            socketio.emit('receive_draw_part', cdata,room=croom+str(csid))
            #logging.info("Send draw part to client "+croom+str(csid)+" from "+str(cdata["offset"])+" to "+str(cdata["offsetEnd"]))

@socketio.on("modif_draws")
def ModifDraws(cdata):
    croom=cdata["room"]
    action=cdata["action"]
    logging.debug(action+" Share :"+str(cdata))
    logging.warning("[->] Modification of draw from "+str(cdata["nodeId"])+ " with "+action + " in room " + str(croom))
    sdata = {"nodeId":cdata["nodeId"]}
    socketio.emit('receive_'+action, sdata,room=croom)
    
# Connection
@socketio.on('connected_grid')#, namespace='/grid')
def config_client(cdata):
    logging.warning("[->] Socket connected to a grid")
    logging.info("[+] Project : " + str(cdata['project']))
    logging.info("[+] Session : " + str(cdata['session']))

    logging.warning("Receive "+str(cdata["user"])+str(cdata["project"])+str(cdata["session"]))
    croom = cdata['session'] # c[lient]room
    session["projectname"]=cdata['project']
    session["sessionname"]=cdata['session']
    join_room(croom)
    clients.append(request.sid)
    logging.debug(rooms()) # rooms() list the rooms for the socket
    #if not(croom in room_dict):
     #   room_dict.append(croom)
    # if room_dict.has_key(croom): # has_key is deprecated in python3
    if croom in room_dict:
        room_dict[croom].append(request.sid)
        logging.info("[+] " + croom + " : Now " + str(len(room_dict[croom])) + " sockets connected to the room")
    else:
        room_dict[croom] = [request.sid]
        if ("username" in session):
            logging.info("[+] " + croom + " : First client to join the room "+session["username"])
        else:
            logging.info("[+] " + croom + " : Anonymous client to join the room.")
    croomsid = cdata['session']+str(request.sid) # c[lient]room
    join_room(croomsid)
    room_dict[croomsid] = [request.sid]
    if ("username" in session):
        logging.info("[+] " + croomsid + " : Individual room "+session["username"])
    else:
        logging.info("[+] " + croomsid + " : Individual room for Anonymous client.")

    clean_rooms()
    logging.info("room_dict are : "+ str(room_dict) + " my rooms "+ str(croom)+ " and "+str(croomsid))

    sdata = {"part_nbr_update": str(len(room_dict[croom])-1)}
    socketio.emit("new_client", sdata, room=croom)
    return {"room":croom, "session_id":request.sid}

@socketio.on("disconnect")
def disconnect_socket():
    logging.warning("[<-] Socket disconnected")
    tmp_sid = request.sid
    for key in room_dict:
        if tmp_sid in room_dict[key]:
            room_dict[key].remove(tmp_sid)
            logging.info ("[-] " + key + " : Socket " + tmp_sid + " disconnected")
            sdata = {"part_nbr_update": str(len(room_dict[key])-1)}
            socketio.emit("new_client", sdata, room=key)
    return room_dict

def clean_rooms():
    try: 
        for key in room_dict:
            if (not room_dict[key]):
                room_dict.pop(key)
    except:
        time.sleep(2)
        clean_rooms()
        
@socketio.on("get_link")
def handle_invite_link_request(cdata):
    croom = cdata["session"]
    is_new_client_active = cdata["type"]
    if (is_new_client_active):
        client_type="active"
    else:
        client_type="passive"
        
    try:
        print (DEFAULT_URL)
    except:
        DEFAULT_URL = "0.0.0.0:5000"

    creation_date=datetime.datetime.now().isoformat()
    # Waiting for database to store: session to join, is_new_client_active, screen type, login of the host user
    #TODO : give only invited username (not owner username) 
    if (client_type=="active"):
        #TODO : save key and creation date
        key=tvdb.passrandom(10)
        sdata = {"link":"http://"+DEFAULT_URL+"/join/"+str(session["sessionname"])+"_"+client_type+"_"+session["username"]+"_"+str(creation_date)+"_"+str(key)}
    else:
        #client_type="passive"
        sdata = {"link":"http://"+DEFAULT_URL+"/join/"+str(session["sessionname"])+"_"+client_type+"_"+"Anonymous"+"_"+str(creation_date)+"_"+str(tvdb.passrandom(10))}

    socketio.emit("get_link_back" ,sdata,room=croom)

# ====================================================================
# Invite link management
@app.route("/join/<link>")
def handle_join_with_invite_link(link):
    logging.warning("Handle join with invite link : "+link)
    if "active" in link:
        new_client_type = "active"
        session["is_client_active"]=True
    elif "passive" in link:
        new_client_type = "passive"
        session["is_client_active"]=False
    else:
        new_client_type = "unknown"
        session["is_client_active"]=False
        logging.error("Going to handle_join_with_invite_link function with error link : '"+str(link)+"'. New client with unknown type.")
        return
    
    session["sessionname"] = link.split("_"+new_client_type+"_")[0]
    logging.warning("Find session :"+str(session["sessionname"]))
    if "passive" in link:
        auth = link.split("_"+new_client_type+"_")[1].split(".{")[0]
    else:
        auth = link.split("_"+new_client_type+"_")[1]
    logging.info("authent : "+str(auth))
    #TODO SECUR : Check invited username is login on if active user !!
    session["username"]=auth.split("_")[0]
    logging.info("username = "+str(session["username"]))
    date=auth.split("_")[1]
    logging.info("date = "+str(date))
    key=auth.split("_")[2]
    logging.info("security key :"+str(key))
    #TODO SECUR : test validity of the key
    
    #print("Session name :",session["sessionname"]," new_client_type :",str(new_client_type)," authent ",str(auth))
    ThisSession=db.session.query(models.Session).filter(models.Session.name == session["sessionname"]).first()
    #print("Session name :",session["sessionname"]," object :",str(ThisSession.name))
    try:
        session["projectname"]=ThisSession.project.name
    except:
        flash("Error with session "+session["sessionname"]+" .")
        return redirect(url_for(".index"))
        
    # TODO : test this comment ?
    # session["is_client_active"]=is_client_active
    if "passive" in link:
        str_my_geom="{"+link.split("_"+new_client_type+"_")[1].split(".{")[1]
        my_geom=str_my_geom.replace('{','{"').replace(',',',"').replace('=','":')
        logging.warning("str json my_geom "+str(my_geom))
        session["geometry"]=my_geom
    else:
        session["geometry"]='{}'
    return redirect('/grid')
    #return(redirect("/grid", project=room))
    #return ("pouet")

# ====================================================================
# Error management
@app.route('/404')
def not_found():
    return "Unknown page. Please modify your address."

# Proxy VNC
# Thank's to https://stackoverflow.com/posts/36601467/revisions
@app.route('/<path:dummy>')
def routevnc(path=None,dummy=None):
    is_noVNC=re.search(r''+"noVNC",dummy)
    if ( dummy == "favicon.ico" ):
        # logging.warning("proxy favicon : \n "+str(request.host_url))
        resp = requests.request(
            method=request.method,
            url=request.host_url,
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False)
    elif (is_noVNC) :
        #logging.debug("request : \n "+str(request))
        logging.debug("proxy noVNC path : \n "+str(path)+":"+str(dummy))
        logging.debug("routevnc : \n url "+str(request.host_url))
        # logging.error("routevnc : \n url "+str(request.host_url)+"\n method "+str(request.method).replace("\r","")+"\n header"+str(request.headers).replace("\r","")+"\n args :"+str(request.args).replace("\r",""))
        
        VNCurl="http://127.0.0.1/"
        logging.debug("Connect with url : "+VNCurl+dummy)
        newurl=request.url.replace(request.host_url, VNCurl)
        logging.debug("Replace url : "+newurl)
        
        logging.debug(dummy+" header :"+str(request.headers))
        resp = requests.request(
            method=request.method,
            url=newurl,
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False)
    else:
        logging.debug("proxy unknwon path : \n "+str(path)+":"+str(dummy)+"  "+str(request.host_url))
        resp = requests.request(
            method=request.method,
            url=request.host_url,
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]
    
    response = Response(resp.content, resp.status_code, headers)
    return response

