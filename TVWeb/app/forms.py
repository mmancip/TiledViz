# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm, recaptcha
from flask_wtf.recaptcha import RecaptchaField
import wtforms
from wtforms import RadioField, SelectField, StringField, PasswordField, BooleanField, SubmitField, IntegerField, TextAreaField, SelectMultipleField, FieldList, FileField, MultipleFileField, widgets
from wtforms.fields.html5 import SearchField
from wtforms.widgets import core, html5
from wtforms.validators import InputRequired, Email, Optional, EqualTo

import markupsafe

import os,sys
sys.path.append(os.path.abspath('../TVDatabase'))
from TVDb import tvdb


# From wtforms/widgets/core.py    
class mySelect(object):
    """
    Renders a select field.

    If `multiple` is True, then the `size` property should be specified on
    rendering to make the field useful.

    The field must provide an `iter_choices()` method which the widget will
    call on rendering; this method must yield tuples of
    `(value, label, selected)`.
    """
    def __init__(self, multiple=False):
        self.multiple = multiple

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        if self.multiple:
            kwargs['multiple'] = True
        if 'required' not in kwargs and 'required' in getattr(field, 'flags', []):
            kwargs['required'] = True

        suggestion_list=[]
        for val, label, selected in field.iter_choices():
            suggestion_list.append(val)
            suggestion_list.append(label)
        html = ['<select %s style="width:1300px; font-family: monospace;">' % core.html_params(name=field.name, **kwargs)]
                
        for val, label, selected in field.iter_choices():
            html.append(self.render_option(val, label, selected))
        html.append('</select>')

        html.append('</br><div id=search_'+field.id+'><label for=filter>Search in all your list :&emsp;</label>')
        html.append('<input id=filter_'+field.id+' type=text class="ui-autocomplete-input" autocomplete="off" style="width:1000px;" >&emsp;')
        html.append('<button class="btn btn-default" type="button" id="Valid_'+field.id+'">Go</button>')
        html.append('</div>')
        html.append('<script type="text/javascript">\n')
        html.append('  var suggestion_list'+field.id+'='+str(suggestion_list)+';\n')
        html.append('  $("#search_'+field.id+'").off("autocompleteselect").on( "autocompleteselect", \n')
        html.append('     function( event, ui ) {\n')
        html.append('          document.getElementById("filter_'+field.id+'").value = ui.item.value})\n')
        html.append('     .on("keypress", function( e ) {\n')
        html.append('       if (e.which == 13 ) { \n')
        html.append('          var searchval=$("#filter_'+field.id+'").val().toLowerCase();\n     var ioption=0;\n')
        html.append('          for (var sugesstr in suggestion_list'+field.id+') {\n')
        html.append('            if ( suggestion_list'+field.id+'[sugesstr].toLowerCase().includes(searchval) ) {\n ')
        html.append('                ioption=2*Math.floor(sugesstr/2);\n')
        html.append('                break}}\n')
        html.append('          $("#'+field.id+'").val(suggestion_list'+field.id+'[ioption]); } })\n')
        html.append('  $("#filter_'+field.id+'").autocomplete({\n')
        html.append('     source: suggestion_list'+field.id+'});\n')
        html.append('  $("#Valid_'+field.id+'").on("click", function() {\n')
        html.append('     var searchval=$("#filter_'+field.id+'").val();\n     var ioption=0;\n')
        html.append('     for (var sugesstr in suggestion_list'+field.id+') {\n')
        html.append('        if ( suggestion_list'+field.id+'[sugesstr] == searchval ) {\n ')
        html.append('           ioption=2*Math.floor(sugesstr/2);\n')
        html.append('           break}}\n')
        html.append('     $("#'+field.id+'").val(suggestion_list'+field.id+'[ioption]);\n')
        html.append('     })\n')
        html.append('</script>')
        return core.HTMLString(''.join(html))

    @classmethod
    def render_option(cls, value, label, selected, **kwargs):
        if value is True:
            # Handle the special case of a 'True' value.
            value = text_type(value)
        
        options = dict(kwargs, value=value)
        if selected:
            options['selected'] = True
        return core.HTMLString('<option %s>%s</option>' % (core.html_params(**options), markupsafe.escape(label)))

class myFixedSelectField(SelectField):
    widget = mySelect(multiple=False)


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
        # recaptcha = RecaptchaField()
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
    NewProjectForm.chosen_project=myFixedSelectField(description='Or choose one of your old projects in this list (with its sessions) :',choices=listprojects,validators=[Optional()])
    NewProjectForm.action_sessions = RadioField(description="Action with the sessions of this project :",default="create",
                                 choices=[("use","Use an existing session for the grid"),
                                          ("modify","modify an existing session"),
                                          ("create","Create new session")],
                                 validators=[Optional()])
    NewProjectForm.submit = SubmitField("Next step")
    return NewProjectForm

            
def BuildAllProjectSessionForm(list_myprojects_sessions,list_invite_sessions):
    class AllProjectSessionForm(FlaskForm):
        pass

    AllProjectSessionForm.chosen_project_session=myFixedSelectField(description='Choose one of your own project / sessions.',choices=list_myprojects_sessions,validators=[Optional()])
    AllProjectSessionForm.chosen_session_invited=myFixedSelectField(description='OR choose one of your collaboration sessions.',choices=list_invite_sessions,validators=[Optional()])
    AllProjectSessionForm.edit = SubmitField("Edit session before grid")
    AllProjectSessionForm.submit = SubmitField("Next step")
    return AllProjectSessionForm

def BuildOldProjectForm(thisproject,listsessions):
    class OldProjectForm(FlaskForm):
        pass
    
    OldProjectForm.projectname=StringField(label="Project name", default=thisproject["name"],validators=[Optional()])
    OldProjectForm.description=StringField(label="Description of this project", default=thisproject["description"],validators=[Optional()])
    OldProjectForm.from_session = RadioField(label='Action on session (required)',
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
    NewSessionForm.submit1 = SubmitField("Next step")
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
    copySessionForm.submit1 = SubmitField("Next step")
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
                                                                ("copy","Copy an old tileset into a new one."),
                                                                ("search","Search another tileset for Session."),
                                                                ("remove","Remove an old tileset in Session."),
                                                                ("useold","Use existing tilesets and go to grid.")],
                                                       default='useold',
                                                       validators=[Optional()])
        else:
            copySessionForm.tilesetaction = RadioField(label='tilesetaction',
                                                       description='Choose to create and add a new tileset or just use all existing ones.',
                                                       choices=[("create","Add a new tileset."),
                                                                ("copy","Copy an old tileset into a new one."),
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
    
    OldTileSetForm.chosen_tileset=myFixedSelectField(description='List of Tileset for user '+username+' :',choices=listtilesets,validators=[Optional()])
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

def BuildTilesSetForm(oldtileset=None,json_tiles_text=None,onlycopy=False,editconnection=False):
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
        
    TilesSetForm.submit1 = SubmitField("Next step")
    TilesSetForm.name = StringField("Tiles Set name (required)", default=name, validators=[InputRequired()])
    if (not onlycopy):
        TilesSetForm.dataset_path = StringField("Path or main URL of dataset (add to tiles)", default=dataset_path, validators=[Optional()])
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
        TilesSetForm.json_tiles_file = FileField("File json object for tileset ",
                                                 validators=[Optional()])

        TilesSetForm.editjson = SubmitField("Use Json editor for this tileset.")
        
        TilesSetForm.script_launch_file = FileField(u'python script for Connection machine to launch the TileSet',
                        validators=[Optional()])

        # TODO
        # TilesSetForm.script_launch_text = TextAreaField("u'Edit here python script for Connection machine.',

        # same option as Connection form in TileSet form because of config files that don't depend of connection.
        TilesSetForm.configfiles = MultipleFileField(description="Configuration files placed in connection dir and upload in CASE dir on HPC frontend.",
                                                     validators=[Optional()])

        if (editconnection):
            TilesSetForm.manage_connection= RadioField(label='Connections',
                                        description='Manage Connection for this tileset.',
                                        choices=[("Use","Use an old one."),
                                                 ("Edit","Edit old connection."),
                                                 ("Quit","Quit running connection."),
                                                 ("reNew","Create a new one."),
                                                 ],
                                        default="Use",
                                        validators=[Optional()])
            # ("Save","Save the connection for reuse."),
            # ("Reload","Reload saved connection."),
            #TilesSetForm.editconnection = SubmitField("Manage connection for this tileset.")

        TilesSetForm.openports_between_tiles = FieldList(IntegerField("port :",validators=[Optional()]),description="Open port in visualisation network",min_entries=2,max_entries=5) 
   
    TilesSetForm.goback = SubmitField("Go back")
    TilesSetForm.submit = SubmitField("Next step")

    return TilesSetForm


def BuildConnectionsForm(oldconnection=None,json_tiles_text=None):
    class ConnectionForm(FlaskForm):
        pass

    if (oldconnection==None):
        host_address=""
        auth_type="ssh"
        container="docker_swarm"
        scheduler="none"
    else:
        host_address=oldconnection.host_address
        auth_type=oldconnection.auth_type
        container=oldconnection.container
        scheduler=oldconnection.scheduler
        
    ConnectionForm.submit1 = SubmitField("Next step")
    ConnectionForm.host_address = StringField("Name or IP of the machine (required)", default=host_address, validators=[InputRequired()])

    ConnectionForm.debug = BooleanField("Debug mode",default=False)
    
    #### liste A REVOIR  (cf TVConnection.py)
    ConnectionForm.auth_type = RadioField(label='Authentication type',
                                          description='Connection to the machine :',
                                          choices=[("ssh","Direct ssh connection"),
                                                   ("rebound","ssh through a gateway"),
                                                   ("persistent","define ssh connection an save it.")
                                          ],
                                          default=auth_type,
                                          validators=[Optional()])

    ConnectionForm.container = StringField("Type of backend use on the machine to launch containers", default=container, validators=[InputRequired()])
    ConnectionForm.scheduler = RadioField(label='Type of scheduler on HPC machine',
                                          description='How to launch containers job on the machine :',
                                          choices=[("none","No schedule at all : you will have to give the list of machines."),
                                                   ("slurm","Slurm scheduler."),
                                                   ("loadleveler","Loadleveler scheduler.")
                                          ],
                                          default=scheduler,
                                          validators=[Optional()])
    ConnectionForm.scheduler_file = FileField("Script to launch CONTAINERs on remote machine (required for connection) : ",validators=[Optional()])
    # ConnectionForm.scheduler_text = TextAreaField("Edit here script to launch CONTAINERs on remote machine.",validators=[Optional()])
    

    # Connection files specific for associated TileSet
    ConnectionForm.configfiles = MultipleFileField(label="Connection configuration files (required for connection). ",
                                                   description="Configuration files placed in connection dir and upload in CASE dir on HPC frontend.",
                                                   validators=[Optional()])

    ConnectionForm.submit = SubmitField("Next step")
    return ConnectionForm
        

class RequestInvitLinks(FlaskForm):
    name = StringField("Tiles Set name", validators=[InputRequired()])
    sessionname = StringField("Project name", validators=[InputRequired()])

# class HomeForm(FlaskForm):
#     gotologin = SubmitField("Go to login page")

# class SettingsForm(FlaskForm):
#     nbr_of_tiles = IntegerField("Number of tiles", validators=[InputRequired()])
#     save = SubmitField("Go to grid")

