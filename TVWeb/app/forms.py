# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm, recaptcha
from flask_wtf.recaptcha import RecaptchaField
import wtforms
from wtforms import RadioField, SelectField, StringField, PasswordField, BooleanField, SubmitField, IntegerField, TextAreaField, \
    SelectMultipleField, FieldList, FileField, MultipleFileField, widgets, HiddenField, DateField, SearchField, FormField, Form
from wtforms.widgets import core
from wtforms.validators import InputRequired, Email, Optional, EqualTo, NumberRange, ReadOnly, Length

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
        for val, label, selected, _ in field.iter_choices():
            suggestion_list.append(val)
            suggestion_list.append(label)
        html = ['<select %s style="width:1300px">' % core.html_params(name=field.name, **kwargs)]
        #; font-family: monospace;
                
        for val, label, selected, _ in field.iter_choices():
            html.append(self.render_option(val, label, selected))
        html.append('</select>')

        html.append('</br><div id=search_'+field.id+'>'+field.description+'</br>')
        html.append('<label for=filter_'+field.id+'>Search in all your list and press Go :&emsp;</label></br>')
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
        return markupsafe.Markup(''.join(html))

    @classmethod
    def render_option(cls, value, label, selected, **kwargs):
        if value is True:
            # Handle the special case of a 'True' value.
            value = text_type(value)
        
        options = dict(kwargs, value=value)
        if selected:
            options['selected'] = True
        return markupsafe.Markup('<option %s>%s</option>' % (core.html_params(**options), markupsafe.escape(label)))

class myFixedSelectField(SelectField):
    widget = mySelect(multiple=False)

class UserField(Form):
    label=""
    username = StringField('Username',
                           validators=[Optional(),
                                       Length(min=6,max=16,
                                              message=('not too short (<6), not too long (>16)...'))
                                       ])
    iseditor = BooleanField("Role editor",default=False,
                            validators=[Optional()])

def BuildRegisterForm(Username=None,Useremail=None,Usercomp=None,Usermanager=None):
    class RegisterForm(FlaskForm):
        pass
    RegisterForm.username = StringField("Username", default=Username, validators=[InputRequired()])
    RegisterForm.email = StringField("E-mail adress", default=Useremail, validators=[InputRequired(), Email()])
    RegisterForm.compagny = StringField("Compagny name", default=Usercomp, validators=[InputRequired()])
    RegisterForm.manager = StringField("Manager name", default=Usermanager, validators=[InputRequired()])
    RegisterForm.password = PasswordField("Password", validators=[
        InputRequired(),
        EqualTo('confirm', message='Passwords must match')])
    RegisterForm.confirm = PasswordField("Confirm password", validators=[InputRequired()])
    RegisterForm.remember_me = BooleanField("Remember me")
    RegisterForm.newpassword = BooleanField("Change password (must be logged in) ",default=Username is not None)
    RegisterForm.choice_project = RadioField("About the project :",choices=[("create","Create a new one ?"),
                                                               ("connect","Connect to an existing one ?")],
                                default="connect")
    RegisterForm.submit = SubmitField("Sign In")
    return RegisterForm

def BuildLoginForm(session):
    class LoginForm(FlaskForm):
        # recaptcha = RecaptchaField()
        pass
    try:
        default_username = session.get("username", "Anonymous")
    except Exception:
        default_username = "Anonymous"
    LoginForm.username = StringField("Username", default=default_username,validators=[InputRequired()])
    LoginForm.password = PasswordField("Password", validators=[InputRequired()])
    LoginForm.remember_me = BooleanField("Remember me")
    LoginForm.newuser = BooleanField("Change password ?")
    LoginForm.choice_project = RadioField(
        label="Action with the project :",
        choices=[("create","Create a new one ?"), ("connect","Connect to an existing one ?")],
        default="connect"
    )
    LoginForm.submit = SubmitField("Next step")
    return LoginForm

def BuildNewProjectForm(listprojects):
    class NewProjectForm(FlaskForm):
        pass
    NewProjectForm.projectname = StringField("New Project name", validators=[Optional()])
    NewProjectForm.description = StringField("Description of this project", validators=[Optional()])
    NewProjectForm.chosen_project=myFixedSelectField(description='Or choose one of your old projects in this list (with its sessions) :',choices=listprojects,validators=[Optional()])
     
    choices=[("use","Use an existing session for the grid"),
             ("create","Create new session")]
    NewProjectForm.action_sessions = RadioField(description="Action with the sessions of this project :",default="create",
                                 choices=choices,
                                 validators=[Optional()])
    NewProjectForm.submit = SubmitField("Next step")
    return NewProjectForm


def BuildAdminForm(list_myprojects,list_myprojects_sessions,list_user_connections,list_all_users=None,list_all_projects=None,list_all_sessions=None,list_all_connections=None):
    #list_invite_sessions,
    class AdminForm(FlaskForm):
        pass

    AdminForm.chosen_project=myFixedSelectField(description='Choose one of your own project.',choices=list_myprojects,validators=[Optional()])
    AdminForm.chosen_project_session=myFixedSelectField(description='Choose one of your own project / sessions.',choices=list_myprojects_sessions,validators=[Optional()])
    # AdminForm.chosen_session_invited=myFixedSelectField(description='OR choose one of your collaboration sessions.',choices=list_invite_sessions,validators=[Optional()])
    AdminForm.chosen_user_connection=myFixedSelectField(description='OR one of your connections.',choices=list_user_connections,validators=[Optional()])
    if (list_all_connections is not None):
        AdminForm.chosen_connections=myFixedSelectField(description='OR one of all other connections.',choices=list_all_connections,validators=[Optional()])

    if (list_all_users is not None):
        AdminForm.all_users=myFixedSelectField(description='Choose one user. !! This will remove all projects/sessions of this user !!',choices=list_all_users,validators=[Optional()])
        #AdminForm.editUser = SubmitField("Edit selected user.")    
        
    if (list_all_projects is not None):
        AdminForm.all_projects=myFixedSelectField(description='Choose one project.',choices=list_all_projects,validators=[Optional()])

    if (list_all_sessions is not None):
        AdminForm.all_sessions=myFixedSelectField(description='Choose one project.',choices=list_all_sessions,validators=[Optional()])
        
    if (list_all_connections is not None):
        AdminForm.all_connections=myFixedSelectField(description='Choose one connection.',choices=list_all_connections,validators=[Optional()])
    
    AdminForm.suppressSelected = SubmitField("Delete SELECTIONS.")    
    AdminForm.suppressAllMyConnections = SubmitField("Delete all MY CONNECTIONS.")
    
    if (list_all_users is not None):
        AdminForm.suprressfreetiles = SubmitField("Delete all FREE TILES.")
        AdminForm.suprressUnusedTilesets = SubmitField("Delete all UNUSED TILESETS.")

    if (list_all_connections is not None):
        AdminForm.suppressAllConnections = SubmitField("Delete ALL CONNECTIONS.")
    AdminForm.submit = SubmitField("Help")
    return AdminForm
            

def BuildAllProjectSessionForm(list_myprojects_sessions,list_invite_sessions):
    class AllProjectSessionForm(FlaskForm):
        pass

    AllProjectSessionForm.chosen_project_session=myFixedSelectField(description='Choose one of your own project / sessions.',choices=list_myprojects_sessions,validators=[Optional()])
    AllProjectSessionForm.chosen_session_invited=myFixedSelectField(description='OR choose one of your collaboration sessions.',choices=list_invite_sessions,validators=[Optional()])
    AllProjectSessionForm.edit = SubmitField("Edit session before grid")
    AllProjectSessionForm.submit = SubmitField("Next step")
    return AllProjectSessionForm

# TODO

def BuildOldProjectForm(thisproject,listsessions, session):
    class OldProjectForm(FlaskForm):
        pass

    can_manage_members=session.get("can_manage_members",False)
    can_edit_session=session.get("can_edit_session",False)
    if (can_edit_session):
        choices=[("use","Use a session"),
                 ("copy","Duplicate a session")]
    else:
        choices=[("use","Use a session")]
        
    OldProjectForm.projectname=StringField(label="Project name", default=thisproject["name"],validators=[Optional()])
    OldProjectForm.description=StringField(label="Description of this project", default=thisproject["description"],validators=[Optional()])
    OldProjectForm.from_session = RadioField(label='Action on session (required)',
                                             description='Choose which action with old session you want :',
                                             choices=choices,
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
    NewSessionForm.users = FieldList(description="Add users",
                                      unbound_field=FormField(UserField),
                                      min_entries=5,max_entries=10)
    NewSessionForm.add_users = SubmitField('Add more users')
    NewSessionForm.Session_config = SubmitField("Edit configuration of the session")
    NewSessionForm.submit = SubmitField("Next step")
    return NewSessionForm

def BuildEditsessionform(oldsession, session, edit=True):
    class editsessionform(FlaskForm):
        pass
    editsessionform.submit1 = SubmitField("Next step")
    editsessionform.sessionname = StringField("New session name", default=oldsession.name, validators=[InputRequired()])
    editsessionform.description = StringField("Description of this session", default=oldsession.description, validators=[InputRequired()])
    ListAllTileSet_ThisSession=[ (str(thistileset.id), thistileset.name) for thistileset in oldsession.tile_sets]

     # - PCA - 
    # Make the PCA by default
    has_pca = "NO" 

    can_manage_members=session.get("can_manage_members",False)
    can_edit_session=session.get("can_edit_session",False)

    # - PCA - 
    # Add a field : number of wanted clusters
    # initialize the json_tiles_nbClusters with :
    #  |_ the old one (the saved one) if want to update the database table  or the json file
    #  |_ the new one passed as argument
    json_tiles_nbClusters = 2  

    if (len(ListAllTileSet_ThisSession) > 0):
        if can_edit_session:
            valid=[Optional()]
        else:
            valid=[ReadOnly()]
        editsessionform.tilesetchoice = RadioField(label='listtilesets',
                                                   description='List all tilesets for this session',
                                                   choices=ListAllTileSet_ThisSession,
                                                   default=ListAllTileSet_ThisSession[0][0],
                                                   validators=valid)
        
        if can_edit_session:
            valid=[Optional()]
        else:
            valid=[ReadOnly()]
        if edit:
            editsessionform.edit = SubmitField("View or edit selected tileset.")
            editsessionform.tilesetaction = RadioField(label='tilesetaction',
                                                       description='Choose to create and add a new tileset or just use all existing ones.',
                                                       choices=[("create","Add a new tileset."),
                                                                ("copy","Copy an old tileset into a new one."),
                                                                ("search","Search another tileset for Session."),
                                                                ("remove","Remove an old tileset in Session."),
                                                                ("useold","Use existing tilesets and go to grid.")],
                                                       default='useold',
                                                       render_kw={'label_class': 'text-decoration-underline', 'radio_class': 'text-decoration-none'},
                                                       validators=valid)
        else:
            editsessionform.tilesetaction = RadioField(label='tilesetaction',
                                                       description='Choose to create and add a new tileset or just use all existing ones.',
                                                       choices=[("create","Add a new tileset."),
                                                                ("copy","Copy an old tileset into a new one."),
                                                                ("search","Search another tileset for Session."),
                                                                ("useold","Use existing tilesets and go to grid.")],
                                                       default='useold',
                                                       render_kw={'label_class': 'text-decoration-underline', 'radio_class': 'text-decoration-none'},
                                                       validators=valid)
            
        # - PCA - 
        editsessionform.has_pca = RadioField(label='- Principal Component Analysis :',
                                             description='Would you like to perform automatically Principal Component Analysis (PCA) on all your tilesets? <br/>\
                                             This option will perform clustering and thus add tags corresponding to groups.',
                                             choices=[("YES","yes"),
                                                      ("NO","no")
                                                      ],
                                             default=has_pca,
                                             validators=valid)
                
        """
            # Add the number of cluster field
            editsessionform.json_tiles_nbClusters = IntegerField("Number of wanted clusters ", default=json_tiles_nbClusters,
                                            validators = [NumberRange(min=2)])
                
            editsessionform.tilesetchoice = RadioField(label='listtilesetsforpca',
                                                   description='List of tilesets for this session : check all the desired ones ',
                                                   choices=ListAllTileSet_ThisSession,
                                                   default=ListAllTileSet_ThisSession[0][0],
                                                   validators=[Optional()])

        """
    else:
        if can_edit_session:
            valid=[Optional()]
        else:
            valid=[ReadOnly()]
        if edit:
            editsessionform.tilesetaction = RadioField(label='tilesetaction',
                                                       description='No old tilesets. Create a first tileset.',
                                                       choices=[("create","Add a new tileset."),
                                                                ("search","Search another tileset for Session.")],
                                                       default='create',
                                                       validators=valid)
        # - PCA - Hidden
        editsessionform.has_pca=HiddenField("no PCA if no TileSet.",default=False,validators=valid)
    
    myproject=oldsession.projects
    myUsers=oldsession.users
    printstr="{0:\xa0<20.20}\xa0|\xa0{1:\xa0<18.18}"
    ListAllUsers_ThisSession=[('NoChoice',printstr.format("User name","role"))]
    for user in myUsers:
        for projm in user.project_members_:
            if projm.project_id == myproject.id:
                ListAllUsers_ThisSession.append((user.id,printstr.format(user.name,projm.role_type)))
    labelUsers='All users in this session and their roles : '
    editsessionform.allusers=myFixedSelectField(label=labelUsers,
                                                choices=ListAllUsers_ThisSession,
                                                validators=[Optional()])

    editsessionform.editusers = SubmitField("Edit users in project members page.")

    if can_manage_members:
        editsessionform.users = FieldList(label="Add new users : ",
                                      unbound_field=FormField(UserField),
                                      min_entries=2,max_entries=10)
        editsessionform.add_users = SubmitField('Add more users')
        
    editsessionform.Session_config = SubmitField("Edit configuration of the session")
    editsessionform.submit = SubmitField("Next step")
    return editsessionform

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


# - PCA - 
#   |_ Add the parameter nbClusters corresponding to the optimal knee value (the optimal value of cluster 
#       for the corresponding tileset)
#       |_ OR calculate it directly with the tilset json_tiles_text
#   |_ the json_tiles_text argument contains the json tileset (the nodes)
#       |_ process here the anatreada script 
#           |_ get the new tileset with the new tags "00_group" for example

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
        
    # - PCA - 
    # Make the PCA by default
    has_pca = "NO" 
    
    TilesSetForm.submit1 = SubmitField("Next step")
    TilesSetForm.name = StringField("Tiles Set name (required)", default=name, validators=[InputRequired()])

    if (not onlycopy):
        TilesSetForm.type_of_tiles = RadioField(label='Type of the tiles',
                                                description='Connection with some pictures or web pages or remote VMs.',
                                                choices=[("PICTURE","a set of pictures on the web or locally"),
                                                         ("URL","a set of web links in html"),
                                                         ("CONNECTION","Use a connection to a remote machine")
                                                ],
                                                default=type_of_tiles,
                                                validators=[Optional()])
        TilesSetForm.json_tiles_text = TextAreaField("Paste json object for tileset ",default=json_tiles_text,
                                                     validators=[Optional()])
        TilesSetForm.json_tiles_file = FileField("File json object for tileset ",
                                                 validators=[Optional()])

        TilesSetForm.editjson = SubmitField("Use Json editor for this tileset.")
        
        TilesSetForm.dataset_path = StringField("Path or main URL of dataset (add to tiles)", default=dataset_path, validators=[Optional()])
        TilesSetForm.script_launch_file = FileField(
            u'python script for Connection machine to launch the TileSet',
            validators=[Optional()])

        # TODO
        # TilesSetForm.script_launch_text = TextAreaField("u'Edit here python script for Connection machine.',

        # same option as Connection form in TileSet form because of config files that don't depend of connection.
        TilesSetForm.configfiles = MultipleFileField(label="ConfigFiles",
            description="Configuration files placed in connection dir and upload in CASE dir on HPC frontend.",
            validators=[Optional()])

        if (editconnection):
            TilesSetForm.createconnection = SubmitField(label="createconnection",description="Create Connection")
            TilesSetForm.editconnection = SubmitField(label="editconnection",description="Edit Connection")
            TilesSetForm.shellconnection = SubmitField(label="shellconnection",description="Direct shell Connection")
            TilesSetForm.manage_connection= RadioField(label='Connections',
                                        description='Manage Connection for this tileset.',
                                        choices=[("Use","Use an old one."),
                                                 ("Quit","Quit running connection."),
                                                 ("reNew","Create a new one."),
                                                 ],
                                        default="Use",
                                        validators=[Optional()])
            # ("Edit","Edit old connection."),
            # ("Save","Save the connection for reuse."),
            # ("Reload","Reload saved connection."),
            #TilesSetForm.editconnection = SubmitField("Manage connection for this tileset.")

        #TilesSetForm.openports_between_tiles = FieldList(IntegerField("port :",validators=[Optional()]),description="Open port in visualisation network",min_entries=2,max_entries=5) 
        # - PCA - 
        # Add the number of cluster field
        TilesSetForm.has_pca = RadioField(label='- Principal Component Analysis :',
                                                description='Would you like to perform automatically Principal Component Analysis (PCA) on your data? <br/>\
                                                            This option will perform clustering and thus add tags corresponding to groups.',
                                                choices=[("YES","yes"),
                                                         ("NO","no")
                                                ],
                                                default=has_pca,
                                                validators=[Optional()])
        
        
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

    # Connection files specific for associated TileSet
    ConnectionForm.configfiles = MultipleFileField(label="Connection configuration files (required for connection). ",
                                                   description="Configuration files placed in connection dir and upload in CASE dir on HPC frontend.",
                                                   validators=[Optional()],default=None)

    
    # Connection with ssh rebounds
    #ConnectionForm.auth_type = HiddenField(default=auth_type)
    ConnectionForm.auth_type = RadioField(label='Authentication type',
                                          description='Connection to the machine :',
                                          choices=[("ssh","Direct ssh connection"),
                                                   ("rebound","ssh through gateway(s)")
                                          ],
                                          default=auth_type,
                                          validators=[Optional()])
    #,
    #                                                ("persistent","define ssh connection an save it.")

    ConnectionForm.container = HiddenField(default=container)
    # ConnectionForm.container = StringField("Type of backend use on the machine to launch containers", default=container, validators=[InputRequired()])
    
    ConnectionForm.scheduler = HiddenField(default=scheduler)
    # ConnectionForm.scheduler = RadioField(label='Type of scheduler on HPC machine',
    #                                       description='How to launch containers job on the machine :',
    #                                       choices=[("none","No schedule at all : you will have to give the list of machines."),
    #                                                ("slurm","Slurm scheduler."),
    #                                                ("loadleveler","Loadleveler scheduler.")
    #                                       ],
    #                                       default=scheduler,
    #                                       validators=[Optional()])
    ConnectionForm.scheduler_file = HiddenField(default=None)
    # ConnectionForm.scheduler_file = FileField("Script to launch CONTAINERs on remote machine (required for connection) : ",
    #                                           validators=[Optional()])
    # ConnectionForm.scheduler_text = TextAreaField("Edit here script to launch CONTAINERs on remote machine.",validators=[Optional()])

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



def BuildRetreiveSessionForm():
    class RetreiveSessionForm(FlaskForm):
        pass
        
    RetreiveSessionForm.session_file = FileField("Session file for TiledViz ",
                                                 validators=[InputRequired()])
    # RetreiveSessionForm.editjson = SubmitField("Use Json editor for this tileset.")
        
    RetreiveSessionForm.goback = SubmitField("Go back")
    RetreiveSessionForm.submit = SubmitField("Next step")

    return RetreiveSessionForm

class InviteForm(FlaskForm):
    client_type = RadioField('Client Type',
                           choices=[('active', 'Active'), ('passive', 'Passive')],
                           default='active')
    max_uses = IntegerField('Maximum Uses', validators=[NumberRange(min=1)], default=1)
    submit = SubmitField('Generate Invitation Link')
    cancel = SubmitField('Cancel')
