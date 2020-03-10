	/** This object is a Tile, a part of an mesh 
	    The node is an element which can contain various contents : pictures, iframes, videos, dockers, etc.
	*/

$(document).ready(    function (){

Tile = function(Mesh) {

    var touchok=('ontouchstart' in document);

    //***************************************************private variable***************************************************//

    var nodeRef=this; // Reference to the node

    var mesh=Mesh;  // Each node has a reference to the mesh to which it belongs

    var id = nodeIdProvider(); // Each node gets an unique id 

    var className = "node";   // Each node belongs to "node" class

    var jsonData = jsDataTab[id]; // The data related to the node, url which contains simulations, visualisations, metadata etc.
    //It is loaded from the js file : nodes.js

    var loaded = false;

    var onoff = true;

    var qrcoded = false;
    
    if(useJsonDataLocation==false)  { // Id of the place where the node is located on the mesh (the mesh is a grid)
	var idLocation = id;
    }
    else if (useJsonDataLocation==true)  { 
	var idLocation = parseInt(jsonData.IdLocation);
    }
    //For example,         the id location on a grid with 3 columns ans 3 lines :                        
    //						| 1	| 2	| 3	|
    //						| 4	| 5	| 6	|
    //						| 7	| 8	| 9	|

    var isMoving = true; // Is the node already moving (true at init) ?

    var mlocation = mesh.me.mlocationProvider(idLocation); // The idLocation determines the node location on the mesh with the idLocation parameters
    var location = mesh.me.locationProvider(idLocation); // The idLocation determines the node location on the screen with the idLocation parameters

    var nodeHeight=mesh.me.getSpread().Y; // Height of a node, depends of the mesh parameters SPREAD
    var nodeWidth=mesh.me.getSpread().X; // Width of a node, depends of the mesh parameters SPREAD


    var state = 0; // This variable is similar to the focus, just a way to know if the node is selected by users
    var isSelected=false; /* This variable is another way to specify if the node is selected 
			     (we need a second variable to check selection because they are many options 
			     which need a selection so we need many way to know if the node is selected) */

    var nodeOpacity = configBehaviour.opacity;

    var nodeAngle = 0;  // Angle for rotation
	    
    // Html tag of the node
    var htmlNode = (    function(){ 
	    htmlPrimaryParent.append('<div id='+id+' class='+className+'></div>');
	    $('#'+id).css({height : nodeHeight, width : nodeWidth, display: "block",  margin: "auto" , backgroundColor : "none"}); 
	    $('#'+id).append('<div id=onoff'+id+' class=onoff>'+ id +'</div>');
	    $('#onoff'+id).hide();
	    $('#'+id).append('<div id=hitbox'+id+' class=hitbox></div>');

	    var infoToDisplay = "";
	    if (configJsonData.useTitle && jsonData.title != "")  { 
			infoToDisplay = jsonData.title.replace(".png", "");
	    } else { 
			infoToDisplay = id;
	    }
	    $('#'+id).append('<div id=info'+id+' class=info>' + infoToDisplay +'</div>');
	    $('.info').css("font-family", configBehaviour.infoFonts[Math.min(configBehaviour.defaultFontIndex, configBehaviour.infoFonts.length)]);
	    $('.info').css("color", configBehaviour.infoTextColor);
	    $('.info').css("font-size", configBehaviour.defautInfoFontSize);
	    if (configBehaviour.alwaysShowInfo)  { 
		$('.info').show();
	    }
	    $('#hitbox'+id).css('background-color', colorHBdefault);
	    // Handle to drag
	    $('#'+id).append('<div id=handle'+id+' class=handle></div>');
	    $('#handle'+id).addClass("drag-handle-on");
	    
	    if (touchok) {
		// Handle to rotate
		$('#'+id).append('<div id=rotate'+id+' class=rotate></div>');
		$("#rotate"+id).css({
			left : (parseInt($('#'+id).css("width"))/2-70)+'px',
			    top : (parseInt($('#'+id).css("height"))-15)+'px',
			    padding: "40px",
			    '-webkit-transform': "scale(0.5)",
			    '-moz-transform': "scale(0.5)",
			    '-transform': "scale(0.5)",
			    });
		$("#rotate"+id).hide();
	    }

	    return $('#'+id);
	}());
    
    /** Tag management
     * */
    var nodeTagList = [];
    var floatingTag = {};
    if (typeof jsonData.tags != 'undefined')  { 
	var nodeTagListTmp = [];
	if (typeof jsonData.tags == "object")  { 
	    nodeTagListTmp = jsonData.tags;
	}
	else if (typeof jsonData.tags == "string" && jsonData.tags != "")  { 
	    nodeTagListTmp = jsonData.tags.split(",");
	}


	for (var item=0;item<nodeTagListTmp.length;item++) {
	    if ( nodeTagListTmp[item].search('{')==0 ) {
		if ( nodeTagListTmp[item].search('{"') == -1 ) {
		    nodeTagListTmp[item]=nodeTagListTmp[item].replace(/{([^,]*),([^,]*),([^,]*),([^,]*)}/,
								      '{"name":"$1","m":$2,"val":$3,"M":$4}')
		}
		nodeTagListTmp[item]=JSON.parse(nodeTagListTmp[item]);
		name=newTag_conformance(nodeTagListTmp[item].name);
		floatingTag[name]={"id": item, "m":nodeTagListTmp[item].m,"val":nodeTagListTmp[item].val, "M":nodeTagListTmp[item].M};
		nodeTagListTmp[item]=name
	    } else {
		nodeTagListTmp[item] = newTag_conformance(nodeTagListTmp[item]);
	    }
	}
	nodeTagList = nodeTagListTmp;
    }
    if (! nodeTagList.some(function(e) {return e=='Off'}) )
	nodeTagList.push("Off");
    nodeTagList.sort();
    // Add On at the end to initialise its color and globalTagsList.
    if ( nodeTagList.some(function(e) {return e=='On'}) )
	nodeTagList.splice(nodeTagList.findIndex(function(e) {return e=='On'}),1);
    nodeTagList.push("On");

    /** Creation of the PostIt related to the node to take some notes about the simulations
	For more details : http://postitall.txusko.com/plugin.html
    */

    var initialNote = "";
    if(typeof jsonData.usersNotes != 'undefined')  { 
	initialNote = jsonData.usersNotes;
    }
    //test
    initialNote = jsonData.comment;
    //"test" + id;
    //#004
    $.PostItAll.new({

	    id		: "postit"+id, // The ID of the HTMLTag of the post it
	    content		: initialNote, // prewritten on the post it 
	    // Position and size
	    position	: 'absolute', 
	    width		: mesh.me.getSpread().X, // At the moment, the post it takes the same space as the node on the mesh
	    height		: mesh.me.getSpread().Y,
	    posX		: location.getX(),
	    posY		: location.getY() + mesh.me.getSpread().Y ,

	    style : { // GLOBAL ?
		tresd           : true,              // General style in 3d format
		backgroundcolor : "grey",            // Background color in new postits when randomColor = false
		textcolor       : "white",           // Text color
		textshadow      : true,              // Shadow in the text
		fontfamily      : 'verdana',         // Default font
		fontsize        : 80,                // Default font size
		arColumn           : 'none',         // Default arColumn : none, top, right, bottom, left
	    },

	    onDblClick: function (id) { return undefined; }                // Triggered on double click

	}, // Callback function, executed after postit creation
	function(){									
	    $('#postit'+id).css({display : "none"}); 
	});
    
    /** Here is created a tab menuEventTab related to the parameters menuEventTab_ of the Menu constructor (see below)
	Each node has a menu which allow users to manage some options 
	Existing ones :
	- Transparency and opacity slider
	- Add a post it or display it if it exists
	- Draw on the node
	- Swap columns
	- Swap lines
	To be added : 
	- Zoom on the node ?
	- 

	The size of the tab menuEventTab determine the number buttons in the menu 
	The function on menuEventTab determine what happens when the users click on the options menu 
	When the users click on the first button menuEventTab(0) is called 
	When the users click on the second  button menuEventTab(1) is called etc.


	These function must be writed like that  :

	function(v,nodeId,optionNumber){

	if(v==true)  {    
	STUFF TO DO WHEN OPTION IS ACTIVE
	} else { 		
	STUFF TO DO WHEN OPTION IS NOT ACTIVE
	}
	}

	where :
	- v  -> true when users active the options, false when users desactive it
	- nodeID -> the nodeId/menuId where the options has been active or desactive 
	- optionNumber -> the number of the options active or desactive


    */
    var menuTitleTab = new Array();
    var menuEventTab = new Array();


    /** Here is created a tab menuIconClassAttributesTab related to the parameters menuIconClassAttributesTab_ of the Menu constructor (see below)
	This table contains the name of the class which allows to give default backgroundImage to the options button
    */
    var menuIconClassAttributesTab = new Array();
    
    /** Flask Version : add a new array MenuShareEvent to manage client/server with menus.
	If one click on a button which have MenuShareEnvet is true. The server will receive a message and 
	dispach the click to the other clients. 
    */
    var MenuShareEvent = new Array();
    
    // To make a node transparent and enable to overlap other nodes
    menuTitleTab.push("Transparent mode to overlay")
    menuEventTab.push(    function(v, nodeId, optionNumber){
	    if (v==true)  { 
		if (configBehaviour.onlyOneTransparentTile && me.getTransparent()!=-1)  { 
		    $('#menu'+me.getTransparent()+'>#option'+optionNumber).click();
		}

		me.setTransparent(nodeId, true);

		$("#menu"+nodeId+">#option"+optionNumber).addClass("closeTransparentButtonIcon").removeClass("transparentButtonIcon");
	    } else { 
		me.setTransparent(nodeId, false);
		$("#menu"+nodeId+">#option"+optionNumber).addClass("transparentButtonIcon").removeClass("closeTransparentButtonIcon");
	    }
	}
	);

    menuIconClassAttributesTab.push("transparentButtonIcon");
    MenuShareEvent.push(true);
    
    // The options to display or not node's postIt
    menuTitleTab.push("Display tile's postIt")
    menuEventTab.push(    function(v,nodeId,optionNumber){

	    if(v==true)  {    

		nodeRef.updatePostItPositionandSize();
		//$.PostItAll.show('postit'+nodeId);

		// This part of code is to show off the postIt if the user resizes the screen or tries to move a node
		var hidePostIt = function(event){

		    event.stopPropagation();
		    $("#menu"+nodeId+">#option"+optionNumber).click();
		    $("#"+nodeId);
		    $( window ).off("resize",hidePostIt);
		    //$(".node").off("mousedown",hidePostIt);

		};

		$( window ).resize(hidePostIt) ;
		//$('.node').mousedown(hidePostIt);

		// Replace the "open option" icon with the "close option" icon
		$("#menu"+nodeId+">#option"+optionNumber).addClass("closeWriteButtonIcon").removeClass("writeButtonIcon");
	    } else { 
		$( window ).off("resize",hidePostIt);
		$.PostItAll.hide('postit'+nodeId);

		// Replace the "close option" icon with the "open option" icon
		$("#menu"+nodeId+">#option"+optionNumber).addClass("writeButtonIcon").removeClass("closeWriteButtonIcon");
	    }
	});

    menuIconClassAttributesTab.push("writeButtonIcon");
    MenuShareEvent.push(true);
    
    /** This function allows us to select and draw on a selected node
	I'll use it, on the next menu options
	NB: You must understand the magnifyingGlass function define on the mesh constructor 
	before try to understandzoomAndDrawOnNodes because zoomAndDrawOnNodes uses some html tag created 
	on the magnifyingGlass function. */

    var zoomAndDrawOnNodes = (    function() {
	    var initialSpread = me.getSpread(); // or mesh.me.getSpread ?

	    return function (nodeId){

		// First : zoom on the node $(#nodeId) with the function magnifyingGlass
		// Compute arguments for magnifyingGlass
		var ratio = me.getSpread().Y/me.getSpread().X;
		//console.log("Ratio in zoomAndDrawOnNodes: " + ratio);
		var nodeTab = new Array();
		nodeTab.push(me.getNode(nodeId));

		// Add unZoom button
		$('body').append('<div id=buttonUnzoom class=unzoomButtonIcon></div>');
		//$('#buttonUnzoom').hide();

		// This function is defined on the mesh constructor and allow us to zoom on the selected node
		me.magnifyingGlass(nodeTab,ratio,initialSpread, false, 0.5);

		// Here we define the layer where the users will draw
		var height = $('#zoomSupport > #Zoomed0').css('height');
		var width = $('#zoomSupport > #Zoomed0').css('width');
		var supportTop = parseInt($('#zoomSupport').css('top').replace('px',''));
		var supportLeft = parseInt($('#zoomSupport').css('left').replace('px',''));

		// NB:  ("#zoomSupport") has been defined in the magnifyingGlass function (not to be confused with helpSupport)
		// The Zoomed0 : is a div with the iframe scaled of the real node,
		// so we no more need to delete some child of $('#zoomSupport > #'+nodeId): menu and hitbox


		// Activate draw menu
		menuDraw.css("visibility", "visible");
		menuDraw.css("top", TagHeight+"px");

		// // Deactivate other magnify menus
		// me.disableOtherZoom("draw")

		// Creation of the layer $("#drawCanvas") on the support if it doesn’t already exist
		var supp = document.getElementById("drawCanvas"+nodeId);
		if (supp==null)  { 
		    $('#zoomSupport').append('<canvas id="drawCanvas'+nodeId+'" class=drawing height='+height+' width='+width+'></canvas>');

		    $("#drawCanvas"+nodeId).css({// GLOBALCSS ?
			    position : "absolute",
				top : 0,
				left : 0,
				width : $('#zoomSupport > #Zoomed0').css('width'),
				height : $('#zoomSupport > #Zoomed0').css('height'),
				zIndex : 300
				});
		} else { 
		    $('#drawCanvas'+nodeId).show();
		}


		if (! touchok) {
		    // Variables needed to draw on the iframe
		    // This tutorial  http://www.williammalone.com/articles/create-html5-canvas-javascript-drawing-app/ can be helpful to understand the following code
		    var clickX = new Array();
		    var clickY = new Array();
		    var clickDrag = new Array();
		    var paint = false;
		    var p=0; // number of paths

		    context = document.getElementById("drawCanvas"+nodeId).getContext("2d");
		    function addClick(x, y, dragging)  { 
			clickX.push(x);
			clickY.push(y);
			clickDrag.push(dragging);
		    }


		    var mousedownDraw = function(e){
			try  {
			    context.strokeStyle = drawingColor;
			}
			catch(e)  { 
			    drawingColor = configBehaviour.draw.defaultColor;
			    context.strokeStyle = drawingColor;
			}
			context.lineJoin = configBehaviour.draw.style;
			context.lineWidth = configBehaviour.draw.width;
				
			    
			var mouseX = e.pageX - supportLeft;
			var mouseY = e.pageY - supportTop;
				
			paint = true;
			addClick(mouseX , mouseY);
			redraw();
		    }
			    
		    var mousemoveDraw = function(e){
				
			if(paint)  { 	
			    var mouseX = e.pageX - supportLeft;
			    var mouseY = e.pageY - supportTop;
				    
			    addClick(mouseX , mouseY, true);
			    redraw();
			}
		    }
			    
		    var mouseupDraw = function(e){
				
			paint = false;
		    }
			    
		    $('#drawCanvas'+nodeId).on({
			    mousedown : mousedownDraw,			    
				mousemove : mousemoveDraw,			    
				mouseup : mouseupDraw,
				});
			

		    function redraw(){
				
			for(var i=p; i < clickX.length; i++) {		
				    
			    p++;
			    context.beginPath();
				    
			    if(clickDrag[i] && i)  {    
				context.moveTo(clickX[i-1]/* + supportTop */, clickY[i-1]);
			    } else { 
				context.moveTo(clickX[i]-1/* + supportTop */ , clickY[i]);
			    }
				    
			    context.lineTo(clickX[i], clickY[i]);
			    context.closePath();
			    context.stroke();			
			}
		    }
			
		} else {
		    var drawing = new Map();	// maps touch IDs to drag state objects
		    var p=0; // number of paths

		    context = document.getElementById("drawCanvas"+nodeId).getContext("2d");

		    var touchstartDraw = function (ev) {
			var hastouched=false;
			try  {
			    context.strokeStyle = drawingColor;
			}
			catch(e)  { 
			    drawingColor = configBehaviour.draw.defaultColor;
			    context.strokeStyle = drawingColor;
			}
			context.lineJoin = configBehaviour.draw.style;
			context.lineWidth = configBehaviour.draw.width;
				
			for (var i = 0; i < ev.changedTouches.length; i++) {
			    var touch = ev.changedTouches[i];
			    var targetid=touch.target.id;
			    console.log("touchstartDraw targetid "+targetid+" point "+touch.pageX +" "+touch.pageY );
			    var mouseX = touch.pageX - supportLeft;
			    var mouseY = touch.pageY - supportTop;
				    
			    drawing.set(touch.identifier, {
				    target: touch.target,
					mouseX : mouseX,
					mouseY : mouseY,
					});

			    hastouched=true;
			}
			if  (hastouched) {
			    hastouched=false;
			    ev.preventDefault();
			    //ev.stopPropagation()
			}
		    }
			    
		    var touchmoveDraw = function (ev) {
			var hastouched=false;
			for (var i = 0; i < ev.changedTouches.length; i++) {
			    var touch = ev.changedTouches[i];
			    var targetid=touch.target.id;
			    console.log("touchmoveDraw targetid "+targetid+" rect "+touch.pageX +" "+touch.pageY );
			    var mouseX = touch.pageX - supportLeft;
			    var mouseY = touch.pageY - supportTop;
				    
			    var drawstate = drawing.get(touch.identifier);

			    context.beginPath();
				    
			    context.moveTo(drawstate.mouseX, drawstate.mouseY);

			    context.lineTo(mouseX, mouseY);
			    context.closePath();
			    context.stroke();			


			    drawstate.mouseX = mouseX;
			    drawstate.mouseY = mouseY;


			    hastouched=true;
			}
			if  (hastouched) {
			    hastouched=false;				    
			    ev.preventDefault();
			    //ev.stopPropagation()
			}
		    }
			    
		    var touchendDraw = function (ev) {
			var hastouched=false;
			for (var i = 0; i < ev.changedTouches.length; i++) {
			    var touch = ev.changedTouches[i];
			    var targetid=touch.target.id;
			    console.log("touchendDraw targetid "+targetid+" rect "+touch.pageX +" "+touch.pageY );
			    drawing.delete(touch.identifier);
				
			    hastouched=true;
			}
			if  (hastouched) {
			    hastouched=false;
			    ev.preventDefault();
			    //ev.stopPropagation()
			}
		    }
			
		    $('#drawCanvas'+nodeId).on({
			    touchstart: touchstartDraw,
				touchmove: touchmoveDraw,
				touchend: touchendDraw
				});
		}
	    };
	})()

    /**Here is created a menu which uses the previous function
       Users have to select a node and this node will be rescaled and the users can draw on it */
    menuTitleTab.push("Draw on tile")
    menuEventTab.push(    function(v,nodeId,optionNumber){

	    if(v==true)  {    
		// Deactivate other magnify menus
		me.disableOtherZoom("draw")
		BlockDragAndDrop();

		zoomAndDrawOnNodes(nodeId);
		// Creation of a button to unzoom
		$('#buttonUnzoom').on({
			click : function(){
			    $(".node").off();
			    // Hide draw menu
			    menuDraw.css("visibility", "hidden");
			    // Activate other magnify menus
			    me.enableOtherZoom("draw")
			    EnableDragAndDrop();

			    $('#drawCanvas'+nodeId).hide();
			    $("#button").off();
			    //console.log("unzoom", $('#button'));
			    $("#button").remove();
			    //$('.hitbox').off("click");
			    me.meshEventReStart();
			}
		    });
	    } else { 	

		// Hide draw menu
		menuDraw.css("visibility", "hidden");

		//$('#buttonUnzoom') has been created on magnifyingGlass function himself called on zoomAndDrawOnNodes
		$('#buttonUnzoom').on({

			// Delete all tools created on magnifyingGlass and zoomAndDrawOnNodes
			click : function(){
			    //console.log("click unzoom button");
			    $(".node").off();
			    // Hide draw menu
			    menuDraw.css("visibility", "hidden");
			    // Activate other magnify menus
			    me.enableOtherZoom("draw")
			    EnableDragAndDrop();

			    $('#drawCanvas'+nodeId).hide();
			    me.meshEventReStart();
			}
		    });

	    }

	}	
	);

    menuIconClassAttributesTab.push("drawButtonIcon");
    MenuShareEvent.push(false);
    
    // To switch columns
    menuTitleTab.push("To switch columns")
    menuEventTab.push(    function(v,nodeId,optionNumber){

	    if(v==true)  {    

		if(mesh.me.getcolumnSelected() == -1 )  { 

		    mesh.me.setcolumnSelected(mesh.me.mlocationProvider( mesh.me.getNode(nodeId).getIdLocation()).getnX());
		    //console.log("colonne : "+mesh.me.mlocationProvider( mesh.me.getNode(nodeId).getIdLocation()).getnX());

		    for(O in mesh.me.getNodes2())  { 
			if(mesh.me.getcolumnSelected() == mesh.me.mlocationProvider( mesh.me.getNodes2()[O].getIdLocation()).getnX() )
			    mesh.me.getNodes2()[O].getHtmlNode().css('boxShadow', configCSS.columnSwapBoxShadow);
		    }

		}
		else if(mesh.me.getcolumnSelected() != -1)  { 
		    var secondColumnSelected = mesh.me.mlocationProvider( mesh.me.getNode(nodeId).getIdLocation()).getnX();



		    var column1Tab = [];
		    var column2Tab = [];

		    for(O in mesh.me.getNodes2())  { 

			if(mesh.me.getcolumnSelected() == mesh.me.mlocationProvider( mesh.me.getNodes2()[O].getIdLocation()).getnX() )  { 
			    column1Tab.push( mesh.me.getNodes2()[O]);
			    mesh.me.getNodes2()[O].getHtmlNode().css({
				    boxShadow: "none"});				
			}

			if(secondColumnSelected == mesh.me.mlocationProvider( mesh.me.getNodes2()[O].getIdLocation()).getnX() )  { 
			    column2Tab.push( mesh.me.getNodes2()[O]);			
			}

		    }

		    var i = 0 ;
		    for(i=0;i<column1Tab.length;i++)  { 
			var tmpBoolBlockMove = i == 0 ? false : true; 
			if(typeof column1Tab[i]!= "undefined" && typeof column2Tab[i]!= "undefined" )  { 
			    mesh.me.switchLocation(column1Tab[i],column2Tab[i],configBehaviour.showAnimationsLineColSwap,true, tmpBoolBlockMove);
			}
		    }
		    mesh.me.setcolumnSelected(-1);
		}



		//console.log(column1Tab);
		//console.log(column2Tab);

		$("#menu"+nodeId+">#option"+optionNumber).click();	
	    } else { 	




	    }	
	}	
	);

    menuIconClassAttributesTab.push("columnButtonIcon");
    MenuShareEvent.push(true);

    // To switch lines
    menuTitleTab.push("To switch lines")
    menuEventTab.push(    function(v,nodeId,optionNumber){

	    if(v==true)  {    

		if(mesh.me.getlineSelected() == -1 )  { 

		    mesh.me.setlineSelected(mesh.me.mlocationProvider( mesh.me.getNode(nodeId).getIdLocation()).getnY());
		    //console.log("line : "+mesh.me.mlocationProvider( mesh.me.getNode(nodeId).getIdLocation()).getnY());

		    for(O in mesh.me.getNodes2())  { 
			if(mesh.me.getlineSelected() == mesh.me.mlocationProvider( mesh.me.getNodes2()[O].getIdLocation()).getnY() )
			    mesh.me.getNodes2()[O].getHtmlNode().css('boxShadow', configCSS.lineSwapBoxShadow);
		    }
		}
		else if(mesh.me.getlineSelected() != -1)  { 
		    var secondLineSelected = mesh.me.mlocationProvider( mesh.me.getNode(nodeId).getIdLocation()).getnY();
		    //console.log(secondLineSelected);


		    var line1Tab = [];
		    var line2Tab = [];

		    for(O in mesh.me.getNodes2())  { 
			//console.log("aa",mesh.me.getlineSelected(),mesh.me.mlocationProvider( mesh.me.getNodes2()[O].getIdLocation()).getnY());
			if(mesh.me.getlineSelected() == mesh.me.mlocationProvider( mesh.me.getNodes2()[O].getIdLocation()).getnY() )  { 
			    line1Tab.push( mesh.me.getNodes2()[O]);	
			    mesh.me.getNodes2()[O].getHtmlNode().css({boxShadow: "none"});						
			}

			if(secondLineSelected == mesh.me.mlocationProvider( mesh.me.getNodes2()[O].getIdLocation()).getnY() )  { 
			    line2Tab.push( mesh.me.getNodes2()[O]);			
			}

		    }

		    var i = 0 ;
		    for(i=0;i<line1Tab.length;i++)  { 
			var tmpBoolBlockMove = i == 0 ? false : true; 
			if(typeof line1Tab[i]!= "undefined" && typeof line2Tab[i]!= "undefined" )  { 
			    mesh.me.switchLocation(line1Tab[i],line2Tab[i],configBehaviour.showAnimationsLineColSwap, true, tmpBoolBlockMove);
			}
		    }
		    mesh.me.setlineSelected(-1);
		}



		//console.log(line1Tab);
		//console.log(line2Tab);

		$("#menu"+nodeId+">#option"+optionNumber).click();	
	    } else { 	




	    }	
	}	
	);

    menuIconClassAttributesTab.push("lineButtonIcon");
    MenuShareEvent.push(true);

    /** Here is created the menu of the node*/
    var nodeMenu = new Menu(id,htmlNode,menuTitleTab,menuEventTab,menuIconClassAttributesTab,MenuShareEvent,{

	    // Position
	    position : "absolute",  
	    top : -120, // GLOBAL ?
	    left : 0,
	    // Style 
	    visible : "hidden", 
	    //margin : "0px 5px 10px 15px", // Not useful, only for the menu and not the buttons

	    // Button default class
	    classN : "node",
	    // Button size
	    height : 100, 
	    width : 100,
	    rightMargin : 30,
	    // Button style
	    //borderStyle : "solid", // GLOBAL
	    //borderWidth : "5px", // GLOBAL
	    //borderColor : "blue" //GLOBAL
	    menubox : false
	});

    $('#menu'+id).append("<div id=fake-tile-opacity-"+id+"></div>");
    $(OpacityZone).append("<div id=tile-opacity-"+id+" class=tile-opacity-menu-zone></div>");
    // tileOpacitySlider is placed after the transparentButtonIcon (in first place)
    tileOpacityLeft=parseInt($($('#menu'+id)[0].childNodes[1]).css("left"))+20;
    $('#fake-tile-opacity-'+id).css({
	position : "relative",
	visibility : "hidden",
	top :0,
	left : tileOpacityLeft,
	//parseInt($('#menu'+id).css("width")),
	//backgroundColor : "red",
	height : parseInt($('#menu'+id).css("height")),
	width : parseInt($('#'+id).css("width")) - tileOpacityLeft,
	zIndex : 0
    });
    this.setOpacityLocation = function () {
	$('#tile-opacity-'+id).css({
	    position : "absolute",
	    top : $('#fake-tile-opacity-'+id).offset().top,
	    left : $('#fake-tile-opacity-'+id).offset().left,
	    //parseInt($('#menu'+id).css("width")),
	    //backgroundColor : "red",
	    height : parseInt($('#menu'+id).css("height")),
	    width : parseInt($('#'+id).css("width")) - tileOpacityLeft,
	    zIndex : 130
	});
    }
    this.setOpacityLocation();
    $('#tile-opacity-'+id).css("visibility","hidden")

    //$('#tile-opacity-'+id).append("<input id=tileOpacitySlider"+id+" class=tile-opacity-slider type='range' name=tileOpacitySlider"+id+" min=0 max=100 value="+nodeOpacity*100+">");

    /** Stickers to tag the node 
	There are 10 differents colors for the tags, some more for other informations.
    */
    var stickers = new Stickers(id,htmlNode);

    for(var k=0;k < nodeTagList.length;k++)  { 
	var name=nodeTagList[k];
	if ($.inArray(nodeTagList[k], globalTagsList) == -1)  { 
	    globalTagsList.push(nodeTagList[k]);
	    var l=globalTagsList.length-1;
	    if (name in floatingTag) {
		globalFloatingTags[name]={"l":l,"m":floatingTag[name]["m"], "M":floatingTag[name]["M"]}
		var outColors=ColorSticker(l,floatingTag[name]);
		globalFloatingTags[name]["cm"]=outColors["cm"];
		globalFloatingTags[name]["cM"]=outColors["cM"];
		globalFloatingTags[name]["symb"]=outColors["symb"];
		attributedTagsColorsArray[name] = globalFloatingTags[name]["cm"];
	    } else {
		attributedTagsColorsArray[name] = ColorSticker(l);
	    }
	}
	if (configTagsBehaviour.showAll)  { 
	    if (name in floatingTag) {
		var outColors=ColorSticker(globalFloatingTags[name]["l"],floatingTag[name]);
		stickers.addSticker(name,attributedTagsColorsArray[name],outColors);
	    } else {
		stickers.addSticker(name,attributedTagsColorsArray[name]);
	    }		
	}
    }
    globalTagsList.sort();
    // remove Off tag at the end of nodeTagList.
    stickers.removeSticker('On');
    nodeTagList.pop();
    //console.log("nodeTagList",nodeTagList)

    /** Zoom button on each node */
    var thezoomnode = new zoomNodes(id);

    /** QRcodes to get URI of the node with a tablet 
     */
    var theqrcode = "";
	    
    //***************************************************methods***************************************************//


    //*****loaded******//

    this.getLoadedStatus = function()  { 
	return loaded;
    }

    this.setLoadedStatus = function (bool)  { 
	loaded = bool;
	if (bool) {
	    if ( nodeTagList.some(function(e) {return e=='Off'}) ) {
		nodeTagList[nodeTagList.findIndex(function(e) {return e=='Off'})] = "On";
		stickers.removeSticker('Off');
		stickers.addSticker("On",attributedTagsColorsArray["On"]);
		this.setQRcodeStatus()
	    }
	} else {
	    if ( nodeTagList.some(function(e) {return e=='On'}) ) {
		nodeTagList[nodeTagList.findIndex(function(e) {return e=='On'})] = "Off";
		stickers.removeSticker('On');
		stickers.addSticker("Off",attributedTagsColorsArray["Off"]);
	    }
	}
	//console.log("nodeTagList setLoadedStatus",nodeTagList, bool)
    }


    //*****OnOff******//

    this.getOnOffStatus = function()  { 
	return onoff;
    }

    this.setOnOffStatus = function (bool)  { 
	onoff = bool;
    }

    //*****QRcode******//
    this.getQRcodeStatus = function()  {	
	return qrcoded;
    }

    this.setQRcodeStatus = function()  {
	if (! qrcoded)
	    theqrcode = new QRcodes(id,jsonData);
	qrcoded=true;
    }
    //******id & idLocation******//

    //--getter 
    this.getId = function(){	
	return id;
    };

    //--getter 
    this.getIdLocation = function(){	
	return idLocation;
    };

    //--setter 
    this.setIdLocation = function(idloc){	
	idLocation=idloc;
    };


    //******Menu******//

    this.getNodeMenu = function(){

	return nodeMenu;
    };

    //******jsonData******//

    //--getter 
    this.getJsonData = function(){	
	return jsonData;
    };

    //--getter 
    this.setJsonDataUrl = function(newurl){	
	jsonData.url=newurl;
    };

    //*****Comment******//

    this.getComment = function()  { 
	return $('#postit'+id)[0].textContent;
    }

    //******nodeOpacity******//

    //--getter 
    this.getNodeOpacity = function(){	
	//console.log("get no",nodeOpacity);
	return nodeOpacity;
    };

    //--getter 
    this.setNodeOpacity = function(newOpacValue){	
	nodeOpacity = newOpacValue;
	//console.log("set no", nodeOpacity);
    };

    //******nodeAngle******//

    //--getter 
    this.getNodeAngle = function(){	
	//console.log("get no",nodeAngle);
	return nodeAngle;
    };

    //--getter 
    this.setNodeAngle = function(newAngleValue){	
	nodeAngle = newAngleValue;
	//console.log("set no", nodeOpacity);
    };

    //******nodeTagList*****//
    //--getter
    this.getNodeTagList = function(){
	return nodeTagList;
    };
    //--addElement
    this.addElementToNodeTagList = function(text_){
	if (nodeTagList.indexOf(text_)==-1)  { 
	    nodeTagList.push(text_);
	    nodeTagList.sort();
	}
	//console.log("after addition", nodeTagList);
    };
    //--removeElement
    this.removeElementFromNodeTagList = function(text_){
	for(var i=0;i<nodeTagList.length;i++)  { 
	    if (nodeTagList[i]==text_)  { 
		nodeTagList.splice(i,1);
		break;
	    }

	}
	stickers.removeSticker(text_);
	//console.log("after removing", nodeTagList);
    };


    //******Stickers******//

    //--getter 
    this.getStickers = function(){	
	return stickers;
    };

    //******QRcode******//

    //--getter 
    this.getQRcode = function(){	
	return theqrcode;
    };


    //******isMoving******//

    //--getter 
    this.getIsMoving = function(){	
	return isMoving;
    }

    //--setter 
    this.setIsMoving = function(boolmoving){	

	isMoving=boolmoving;
    }	




    //******htmlNode******//	

    //--getter
    this.getHtmlNode = function(){

	return htmlNode;
    }

    //--update	
    /** 
	Exemple : 
	********I moved my node ( the JS object) to some location, so to see it on the screen I need to move my htmlNode 
	-> node.updateHtmlNodeFromLoc(node.getLocation());

	********I moved my htmlNode, so i need to update the node Location 
	-> node.updateHtmlNodeLoc();

	You can also choose if you want an animation...

	You don't have to use directly these functions, they are just tools to others functions which manage 
	node position
    */	

    this.isInViewport = function() {
	if (my_inactive) {
	    var hnode=this.getHtmlNode();
	    window_test=my_window["left"] < relativeLeft+hnode.position().left+parseInt(hnode.css("width")) &&
		my_window["right"] > relativeLeft+hnode.position().left && 
		my_window["top"] < hnode.position().top+parseInt(hnode.css("height")) &&
		my_window["down"] > hnode.position().top
	    //console.log("window test :",window_test)
	    return window_test;
	} else
	    return true;
    };

    this.updateUrl = function() {
	var id=this.getId();
	var iframe = $('#iframe'+id);
	if(this.getJsonData().url!='undefined' && this.getOnOffStatus())  { 
	    if (iframe.css("display") != "inline") {
		iframe.show();
		//this.setLoadedStatus(true);
	    } else {
		// loadfunction = function () {
		if ( this.isInViewport() ) {
		    if (iframe.attr("src") == "") {
			iframe.attr("src",this.getJsonData().url);
			this.setLoadedStatus(true);
		    }
		} else {
		    iframe.attr("src","");
		    this.setLoadedStatus(false);
		}
		// }
		// loadfunction()
		//setTimeout(loadfunction, id*100);
	    }
	}
    };
    
    this.updateHtmlNodeFromLoc = function(loc){
	var position = htmlNode.position();
	position.left=loc.getX();
	position.top=loc.getY();
	// This line is the grid :
	htmlNode.offset(position);
	// Update URL if tile becomes visible
	this.updateUrl();
    };

    this.updateHtmlNodeFromHW = function(newHeight,newWidth){
	htmlNode.css({height : newHeight , width : newWidth});
    };

    this.updateLocFromHtmlNode = function(booleanAnimation){
	var position = htmlNode.offset();
	location.setX(position.left);
	location.setY(position.top);	
    };


    //******State******// 
    //remember state is a number and are just a way to distinguish different state of the node
    //States : 0 = not clicked
    //	   1 = hovered
    //	   2 = clicked
    //	   3 = drag and drop achieved
    //	   4 = transparent

    //--update		
    this.updateHtmlNodeState = function(newState){
	state=newState;
    }

    //--getter
    this.getState = function(){	
	return state;
    };



    //******Selected******// 

    //--update node	
    //remember state is a boolean and are just another way to distinguish if the node is selected or not

    this.updateSelectedStatus = function(newStatus){

	isSelected=newStatus;

	if(isSelected==true)  { 
	    mesh.addSelectedNode(this);
	    //$('#'+id).css("color","red");
	    var HB=$('#hitbox'+id);
	    HB.css('background-color', colorHBselected);
	} else { 
	    mesh.removeSelectedNode(this);
	    var HB=$('#hitbox'+id);
	    HB.css('background-color', colorHBdefault);
	}
    }

    //--getter node selected status
    this.getSelectedStatus = function(){
	return isSelected;
    };



    //******height and width******//

    this.updateHW= function (newHeight,newWidth){
	// minHeight and minWidth are yet to test ! 
	if(typeof newHeight == 'number' && newHeight > configBehaviour.minHeight)  { 
	    height=newHeight;
	} else { 
	    height=configBehaviour.minHeight;
	}

	if(typeof newWidth == 'number' && newWidth > configBehaviour.minWidth)  { 
	    width=newWidth;
	} else { 
	    width=configBehaviour.minWidth;
	}

	this.updateHtmlNodeFromHW(height, width);
    }




    //******location & mlocation******//

    //--getter
    this.getLocation = function (){

	return location;
    }

    //--getter
    this.getmLocation = function (){

	return mlocation;
    }

    //--setter

    this.setLocation = function(loc, boolAnimation, speed_){

	if(boolAnimation==true  && this.getIsMoving()==false  )  { 

	    this.setIsMoving(true);

	    //this.updateLocFromHtmlNode();
	    var currentLoc = this.getLocation();
	    loc.setX(loc.getX());
	    loc.setY(loc.getY());
	    var sx=loc.getX()-currentLoc.getX();
	    var sy=loc.getY()-currentLoc.getY();
	    var distInit = Math.sqrt(sx*sx+sy*sy);

	    if(typeof speed_ =='number' && speed_ > 0 )  { 
		var speed = parseInt(speed_);
	    } else { 
		var speed=parseInt(configBehaviour.animationSpeed);
		//console.log(speed);
	    }

	    var hnode=this;
	    var u=0;
	    var move = function(){


		$('#'+hnode.getId()).animate({ "left" : "+="+speed*sx/distInit, "top" : "+="+speed*sy/distInit}, 10, "linear",

					     function() {
						 hnode.updateLocFromHtmlNode();
						 currentLoc = hnode.getLocation();
						 u++;

						 var slocx=loc.getX()-currentLoc.getX();
						 var slocy=loc.getY()-currentLoc.getY();
						 var distLoc=Math.sqrt(slocx*slocx+slocy*slocy);
						 if(distLoc>speed+1 && u<50)  { 
						     move();
						     hnode.setOpacityLocation();
						 } else { 
						     hnode.setLocation(me.locationProvider(hnode.getIdLocation()) );
						     //return 0;
						 }	

					     }
					     );													
		return 0;				
	    };		

	    move();
	} else { 	
	    location = loc;
	    this.updateHtmlNodeFromLoc(location, boolAnimation);
	}
	this.setIsMoving(false);
	this.setOpacityLocation();
    }



    //******Post It All ******//

    //--update position & size
    this.updatePostItPositionandSize = function(){

	// for(var k=0;k < nodeTagList.length;k++)  { 
	//     var name=nodeTagList[k];
	//     if (name in floatingTag) {
	// 	$('#postit'+id)[0].textContent=$('#postit'+id)[0].textContent+'\n'
	// 	    +floatingTag[name]["m"].toString()+" <= "+floatingTag[name]["val"].toString()+" <= "+floatingTag[name]["M"].toString();
	//     }
	// }

	var options = {id : "postit"+id,posX : this.getLocation().getX() , posY	: this.getLocation().getY() + mesh.me.getSpread().Y };
	//, width : mesh.me.getSpread().X, height	: mesh.me.getSpread().Y
	$('#postit'+id).postitall('options', options);
	//$('#postit'+id).remove();


    };



    //******Special methods ******//



    /** When a node is created, we need to place him on screen*/
    (    function(){
	nodeRef.setLocation(location,false);
    }());

};
    })
