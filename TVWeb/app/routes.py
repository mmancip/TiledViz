# -*- coding: utf-8 -*-

# routes are defined here, then imported in __init__.py

from flask import render_template, flash, Markup, redirect, session, request, jsonify, make_response, url_for
from sqlalchemy.orm.session import make_transient
from sqlalchemy.orm.attributes import flag_modified
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

from app import app, socketio, db

from app.forms import RegisterForm, BuildLoginForm, BuildNewProjectForm, BuildAllProjectSessionForm, BuildOldProjectForm, BuildNewSessionForm, BuildTilesSetForm, BuildCopySessionForm, BuildOldTileSetForm, BuildConfigSessionForm, BuildTilesSetForm
#HomeForm, SettingsForm,

import app.models as models # DB management
import json, os, pprint
# import gzip,base64

import logging

from flask_socketio import emit, join_room, rooms

import werkzeug.exceptions
from werkzeug.utils import secure_filename

import sys,re,traceback
import datetime

sys.path.append(os.path.abspath('../TVDatabase'))
from TVDb import tvdb
tvdb.session=db.session

# TODO: Convert to use database ?
clients = [] # Array to store clients
room_dict = {} # Dict to store rooms (and sub-arrays for clients in each room)
cookie_persistence = False # Opt-in (TODO: better in config?)
config = {}
is_client_active = True
tiles_data={}
tiles_data["nodes"]=[]

jsontransfert={}

# Global functions : creation and copy DB elements

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
    newsession.id=db.session.query(models.Session.id).order_by(models.Session.id.desc()).first().id+1
    db.session.commit()
    copy_users_session(newsession,oldusers)
    db.session.commit()
        
    session["sessionname"]=str(sessionname)
    return newsession
    
# Define new TileSet
def create_newtileset(tilesetname, thesession, type_of_tiles, datapath, creation_date):
    newtileset = models.TileSet(name=tilesetname,
                                type_of_tiles = type_of_tiles,
                                Dataset_path = datapath,
                                creation_date=creation_date)
    
    exist=db.session.query(models.TileSet.id).filter_by(name=tilesetname).scalar() is not None

    if (not exist):
        # Last TileSet id +1
        newtileset.id=db.session.query(models.TileSet.id).order_by(models.TileSet.id.desc()).first().id+1
        db.session.commit()
        thesession.tile_sets.append(newtileset)
        db.session.commit()
    else:
        newtileset=db.session.query(models.TileSet).filter_by(name=tilesetname).one()
    return newtileset,exist

# Convert Tile fron json file structure to database object
def convertTile(Mynode,tilesetname,connectionbool,urlbool,datapath):
    url=Mynode["url"]

    # TODO : add connectionbool test
    ConnectionPort=0
    if (urlbool):
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

# Define new session
def save_session(oldsessionname, newsuffix, alltiles):
    creation_date=datetime.datetime.now()
    oldsession=db.session.query(models.Session).filter_by(name=oldsessionname).one()
    projectid=oldsession.id_projects
    # TODO : max length of Session.name (=80) ?
    # mais parent with date may be too long
    #=> notion of heritage for session and tilsets in DB    
    newsessionname=session["sessionname"]+'_'+newsuffix
    newsession = models.Session(name=newsessionname,
                                description=str(oldsession.description),
                                id_projects=projectid,
                                creation_date=creation_date)
    newsession.id=db.session.query(models.Session.id).order_by(models.Session.id.desc()).first().id+1
    db.session.commit()

    oldusers=oldsession.users
    for user in oldusers:
        newsession.users.append(user)
        db.session.commit()
                    
    db.session.commit()
    alltilesjson = alltiles["nodes"]
    for tileset in oldsession.tile_sets:
        # copy tilesets
        tilesetname=tileset.name

        urlbool=False
        connectionbool=False        
        if (tileset.type_of_tiles == "PICTURE" or tileset.type_of_tiles == "URL"):
            urlbool=True
        elif(tileset.type_of_tiles == "CONNECTION"):
            # Creation of the tiles and launch connection to remote machine.
            connectionbool=True
            
        datapath=tileset.Dataset_path
        tileset1,exist=create_newtileset(tilesetname+'_'+newsuffix, newsession,
                                   tileset.type_of_tiles, datapath, creation_date)
        if (not exist):
            try:
                db.session.add(tileset1)
                db.session.commit()
            except Exception:
                traceback.print_exc(file=sys.stderr)
        logging.debug("add tileset1 :"+tileset1.name)
        for tile in tileset.tiles:
            try :
                i=next(i for i, item in enumerate(alltilesjson) if (item["title"] == tile.title))
            except StopIteration:
                i=-1
            logging.debug("new tile :"+tile.title+" i "+str(i))
            if (i > -1):
                Mynode=alltilesjson[i]
                #print("Mynode :",str(Mynode)," type ",str(type(Mynode))," type tags ",str(type(Mynode["tags"])))
                title,name,comment,tags,variable,pos_px_x,pos_px_y,IdLocation,url,ConnectionPort = convertTile(Mynode,tilesetname,connectionbool,urlbool,datapath)
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
@app.route('/index')
@app.route('/home')
def index():
    try: 
        logging.warning(str(session))
        user = {"username" : session["username"] } # Test for cookie?
        project = session["projectname"]
        psession = session["sessionname"]
        is_client_active = session["is_client_active"]
    except KeyError as e: # If session["username"] does not exist (no cookie yet)
        logging.warning(e)
        user = {"username" : "Anonymous"} # If the cookie is not present
        project = "test"
        psession = "testsession"
        is_client_active = False
        session["username"]=user["username"]
        session["projectname"]=project
        session["sessionname"]=psession
        session["is_client_active"]=is_client_active
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
        
        exists = db.session.query(models.User.id).filter_by(name=session["username"]).scalar() is not None
        if exists:
            if (showexist):
                flash("Known user {}, remember_me={}".format(myform.username.data, myform.remember_me.data))
                showexist=False
                return render_template("main_login.html", title="TiledViz register", form=myform)
            logging.warning("username already exists.")
            hashPassword,hashSalt=db.session.query(models.User.password,models.User.salt).filter_by(name=session["username"]).one()
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
        session["username"] = myform.username.data
        try:
            User=db.session.query(models.User).filter_by(name=session["username"]).one()
        except:
            flash("Login rejected : '{}' for username does not exist.".format(session["username"]))
            return redirect("/login")
        exists = User.id is not None
        
        if exists:
            hashPassword=User.password
            hashSalt=User.salt
            testP=tvdb.testpassprotected(models.User,session["username"],myform.password.data,hashPassword,hashSalt)
            if (testP):
                logging.info('Correct password.')
                session["is_client_active"]=True
                if(myform.choice_project.data == "create"):
                    # Go to project page now
                    return redirect("/project")
                elif (myform.choice_project.data == "modify"):
                    return redirect("/oldsessions")
                else:
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

# Create new project
@app.route('/project', methods=["GET", "POST"])
def project():
    try:
        flash("Create new or use an old project for user {}".format(session["username"]))
        user=db.session.query(models.User.id).filter_by(name=session["username"]).one()
    except:
        flash("Project requested : User must login !")
        return redirect("/login")

    # All projects own by user
    projects = db.session.query(models.Project).filter_by(id_users=user.id)
    myprojects=[]
    for theproject in projects:
        ListsessionsTheproject=db.session.query(models.Session.name).filter_by(id_projects=theproject.id)
        allsessionsname=[ asessionTheproject.name for asessionTheproject in ListsessionsTheproject ]
        myprojects.append((str(theproject.id),theproject.name+" "+theproject.description+" with sessions : "+str(allsessionsname)))

    myform = BuildNewProjectForm(myprojects)()
    if myform.validate_on_submit():
        user=db.session.query(models.User.id).filter_by(name=session["username"]).one()
        logging.info("in project")
        
        # TODO : Add test if the user is authorized to use this project ? ==> NO only own project
        if (myform.chosen_project.data=="None"):
            project_id = db.session.query(models.Project.id).filter_by(name=myform.projectname.data).scalar()
        else:
            project_id = int(myform.chosen_project.data)
        exists = project_id is not None
        logging.debug("Project exists "+str(exists)+" id : "+str(project_id))
        if exists:
            if (myform.chosen_project.data == "None"):
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
        elif (myform.chosen_project.data == "None"):
            creation_date=datetime.datetime.now()
            project = models.Project(name=str(myform.projectname.data),
                                     creation_date=str(creation_date),
                                     id_users=user,
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
        flash("All projects and sessions for user {}".format(session["username"]))
        user=db.session.query(models.User.id).filter_by(name=session["username"]).one()
    else:
        flash("All projects and sessions : User must login !")
        return redirect("/login")

    if (session["username"] == "Anonymous"):
        return 'User not logged in <br>' + "<b><a href = '/login'>click here to log in.</a></b>"

    message='{"username": '+session["username"]+'}'
    logging.info("in allmysessions")
    
    # All projects own by user
    projects = db.session.query(models.Project).filter_by(id_users=user.id)
    # All sessions own of those projects
    mysessions=[]
    for theproject in projects:
        ListsessionsTheproject=db.session.query(models.Session.name).filter_by(id_projects=theproject.id)
        [ mysessions.append((theproject.name,ListsessionTheproject)) for ListsessionTheproject in ListsessionsTheproject ]

    listsessions=[]
    for thissessions in mysessions:
        #logging.debug("Build listsessions for project "+str(thissessions[0]))
        #logging.debug("List sessions for this project "+str(thissessions[1]))
        for thissession in thissessions[1]:
            listsessions.append((str(thissession),"Project "+str(thissessions[0])+" session "+str(thissession)+" : "+db.session.query(models.Session).filter_by(name=thissession).one().description))
            
    # All sessions this user has been invited to
    invite_sessions = db.session.query(models.Session.name).filter(models.Session.users.any(id=user.id)).all()

    for thissession in invite_sessions:
        logging.debug("Build listsessions for invite_session "+str(thissession.name))
        listsessions.append((str(thissession.name),"Invite session "+str(thissession.name)+" : "+db.session.query(models.Session).filter_by(name=thissession).one().description))

    myform = BuildAllProjectSessionForm(listsessions)()
    if myform.validate_on_submit():
        session["sessionname"]=myform.chosen_session.data
        logging.debug("Chosen session "+str(myform.chosen_session.data))
        logging.debug("Which is session "+str(db.session.query(models.Session.id).filter_by(name=session["sessionname"]).one()[0]))
        its_project_id=db.session.query(models.Session).filter_by(name=session["sessionname"]).one().id_projects
        session["projectname"]=db.session.query(models.Project).filter_by(id=its_project_id).one().name
        logging.debug("And have project id "+str(its_project_id)+" which is "+str(session["projectname"]))
        session["is_client_active"]=True
        if(myform.edit.data):
            logging.debug("go to edit old session : "+myform.chosen_session.data)
            message = '{"oldsessionname":"'+myform.chosen_session.data+'"}'
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
        newsession=create_newsession(myform.sessionname.data, myform.description.data, id_projects, myform.users)
        try:
            db.session.add(newsession)
            db.session.commit()
        except Exception:
            traceback.print_exc(file=sys.stderr)
            
            flash("Session with name {} already exists".format(myform.sessionname.data))
            return render_template("main_login.html", title="New session TiledViz", form=myform)

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
    oldsession = db.session.query(models.Session).filter_by(name=oldsessionname).one()    
    myform = BuildCopySessionForm(oldsession,edit=False)()
    if myform.validate_on_submit():
        logging.debug("copySessionForm : ")
        if myform.add_users.data:
            myform.users.append_entry()
            message = '{"oldsessionname":"'+session["sessionname"]+'"}'
            flash("New user avaible for user {} in session {}".format(session["username"], myform.sessionname.data))
            # TODO !! => send invitation to new users ?
            return render_template("main_login.html", title="Copy session TiledViz", form=myform)

        newsession=create_newsession(myform.sessionname.data, myform.description.data, oldsession.id_projects, myform.users)

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
            flash("You must change session name in session {}".format(myform.sessionname.data))
            return render_template("main_login.html", title="Copy session TiledViz", form=myform, message=message)
        if (myform.edit.data):
            #print("Go to editsession on"+newsession.name)
            message = '{"oldsessionname":"'+newsession.name+'"}'
            return redirect(url_for(".editsession",message=message))
        
        theaction=myform.tilesetaction.data
        
        try:    
            oldtilesetid=int(myform.tilesetchoice.data)
            message = '{"oldtilesetid":'+str(tilesetid)+'}'
        except :
            #traceback.print_exc(file=sys.stderr)
            if ( theaction != "search" and theaction != "copy" and not myform.edit.data):
                    logging.debug("You must check a tileset for this action {}".format(theaction))
                    flash("You must check a tileset for this action {}".format(theaction))
                    message = '{"oldsessionname":'+newsession.name+'}'
                    return redirect(url_for(".editsession",message=message))

        logging.debug("Action tileset : "+str(message)+" "+theaction)
        if myform.Session_config.data:
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
    oldsession = db.session.query(models.Session).filter_by(name=oldsessionname).one()    
    myform = BuildCopySessionForm(oldsession,edit=True)()
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
                thistileset=db.session.query(models.TileSet).filter_by(id=tilesetid).one()
                logging.debug("TileSet for remove : "+str(thistileset))
                oldsession.tile_sets.remove(thistileset)
                db.session.commit()
            except Exception:
                traceback.print_exc(file=sys.stderr)
                
                flash("Error remove tileset {}".format(db.session.query(models.TileSet).filter_by(id=tilesetid).one().name))
            message = '{"oldsessionname":"'+oldsessionname+'"}'
            return redirect(url_for(".editsession",message=message))
    return render_template("main_login.html", title="Edit session TiledViz", form=myform, message=message)

# List all old tilesets I am in
@app.route('/searchtileset', methods=["GET", "POST"])
def searchtileset():
# Old Tileset page
    message=json.loads(request.args["message"])
    oldsessionname=message["oldsessionname"]
    oldsession = db.session.query(models.Session).filter_by(name=oldsessionname).one()    

    querysessions= models.Session.query.filter(models.Session.users.any(name=session["username"])).all()
    logging.warning("querysessions = "+str(querysessions))

    listtilesets=[]
    for thissession in querysessions:
        #thissession=db.session.query(model.Session).filter_by(id=thissessionid[0])
        for tileset in thissession.tile_sets:
            elem=(str(tileset.id),str(tileset.name))
            if ( elem not in listtilesets ):
                listtilesets.append(elem)
    logging.debug("For user : "+session["username"]+" list old tilesets :"+str(listtilesets))
    flash("Search TileSet for user with name {} creation problem :".format(session["username"]))    
    myform = BuildOldTileSetForm(session["username"], listtilesets)()
    if myform.validate_on_submit():
        try:
            thisTS=db.session.query(models.TileSet).filter_by(id=myform.chosen_tileset.data[0]).one()
            oldsession.tile_sets.append(thisTS)
            db.session.commit()
        except:
            message = '{"oldsessionname":"'+session["sessionname"]+'"}'
            flash("Error : no TileSet Selected.")
            return redirect(url_for(".searchtileset",message=message))
        message = '{"oldsessionname":"'+oldsessionname+'"}'
        return redirect(url_for(".editsession",message=message))

    return render_template("main_login.html", title="Old projects TiledViz", form=myform)

# Config Session : give the json (depend of static/js/config_default.json)
@app.route('/configsession', methods=["GET", "POST"])
def configsession():
    message=json.loads(request.args["message"])

    sessionname=message["sessionname"]
    thesession = db.session.query(models.Session).filter_by(name=sessionname).one()

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

        # Detect how the data of tiles has been inserted :
        # if json structure is inserted with text area
        json_tiles = myform.json_tiles_text.data
        
        # Translate json text in structure
        jsonTileSet = json.loads(json_tiles)
        nbr_of_tiles = len(jsonTileSet["nodes"])
        logging.info("Number of tiles "+str(nbr_of_tiles))

        # json_tiles_file = FileField("File json object for tileset ")
        # json_file = open(json_tile_file).read()
    
        # openports_between_tiles = FieldList(IntegerField("port :",validators=[Optional()]),description="Open port in visualisation network",min_entries=2,max_entries=5) 
        # option_input_json_file = FileField(u'Json configuration input File', [wtforms.validators.regexp(u'json$')])
        # script_launch_file = FileField(u'bash script to launch each tile')
        
        urlbool=False
        connectionbool=False
        if (myform.type_of_tiles.data == "PICTURE" or myform.type_of_tiles.data == "URL"):
            urlbool=True
        elif(myform.type_of_tiles.data == "CONNECTION"):
            #TODO: TVSecure Creation of the tiles and launch connection to remote machine.
            connectionbool=True
            # Wait ? for connection ?
        
        #print(session["sessionname"])
        conn_session=db.session.query(models.Session).filter_by(name=session["sessionname"]).one()
        creation_date=datetime.datetime.now()
        tilesetname=myform.name.data
        datapath=str(myform.dataset_path.data)
        newtileset,exist=create_newtileset(tilesetname, conn_session, myform.type_of_tiles.data, datapath, creation_date)
        if (not exist):
            try:
                db.session.add(newtileset)
                db.session.commit()
            except Exception:
                traceback.print_exc(file=sys.stderr)
                
                flash("TileSet with name {} creation problem :".format(tilesetname))    
                return render_template("main_login.html", title="New TileSet TiledViz", form=myform, message=message)
        
        # Insert tiles into DB :
        tiles=[]
        #TODO We must add connection id in tiles"
        id_connection=-1
        if (connectionbool):
            #id_connection=newtileset.connection.id
            pass
        for i in range(nbr_of_tiles):
            Mynode=jsonTileSet["nodes"][i]

            title,name,comment,tags,variable,pos_px_x,pos_px_y,IdLocation,url,ConnectionPort = convertTile(Mynode,tilesetname,connectionbool,urlbool,datapath)
            
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
                                  # id_connections=id_connection,
            newtile.id=db.session.query(models.Tile.id).order_by(models.Tile.id.desc()).first().id+1
            db.session.add(newtile)
            db.session.commit()
            logging.warning(str(i)+" add tile "+str(newtile.id)+" "+str(newtile.title))
            
            newtileset.tiles.append(newtile)
            db.session.commit()


        session["is_client_active"]=True

        message = '{"oldsessionname":"'+session["sessionname"]+'"}'
        return redirect(url_for(".editsession",message=message))
    
    return render_template("main_login.html", title="New TileSet TiledViz", form=myform, message=message)


# Copy and edit an old TileSet
# Only copy old tiles and search for last (title, comment) in DB
@app.route('/copytileset', methods=["GET", "POST"])
def copytileset():
    message=json.loads(request.args["message"])
    logging.warning("copytileset : "+str(message))
    oldtilesetid=message["oldtilesetid"]
    oldtileset=db.session.query(models.TileSet).filter_by(id=oldtilesetid).one()
    myform = BuildTilesSetForm(oldtileset)()

    flash("Tileset {} copy for user {} in session {}".format(oldtileset.name,session["username"],session["sessionname"]))
    if myform.validate_on_submit():
        logging.info("in copy tileset")
        
        if (myform.name.data == oldtileset.name):
            message = '{"oldtilsetid":"'+str(oldtilesetid)+'"}'
            flash("You must change tilsetname to copy tileset {}".format(oldtileset.name))
            return render_template("main_login.html", title="Copy tileset TiledViz", form=myform, message=message)

        # Detect how the data of tiles has been inserted :
        # if json structure is inserted with testarea
        json_tiles = myform.json_tiles_text.data
        
        # Translate json text in structure
        jsonTileSet = json.loads(json_tiles)
        nbr_of_tiles = len(jsonTileSet["nodes"])
        logging.info("Number of tiles "+str(nbr_of_tiles))

        # json_tiles_file = FileField("File json object for tileset ")
        # json_file = open(json_file_name).read()
    
        # openports_between_tiles = FieldList(IntegerField("port :",validators=[Optional()]),description="Open port in visualisation network",min_entries=2,max_entries=5) 
        # option_input_json_file = FileField(u'Json configuration input File', [wtforms.validators.regexp(u'json$')])
        # script_launch_file = FileField(u'bash script to launch each tile')
        
        urlbool=False
        connectionbool=False
        if (myform.type_of_tiles.data == "PICTURE" or myform.type_of_tiles.data == "URL"):
            urlbool=True
        elif(myform.type_of_tiles.data == "CONNECTION"):
            # Creation of the tiles and launch connection to remote machine.
            connectionbool=True
        
        sessioncopy=db.session.query(models.Session).filter_by(name=session["sessionname"]).one()
        creation_date=datetime.datetime.now()
        tilesetname=myform.name.data
        newtileset, exist=create_newtileset(myform.name.data, sessioncopy, myform.type_of_tiles.data, myform.dataset_path.data, creation_date)
        if (not exist):
            try:
                db.session.add(newtileset)
                db.session.commit()
            except Exception:
                traceback.print_exc(file=sys.stderr)

                flash("TileSet creation with name {} problem :".format(tilesetname))    
                return render_template("main_login.html", title="New TileSet TiledViz", form=myform, message=message)


        newtileset.tiles=[]
        for i in range(nbr_of_tiles):
            Mynode=jsonTileSet["nodes"][i]

            urlbool=False
            datapath=""

            title,name,comment,tags,variable,pos_px_x,pos_px_y,IdLocation,url,ConnectionPort = convertTile(Mynode,tilesetname,connectionbool,urlbool,datapath)
            
            # search last tile with (title, comment) => in oldtileset ??
            try:
                oldtile=db.session.query(models.Tile).filter_by(title=title,comment=comment).order_by(models.Tile.id.desc()).first()
                if (oldtile is not None):
                    newtileset.tiles.append(oldtile)
                    logging.warning(str(i)+" add tile "+str(oldtile.id))
                else:
                    message = '{"oldtilsetid":"'+str(oldtilesetid)+'"}'
                    flash("You can't change tileset during copy for  {}".format(oldtileset.name))
                    return render_template("main_login.html", title="Copy tileset TiledViz", form=myform, message=message)

            except Exception:
                traceback.print_exc(file=sys.stderr)
                
                logging.error("Tile not found "+str(Mynode["title"])+" "+str(Mynode["comment"])+" "+str(Mynode["tags"]))

            db.session.commit()

        
        session["is_client_active"]=True
        message = '{"oldsessionname":"'+session["sessionname"]+'"}'
        return redirect(url_for(".editsession",message=message))
            
    return render_template("main_login.html", title="Copy TileSet TiledViz", form=myform, message=message)


# Edit old new TileSet
@app.route('/edittileset', methods=["GET", "POST"])
def edittileset():
    message=json.loads(request.args["message"])
    logging.warning("edittileset : "+str(message))

    oldtilesetid=message["oldtilesetid"]
    oldtileset=db.session.query(models.TileSet).filter_by(id=oldtilesetid).one()

    # Detect how the data of tileset has been inserted :        
    if ( session["sessionname"] in  jsontransfert):
        if ( "TheJson" in  jsontransfert[session["sessionname"]]):
            # if TheJson is already define in message, it has been edited by jsoneditor (call beside)
            TheJson=jsontransfert[session["sessionname"]]["TheJson"]
            jsontransfert[session["sessionname"]].pop("TheJson")
            try:
                json_tiles_text=json.JSONEncoder().encode(TheJson)
                #print("edittileset json_tiles_text) ",json_tiles_text)
                myform = BuildTilesSetForm(oldtileset,json_tiles_text)()
            except:
                traceback.print_exc(file=sys.stderr)
                flash("Error from json editor. Please try again.")
                return redirect(url_for(".edittileset",message=message))
        else:
            myform = BuildTilesSetForm(oldtileset)()
    else:
        myform = BuildTilesSetForm(oldtileset)()

    flash("Tileset {} edit for user {} in session {}".format(oldtileset.name,session["username"],session["sessionname"]))
    if myform.validate_on_submit():
        logging.info("in tileset")
        
        # Detect how the data of tiles has been inserted :
        # if json structure is inserted with testarea
        json_tiles = myform.json_tiles_text.data
        
        if myform.editjson.data:
            jsontransfert[session["sessionname"]]={"callfunction": '{"function":"edittileset",'+'"args":{"oldtilesetid":"'+str(oldtilesetid)+'"}}',
                                                   "TheJson":json_tiles}
            # json_gziped=base64.b64encode(gzip.compress(json_tiles.encode('utf-8')))
            #return redirect(url_for(".jsoneditor",callfunction=callfunction,TheJson=json_gziped))
            return redirect(url_for(".jsoneditor"))

        # Get a json file from in client ? 
        # print("Read the file ",myform.json_tiles_file.data)
        # if (myform.json_tiles_file.data == ""):
        # Translate json text in structure
        jsonTileSet = json.loads(json_tiles)
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

        
        # openports_between_tiles = FieldList(IntegerField("port :",validators=[Optional()]),description="Open port in visualisation network",min_entries=2,max_entries=5) 
        # option_input_json_file = FileField(u'Json configuration input File', [wtforms.validators.regexp(u'json$')])
        # script_launch_file = FileField(u'bash script to launch each tile')

        # Insert and create NEW tiles into TileSet or delete OLD tiles from TileSet.tiles list ?
        old_nbr_of_tiles=len(oldtileset.tiles)
        if (nbr_of_tiles > old_nbr_of_tiles):
            insertnewtiles=True
        elif (nbr_of_tiles < old_nbr_of_tiles):
            deletesometiles=True
            
        urlbool=False
        connectionbool=False
        if (myform.type_of_tiles.data == "PICTURE" or myform.type_of_tiles.data == "URL"):
            urlbool=True
        elif(myform.type_of_tiles.data == "CONNECTION"):
            # Creation of the tiles and launch connection to remote machine.
            connectionbool=True
        

        tilesetname=oldtileset.name
        
        creation_date=datetime.datetime.now()
        datapath=str(myform.dataset_path.data)

        oldtileset.datapath=datapath
        oldtileset.creation_date=creation_date
        db.session.commit()

        

        oldtileset.tiles=[]

        #TODO We must add connection id in tiles"
        id_connection=-1
        if (connectionbool):
            #id_connection=newtileset.connection.id
            pass
        for i in range(nbr_of_tiles):
            Mynode=jsonTileSet["nodes"][i]
            #print (str(i)+" "+str(Mynode))

            title,name,comment,tags,variable,pos_px_x,pos_px_y,IdLocation,url,ConnectionPort = convertTile(Mynode,tilesetname,connectionbool,urlbool,datapath)
            
            # Insert and create only NEW tiles into TileSet or edit OLD tiles from TileSet.tiles list ?
            # search if Tile already exists :
            try:
                # unicity for (title, comment, tags) (url ?)
                oldtile=db.session.query(models.Tile).filter_by(title=title,comment=comment).order_by(models.Tile.id.desc()).first()
                if (type(oldtile) == "NoneType"):
                    # search with url ? (if comment has changed)
                    oldtile=db.session.query(models.Tile).filter_by(title=title,source={"name":name,"url":url,"connection":ConnectionPort,"variable":variable}).order_by(models.Tile.id.desc()).first()
                oldtileid=oldtile.id
                logging.warning(str(i)+" Modify old tile "+str(oldtileid))
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
            except Exception:
                traceback.print_exc(file=sys.stderr)
                
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
                newtile.id=db.session.query(models.Tile.id).order_by(models.Tile.id.desc()).first().id+1
                db.session.add(newtile)
                db.session.commit()
                oldtileset.tiles.append(newtile)
                logging.warning(str(i)+" add tile "+str(newtile.id))
                # id_connections=id_connection,
                db.session.commit()
        
        session["is_client_active"]=True
        message = '{"oldsessionname":"'+session["sessionname"]+'"}'
        return redirect(url_for(".editsession",message=message))
        #return redirect("/grid")
        
        # json_tiles_file = FileField("File json object for tileset ")
    # json_file = open(json_file_name).read()
    
    # openports_between_tiles = FieldList(IntegerField("port :",validators=[Optional()]),description="Open port in visualisation network",min_entries=2,max_entries=5) 
    # option_input_json_file = FileField(u'Json configuration input File', [wtforms.validators.regexp(u'json$')])
    # script_launch_file = FileField(u'bash script to launch each tile')
    
    return render_template("main_login.html", title="Edit TileSet TiledViz", form=myform, message=message)

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
        # print("message before redirect :",str(message))
        #print("request ",request.form.get("submit"))
        TheJson=json.loads(request.form.get("submit"))
        OutJson=json.dumps(TheJson).replace("'", '"')
        #print("message OutJson :",OutJson)
        jsontransfert[session["sessionname"]]={"TheJson":TheJson}
        # message["TheJson"]=str(base64.b64encode(gzip.compress(OutJson.encode('utf-8'))))
        #print("message json :",message)
        message=json.dumps(message) #.replace("'", '"')
        #print("message str :",message)
        return redirect(url_for("."+callfunction["function"],message=message))
    return render_template("jsoneditor.html",TheJson=TheJson)

# ====================================================================
# Grid/main page
@app.route('/grid', methods=['GET', 'POST'])
def show_grid():
    #user = "Anonymous", project = "test", psession = "stest", is_client_active = True
    is_client_active=session["is_client_active"]
    if request.method == 'POST' and "new room" in request.form :
        psession = request.form['new room']
        # TODO: properly close the old socket, or remove it from the room 
        # (usefulness? it's only a testing tool at this point')
        logging.info("[!] Change session room to " + psession)
        session["sessionname"]=psession
        thesession = db.session.query(models.Session).filter_by(name=psession).one()
        project = session["projectname"]=thesession.project.name
    else: # GET
        if (is_client_active):
            try:
                cookieuser = {"username" : session["username"] }
            except:
                return redirect("/login")


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
        logging.debug("Grid with session :"+str(session["projectname"])+" "+srt(session["sessionname"])+" "+str(session["username"]))
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
    for thistileset in ThisSession.tile_sets:
        nbtiles=len(thistileset.tiles)
        nbr_of_tiles = nbr_of_tiles + nbtiles
        tiledata=tvdb.encode_tileset(thistileset)
        tiles_data["nodes"]=tiles_data["nodes"]+tiledata
        
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
    logging.debug("config : "+str(ThisSession.config))
    if (ThisSession.config is None):
        flash("Session {} does not have a valid configuration for grid.".format(session["sessionname"]))
        message = '{"sessionname":"'+session["sessionname"]+'"}'
        return redirect(url_for(".configsession",message=message))

    try:
        lang=TheConfig["language"];
    except:
        lang="EN";

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
                           json_geom=psgeom,
                           participants=part_nbr,
                           is_client_active=is_client_active,
                           json_data=tiles_data,
                           json_config=json.dumps(TheConfig),
                           helpPath = help_path)

@socketio.on("save_Session")
def saveSession(cdata):
    croom=cdata["room"]
    logging.warning("[->] saveSession " + str(cdata["NewSuffix"]) + " in room " + str(croom))
    alltilesjson=json.loads(cdata["Session"].replace("'", '"'));
    save_session(str(session["sessionname"]),str(cdata["NewSuffix"]),alltilesjson)

@socketio.on("deploy_Session")
def deploySession(cdata):
    croom=cdata["room"] # room is old session
    logging.warning("[->] deploySession NEW ROOM : '" + str(cdata["NewRoom"]) + "' from room " + str(croom))
    sdata = {"NewRoom":cdata["NewRoom"]}
    session["sessionname"]=cdata["NewRoom"];
    socketio.emit('receive_deploy_Session', sdata,room=croom) # change room for new session ?

@socketio.on("save_Config")
def saveSession(cdata):
    croom=cdata["room"]
    logging.warning("[->] saveConfig in room " + str(croom))
    configJson=json.loads(cdata["Config"].replace("'", '"'));
    #save_config(str(session["sessionname"]),str(cdata["NewSuffix"]),configjson)
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
    logging.warning("[->] Click on "+action+ " "+ str(action) + " in room " + str(croom))
    sdata = {"action":action,"id":cdata["id"]}
    socketio.emit('receive_click', sdata,room=croom)

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
        logging.info("[+] " + croom + " : First client to join the room "+session["username"])
    croomsid = cdata['session']+str(request.sid) # c[lient]room
    join_room(croomsid)
    room_dict[croomsid] = [request.sid]
    logging.info("[+] " + croomsid + " : Individual room "+session["username"])
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

    return "no socket found !"

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
    logging.warning(link)
    if "active" in link:
        new_client_type = "active"
        is_client_active=True
    elif "passive" in link:
        new_client_type = "passive"
        is_client_active=False
    session["sessionname"] = link.split("_"+new_client_type+"_")[0]
    logging.warning("Find session :"+str(session["sessionname"]))
    if "passive" in link:
        auth = link.split("_"+new_client_type+"_")[1].split(".{")[0]
    else:
        auth = link.split("_"+new_client_type+"_")[1]
    logging.info("authent : "+str(auth))
    #TODO : Check invited username is login on if active user !!
    session["username"]=auth.split("_")[0]
    logging.info("username = "+str(session["username"]))
    date=auth.split("_")[1]
    logging.info("date = "+str(date))
    key=auth.split("_")[2]
    logging.info("security key :"+str(key))
    #TODO : test validity of the key
    
    #print("Session name :",session["sessionname"]," new_client_type :",str(new_client_type)," authent ",str(auth))
    ThisSession=db.session.query(models.Session).filter(models.Session.name == session["sessionname"]).first()
    #print("Session name :",session["sessionname"]," object :",str(ThisSession.name))
    try:
        session["projectname"]=ThisSession.project.name
    except:
        flash("Error with session "+session["sessionname"]+" .")
        return redirect(url_for(".index"))
        
    session["is_client_active"]=is_client_active
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
    return "please try again"
