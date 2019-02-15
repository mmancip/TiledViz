# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
import wtforms
from wtforms import RadioField, SelectField, StringField, PasswordField, BooleanField, SubmitField, IntegerField, TextAreaField, SelectMultipleField, FieldList, FileField
from wtforms.validators import InputRequired, Email, Optional, EqualTo

import os,sys
sys.path.append(os.path.abspath('../TVDatabase'))
from TVDb import tvdb

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired()])
    email = StringField("E-mail adress", validators=[InputRequired(), Email()])
    compagny = StringField("Compagny name", validators=[InputRequired()])
    manager = StringField("Manager name", validators=[InputRequired()])
    password = PasswordField("Password", validators=[
        InputRequired(),
        EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField("Confirm password", validators=[InputRequired()])
    remember_me = BooleanField("Remember me")
    choice_project = RadioField("About the project :",choices=[("create","Create a new one ?"),
                                                               ("connect","Connect to an existing one ?")],
                                default="connect")
    submit = SubmitField("Sign In")


def BuildLoginForm(session):
    class LoginForm(FlaskForm):
        pass
    LoginForm.newuser = BooleanField("Register new user ?")
    LoginForm.username = StringField("Username", default=session["username"],validators=[InputRequired()])
    LoginForm.password = PasswordField("Password", validators=[InputRequired()])
    LoginForm.remember_me = BooleanField("Remember me")
    LoginForm.choice_project = RadioField(description="Action with the project :",choices=[("create","Create a new one ?"),
                                                               ("connect","Connect to an existing one ?")],
                                default="connect")
    LoginForm.submit = SubmitField("Next step")
    return LoginForm

def BuildNewProjectForm(listprojects):
    class NewProjectForm(FlaskForm):
        pass
    NewProjectForm.projectname = StringField("New Project name", validators=[Optional()])
    NewProjectForm.description = StringField("Description of this project", validators=[Optional()])
    NewProjectForm.chosen_project=RadioField(description='Or choose one of your old projects in this list (with its sessions) :', validators=[Optional()],choices=listprojects)
    NewProjectForm.action_sessions = RadioField(description="Action with the sessions of this project :",default="create",
                                 choices=[("use","Use an existing session for the grid"),
                                          ("modify","modify an existing session"),
                                          ("create","Create new session")],
                                 validators=[Optional()])
    NewProjectForm.submit = SubmitField("Next step")
    return NewProjectForm

def BuildAllProjectSessionForm(listsessions):
    class AllProjectSessionForm(FlaskForm):
        pass
    
    AllProjectSessionForm.chosen_session=RadioField(description='List all you own project / sessions and all your invite sessions :',choices=listsessions)
    AllProjectSessionForm.edit = SubmitField("Edit session before grid")
    AllProjectSessionForm.submit = SubmitField("Next step")
    return AllProjectSessionForm

def BuildOldProjectForm(thisproject,listsessions):
    class OldProjectForm(FlaskForm):
        pass
    
    OldProjectForm.projectname=StringField(label="Project name", default=thisproject["name"],validators=[Optional()])
    OldProjectForm.description=StringField(label="Description of this project", default=thisproject["description"],validators=[Optional()])
    OldProjectForm.from_session = RadioField(label='Action on session',
                                             description='Choose which action with old session you want :',
                                             choices=[("use","Use a session"),
                                                      ("edit","Edit a session"),
                                                      ("copy","Duplicate a session")],
                                             default='use',
                                             validators=[InputRequired()])
    OldProjectForm.chosen_session=RadioField(label='List of sessions for project '+thisproject["name"]+' :',choices=listsessions)
    OldProjectForm.submit = SubmitField("Next step")
    return OldProjectForm

def BuildNewSessionForm():
    class NewSessionForm(FlaskForm):
        pass
    NewSessionForm.sessionname = StringField("Session name", validators=[InputRequired()])
    NewSessionForm.description = StringField("Description of this session", validators=[InputRequired()])
    NewSessionForm.users = FieldList(description="Others users",unbound_field=StringField("user", validators=[Optional()]),min_entries=5,max_entries=10)
    NewSessionForm.add_users = SubmitField('Add more users')
    NewSessionForm.Session_config = SubmitField("Edit configuration of the session")
    NewSessionForm.submit = SubmitField("Next step")
    return NewSessionForm

def BuildCopySessionForm(oldsession=None,edit=True):
    class copySessionForm(FlaskForm):
        pass
    copySessionForm.sessionname = StringField("New session name", default=oldsession.name, validators=[InputRequired()])
    copySessionForm.description = StringField("Description of this session", default=oldsession.description, validators=[InputRequired()])
    ListAllTileSet_ThisSession=[ (str(thistileset.id), thistileset.name) for thistileset in oldsession.tile_sets]
    if (len(ListAllTileSet_ThisSession) > 0):
        copySessionForm.tilesetchoice = RadioField(label='listtilesets',
                                                   description='List all tilesets for this session',
                                                   choices=ListAllTileSet_ThisSession,
                                                   default=ListAllTileSet_ThisSession[0][0],
                                                   validators=[Optional()])
        
        copySessionForm.edit = SubmitField("Edit selected tileset.")
        if edit:
            copySessionForm.tilesetaction = RadioField(label='tilesetaction',
                                                       description='Choose to create and add a new tileset or just use all existing ones.',
                                                       choices=[("create","Add a new tileset."),
                                                                ("copy","Copy and edit an old tileset into a new one."),
                                                                ("search","Search another tileset for Session."),
                                                                ("remove","Remove an old tileset in Session."),
                                                                ("useold","Use existing tilesets and go to grid.")],
                                                       default='useold',
                                                       validators=[Optional()])
        else:
            copySessionForm.tilesetaction = RadioField(label='tilesetaction',
                                                       description='Choose to create and add a new tileset or just use all existing ones.',
                                                       choices=[("create","Add a new tileset."),
                                                                ("copy","Copy and edit an old tileset into a new one."),
                                                                ("search","Search another tileset for Session.")],
                                                       default='search',
                                                       validators=[Optional()])
            
        ListAllUsers_ThisSession=[ thisuser.name for thisuser in oldsession.users]
        copySessionForm.users = FieldList(description="Others users",
                                          unbound_field=StringField("user", validators=[Optional()]),
                                          default=ListAllUsers_ThisSession,
                                          min_entries=5,max_entries=10)
    else:
        if edit:
            copySessionForm.tilesetaction = RadioField(label='tilesetaction',
                                                       description='No old tilesets. Create a first tileset.',
                                                       choices=[("create","Add a new tileset."),
                                                                ("search","Search another tileset for Session.")],
                                                       default='create',
                                                       validators=[Optional()])
        ListAllUsers_ThisSession=[ thisuser.name for thisuser in oldsession.users]
        copySessionForm.users = FieldList(description="Others users",
                                          unbound_field=StringField("user", validators=[Optional()]),
                                          default=ListAllUsers_ThisSession,
                                          min_entries=5,max_entries=10)
    copySessionForm.Session_config = SubmitField("Edit configuration of the session")
    copySessionForm.add_users = SubmitField('Add more users')
    copySessionForm.submit = SubmitField("Next step")
    return copySessionForm

def BuildOldTileSetForm(username,listtilesets):
    class OldTileSetForm(FlaskForm):
        pass
    
    OldTileSetForm.chosen_tileset=RadioField(label='TileSetChoice',
                                             description='List of Tileset for user '+username+' :',
                                             choices=listtilesets,
                                             default=listtilesets[0][0],
                                             validators=[Optional()])
    OldTileSetForm.submit = SubmitField("Next step")
    return OldTileSetForm

def BuildConfigSessionForm(oldConfig,json_configs_text):
    class ConfigForm(FlaskForm):
        pass
    ConfigForm.jsonConfig={}
    #print("BuildConfigSessionForm :",oldConfig)
    ConfigForm.json_config_text = TextAreaField("Past json object for configuration of Session ",
                                                default=json_configs_text,
                                                validators=[Optional()])
    ConfigForm.editjson = SubmitField("Use Json editor for this configuration.")
    ConfigForm.submit = SubmitField("Next step")
    return ConfigForm

def BuildTilesSetForm(oldtileset=None,json_tiles_text=None):
    class TilesSetForm(FlaskForm):
        pass
    if (oldtileset==None):
        name=""
        dataset_path=""
        type_of_tiles="PICTURE"
        json_tiles_text=""        
    else:
        name=oldtileset.name
        dataset_path=oldtileset.Dataset_path
        type_of_tiles=oldtileset.type_of_tiles
        #json transformation :
        if (json_tiles_text==None):
            json_tiles_text=tvdb.decode_tileset(oldtileset)
        
    TilesSetForm.name = StringField("Tiles Set name", default=name, validators=[InputRequired()])
    TilesSetForm.dataset_path = StringField("Path or main URL of dataset", default=dataset_path, validators=[InputRequired()])
    TilesSetForm.type_of_tiles = RadioField(label='Type of the tiles',
                            description='Connection with a VM, a picture, a web page.',
                            choices=[("PICTURE","a set of pictures on the web or locally"),
                                     ("URL","a set of web links in html"),
                                     ("CONNECTION","Use a connection to a remote machine")
                                     ],
                            default=type_of_tiles,
                            validators=[Optional()])
    TilesSetForm.json_tiles_text = TextAreaField("Past json object for tileset ",default=json_tiles_text,
                    validators=[Optional()])
    # TilesSetForm.json_tiles_file = FileField("File json object for tileset ",
    #                 validators=[Optional()])
    TilesSetForm.editjson = SubmitField("Use Json editor for this tileset.")
    
    TilesSetForm.openports_between_tiles = FieldList(IntegerField("port :",validators=[Optional()]),description="Open port in visualisation network",min_entries=2,max_entries=5) 
    # TilesSetForm.option_input_json_file = FileField(u'Json configuration input File',
    #                 validators=[Optional(), wtforms.validators.regexp(u'json$')])
    # TilesSetForm.script_launch_file = FileField(u'bash script to launch each tile',
    #                 validators=[Optional()])
    
    TilesSetForm.submit = SubmitField("Next step")

    return TilesSetForm


class RequestInvitLinks(FlaskForm):
    name = StringField("Tiles Set name", validators=[InputRequired()])
    sessionname = StringField("Project name", validators=[InputRequired()])

# class HomeForm(FlaskForm):
#     gotologin = SubmitField("Go to login page")

# class SettingsForm(FlaskForm):
#     nbr_of_tiles = IntegerField("Number of tiles", validators=[InputRequired()])
#     save = SubmitField("Go to grid")

