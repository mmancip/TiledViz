try{
$(document).off('touchstart');
$(document).off('touchmove');
$(document).off('touchend');
$(window).off('touchstart');
$(window).off('touchmove');
$(window).off('touchend');
$(window).off("contextmenu");
$(document.body).off('touchmove');
$(window).css("touch-action","none");

$(document).ready( function(){
    $(window).on('touchmove', function(e)
		 {
		     e.preventDefault();
		 });

    socket = io.connect('http://' + document.domain + ':' + location.port);
    
    console.log("my session is :",  my_session);
    socket.on("connect", function(){
	var cdata = {"user": my_user, "project" : my_project, "session": my_session };
	socket.emit("connected_grid",
		    cdata, 
		    function(sdata){
			console.log(sdata);
			console.log("Socket connection running: ID:" + sdata["session_id"]+", room: "+
				    sdata["room"]);
			
		    });
    });

    $("#notifications").html("Here is the grid. You can get help with '?' button.")


    var update_client_number = function(new_nbr){
	var new_text = "";
	if (new_nbr == 0){ // 0: first client (socket not yet created), 1: refresh
	    new_text = "alone";
	}
	else if (new_nbr == 1){
	    new_text = "with another participant";
	}
	else{
	    var tmp_nbr = new_nbr - 1;
	    new_text = "with " + new_nbr + " other participants";
	}
	console.log($('#join-clients').text());
	$('#join-clients').text(new_text);	
	console.log("updated to " + $('#join-clients').text());
	
    };
    
    htmlPrimaryParent = $('#primaryparent'); // CSS in style.css
    // Check presence of the config file
    try{
	lang=json_config.language;
	console.log(lang=="FR" ? "FR selected" : "EN selected" );
	htmlPrimaryParent.off('mouseleave');
	htmlPrimaryParent.off('mouseenter');
	htmlPrimaryParent.off('mousedown');
	htmlPrimaryParent.off('mouseup');
	htmlPrimaryParent.off('touchstart');
	htmlPrimaryParent.off('touchmove');
	htmlPrimaryParent.off('touchend');
    }
    catch(err){
	htmlPrimaryParent.css({
	    margin : 0,
	    padding : 0,
	    overflow : "auto"
	});
	htmlPrimaryParent.append('<div id=warning class="warning blink"><img src="images/warning.png"></br></br>'+
				 'Warning, a configuration file is missing! You should have either a <b>config_default.js</b> in the folder TileViz,'+
				 ' or a <b>config.js</b> in the parent repository!</div>');
	$('#header').css('height', 0);
	console.log("error catched");
	warn = $('#warning');
	warn.css({
	    top : -250,
	    left : 0,
	    width : window.innerWidth,
	    height : 1500,
	    zIndex : 999,
	    backgroundColor : "white",
	    fontSize : 100,
	    padding : 100,
	    //verticalAlign : "middle",
	});
    }
    // Use to compute exact positions of tiles in the window for hiding some out of the real viewport.
    relativeLeft=parseInt(htmlPrimaryParent.css('width'))/2;

    // Marge from top
    TopPP = htmlPrimaryParent.css("marginTop");

    // Show new client connection
    socket.on('new_client', function(sdata){
	console.log(sdata, "new client");	
	update_client_number(sdata['part_nbr_update'])
	htmlPrimaryParent.click();
    });
    
    // Split geometry for Anonymous user
    console.log("my_geometry =",my_geometry);
    if ( my_geometry["DISPLAYWIDTH"] === undefined) {
	var grid_width = parseInt($('#main-grid').css("width"));
	//var grid_height = parseInt($('#main-grid').css("height"));
	var grid_height = window.innerHeight; // TODO: Find a better solution, suitable to various displays
	my_window={"left":0,
		   "right":window.innerWidth,
		   "top":0,
		   "down":window.innerHeight}
    } else {
	displaywidth=parseInt(my_geometry["DISPLAYWIDTH"]);
	displayheight=parseInt(my_geometry["DISPLAYHEIGHT"]);
	shiftleft=parseInt(my_geometry["SHIFTLEFT"]);
	shifttop=parseInt(my_geometry["SHIFTTOP"]);
	var grid_width = parseInt(my_geometry["WALLWIDTH"]);
	var grid_height = parseInt(my_geometry["WALLHEIGHT"])
	
	// padding = 20%
	padding_left=displaywidth/5;
	padding_top=displayheight/5;
	my_window={"left":-shiftleft-padding_left,
		   "right":-shiftleft+displaywidth+padding_left,
		   "top":-shifttop-padding_top,
		   "down":-shifttop+displayheight+padding_top}
    }
    console.log("Window computed with my_geometry : ",my_window)

    /* LIST OF USEFUL PARAMETERS 
       Use a research (Ctrl + F) to find related variable on the code

       IMPORTANT: all parameters loaded with "config…" are defined in the corresponding part of config_default.js or config.js in the TileVizCases folder.

       #001 Use json data to place the node on screen
       #002 Define colors avalaible for the legend of the filter, the size of the table limits the number of search
       #003 Define global parameters for the PostIt module
       #004 Individual parameters of all node's postit
       #005 Load all the data on start or only nodes visible on screen
       #006 Number of nodes on the mesh 
       #007 Choose to fix the number of columns
       #008 This number is the maximal numbers of columns if the number of columns is not fixed 
       or this number is the numbers of columns if the number of columns is fixed 
       #009 Set the lateral gap between two nodes
       #010 Set the vertical gap between two nodes
       #011 Size of the target zone for drag and drop
       #013 When you choose an option, other options are automtically disabled
    */	

    //Global variables

    //#001
    useJsonDataLocation=configJsonData.useLocation; //Use the json data to set location of the node

    /**All simulations are managed with two JS classes: 
       - Tile: Each Tile contains a simulation (embedded in an iframe )  
       - Mesh class: Constituted by Tile objects 
    */  
    /**#002 Definition of the colors with the configuration file 
     */
    colorFilterStickersTab = configColors.FilterStickersTab; 
    colorTagStickersTab = configColors.TagStickersTab; // 10 colors
    attributedTagsColorsArray = new Array();
    globalTagsList =[];
    currentSelectedTag = "";
    colorHBdefault = configColors.HBdefault;
    colorHBonfocus = configColors.HBonfocus;
    colorHBselected = configColors.HBselected;
    colorHBtoZoom = configColors.HBtoZoom;



    // Manipulation to get the RGB conversation of HBselected, HBtoZoom.
    htmlPrimaryParent.append('<div id=color></div>');
    $('#color').css('background-color', colorHBselected);
    colorHBselectedRGB = $('#color').css('background-color');
    $('#color').css('background-color', colorHBtoZoom);
    colorHBtoZoomRGB = $('#color').css('background-color');
    $('#color').remove();

    /**#003 PostIt options // GLOBAL ? 
       for more details see :  http://postitall.txusko.com/plugin.html
    */
    $.fn.postitall.globals = {
	prefix          : '#',//Id note prefixe
	filter          : 'domain',     //Options: domain, page, all
	savable         : false,        //Save postit in storage
	randomColor     : false,         //Random color in new postits
	toolbar         : true,         //Show or hide toolbar
	autoHideToolBar : true,         //Animation effect on hover over postit showing/hiding toolbar options
	removable       : true,         //Set removable feature on or off
	askOnDelete     : true,         //Confirmation before note removal
	draggable       : false,         //Set draggable feature on or off
	resizable       : true,         //Set resizable feature on or off
	editable        : true,         //Set contenteditable and enable changing note content
	changeoptions   : true,         //Set options feature on or off
	blocked         : true,         //Postit can not be modified
	minimized       : true,         //true = minimized, false = maximixed
	expand          : false,         //Expand note
	fixed           : true,         //Allow to fix the note in page
	addNew          : true,         //Create a new postit
	showInfo        : false,         //Show info icon
	pasteHtml       : true,         //Allow paste html in contenteditor
	htmlEditor      : true,         //Html editor (trumbowyg)
	autoPosition    : false,         //Automatic reposition of the notes when user resizes the screen
	addArColumn     : 'back'        //Add an arColumn to notes : none, front, back, all
    };

    //#005
    chargeAllContentOnStart = configBehaviour.loadAllContentOnStart;

    //#005-2
    //if  distance_from_the_bottom_for_loading = 0 : nodes are loaded only when they start to be visible on the screen
    distance_from_the_bottom_for_loading = parseInt(window.outerHeight);
    // distance_from_the_bottom_for_loading = parseInt(window.innerHeight);  this will load the node where their top-left coin is distant from down of the screen from under "distance_for_loading" px
    //
    // TODO : add "distance_from_the_top_for_unloading = ?" to unload nodes that are not visible anymore ?
    //
    
    //#006 Number of nodes on the mesh
    mesh_cardinal = jsDataTab.length;
    //mesh_cardinal = configBehaviour.meshCardinal; // for testing purposes !
    //#007  
    bool_fix_number_of_columns = configBehaviour.fixColumnNumber; // True seems to not behave properly when running on WildOS :'(
    //#008
    maximal_number_of_columns = configBehaviour.maxColumnNumber;  
    //#009
    gapBetweenColumns = configBehaviour.spaceBetweenColumns;
    //#010
    gapBetweenLines = configBehaviour.spaceBetweenLines;

    //#011 size of the targetZone for drag and drop 
    //Must be ( targetSize > 2) strict inequality is very important | the target  a targetSize value close to 2 means : the size of the drop zone is equal to the size of an node 
    //The target zone is a rectangle centered on top-left of the target node
    targetSize = configBehaviour.targetSize;
    //#013
    only_one_option = configBehaviour.onlyOneOption;
    
    // MODAL	
    is_new_client_active = true // DEFAULT behavior
    $('[id*=_new_client]').on("click", function(event){ // To select both buttons (active and passive)
	console.log("click new client "+this.id);
	if (this.id.match("active")) {
	    is_new_client_active = true;
	} else if (this.id.match("passive")) {
	    is_new_client_active = false;
	} else {
	    is_new_client_active = undefined;
	}

	$('[id*=_new_client]').removeClass("btn-selected");
	$('#'+this.id).addClass("btn-selected");
    });
    
    $('#getUrl').on("click", function(){
	cdata ={"type":is_new_client_active, "session":my_session,"user": "todo username" }
	console.log("get url clicked");
	socket.emit("get_link", cdata);
    });
    socket.on("get_link_back", function(sdata){
	console.log("i am the new link", sdata["link"]);
	$('#custom-url').val(sdata["link"]);
    });
  
    // http://davidzchen.com/tech/2016/01/19/bootstrap-copy-to-clipboard.html : ressource on copying things (like
    // this cute URL) to clipboard
    // TODO: get user input on best way to share URL: mail? copy/paste? QR code?
    //$('#copy-button').tooltip();
    $('#copy-button').on("click", function(){
	var input = document.querySelector("#custom-url");
	input.setSelectionRange(0, input.value.length + 1);
	try {
	    var success = document.execCommand("copy");
	    if (success) {
		console.log("copy success");
	    } else {
		console.log("copy error");
	    }

	} catch (err) {
	    console.log(err);
	}
    });

    var cleanModal = function(){
	$('#custom-url').val("URL");
	console.log("url resetted");
    };
    $('#closeModal').on({
	click: cleanModal
    });

    // Menu shared between clients
    socket.on('receive_Menu_click', function(sdata){
     	console.log("receive_Menu_click",sdata);
	var thisoption=$('#menu'+sdata.Menu+'>#option'+sdata.optionNumber);
	var listClass=thisoption.attr("class").split(" ");
	if ( listClass.find(function(s) {return s.toLowerCase().indexOf(sdata.optionButton.toLowerCase()) != -1 }) != undefined) {
	    thisoption.addClass("NotSharedAgain");
	    thisoption.click();
	    thisoption.removeClass("NotSharedAgain");
	} else {
	    var numOfEvents=$('#menu'+sdata.Menu).children().length;
	    for(var optionNumber=0; optionNumber<numOfEvents; optionNumber++)  {
		thisoption=$('#menu'+sdata.Menu+'>#option'+optionNumber);
		listClass=thisoption.attr("class").split(" ");
		if (listClass.find(function(s) {return s.toLowerCase().indexOf(sdata.optionButton.toLowerCase()) != -1 }) != undefined) {
		    thisoption.addClass("NotSharedAgain");
		    thisoption.click();
		    thisoption.removeClass("NotSharedAgain");
		    break;
		}
	    }
	}
    });
    
    // Global click actions shared between clients
    socket.on('receive_click', function(sdata){
     	console.log("receive_click",sdata);
	$('.'+sdata.action+'#'+sdata.id).addClass("NotSharedAgain");
	$('.'+sdata.action+'#'+sdata.id).click();
	$('.'+sdata.action+'#'+sdata.id).removeClass("NotSharedAgain");
    });
    // emit function used to send shared clicks
    emit_click=function(action,id) {
	if (! $('.'+action+'#'+id).hasClass("NotSharedAgain")) {			    
		cdata={"room":my_session,"id":id,"action":action};
		socket.emit("click", cdata, function(sdata){
 		    console.log("socket send click ", cdata);				
		});
		return true;
	} else
	    return false
    }
    
    // Change opacity shared between clients
    socket.on('receive_Force_Opacity', function(sdata){
     	console.log("receive_Force_Opacity",sdata);
	id=sdata["Id"];
	opacity=sdata["Opacity"];
	$('#tileOpacitySlider'+id).val(opacity*100);
	$('#tileOpacitySlider'+id).change();
	$('#'+id).css("opacity", opacity);
    });
    
    // Add new tag
    socket.on('receive_Add_Tag', function(sdata){
     	console.log("receive_Add_Tag",sdata);
	mesh.AddNewTag(sdata["NewTag"])
    });

    socket.on('receive_deploy_Session', function(sdata){
     	console.log("receive_deploy_Session",sdata);
	$('#gGnewroom').val(sdata['NewRoom']);
	$('#notifications').html('<div id=ValidateNewRoom height="10%" width="50%" style="font-size:100" ></div>');
	$("#ValidateNewRoom").append('<h1> Are you OK to change for this room ? Yes = click "Submit"</h1>'
			+'<button id="ChangeRoomNo" name="ChangeRoomNo" class="btn btn-info" >No</button>');
	$("#ChangeRoomNo").on("click",function() {
	    $("#ValidateNewRoom").remove()
	})
	if ( my_user == "Anonymous" ) {
	    $('#gGsubmit').click()
	}
    });

    // global bool initialized for buttonShare to deploy config but not on the user that have emited the signal.
    myOwnConfig=false;
    socket.on('receive_deploy_Config', function(sdata){
     	console.log("receive_deploy_Config",sdata);
	if (myOwnConfig) {
	    myOwnConfig=false;
	    return
	}
	$('#notifications').html('<div id=ValidateNewConfig height="10%" width="50%" style="font-size:100" ></div>');
	$("#ValidateNewConfig").append('<h1> Are you OK to change for the new config ?</h1>'
			+'<button id="ChangeConfigYes" name="ChangeConfigYes" class="btn btn-info" >Yes</button>'
			+'<button id="ChangeConfigNo" name="ChangeConfigNo" class="btn btn-info" >No</button>');
	$("#ChangeConfigYes").on("click",function() {
	    configJson=sdata["Config"];
	    UpdateParameters(configJson);
	    $("#ValidateNewConfig").remove()
	})
	$("#ChangeConfigNo").on("click",function() {
	    $("#ValidateNewConfig").remove()
	})
	if ( my_user == "Anonymous" ) {
	    $('#ChangeConfigYes').click()
	}
    });
     
    //Launch the mesh
    mesh = new Mesh(mesh_cardinal,bool_fix_number_of_columns,maximal_number_of_columns);
    mesh.meshEventStart();
    mesh.startLoading();
    $('body').css('background-image','url(../static/images/fond.png)');
    // TODO : build suggestion_list from tags (this next line), comments, titles, variables, ...
    suggestion_list = globalTagsList
	.concat($('.info').map(function(){ return $.trim($(this).text());}).get())
	.concat(me.getNodes2().map(function(e){return $.trim(e.getJsonData().comment); }));
    // if ( my_user == "Anonymous" ) {
	// MinPP=Math.min.apply(Math, $('.node').map(function(){ return parseInt($(this).css("top")); }).get());
	// console.log("min y tile ",MinPP)
	// MinPP=-MinPP/me.getNumOfColumns()/my_geometry.APPSCALE;
	// console.log("min y tile with resize ",MinPP)
	// //MinPP=-(MinPP*window.devicePixelRatio)/$('#0').height();
	// MinPP=MinPP + ( $('#primaryparent').position().top + parseInt($('#primaryparent').css("marginTop")) );
	// console.log("min y tile with shift ",MinPP)
	// console.log("grid height ",grid_height)
	// if (MinPP < grid_height) {
	//     TopPP=(parseInt(TopPP)+grid_height-MinPP);
	//     TopPP=1800
	//     htmlPrimaryParent.css("marginTop",TopPP+"px");
	// }
	//TopPP=1200;
	//htmlPrimaryParent.css("marginTop",TopPP+"px");
	TopPP = 0;
    // } else {
    // 	TopPP = 0;
    // }
});

} catch(err){
    console.log(err,true);
}
