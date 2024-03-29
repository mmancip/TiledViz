	/** Mesh Class 
	    This object will manage all the nodes
	    The mesh here is a grid but it's possible to modify (add options)
	    setLocation and setmLocation to propose other kinds of meshes

	    Parameters :
	    - cardinal -> number of mesh elements ( i.e. number of node/simulation)
	    - NumColumnsConstant -> If the number of must be constant ( if not, the number of columns will gColumnth with the screen size)
	    - maxNumOfColumns_ -> if  NumColumnsConstant=true  , maxNumOfColumns_ will determine the numbre of columns on the grid 
	    if  NumColumnsConstant=false, maxNumOfColumns_ will determine the maximal number on the grid	, if the screen is too big, node and his contents will be rescale
	*/

$(document).ready(    function (){

    addBlink=function(myButton) {
	if (typeof(myButton.addClass) == "undefined") {
	    $('#'+myButton.id).addClass('BlinkIcon');
	} else { 
	    myButton.addClass('BlinkIcon');
	}

	myButtonUnBlink=function(myButton) {
	    if (typeof(myButton.removeClass) == "undefined") {
		$('#'+myButton.id).removeClass('BlinkIcon');
		var theId=myButton.id;
	    } else { 
		myButton.removeClass('BlinkIcon');
		var theId=myButton.prop('id');
	    }
	    //console.log("myButtonUnBlink",theId);
	}
	setTimeout(myButtonUnBlink,2000,myButton);
    };

    // add a short blink on legend if a notification is printed.
    var notif_observer = new MutationObserver(function(e) {addBlink($(".main-legend-zone"))});
    notif_observer.observe($('#notifications').get(0), {childList: true, subtree: true});

    // Get style.css StyleSheet Rules
    var stylesheets = document.styleSheets;
    var sstyleRuleBorderBlink="";
    var BorderBlinkColor=false;
    if (stylesheets) {
      var sstyle = "";
      var RuleBorderBlinkId = "";
      for (var i = 0; i < stylesheets.length; ++i) {
        if (stylesheets[i].href) {
      	  if (stylesheets[i].href.includes("style.css")) {		    
      	      sstyle = stylesheets[i];
      	      // Chrome definition
      	      try {
      	          for (var j = 0; j < sstyle.rules.length; ++j ) {
      	     	      if (sstyle.rules[j].type == 7) 
      	     		  if (sstyle.rules[j].cssRules[0].style.cssText.includes("outline-color")) {
      	     		      RuleBorderBlinkId=j;
      	     		      sstyleRuleBorderBlink=sstyle.rules[j].cssRules[0].style;
      	     		      BorderBlinkColor=true;
      	     		      break;
			  }
      	          }
      	      } 	catch(err)  {
      	          // Firefox definition
      	          try {
      	     	      for (var j = 0; j < sstyle.cssRules.length; ++j ) {
      	     		  if (sstyle.cssRules[j].cssText.includes("outline-color")) {
      	     		      RuleBorderBlinkId=j;
      	     		      sstyleRuleBorderBlink=sstyle.cssRules[j];
      	     		      BorderBlinkColor=true;
      	     		      break;
			  }
      	     	      }
      	          } catch(err1)  {
      	     	      // not portable
      	          }
      	      }
      	  }
        }
      }
    }
	
    addBorderBlink=function(myElem,myColor) {
	if (typeof(myElem.addClass) == "undefined") {
	    //$('#'+myElem.id).css("outline-color",myColor);
	    if (BorderBlinkColor)
		sstyleRuleBorderBlink.cssText=sstyleRuleBorderBlink.cssText.replace(/outline-color: .*;/,"outline-color: "+myColor+";");
	    $('#'+myElem.id).addClass('BlinkBorder');
	    
	} else if (typeof(myElem[0]) == "object") {
	    //myElem.css("outline-color",myColor);
	    if (BorderBlinkColor)
		sstyleRuleBorderBlink.cssText=sstyleRuleBorderBlink.cssText.replace(/outline-color: .*;/,"outline-color: "+myColor+";");
	    myElem.addClass('BlinkBorder');
	}

	myElemBorderUnBlink=function(myElem) {
	    if (typeof(myElem.removeClass) == "undefined") {
		$('#'+myElem.id).css("border","hidden");
		$('#'+myElem.id).removeClass('BlinkBorder');
		var theId=myElem.id;
	    } else if (typeof(myElem[0]) == "object") {
		myElem.css("border","hidden");
		myElem.removeClass('BlinkBorder');
		var theId=myElem.prop('id');
	    }
	}
	setTimeout(myElemBorderUnBlink,2000,myElem);
    };

    function download(content, fileName, contentType) {
	var a = document.createElement("a");
	var file = new Blob([content], {type: contentType});
	a.href = URL.createObjectURL(file);
	a.download = fileName;
	a.click();
	URL.revokeObjectURL(a.href)
    }
    //download(jsonData, 'json.txt', 'text/plain');
    
    _allowDragAndDrop = true; // block Drag and Drop if false
    BlockDragAndDrop=function() {
	_allowDragAndDrop = false;
	$('.handle').addClass("drag-handle-off").removeClass("drag-handle-on");
    };

    EnableDragAndDrop=function() {
    	_allowDragAndDrop = true;
	$('.handle').addClass("drag-handle-on").removeClass("drag-handle-off");
    }

    function parseBool(val) { return val === true || val === "true" };
    
Mesh = function(cardinal,NumColumnsConstant,maxNumOfColumns_) {

    $('#legend').html("<h1>Working on "+my_session+"</h1> <h2>Number of nodes : "+cardinal.toString()+"</h2>");

    // Bool to add initial position in tags of each tile
    var debugPos = false;
    
    me = this; // Reference to the mesh
    var nodeCardinal = cardinal; // Number of nodes on the mesh
    var nodesById = []; // Table containing all the nodes on the mesh indexed by --> "node"+id<-- 
    // Example : nodesById ["node"+0] -> get the node with id =0;
    var nodesByLoc = []; // Table containing all the nodes on the mesh indexed by idLocation 
    // Example : nodesByLoc [0]-> give the node located at the top-left place;
    var nodesOldPositions = []; // Double table containing position of nodes after each user-made movement
    // Example : nodesById[5][3] ->gives the idlocation of third (id = 3) node after 5 users actions where node has been moved
    // To debug nodesByLoc and nodesById :
    // arr=[]; for (var U in nodesById) { arr.push([nodesById[U].getIdLocation(),U,nodesById[U].getId()]) }; arr
    // arr.sort((a, b) => a[0] - b[0]).map(x=>x[2]) must be always "equal" to nodesByLoc.map(x=>x.getId()) 
    var stepBack=1; // Variable to help managing nodesOldPositions : it is incremented when users go back and decremented when users go forward 
    var lines = []; // Contains references to the first node of each line
    var columns = []; // Contains references to the first node of each column
    var numOfLines = []; // Number of lines
    var numOfColumns = []; // Number of columns
    var maxNumOfColumns = maxNumOfColumns_; // Maximal number of columns
    var locationJsonDataConsistency = false ; // Decided in the next function
    var widthTab = new Array(); // Table indexed by the id:  widthtab[theid] contains the width of the picture on the node with id = theid 
    var heightTab = new Array(); // Same for the height
    var columnSelected = -1 ;  // Contains the number of a selected column (first column corresponds to 0)
    var lineSelected = -1 ; // Contains the number of a selected line (first line corresponds to 0)

    var touchspeed = configBehaviour.touchSpeed; // speed of touch move;

    // Rotation increment
    var RotInc=0.5;
    if (parseBool(configBehaviour.smoothRotation)) {
	RotInc=parseFloat(configBehaviour.RotationSpeed); //for a smooth touchmove rotation
    } else {
	// for a turn over with only touchstart / touchend (no touchmove) events
	RotInc=180; 
    }


    var zoomSelection = false;
    var removingTag = false;
    var tagToRemove = "";
    var selectingTags = false;
    var tagToSelect = "";
    var alignTags = false;
    var alignOrderTag=true; // true is increase, false is decrease
    
    var hideNodesTag = false;
    var killNodesTag = false;
    var transparentNode = -1; // Default

    var HideNodesTagFlag=false; // Flag indicated the use of HideTags menu to hide nodes with selected tag in tagMenu.

    var KillNodesTagFlag=false; // Flag indicated the use of KillTag menu to suppress nodes with selected tag in tagMenu.
    var SelectionMultipleTagsFlag = false;     // Flag indicated the use of SelectMultipleTags for grouping tags in a new tag.
    var seltags=""; // Name of the selection tag if SelectionMultipleTagsFlag = true
    var SelectionNodeToTagFlag=false; // Flag indicated the use of SelectionNodeToTag menu to add tag for nodes in selection.
    var PaletteNodeTagFlag=false; // Flag indicated the use of ChoosingColor menu to change tag color with selected tag in tagMenu.

    TagHeight=0; // tag-legend zone height
    
    // Correct wrong default config
    if (!! configBehaviour.onlyMasterMS)
	configBehaviour.onlyMasterMS=false
    configBehaviour.touchonWindow=false
    
    // Getter and setter for zoomSelection
    this.getZoomSelection = function(){
	return zoomSelection;
    };

    this.setZoomSelection = function (bool){
	zoomSelection = bool;		
    };

    // Getter and setter for removingTag
    this.getRemovingTag = function(){
	return removingTag;
    };

    this.setRemovingTag = function(bool){
	removingTag = bool;
    };

    this.getTagToRemove = function(){
	return tagToRemove;
    };

    this.setTagToRemove = function(text){
	tagToRemove = text;
    };

    // Getters and setters for selectingTags
    this.getSelectTags = function()  { 
	return selectingTags;
    };
    this.setSelectTags = function(bool){
	selectingTags = bool;
    };

    this.getSelectionTag = function()  { 
	return SelectionNodeToTagFlag;
    };
    this.setSelectionTag = function(bool){
	SelectionNodeToTagFlag = bool;
    };

    this.getSelectMultipleTags = function()  { 
	return SelectionMultipleTagsFlag;
    };
    this.setSelectMultipleTags = function(bool){
	SelectionMultipleTagsFlag = bool;
	if (! SelectionMultipleTagsFlag) {
	    $('.closeSelectMultipleTagsButtonIcon').removeClass('closeSelectMultipleTagsButtonIcon').addClass('selectMultipleTagsButtonIcon');
	}
    };

    
    this.getTagToSelect = function(){
	return tagToSelect;
    };

    this.setTagToSelect = function(text){
	tagToSelect = text;
    };


    // Getters and setters for alignTags
    this.getAlignTags = function()  { 
	return alignTags;
    };
    this.setAlignTags = function(bool){
	alignTags = bool;
    };

    // Getters and setters for hideNodesTag
    this.getHideNodesTag = function()  { 
	return hideNodesTag;
    };
    this.setHideNodesTag = function(bool){
	hideNodesTag = bool;
    };

    this.getHideNodesTagFlag = function()  { 
	return HideNodesTagFlag;
    };
    this.setHideNodesTagFlag = function(bool){
	HideNodesTagFlag = bool;
    };

    // Getters and setters for killNodesTag
    this.getkillNodesTag = function()  { 
	return killNodesTag;
    };
    this.setkillNodesTag = function(bool){
	killNodesTag = bool;
    };

    this.getKillNodesTagFlag = function()  { 
	return KillNodesTagFlag;
    };
    this.setKillNodesTagFlag = function(bool){
	KillNodesTagFlag = bool;
    };

    // Add Opacity sliders zone
    $('header').append("<div id=OpacityZone ></div>")
    
    // Getter and setter for the transparency
    this.getTransparent = function(){
	return transparentNode;
    };
    this.setTransparent = function(id, state){ // State is true to set the node transparent, false to unset it

	transparentNode = state ? id : -1;

	this.getNode(id).updateHtmlNodeState(state ? 4 : 0);
	var nodeOpacity = this.getNode(id).getNodeOpacity();
	$('#'+id).css("opacity", state ? nodeOpacity : 1);
	$('#'+id).css("z-index", state ? 100 : 0 );
	$('#tile-opacity-'+id).css("visibility", state ? "visible" : "hidden");

	if (state)  { 
	    $('#'+id).addClass("transparentNode");
	    for( mi in $('#menu'+id)[0].childNodes ){
		m=$('#menu'+id)[0].childNodes[mi];
		if (m.id && m.id.search("option") > -1) {
		    if ( m.className.search("transparentButtonIcon") > -1) {
		    } else {
			$('#menu'+id+'>#'+m.id).css({visibility : "hidden"});
		    }
		}
	    }
	    $('#tile-opacity-'+id).append("<input id=tileOpacitySlider"+id+" class=tile-opacity-slider type='range' name=tileOpacitySlider"+id+" min=0 max=100 value="+nodeOpacity*100+">");
	    $('#tileOpacitySlider'+id).off("click").off("mousup");
	    $('#tileOpacitySlider'+id).on({
		click : function(){
		    var nodeOpacity_ = Math.max($('#tileOpacitySlider'+id).val()/100, 0.1);
		    $('#'+id).css("opacity", nodeOpacity_);
		},
		mouseup : function(e) {
		    var nodeOpacity_ = $('#tileOpacitySlider'+id).val()/100;
		    cdata={"room":my_session,"Id":id,"Opacity":nodeOpacity_};
		    socket.emit("change_Opacity", cdata, callback=function(sdata){
 		    	console.log("socket change Opacity Tag ", cdata);				
		    });
		}
	    });
	    var val = ($('#tileOpacitySlider'+id).val() - $('#tileOpacitySlider'+id).attr('min')) / ($('#tileOpacitySlider'+id).attr('max') - $('#tileOpacitySlider'+id).attr('min'));

	    $('#tileOpacitySlider'+id).css('background-image',
					   '-webkit-gradient(linear, left top, right top, '
					   + 'color-stop(' + val + ', rgb(255, 0, 0)), '
					   + 'color-stop(' + val + ', rgb(0, 255, 0))'
					   + ')'
					   );
	    ;

	    $('#tileOpacitySlider'+id).change(function () {
		    var val = ($(this).val() - $(this).attr('min')) / ($(this).attr('max') - $(this).attr('min'));

		    $(this).css('background-image',
				'-webkit-gradient(linear, left top, right top, '
				+ 'color-stop(' + val + ', rgb(255, 0, 0)), '
				+ 'color-stop(' + val + ', rgb(0, 255, 0))'
				+ ')'
			       );
		});

	} else { 
	    $('#'+id).removeClass("transparentNode");
	    me.meshEventReStart();

	    for( mi in  $('#menu'+id)[0].childNodes ){
		m=$('#menu'+id)[0].childNodes[mi];
		if (m.id && m.id.search("option") > -1) {
		    if (m.className.search("transparentButtonIcon") > -1)  {
		    } else {
			$('#menu'+id+'>#'+m.id).css({visibility : ""});
		    }
		}
	    }
	    $('#tile-opacity-'+id).css("visibility", "hidden");
	    me.getNode(id).setNodeOpacity(Math.max($('#tileOpacitySlider'+id).val()/100, 0.1));
		    
	    $('#tileOpacitySlider'+id).remove();

	}

    };


    /** We use jsonData to place our node on the screen only if the jsondata are 
	consistent.*/
    (    function(){

	var j = 0;
	var t = 0;
	var Ntab = new Array();
	for(j=0;j<jsDataTab.length;j++)  { 
	    Ntab.push(j);
	}
	for(j=0;j<jsDataTab.length;j++)  { 
	    if(typeof parseInt(jsDataTab[j].IdLocation) == "number" && Ntab.indexOf(parseInt(jsDataTab[j].IdLocation)) > -1)  { 
		Ntab.splice(Ntab.indexOf(parseInt(jsDataTab[j].IdLocation)),1);
		t++;
	    }
	}
	if(t==jsDataTab.length){
	    locationJsonDataConsistency =true;
	    useJsonDataLocation=true;

	} else { 
	    locationJsonDataConsistency = false;
	    useJsonDataLocation=false;

	}
    })();

    /**
       ColumnStyle variable is the parameter to manage the table visible on screen
       NumColumnsConstant -> If the number of must be constant ( if not, the number of columns will gColumnth with the screen size)
       maxNumOfColumns_ -> if  NumColumnsConstant=true  , maxNumOfColumns_ will determine the numbre of columns on the grid 
       if  NumColumnsConstant=false, maxNumOfColumns_ will determine the maximal number on the grid	, if the screen is too big, node and his contents will be rescale
    */
    var ColumnStyle = "dynamic"; 
    (    function(){

	if( !(typeof maxNumOfColumns =='number' && maxNumOfColumns> 2))  { 
	    maxNumOfColumns = 10;
	}

	if( NumColumnsConstant == true )  { 	
	    ColumnStyle = "static";
	}

    }());


    // Size of the nodes
    var spread = configBehaviour.spread;
    // Add 2% in X direction to be able to focus and type characters inside the iframe
    spread.X = spread.X*1.02;

    var borderSize = configBehaviour.borderSize; // In pixels

    var selectedNodes= new Array();// Table containing all selected nodes (TO DO : see if possible to use the same table for the two mechanisms ?)

    var nodesToToggle = new Array(); // Table to store a node to toggle with another (manipulations with the hitbox)

    var nodesToZoom = new Array(); // Table to store the nodes to zoom on (used with the hitbox and the menu)

    var appliedFilters = new Array();// Table containing all applied filters

    var listedTags = new Array(); // Table containing all user-created tags	

    //******nodesToZoom******//

    //--add node to zoom on 
    this.addNodeToZoom = function(node){	
	if (nodesToZoom.indexOf(node)==-1)  { 
	    nodesToZoom.push(node);	
	}
    }

    //--remove node to zoom on
    this.removeNodeToZoom = function(node){	
	nodesToZoom.splice(nodesToZoom.indexOf(node),1);
    };

    //--getter node selected status table
    this.getNodesToZoom = function(){
	return nodesToZoom;
    };

    //--reset table
    this.resetNodesToZoom = function(){
	nodesToZoom = new Array();
	for (O in nodesByLoc)
	    if (nodesByLoc[O].getNodeInViewportStatus())
		nodesByLoc[O].sub('hitbox').css({backgroundColor : colorHBdefault});

	return nodesToZoom;
    };

    /** This function allows us to zoom on a selection of nodes chosen by users on screen interface 
	Used for three different purposes : 
	-> Second option of global menu (zoom on filtered nodes)
	-> Third option of global menu (zoom on selected nodes)
	-> Second option of node menu (zoom on a node to draw upon it)

	Parameters : 
	- nodeZoomTab -> table containing the node chosen by users 
	- ratio -> sets the size of the zoom  (ratio = 1 <=> the same size)
	- initSpread -> original size of the node (to define the ratio)
	- Haswaypoint -> use waypoint to draw only visible magnified nodes (optionnal default false) 
    */	
    this.magnifyingGlass = function(nodeZoomTab,ratio,initSpread,Haswaypoint, initScale){
	// Size of the support for the zoomed node
	var initScale_ = initScale || false;
	if (initScale_) {
	    var supportW = parseInt(window.innerWidth*initScale_)-90;
	    var supportH = parseInt(ratio*(parseInt(window.innerWidth*initScale_)-500));
	    var Zscale=initScale_;
	} else {
	    var supportW = parseInt(window.innerWidth)-90;
	    var supportH = parseInt(ratio*(parseInt(window.innerWidth)-500));
	    var Zscale=1;
	}

	// No waypoint by default
	var Haswaypoint_ = Haswaypoint || false ;

	//waypoints are the object which can detect when a object are entering on screen
	// see http://imakewebthings.com/waypoints/ for details
	var waypoint = new Array();

	// Definition of the background $(#superSail) 
	if(nodeZoomTab.length!=0){		
	    // (each time tiles are magnified, it will be removed and re-created since it’s not a complex and heavy element)
	    $("body").append('<div id=superSail></div>');
	    $("#superSail").css({ // GLOBALCSS !
		    position : 'absolute',
			top : TagHeight,
			left : 0,
			height : "110%",
			width : "100%",
			backgroundColor : "black",
			opacity : "0.9",
			zIndex : 200,
			});
	    $("#superSail").off('touchstart');
	    $("#superSail").off('touchmove');
	    $("#superSail").off('touchend');
	    $('#superSail').append('<div id=buttonUnzoom class=unzoomButtonIcon></div>');
	    $('#buttonUnzoom').css({	// GLOBALCSS !					
		position : "fixed", 
		top : 0 ,
		left : parseInt($(me.menu.getHtmlMenuSelector()).css("width")),
		height : 200,
		width : 200,
		zIndex : 802,	
		backgroundColor: "rgba(0, 0, 0, 0.95)"
	    });


	    // unload nodes streams
	    for (O in nodesByLoc)
		if (nodesByLoc[O].getNodeInViewportStatus())
		    nodesByLoc[O].sub('iframe').hide();
	    // for(O in nodesById)  {
	    // 	nodesById[O].setLoadedStatus(false);
	    // }

	    // Additionnal space between columns
	    shiftcol=105

	    // Definition of the support $(#zoomSupport) for the node
	    // (only the first time, then it will be hidden and shown again)
	    var supp = document.getElementById("zoomSupport");
	    if (supp==null)  { 
		$("body").append('<div id=zoomSupport style="overflow-y: scroll;"></div>');
		$("#zoomSupport").css({ // GLOBALCSS !
			position: "fixed",
			    //top: (parseInt(window.innerHeight)-ratio*(parseInt(window.innerWidth)-500))/2,
		    top:Math.max(450,TagHeight+240),
			    left: -shiftcol-50,
			    marginTop: "0",
			    width: "102.5%",
			    height: "98%",
			    backgroundColor : "grey",
			    opacity : "1.",
			    display : "flex",
			    flexWrap: "wrap",
			    zIndex : 201,
			    });
		$("#zoomSupport").off('touchstart');
		$("#zoomSupport").off('touchmove');
		$("#zoomSupport").off('touchend');
	    } else { 
		$('#zoomSupport').show();
	    }

	    // Size of the grid
	    // Search for the upper and closest square number of the cardinal of the set of nodes chosen by users
	    var L = Math.min(nodeZoomTab.length,2);
	    if ( nodeZoomTab.length > 12 ) {
		L = Math.min(nodeZoomTab.length,3);
	    }

	    var W = supportW/L;
	    var H = supportH/L;

	    //console.log(H, W, supportH, supportW);
	    // Building the grid

	    // Number of zoomed elements
	    var NbZ=nodeZoomTab.length

	    // Number of lines
	    var NbL=Math.max(NbZ/L,1);

	    // space between zoomed tiles
	    var shiftX=60;
	    var shiftY=60;

	    var zoomX=W-shiftX;
	    ///initSpread.Y
	    var zoomY=H-shiftY;
	    //-shiftleft
	    // shiftleft=parseInt($('#zoomSupport>#'+id+'>#hitbox'+id).css('width'))		    
	    var Zscale=H/initSpread.Y;

	    shifttop=function(e) { return (H+60)*parseInt(e/L)+shiftY };
	    shiftleft=function(e) { return W*parseInt(e % L)+shiftX };

	    // To suppress properly some zoomed node :
	    nodeZoomState=new Array();
	    nodeZoomState.length=NbZ;
	    nodeZoomState.fill(true)
	    
	    // Stickers : on click, erase the sticker from the node
	    ZclickSticker = function(){
		// console.log("sticker clicked", this.id);
		var splittedId = this.id.split("_");
		var nodeId = splittedId.pop();
		var node = me.getNode(nodeId);
		var zoomed = $('#Zoomed'+nodeId);
		zoomed.children(".stickers_zone").find('#'+this.id).remove();
		var nodelev=$('#'+nodeId).css("z-index");
		$('#'+nodeId).css("z-index",999);
		thisSticker=$('#'+nodeId).children(".stickers_zone").find('#'+this.id);
		thisSticker.show();
		$('#'+nodeId).show();
		thisSticker.click();
		$('#'+nodeId).css("z-index",nodelev);
	    };


	    for(var e=0;e<NbZ;e++){

		thisnode=nodeZoomTab[e];
		// thisnode.updateSelectedStatus(false);

		id=thisnode.getId();
		thisnodeId=$("#"+thisnode.getId());
		var iframe2 = $('#iframe'+id);

		$("body").append('<div id=Zoomed'+e+' class=Zoomed></div>');
		thiszoom=$("#Zoomed"+e);
		thiszoom.appendTo("#zoomSupport");

		thiszoom.css({ // GLOBALCSS !
			position : 'absolute',
		    	    top : shifttop(e),
		            left : shiftleft(e)+shiftcol,
			    height : H,
			    width : W,
			    backgroundColor : "black",
			    opacity : "1.",
			    zIndex : 220,
			    });
		//				left : shiftleft,
		// thiszoom.off('touchstart');
		// thiszoom.off('touchmove');
		// thiszoom.off('touchend');

		// Copy iframe src from initial node
		iframesrc=thisnode.getJsonData().url;

		//htmlPrimaryParent.append('<div id='+id+' class='+className+'></div>');

		//iframe2=$("#iframe"+id); 		if (iframe2.is(':visible'))
		thiszoom.append('<iframe id=Ziframe'+e+' height="'+initSpread.Y+'px" width="'+initSpread.X+'px" position="relative"'+' scrolling="yes"'+' frameborder=0'+' src=""></iframe>');

		if ( Haswaypoint_ ) {

		    waypoint[e] =	new Waypoint({
				
			    offset : 'bottom-in-view' ,
			    element: document.getElementById("Zoomed"+e),
			    
			    handler: (    function(){
				    
				    var id = e;
				    var iframesrc_=iframesrc;
				    return function(direction) {
					if (direction == "down") {
					    iframe2=$('#Ziframe'+id);
					    if (iframe2.attr("src")=="")
						iframe2.attr("src",iframesrc_);
					    waypoint[id].destroy();
					} else {
					    iframe2=$('#Ziframe'+id);
					    if (iframe2.attr("src")=="")
						iframe2.attr("src",iframesrc_);
					    waypoint[id].destroy();
					}
				    };
				    
				})()
			    
			});
		} else 
		    $('#Ziframe'+e).attr("src",iframesrc);

		// Copy info from initial node
		var Zinfo=thisnodeId.children(".info").clone().css('display','block').appendTo("#Zoomed"+e);
		Zinfo[0].id="Z"+Zinfo[0].id;
		
		Zframe=$('#Ziframe'+e);
		Zframe.css('-webkit-transform','scale('+Zscale+')').css('-moz-transform','scale('+Zscale+')');
		// Zframe.off('touchstart');
		// Zframe.off('touchmove');
		// Zframe.off('touchend');

		Zinfo.css('-webkit-transform','scale('+Zscale/2+')').css('-moz-transform','scale('+Zscale/2+')');
		Zinfo.css('top',"-60px").css("left",zoomX*1./2).css("position","absolute");;
		Zinfo.show();
		
		// Copy sticker zone
		var Zsticker=thisnodeId.children(".stickers_zone").clone().css('display','block').appendTo("#Zoomed"+e);
		Zsticker[0].id="Z"+Zsticker[0].id;

		// Supress this zoomed node 
		thiszoom.prepend('<div id="Zclose'+e+'" class=unzoomButtonIcon></div>');
		Zclose=$('#Zclose'+e);
		Zclose.css({
		    position: 'absolute',
		    height:200,
		    width: 200,
		    left: spread.X*Zscale,
		    top: 0,
		    zIndex:400,
		    '-webkit-transform':'scale('+Zscale/4+')',
		    '-moz-transform':'scale('+Zscale/4+')'
		});
		Zclose.on("click",function() {
		    var e = parseInt(this.id.replace("Zclose",""));
		    $("#Zoomed"+e).remove();
		    nodeZoomState[e]=false;
		    var iter=0;
		    for(var ee=0;ee<NbZ;ee++){
			if ( ee != e && nodeZoomState[ee] ) {
			    thiszoom=$("#Zoomed"+ee);

			    thiszoom.css({
	    			top : shifttop(iter),
	    			left : shiftleft(iter)
			    });
			    iter = iter + 1;
			}
		    }
		});

		Zsticker.css('-webkit-transform','scale('+Zscale/2+')').css('-moz-transform','scale('+Zscale/2+')');
		Zsticker.css({
		    left: spread.X*Zscale+80,
		    top: (parseInt(Zclose.css("top"))+
			  parseInt(Zclose.css("height")))*Zscale,
		    position: "absolute",
		    display: "block",
		    zIndex:999		  
		});
		Zsticker.children('.sticker').on({
		    click : ZclickSticker
		});
	    }
	}

	// Add zoom slider
	var zoomValue = $('#zoomSupport').children(".Zoomed").children("iframe").css("transform");
	zoomValue = zoomValue.replace("matrix(", "").replace(")", "").split(",")[0];
	//console.log("zoom value", zoomValue);
	$('#superSail').append("<div id=zoom-slider-label>Zoom level</div>")
	.append("<input id=zoomSlider name=zoomSlider class=slider type=range min="+zoomValue/2+" max="+2*zoomValue+" step=0.01 value="+zoomValue+" oninput='zoom.value=zoomSlider.value.toString()'>")
	.append("<output name=zoom id=zoom class=slider for=zoomSlider>"+zoomValue+"</output>");

	$('#zoomSlider').change(function () {
		var val = ($(this).val() - $(this).attr('min')) / ($(this).attr('max') - $(this).attr('min'));
			
		$(this).css('background-image',
			    '-webkit-gradient(linear, left top, right top, '
			    + 'color-stop(' + val + ', rgb(255, 0, 0)), '
			    + 'color-stop(' + val + ', rgb(0, 255, 0))'
			    + ')'
			    );
	    });
	$('#zoom-slider-label').css({
		position : "fixed",
		    fontSize : "150px",
		    top :0,
		    left : "50%",
		    color : "white",
		    backgroundColor: "rgba(0, 0, 0, 1)"
		    });
	$('#zoomSlider').css({
		position : "fixed",
		    top : parseInt($('#buttonUnzoom').css("height")),
		    left : "60%",
	            width : 30/100 * parseInt($('header').css("width")),
		    backgroundColor: "rgba(0, 0, 0, 1)"
		    });
	var val = (zoomValue - $('#zoomSlider').attr('min')) / ($('#zoomSlider').attr('max') - $('#zoomSlider').attr('min'));
			
	$('#zoomSlider').css('background-image',
			     '-webkit-gradient(linear, left top, right top, '
			     + 'color-stop(' + val + ', rgb(255, 0, 0)), '
			     + 'color-stop(' + val + ', rgb(0, 255, 0))'
			     + ')'
			     );
	$('#zoom').css({
		position: "fixed",
		    fontSize : "150px",
		    left : parseInt($('#zoomSlider').css("width")) + parseInt($('#zoomSlider').css("left")),
		    top: 0,
		    color: "white",
		    zIndex: 802,
		    padding: "0px 50px",
		    backgroundColor: "black"
		    });
	//$('#zoom').css('background-image','none');

	$('#zoomSlider').on({
		click : function(e){
		    if ( configBehaviour.sharedSliderZoom && emit_click_val('slider','zoomSlider', $('#zoomSlider').val()) )
			return
		    if ( configBehaviour.sharedSliderZoom && emit_click_val('slider','zoom', $('#zoomSlider').val()) )
			return
		    
		    var newZoom = $('#zoomSlider').val();
		    $('#zoom').val(newZoom);
		    var ratio = newZoom/zoomValue;
		    $('#zoomSupport').css("-moz-transform","scale("+ratio+")").css("-webkit-transform","scale("+ratio+")").css("transform-origin", "0 0 0");
		    e.stopPropagation(); // To stay on zoomSupport
		}
								
								
	    });

	// unZoom function
	$('#buttonUnzoom').on('click',function(){		

	    $("#superSail").remove();
	    $("#zoomSupport").hide();
	    $('#zoomSupport').css("-moz-transform","scale(1)").css("-webkit-transform","scale(1)").css("transform-origin", "0 0 0");
	    $('#zoomSupport').children(".Zoomed").remove();
	    $("#buttonUnzoom").off();
	    $("#buttonUnzoom").remove();

	    // TODO : only on and visible
	    for (O in nodesByLoc)
		if (nodesByLoc[O].getNodeInViewportStatus()) {
		    nodesByLoc[O].sub('hitbox').off().on("click", clickHBSelect);
		    nodesByLoc[O].sub('iframe').show();
		}
	    //me.startLoading();
	    
	});

	return Zscale;
    };


    
    var moveMesh = function(direction)  { 
	numOfLines = Math.floor(nodeCardinal / numOfColumns);
	numOfLines = Math.min(numOfLines, nodeCardinal);

	me.computeNumColumns();
	for (var i=0;i<(numOfLines-1);i++)  { 
	    //console.log(i, numOfLines);
	    if (direction == "up")  { 
		//console.log("going up", i);
		var firstLine = i;
		var secondLine = i+1 == numOfLines ? 0 : i+1;
	    }
	    else if (direction == "down")  { 
		//console.log("going down", i);
		var firstLine = numOfLines - 1 - i;
		var secondLine = numOfLines - 2 - i;
	    }

	    var firstLineTab = new Array();
	    var secondLineTab = new Array();

	    for (O in nodesByLoc)  { 
		if (me.mlocationProvider(nodesByLoc[O].getIdLocation()).getnY() == firstLine )  { 
		    firstLineTab.push(nodesByLoc[O]);
		}
		else if (me.mlocationProvider(nodesByLoc[O].getIdLocation()).getnY() == secondLine )  { 
		    secondLineTab.push(nodesByLoc[O]);
		}
	    }
	    for (var j=0; j<Math.max(firstLineTab.length, secondLineTab.length);j++)  { 
		var tmpBoolBlockMove = j == 0 ? false : true; 
		if(typeof firstLineTab[j]!= "undefined" && typeof secondLineTab[j]!= "undefined" )  { 
		    me.switchLocation(firstLineTab[j],secondLineTab[j],configBehaviour.showAnimationsLineColSwap, true, tmpBoolBlockMove);
		}
	    }
	}
	for (O in nodesByLoc)  { 
	    if (nodesByLoc[O].getNodeInViewportStatus()) {
		//nodesByLoc[O].getOnOffStatus() &&
	    	SetOn(nodesByLoc[O].getId());
	    } else {
	    	SetOff(nodesByLoc[O].getId());
	    }
	}
	// for (O in nodesByLoc)
	//     console.log(O,nodesByLoc[O].getId(),nodesByLoc[O].getIdLocation(),nodesByLoc[O].getHtmlNode().children("iframe"))
    };
    
    // Refresh nodes function
    
    refreshNodes = function (node) {

	// check if optionnal argument node is present (node can be "0" == false in javascript)
	var hasNoNode=false
	if (typeof(node) == "undefined")
 	    hasNoNode = true

	//console.log("test refresh");

	if (hasNoNode) {// ie no node specified -> refresh all nodes
	    for (O in nodesByLoc)  { 
		nodesByLoc[O].setNodeInViewportStatus()
		if (nodesByLoc[O].getNodeInViewportStatus()) {
		    me.loadContent(O);
		    SetOn(nodesByLoc[O].getId());
		} else {
		    SetOff(nodesByLoc[O].getId());
		}
		//     nodesByLoc[O].getHtmlNode().children('iframe')[0].setAttribute("src","");
		//     nodesByLoc[O].getHtmlNode().children('iframe')[0].setAttribute("src",nodesByLoc[O].getJsonData().url);
	    }

	    for (O in nodesById) {
		me.unsetDraggable(nodesById[O].getId(), false, false);
	    }

	    // Onnodes = $('.On').parent().parent().children('iframe');
	    // for (node in Onnodes) {
	    // 	if (node != "prevObject" && typeof Onnodes[node] == "object"
	    // 	    && nodesByLoc[Onnodes[node].parentElement.id].getLoadedStatus()) {
	    // 	    Onnodes[node].setAttribute("src","")
	    // 	    Onnodes[node].setAttribute("src",nodesById["node"+Onnodes[node].parentElement.id].getJsonData().url);
	    // 	}
	    // }
	    // for (node in Onnodes) {
	    // 	if (node != "prevObject" && typeof Onnodes[node] == "object") {
	    // 	    Onnodes[node].setAttribute("src",oldSrc[node]);
	    // 	}
	    // }
	} else {
	    nodesByLoc[node].setNodeInViewportStatus()
	    me.unsetDraggable(node); 
	} 
	me.meshEventReStart();

	EnableDragAndDrop();
    };

    receive_deploy_Selection=false
    socket.on('receive_deploy_Selection', function(sdata){
     	console.log("receive_deploy_Selection",sdata);
	var listSelectionIds = eval(sdata["Selection"]);
	for (O in listSelectionIds) {
	    var HB = $('#hitbox' + listSelectionIds[O]);
	    var node = nodesById["node"+listSelectionIds[O]];
	    node.updateSelectedStatus(true); 
	    me.addNodeToZoom(node); 
	    HB.css({backgroundColor : colorHBtoZoom});
	}
	receive_deploy_Selection=true
    });

    // Update the Mesh
    socket.on('receive_deploy_nodes', function(sdata){
     	console.log("receive_deploy_nodes",sdata);
	var jsDataTab_mod = sdata["modtiles_data"]; // modtiles_data.append([tile1,tile2])

	// modifiy some nodes
	for ( idadd in jsDataTab_mod ) {
	    var tile1=jsDataTab_mod[idadd][0]
	    var tile2=jsDataTab_mod[idadd][1]
	    for (O in nodesById)  {
		var node=nodesById[O];
		var Id=node.getId();
		if (node.getJsonData()["url"] == tile2["url"]) {

		    var newTags=node.updatedata(tile2);
		    
		    // update global Tags ?
		    for (var itag in newTags) { 
			me.AddNewTag(newTags[itag]);
		    }			
		}
	    }
	}
	

	refreshNodes();
	//me.meshEventStart();
	me.meshEventReStart();
	me.startLoading();
	
	// update search list
	suggestion_list = globalTagsList
	    .concat($('.info').map(function(){ return $.trim($(this).text());}).get())
	    .concat(Object.keys(nodesById).map(function(e){return $.trim(nodesById[e].getJsonData().comment); }));
    });
    
    /**	Here is created a tab menuEventTab related to the parameters menuEventTab_ of the Menu constructor (see below)



	The size of the tab menuEventTab determine the number of menu button 
	The funtion on menuEventTab determine what happens when the users click on the options menu 
	When the users click on the first button menuEventTab(0) is called 
	When the users click on the second  button menuEventTab(1) is called etc.


	These functions must be writed along the following template :

	function(v,id,optionNumber){

	if(v==true)  {    
	STUFF TO DO WHEN OPTION IS ACTIVE
	} else { 		
	STUFF TO DO WHEN OPTION IS NOT ACTIVE
	}
	}

	where :
	- v  -> true when users active the options, false when users desactive it	
	- id, the id of the menu selected
	- theoptions selected on the menu 

	Flask Version : add a new array MenuShareEvent to manage client/server with menus.
	If one click on a button which have MenuShareEnvet is true. The server will receive a message and 
	dispach the click to the other clients. 
    */

    /** TAG MENU
     * Functions :
     * - Add a tag
     * - Remove a tag
     * - Align a selection of tiles with a tag
     * - Remove all tags
     */

    var tagMenuTitleTab = new Array();
    var tagMenuEventTab = new Array();
    var tagMenuIconClassAttributesTab = new Array();
    var tagMenuShareEvent = new Array();

    var tagAlignOrderTagsMenuTitleTab = new Array();
    var tagAlignOrderTagsMenuEventTab = new Array();
    var tagAlignOrderTagsMenuIconClassAttributesTab = new Array();
    var tagAlignOrderTagsMenuShareEvent = new Array();

    var tagHideTagsMenuTitleTab = new Array();
    var tagHideTagsMenuEventTab = new Array();
    var tagHideTagsMenuIconClassAttributesTab = new Array();
    var tagHideTagsMenuShareEvent = new Array();

    var tagKillTagsMenuTitleTab = new Array();
    var tagKillTagsMenuEventTab = new Array();
    var tagKillTagsMenuIconClassAttributesTab = new Array();
    var tagKillTagsMenuShareEvent = new Array();

    var tagSelectionMenuTitleTab = new Array();
    var tagSelectionMenuEventTab = new Array();
    var tagSelectionMenuIconClassAttributesTab = new Array();
    var tagSelectionMenuShareEvent = new Array();

    var tagManagementMenuTitleTab = new Array();
    var tagManagementMenuEventTab = new Array();
    var tagManagementMenuIconClassAttributesTab = new Array();
    var tagManagementMenuShareEvent = new Array();

    var EndOfGroupping=false;
    // User interaction
    // Tags	
    clickTagInLegend = function(){
	if (! PaletteNodeTagFlag)
	    if (emit_click("tag",this.id))
		return
	if(me.getRemovingTag())  { 
	    var tagToRemove = document.getElementById(this.id);
	    for(O in nodesByLoc)  { 
		nodesByLoc[O].removeElementFromNodeTagList(this.id);
	    }
	    $('#tag-notif').text("Tag " + this.id + " removed from tag list and tiles.");
	    $('.tag#'+this.id).remove();//removeChild(tagToRemove);
	    var idTag=globalTagsList.indexOf(this.id)
	    var name=globalTagsList[idTag];
	    delete globalTagsColors[name];
	    globalTagsList.splice(idTag,1);
	    currentSelectedTag = "";

	} else if (me.getSelectTags())  { 
	    var tagToSelect = this.id;
	    var w = 0;
	    for (O in nodesById)  { 
		if (me.hasTag(nodesById[O], tagToSelect))  {
		    var HB = $('#hitbox' + nodesById[O].getId());
		    nodeSelect(nodesById[O],HB);
		    w ++;
		}
	    }
	    if (w==0){
		$('#tag-notif').text("No matching tiles for tag " + tagToSelect + " found");
	    } else {
		$('#tag-notif').text(w + " matching tiles for tag " + tagToSelect + " found");
		addBlink(this);
	    }

	} else if (me.getAlignTags())  { 
	    var thisTagToGroup = this.id;
	    var w = 0;
	    var floatT=[]
	    var hasFloatingT=false
	    for (O in nodesById)  { 
		if (me.hasTag(nodesById[O], thisTagToGroup))  {
		    if (me.hasFloatingTag(nodesById[O], thisTagToGroup)) {
			hasFloatingT=true;
			floatT[w]=[nodesById[O].getFloatingTag()[thisTagToGroup]["val"],O,nodesById[O].getId()];
		    } else {
			mesh.switchLocation(nodesById[O], nodesByLoc[w], false, true);
		    };
		    w ++;
		}
	    }
	    if (hasFloatingT) {
		var sfloatT = Array.from(floatT);
		if (alignOrderTag) {
		    sfloatT.sort((a, b) => a[0] - b[0]);
		} else {
		    sfloatT.sort((a, b) => b[0] - a[0]);
		}
		for (var w=0; w<sfloatT.length;w++)  { 
		    var O=sfloatT[w][1];
		    mesh.switchLocation(nodesById[O], nodesByLoc[w], false, true);
		}
	    }
		    
	    if (w==0){
		$('#tag-notif').text("No matching tiles for tag " + thisTagToGroup + " found");
	    } else {
		$('#tag-notif').text(w + " matching tiles for tag " + thisTagToGroup + " found");
		addBlink(this);
	    }

	    if(chargeAllContentOnStart==false)  { 
		me.computeNumColumns();
		for(O in nodesById){
		    node = nodesById[O];
		    if( node.getLoadedStatus() == false && mesh.locationProvider(node.getIdLocation()).getY()<window.innerHeight  )  { 
			//console.log(node.getmLocation().getnX());
			ratio=mesh.loadContent(node.getId());
			//node.setLoadedStatus(true);
		    }
		}
	    }
	    for (O in nodesByLoc)  { 
		if (nodesByLoc[O].getNodeInViewportStatus()) {
		    //nodesByLoc[O].getOnOffStatus() &&
	    	    SetOn(nodesByLoc[O].getId());
		} else {
	    	    SetOff(nodesByLoc[O].getId());
		}
	    }
	    EndOfGroupping=true;

	} else if (me.getHideNodesTagFlag()) {
	    var thisTagToGroup = this.id;
	    if (me.getHideNodesTag())  { 
		// Hide nodes for this tag 
		for (O in nodesByLoc)  { 
		    if (me.hasTag(nodesByLoc[O], thisTagToGroup))  { 
			Id=nodesByLoc[O].getId();
			SetOff(Id);
		    }
		}
		$('#tag-notif').text("Hiding the tiles bearing " + thisTagToGroup + " tag. (To make them visible again, click on the icon in the tag menu, then on the tag again)")
		addBlink(this);
 	    } else {
		// Show nodes for this tag 
		var thisTagToGroup = this.id;
		for (O in nodesByLoc)  { 
		    if (me.hasTag(nodesByLoc[O], thisTagToGroup))  { 
			Id=nodesByLoc[O].getId();
			SetOn(Id);
		    }
		}
		$('#tag-notif').text("Showing the tiles bearing " + thisTagToGroup + " tag.")
		addBlink(this);
 	    }
	} else if (KillNodesTagFlag) {
	    var tagToKill = this.id;
	    // Kill nodes for this tag 
	    for (O in nodesByLoc)  { 
		if (me.hasTag(nodesByLoc[O], tagToKill))  { 
		    Id=nodesByLoc[O].getId();
		    nodeCardinal--;
		    node=$('#'+Id);
		    SetOff(Id);
		    nodesByLoc[O].removeElementFromNodeTagList(tagToKill);
		    nodeEnd=nodesByLoc[nodeCardinal];
		    mesh.switchLocationShiftColumnLine(nodesByLoc[O],nodeEnd,false,false);
		    nodesByLoc.splice(nodeCardinal,1);
		    //node.hide();
		}
 	    }
	    $('#tag-notif').text("Killing the tiles bearing " + tagToKill + " tag.")
	    $('.tag#'+tagToKill).remove();
	    addBlink(this);
	} else if (SelectionNodeToTagFlag) {
	    currentSelectedTag = this.id;
	    // Add tag for nodes in selection
	    var listSelectionTiles=me.getSelectedNodes()
	    for(O in listSelectionTiles)  { 
		var HBid = "hitbox"+listSelectionTiles[O].getId();
		//clickHBTag(HBid);
		listSelectionTiles[O].getStickers().addSticker(currentSelectedTag, attributedTagsColorsArray[currentSelectedTag],true);
		listSelectionTiles[O].addElementToNodeTagList(currentSelectedTag);
	    }
	    $('#tag-notif').text(" Add selected tiles to tag " + this.id);
	    
	    addBlink(this);
	} else if (SelectionMultipleTagsFlag) {
	    var thisTag = this.id;
	    var thisDiv = this;
	    var color = attributedTagsColorsArray[received_newtag];
	    var newSelTagDiv = document.getElementById(received_newtag);
	    var funSelTag = function() {
		if (receive_Add_Tag) {
		    clearInterval(checkEndaddSelTag);
		    addBlink(thisDiv);
		    addBlink(newSelTagDiv);

		    for (O in nodesById)  { 
			if (me.hasTag(nodesById[O], thisTag))  {
			    nodesById[O].getStickers().addSticker(received_newtag,color);
			    nodesById[O].addElementToNodeTagList(received_newtag);
			}
		    }
		    $('#tag-notif').text(" Add tiles from tag " + thisTag + " to selection tag " + received_newtag);
		}
	    }
	    var checkEndaddSelTag = setInterval(funSelTag, 100);
	    
	} else if (PaletteNodeTagFlag) {
	    var tagToColor = this.id;
	    var colorChoose;
	    var defaultColor = colourNameToHex(configBehaviour.draw.defaultColor);
	    colorChoose = document.querySelector("#colorChoose");
	    colorChoose.value = defaultColor;

	    $('#'+tagToColor).css("outline-style", "solid");
	    
	    var TagColor = defaultColor;

	    window["updateFirst"+tagToColor] = function (event) {
		TagColor = event.target.value;
	    }
	    window["updateAll"+tagToColor] = function (event) {
		$('#'+tagToColor).css("outline-style", "none");
		cdata={"room":my_session,"OldTag":tagToColor,"TagColor":TagColor};
		socket.emit("color_Tag", cdata, callback=function(sdata){
 		    console.log("socket change color Tag ", cdata);
		});
		colorChoose.removeEventListener("input", window["updateFirst"+tagToColor]);
		colorChoose.removeEventListener("change", window["updateAll"+tagToColor]);
		delete window["updateFirst"+tagToColor];
		delete window["updateAll"+tagToColor];
	    }
	    
	    colorChoose.addEventListener("input", window["updateFirst"+tagToColor], false);
	    colorChoose.addEventListener("change", window["updateAll"+tagToColor], false);
	    colorChoose.select();
	    
	} else { // DEFAULT behaviour: click on a tag = make it ready to be given to a tile
	    if (currentSelectedTag != this.id)  { // Click on a different tag than the previous one
		$('#'+this.id).css("outline", "10px solid white");
		$('#'+this.id).css("z-index", 500);
		if (currentSelectedTag != "")  { // Previous tag was existing (and not blank) : un-select it
		    $('#'+currentSelectedTag).css("outline-style", "none");
		    $('#'+currentSelectedTag).css("z-index", 149);
		}
		currentSelectedTag = this.id;
		$('#tag-notif').text("Selected tag: " + currentSelectedTag + "; you may now click on the left border of a tile to give it the tag.");
	    }
	    else // Un-select current tag
	    {
		$('#'+this.id).css("outline-style", "none");
		$('#'+this.id).css("z-index", 149);
		currentSelectedTag = "";
		$('#tag-notif').text("No selected tag.");
	    }
	    addBlink(this);
	}
    };

    // Stickers : on click, erase the sticker from the node
    clickSticker = function(){
	//console.log("sticker clicked", this.id);
	if (emit_click("sticker",this.id))
	    return
	var splittedId = this.id.split("_");
	var nodeId = splittedId.pop();
	var node = nodesById["node"+nodeId];
	node.removeElementFromNodeTagList(splittedId.join("_"));
    };

    // Add a tag
    this.AddNewTag=function(tmpNewTag) {
	var k = -1;
	if ( $.inArray(tmpNewTag, globalTagsList) == -1 ) {
	    globalTagsList.push(tmpNewTag);
	    var k = globalTagsList.length -1;
	    var l = k;
	    globalTagsColors[tmpNewTag]={"l":l};
	} else {
	    var k = globalTagsList.indexOf(tmpNewTag);
	    var l = globalTagsColors[tmpNewTag]["l"];
	}	    
	$('#tag-legend').append('<div id =' + globalTagsList[k] + ' class=tag>' + globalTagsList[k] + '</div>');
	var thisNewTagFun=function() {
	    try  {
		var A=$('#'+globalTagsList[k]).position();
		clearInterval(TagPosFun);

		if ($('#'+globalTagsList[k]).position().left==0) {
		    $("#tag-legend").css({ height: $("#tag-legend").height()+$('#'+globalTagsList[k]).height() });
		}
		try {
		    $('#'+globalTagsList[k]).css('background-color',ColorSticker(l));
		    attributedTagsColorsArray[globalTagsList[k]] =$('#'+globalTagsList[k]).css("background-color");
		    $('#tag-notif').text("New tag added: " + tmpNewTag);
		}
		catch(err)  { 
		    $('#tag-legend div:last').remove();
		    console.log("Tag not valid", tmpNewTag);
		    $('#tag-notif').text("Invalid tag: " + tmpNewTag + ", please try again.");
		}

		TagHeight=($("#tag-legend").height());
	
		if ( my_user != "Anonymous" ) {
		    TopPP=TagHeight;
		    htmlPrimaryParent.css("marginTop",TopPP+"px");
		    ppot=TopPP;
		}
		$('.tag').off("click").on({
		    click : clickTagInLegend
		});
	    } catch(err)  {
		//Not Yet
	    }
	};
	var TagPosFun = setInterval( thisNewTagFun, 100);
    }

    // Color tag
    this.ChangeColorTag = function(thisTag, NewColor) {
	$('#'+thisTag).css('background-color',NewColor);
	attributedTagsColorsArray[thisTag] = NewColor;
	for (O in nodesByLoc)  { 
	    if (me.hasTag(nodesByLoc[O], thisTag))  { 
		nodesByLoc[O].getStickers().colorSticker(thisTag,NewColor);
	    }
	}
    }
    
    /** Disable or enable other tags functions
     */
    this.disableOtherTagFunction = function (mytagfunction) {
	var ListTagFunction=["AlignTags","HideNodesTagFlag","KillNodesTagFlag","SelectTags","SelectionTag","SelectMultipleTags"];
	for (var otherTag in ListTagFunction) {
	    var thisTag=ListTagFunction[otherTag];
	    if ( thisTag != mytagfunction )
		eval("me.set"+thisTag+"(false)");
	}
	eval("me.set"+mytagfunction+"(true)");
    };
    
    // Align/group similarly tagged nodes
    tagMenuTitleTab.push("Align/group similarly tagged nodes")
    tagMenuEventTab.push(    function(v, id, optionNumber){
	    if(v==true)  { 
		//console.log("grouping tags");
		me.disableOtherTagFunction("AlignTags");
		me.setAlignTags(true);
		$('#'+id+'option'+optionNumber).removeClass('alignTagButtonIcon').addClass('closeAlignTagButtonIcon');
	    } else { 
		//console.log("end grouping tag");
		me.setAlignTags(false);
		$('#'+id+'option'+optionNumber).removeClass('closeAlignTagButtonIcon').addClass('alignTagButtonIcon');
	    }
	});
    tagMenuIconClassAttributesTab.push("alignTagButtonIcon");
    tagMenuShareEvent.push(true);

    // Align/group similarly tagged nodes
    tagMenuTitleTab.push("Order floatting tagged nodes")
    tagMenuEventTab.push(    function(v, id, optionNumber){
	    if(v==true)  { 
		//console.log("align order tags");
		$('#'+id+'option'+(optionNumber-1)).click();
		menuAlignOrderTags
		    .css("top",menuTags.position()["top"]+200)
		    .css("left",$('.alignOrderTagsMenuButtonIcon').position()["left"]+menuTags.position()["left"])
		    .css("visibility", "visible");
		$('#'+id+'option'+optionNumber).removeClass('alignOrderTagsMenuButtonIcon').addClass('closeAlignOrderTagsMenuButtonIcon');
	    } else { 
		//console.log("end align order tag");
		menuAlignOrderTags.css("visibility", "hidden");
		$('#'+id+'option'+optionNumber).removeClass('closeAlignOrderTagsMenuButtonIcon').addClass('alignOrderTagsMenuButtonIcon');
	    }
	});
    tagMenuIconClassAttributesTab.push("alignOrderTagsMenuButtonIcon");
    tagMenuShareEvent.push(true);

    tagAlignOrderTagsMenuTitleTab.push("Increasing sort")
    tagAlignOrderTagsMenuEventTab.push(    function(v, id, optionNumber){
	me.disableOtherTagFunction("AlignTags");
	me.setAlignTags(true);
    	if(v==true)  { 
	    //console.log("Align order decrease");
    	    $('#'+id+'option'+optionNumber).removeClass('increaseOrderTagsButtonIcon').addClass('closeIncreaseOrderTagsButtonIcon');
    	    $('#'+id+'option'+(optionNumber+1)).removeClass('decreaseOrderTagsButtonIcon').addClass('closeDecreaseOrderTagsButtonIcon');
	    alignOrderTag=false
	} else { 	
	    //console.log("Align order increase");
    	    $('#'+id+'option'+optionNumber).removeClass('closeIncreaseOrderTagsButtonIcon').addClass('increaseOrderTagsButtonIcon');
    	    $('#'+id+'option'+(optionNumber+1)).removeClass('closeDecreaseOrderTagsButtonIcon').addClass('decreaseOrderTagsButtonIcon');
	    alignOrderTag=true
	}
    });
    tagAlignOrderTagsMenuIconClassAttributesTab.push('increaseOrderTagsButtonIcon')
    tagAlignOrderTagsMenuShareEvent.push(true);

    tagAlignOrderTagsMenuTitleTab.push("Decreasing sort")
    tagAlignOrderTagsMenuEventTab.push(    function(v, id, optionNumber){
	me.disableOtherTagFunction("AlignTags");
	me.setAlignTags(true);
    	if(v==true)  { 
	    //console.log("Align order increase");
    	    $('#'+id+'option'+optionNumber).removeClass('decreaseOrderTagsButtonIcon').addClass('closeDecreaseOrderTagsButtonIcon');
    	    $('#'+id+'option'+(optionNumber-1)).removeClass('increaseOrderTagsButtonIcon').addClass('closeIncreaseOrderTagsButtonIcon');
	    alignOrderTag=false
	} else { 
	    //console.log("Align order decrease");
    	    $('#'+id+'option'+optionNumber).removeClass('closeDecreaseOrderTagsButtonIcon').addClass('decreaseOrderTagsButtonIcon');
    	    $('#'+id+'option'+(optionNumber-1)).removeClass('closeIncreaseOrderTagsButtonIcon').addClass('increaseOrderTagsButtonIcon');
	    alignOrderTag=true
	}
    });
    tagAlignOrderTagsMenuIconClassAttributesTab.push('decreaseOrderTagsButtonIcon')
    tagAlignOrderTagsMenuShareEvent.push(true);



    // Hide/Show nodes with tags menu
    tagMenuTitleTab.push("Hide/Show nodes with tags menu")
    tagMenuEventTab.push(    function(v, id, optionNumber){
	    if(v==true)  { 
		menuHideTags
		    .css("top",menuTags.position()["top"]+200)
		    .css("left",$('.hideTagsMenuButtonIcon').position()["left"]+menuTags.position()["left"])
		    .css("visibility", "visible");
		$('#'+id+'option'+optionNumber).removeClass('hideTagsMenuButtonIcon').addClass('closeHideTagsMenuButtonIcon');
	    } else { 
		me.tagHideTagsMenu.closeAllOptions();
		menuHideTags.css("visibility", "hidden");
		$('#'+id+'option'+optionNumber).removeClass('closeHideTagsMenuButtonIcon').addClass('hideTagsMenuButtonIcon');
	    }
	});
    tagMenuIconClassAttributesTab.push("hideTagsMenuButtonIcon");
    tagMenuShareEvent.push(true);

    tagHideTagsMenuTitleTab.push("Hide nodes")
    tagHideTagsMenuEventTab.push(    function(v, id, optionNumber){
    	    if(v==true)  { 
		//console.log("Hide nodes with tags");
    		me.disableOtherTagFunction("HideNodesTagFlag");
    		me.setHideNodesTagFlag(true);
		me.setHideNodesTag(true);
    		$('#'+id+'option'+optionNumber).removeClass('hideTagsButtonIcon').addClass('closeHideTagsButtonIcon');
	    } else { 
		//console.log("Show nodes with tags");
    		me.setHideNodesTagFlag(false);
		me.setHideNodesTag(false);
    		$('#'+id+'option'+optionNumber).removeClass('closeHideTagsButtonIcon').addClass('hideTagsButtonIcon');
	    }
	});
    tagHideTagsMenuIconClassAttributesTab.push('hideTagsButtonIcon')
    tagHideTagsMenuShareEvent.push(true);
    
    tagHideTagsMenuTitleTab.push("Show nodes")
    tagHideTagsMenuEventTab.push(    function(v, id, optionNumber){
    	    if(v==true)  { 
    		//console.log("Hide nodes with tags");
    		me.setHideNodesTagFlag(true);
		me.setHideNodesTag(false);
    		$('#'+id+'option'+optionNumber).removeClass('showTagsButtonIcon').addClass('closeShowTagsButtonIcon');
    	    } else { 
    		//console.log("Show nodes with tags");
    		me.disableOtherTagFunction("HideNodesTagFlag");
    		$('#'+id+'option'+optionNumber).removeClass('closeShowTagsButtonIcon').addClass('showTagsButtonIcon');
    		me.setHideNodesTagFlag(false);
		me.setHideNodesTag(true);
    	    }
    	});
    tagHideTagsMenuIconClassAttributesTab.push('showTagsButtonIcon')
    tagHideTagsMenuShareEvent.push(true);

    // Kill nodes with selected tags menu
    tagMenuTitleTab.push("Kill tiles with selected tag")
    tagMenuEventTab.push(    function(v, id, optionNumber){
	    if(v==true)  { 
		//console.log("Kill nodes with tags");
		me.disableOtherTagFunction("KillNodesTagFlag");
		$('#'+id+'option'+optionNumber).removeClass('KillTagButtonIcon').addClass('closeKillTagButtonIcon');
	    } else { 
		mesh.globalLocationProvider();
		me.setKillNodesTagFlag(false);
		//console.log("Show nodes with tags");
		$('#'+id+'option'+optionNumber).removeClass('closeKillTagButtonIcon').addClass('KillTagButtonIcon');
	    }
	});
    tagMenuIconClassAttributesTab.push("KillTagButtonIcon");
    tagMenuShareEvent.push(true);

    // Selection sub-menu.
    tagMenuTitleTab.push("Selection menu.")
    tagMenuEventTab.push(    function(v, id, optionNumber){
	if(v==true)  { 
	    menuSelectionTags
		.css("top",menuTags.position()["top"]+200)
		.css("left",$('.selectTagMenuButtonIcon').position()["left"]+menuTags.position()["left"])
		.css("visibility", "visible");
	    $('#'+id+'option'+optionNumber).removeClass('selectTagMenuButtonIcon').addClass('closeSelectTagMenuButtonIcon');
	} else { 
	    me.tagSelectionMenu.closeAllOptions();
	    menuSelectionTags.css("visibility", "hidden");
	    $('#'+id+'option'+optionNumber).removeClass('closeSelectTagMenuButtonIcon').addClass('selectTagMenuButtonIcon');
	}
    });
    tagMenuIconClassAttributesTab.push("selectTagMenuButtonIcon");
    tagMenuShareEvent.push(true);

    // Select similarly tagged nodes for zoom or MS.
    tagSelectionMenuTitleTab.push("Select tiles with a tag.")
    tagSelectionMenuEventTab.push(    function(v, id, optionNumber){
	    if(v==true)  { 
		//console.log("selecting tags");
		me.disableOtherTagFunction("SelectTags");
		$('#'+id+'option'+optionNumber).removeClass('selectTagButtonIcon').addClass('closeSelectTagButtonIcon');
	    } else { 
		//console.log("end selecting tag");
		me.setSelectTags(false);
		$('#'+id+'option'+optionNumber).removeClass('closeSelectTagButtonIcon').addClass('selectTagButtonIcon');
	    }
	});
    tagSelectionMenuIconClassAttributesTab.push("selectTagButtonIcon");
    tagSelectionMenuShareEvent.push(true);

    // Add selected tag to all nodes in current selection
    tagSelectionMenuTitleTab.push("Add tag for nodes in selection")
    tagSelectionMenuEventTab.push(    function(v, id, optionNumber){
	    if(v==true)  { 
		//console.log("Add tag for nodes in selection");
		me.disableOtherTagFunction("SelectionTag");
		$('#'+id+'option'+optionNumber).removeClass('selectionToTagButtonIcon').addClass('closeSelectionToTagButtonIcon');
	    } else {
		SelectionNodeToTagFlag=false;
		$('#'+id+'option'+optionNumber).removeClass('closeSelectionToTagButtonIcon').addClass('selectionToTagButtonIcon');
	    }
	});
    tagSelectionMenuIconClassAttributesTab.push("selectionToTagButtonIcon");
    tagSelectionMenuShareEvent.push(true);

    // Select multiple tags for grouping tags in a new tag.
    var SelTags=[]
    tagSelectionMenuTitleTab.push("Select tiles with multiple tags.")
    tagSelectionMenuEventTab.push(    function(v, id, optionNumber){
	    if(v==true)  { 
		//console.log("selecting multiple tags");
		me.disableOtherTagFunction("SelectMultipleTags");
		
		seltags="Sel"+SelTags.length;
		SelTags.push(seltags);
 		console.log("select multiple tags : New Tag ",seltags);
		// Here we can't give option to block shareAgain because we have just click on it.
		var upMenuTag=$('.closeSelectTagMenuButtonIcon')[0].id;
		emit_newTag(upMenuTag,seltags);

		$('#'+id+'option'+optionNumber).removeClass('selectMultipleTagsButtonIcon').addClass('closeSelectMultipleTagsButtonIcon');
	    } else { 
		//console.log("end selecting multiple tag");
		me.setSelectMultipleTags(false);
	    }
	    cdata={"room":my_session,"SelTags":seltags,"bool":v};
	    socket.emit("switch_MultipleTag", cdata, callback=function(sdata){
 		console.log("Emit switch multiple tags : ", cdata);
	    });
	});
    tagSelectionMenuIconClassAttributesTab.push("selectMultipleTagsButtonIcon");
    tagSelectionMenuShareEvent.push(false);

    socket.on('receive_multiple_Tags', function(sdata){
     	console.log("receive_multiple_Tags",sdata);
	if (Boolean(sdata.bool)) {
	    me.disableOtherTagFunction("SelectMultipleTags");
	    seltags=sdata.SelTags;
	    $('.selectMultipleTagsButtonIcon').removeClass('selectMultipleTagsButtonIcon').addClass('closeSelectMultipleTagsButtonIcon');
	} else {
	    me.setSelectMultipleTags(false);
	    $('.closeSelectMultipleTagsButtonIcon').removeClass('closeSelectMultipleTagsButtonIcon').addClass('selectMultipleTagsButtonIcon');
	}
    });

    // Management sub-menu.
    tagMenuTitleTab.push("Management menu.")
    tagMenuEventTab.push(    function(v, id, optionNumber){
	if(v==true)  {
	    menuManagementTags
		.css("top",menuTags.position()["top"]+200)
		.css("left",$('.managementTagMenuButtonIcon').position()["left"]+menuTags.position()["left"])
		.css("visibility", "visible");
	    $('#'+id+'option'+optionNumber).removeClass('managementTagMenuButtonIcon').addClass('closeManagementTagMenuButtonIcon');
	} else { 
	    me.tagManagementMenu.closeAllOptions();
	    menuManagementTags.css("visibility", "hidden");
	    $('#'+id+'option'+optionNumber).removeClass('closeManagementTagMenuButtonIcon').addClass('managementTagMenuButtonIcon');
	}
    });
    tagMenuIconClassAttributesTab.push("managementTagMenuButtonIcon");
    tagMenuShareEvent.push(true);

    // Add new tag
    tagManagementMenuTitleTab.push("Add new tag")
    tagManagementMenuEventTab.push(    function(v, id, optionNumber){
	    if(v==true)  { 
		//console.log("adding tag");

		var tmp = document.getElementById("add-tag");
		if (tmp == null)  { 
		    menuTags.append("<div id=add-tag></div>");	
		    $('#add-tag').css({ //GLOBALCSS
			    position:"relative",
				top : 0,
				//left : parseInt($(me.menu.getHtmlMenuSelector()).css('width')), 
				left : 0,
				height : 100,
				width : parseInt($(me.tagMenu.getHtmlMenuSelector()).css('width')),
				backgroundColor : "black",
				fontSize : 50,
				color : "white"					
				});
		    $('#add-tag').append("<label for=new-tag>Add Tag : </label>").append("<input id=new-tag type=text placeholder='New tag ?'>");
			$('#new-tag').css({//GLOBALCSS
			    position : "relative", 
				top : 10,
				//left : parseInt($(me.menu.getHtmlMenuSelector()).css('width')), 
				left : 0,
				zIndex : 131, 
				height : 80,
				width : parseInt($(me.tagMenu.getHtmlMenuSelector()).css('width')),
				fontSize : 70
				});
		    $('#new-tag').autocomplete({
			    source: suggestion_list 
				});
		} else { 
		    $('#add-tag').show();
		    $('#new-tag').show();

		}
		var left_ = parseInt($(me.menu.getHtmlMenuSelector()).css("width"));
		var width_= parseInt($('header').css('width')) - left_ -600 /*- parseInt($('body').prop("scrollwidth"))*/; // 600 is for the three buttons on the right

		$('#add-tag').off("tap focusin click").on("tap focusin click",
		    function(){
			    $('.tag').off("click");

			$('#add-tag').off("keypress").on({
				    keypress : function(e){
					if (e.which == 13 ) {
					    if ( $('#new-tag').val().trim()!='')  { // ENTER 
						var tmpNewTag = $('#new-tag').val().trim();// .trim() to avoid whitespace or encoding problems
						tmpNewTag = newTag_conformance(tmpNewTag);
						if ($.inArray(tmpNewTag, globalTagsList) == -1)  { // Check if the new tag is not already stored as tag
 		    				    console.log("add New Tag ", tmpNewTag);
						    emit_newTag("add-tag",tmpNewTag);

						} else { 
						    console.log("Tag already exists!");
						    $('#tag-notif').text("This tag already exists!");
						}
						$('#new-tag').val("");
						//console.log("exitting add button");
					   }
					    $('#menu'+id+">#option"+optionNumber).click();
					}
				    }
				});
			}
		    );
		$('#add-tag').off("autocompleteselect").on("autocompleteselect", function(event, ui) {
			document.getElementById("new-tag").value = ui.item.value;
			var myEvent = jQuery.Event("keypress");
			myEvent.which = 13;
			myEvent.keyCode = 13;
			$('#add-tag').trigger(myEvent);
			$('#new-tag').value = ""; // This line
			return false; // *and* this line: to clean the field for the next use!

		    });


		$('#'+id+'option'+optionNumber).removeClass('addTagButtonIcon').addClass('closeAddTagButtonIcon');
	    } else { 
			//console.log("end adding tag");
			$('#add-tag').hide();
			$('#new-tag').hide();
			$('#'+id+'option'+optionNumber).removeClass("closeAddTagButtonIcon").addClass("addTagButtonIcon");
	    }
	});

    tagManagementMenuIconClassAttributesTab.push("addTagButtonIcon");
    tagManagementMenuShareEvent.push(false);

    // Remove tag
    tagManagementMenuTitleTab.push("Remove tag")
    tagManagementMenuEventTab.push(    function(v, id, optionNumber){
	    if(v==true)  { 
		//console.log("removing tag");
		$('#'+id+'option'+optionNumber).removeClass("removeTagButtonIcon").addClass("closeRemoveTagButtonIcon");
		me.setRemovingTag(true);
	    } else { 
		//console.log("end removing tag");
		$('#'+id+'option'+optionNumber).removeClass("closeRemoveTagButtonIcon").addClass("removeTagButtonIcon");
		me.setRemovingTag(false);
	    }
	});
    tagManagementMenuIconClassAttributesTab.push("removeTagButtonIcon");
    tagManagementMenuShareEvent.push(true);

    // Brush icon : to erase the tags all at once (is also triggered to clean legend and stickers when exitting tag mode)
    tagManagementMenuTitleTab.push("Erase all the tags")
    tagManagementMenuEventTab.push(    function(v,id, optionNumber){
	    //console.log("erasing tags");
	var buffer=0;
	//$('header')
	    $("#tag-legend").prepend('<div id="validateDelTags" height="10%" width="20%" style="z-index: 100; color: yellow; font-size: 50"><h1>Are you sure you want to suppress all tags ?</h1></div>')
	// $('#validateDelTags').css({
	    
	//     ,
	// })
	$('#validateDelTags').append('<button id="validButtonYes" name="validButtonYes" class="validateDelTags btn btn-info" >Yes</button>');
	$('#validateDelTags').append('&nbsp;&nbsp;');
	$('#validateDelTags').append('<button id="validButtonNo" name="validButtonNo" class="validateDelTags btn btn-info" >No</button>');
	$('#validButtonYes').off("click").on({
		    // Delete all tools created on magnifyingGlass and zoomAndDrawOnNodes
	    click : function() {
		if (emit_click("validateDelTags","validButtonYes"))
		    return
		while(globalTagsList.length>0)  { 
		    delete globalTagsColors[globalTagsList[globalTagsList.length-1]];
		    buffer=globalTagsList.pop();
		    
		    for(O in nodesById)  { 
			nodesById[O].removeElementFromNodeTagList(buffer);
		    }
		}
		$('#tag-legend').children().remove();
		for (O in nodesByLoc)
		    if (nodesByLoc[O].getNodeInViewportStatus()) {
			$('#node'+O).css({
			    opacity : 1
			});
		    }
		$('#validateDelTags').remove()
		//console.log("end erasing tags");
	    }})
	$('#validButtonNo').off("click").on({
	    click : function() {
		if (emit_click("validateDelTags","validButtonNo"))
		    return
		$('#validateDelTags').remove()
	    }})
	});
    tagManagementMenuIconClassAttributesTab.push("brushButtonIcon");
    tagManagementMenuShareEvent.push(true);

    // Choose stickers color
    tagManagementMenuTitleTab.push("Choose stickers color")
    tagManagementMenuEventTab.push(    function(v, id, optionNumber){
	    if(v)  { 
		var defaultColor = colourNameToHex(configBehaviour.draw.defaultColor);
		$('#menu'+id).append('<div id=color-picker-zone style="position: absolute; top: 200px; left: 1100px"></div>');
		$('#color-picker-zone').append('<label for="colorChoose" style="height: 200px; width: 400px; color: white; font-size: 4em">Color:</label>');
		$('#color-picker-zone').append('<input type="color" value="'+defaultColor+'" id="colorChoose" style="height: 200px; width: 200px; font-size: 2em">');
		PaletteNodeTagFlag=true;
		$('#'+id+'option'+optionNumber).removeClass('paletteButtonIcon').addClass('closePaletteButtonIcon');
	    } else { 
		$('#color-picker-zone').remove();
		PaletteNodeTagFlag=false;
		$('#'+id+'option'+optionNumber).removeClass('closePaletteButtonIcon').addClass('paletteButtonIcon');
	    }
	});
    tagManagementMenuIconClassAttributesTab.push("paletteButtonIcon");
    tagManagementMenuShareEvent.push(false);

    
    // Action menu

    var actionGlobalMenuTitleTab = new Array();
    var actionGlobalMenuEventTab = new Array();
    var actionGlobalMenuIconClassAttributesTab = new Array();
    var actionGlobalMenuShareEvent = new Array();

    for ( var TS in json_actions) {
	for ( var thisAction in json_actions[TS]) {
	    var FuncName=json_actions[TS][thisAction][0];
	    var IconName=json_actions[TS][thisAction][1];
	    actionGlobalMenuTitleTab.push(TS+"_"+FuncName);
	    actionGlobalMenuEventTab.push( (function() {
		var TS_=TS;
		var thisAction_=thisAction;
		return function( v, id, optionNumber){
		    idAction = parseInt(thisAction_.replace("action",""));

    		    var selections = [];
    		    var listSelectionTiles=me.getNodesToZoom();
    		    for(O in listSelectionTiles)  {
			// Only selection for the right tag
			if (listSelectionTiles[O].getJsonData().tags.filter(x=>x==TS_).length)
    			    selections.push(parseInt(listSelectionTiles[O].getJsonData().variable.replace("ID-",""))-1);
    		    }
		    if (selections.length == 0)
			selections=","
		    else
			selections=selections.toString()
		    addBlink($('#'+id+"option"+optionNumber));
		    cdata={"room":my_session,"id":id,"TileSet":TS_,"action":thisAction_,"selections":selections};
		    socket.emit("action_click", cdata, callback=function(sdata){
 			console.log("socket send action_click ", cdata);
		    });
		}
	    })() );
	    actionGlobalMenuIconClassAttributesTab.push(TS+"_"+IconName+"ButtonIcon");
	    actionGlobalMenuShareEvent.push(false);
	}
    }

    /** DRAW MENU
     * Functions :
     * - Choose drawing color
     * - Choose drawing style
     * - Clear drawing
     * - Save drawing
     * - Close drawing
     */

    var drawMenuTitleTab = new Array();
    var drawMenuEventTab = new Array();
    var drawMenuIconClassAttributesTab = new Array();
    var drawMenuShareEvent = new Array();

    // Choose drawing color
    drawMenuTitleTab.push("Choose drawing color")
    drawMenuEventTab.push(    function(v, id, optionNumber){
	    if(v)  { 
		var defaultColor = colourNameToHex(configBehaviour.draw.defaultColor);
		$('#menu'+id).append('<div id=color-picker-zone style="position: absolute; top: 0px; left: 1100px"></div>');
		$('#color-picker-zone').append('<label for="colorChoose" style="height: 200px; width: 400px; color: white; font-size: 4em">Color:</label>');
		$('#color-picker-zone').append('<input type="color" value="'+defaultColor+'" id="colorChoose" style="height: 200px; width: 200px; font-size: 2em">');
		var colorChoose;
		colorChoose = document.querySelector("#colorChoose");
		colorChoose.value = defaultColor;
		colorChoose.addEventListener("input", updateFirst, false);
		colorChoose.addEventListener("change", updateAll, false);
		colorChoose.select();

		drawingColor = defaultColor;

		function updateFirst(event) {
		    drawingColor = event.target.value;
		}
		function updateAll(event) {
		    drawingColor = event.target.value;
		}

		$('#'+id+'option'+optionNumber).removeClass('paletteButtonIcon').addClass('closePaletteButtonIcon');
	    } else { 
		$('#color-picker-zone').remove();
		$('#'+id+'option'+optionNumber).removeClass('closePaletteButtonIcon').addClass('paletteButtonIcon');
	    }
	});
    drawMenuIconClassAttributesTab.push("paletteButtonIcon");
    drawMenuShareEvent.push(false);

    // Choose line width !
    drawMenuTitleTab.push("Choose line width !")
    drawMenuEventTab.push(    function(v, id, optionNumber){
	    if(v)  { 
		//console.log("choose style");
		$('#menu'+id).append("<input name=lineWidthSelector id=lineWidthSelector min=0 type=number>");
		$('#lineWidthSelector').css({
			position : "absolute",
			    top : parseInt($('#'+id+'option'+optionNumber).css("height")),
			    left : parseInt($('#'+id+'option'+optionNumber).css("left")),
			    width : parseInt($('#'+id+'option'+optionNumber).css("width")),
			    });
		$('#lineWidthSelector').val(configBehaviour.draw.width);

		var changeLineWidth = function(){
		    configBehaviour.draw.width = $('#lineWidthSelector').val();
		    //console.log("new line width value : ", configBehaviour.draw.width);
		};

		$('#lineWidthSelector').off("change").on({
			change : changeLineWidth
			    });

		$('#'+id+'option'+optionNumber).removeClass('lineWidthButtonIcon').addClass('closeLineWidthButtonIcon');
	    } else { 
		//console.log("end choose style");
		$('#lineWidthSelector').remove();
		$('#'+id+'option'+optionNumber).removeClass("closeLineWidthButtonIcon").addClass("lineWidthButtonIcon");
	    }
	});
    drawMenuIconClassAttributesTab.push("lineWidthButtonIcon");
    drawMenuShareEvent.push(false);

    // Brush icon : to erase the drawing
    drawMenuTitleTab.push("Brush icon : to erase the drawing")
    drawMenuEventTab.push(    function(v,id, optionNumber){
	    context.clearRect(0, 0, context.canvas.width, context.canvas.height);
	    clickX = new Array();
	    clickY = new Array();
	    clickDrag = new Array();
	    p=0;	
	});
    drawMenuIconClassAttributesTab.push("brushButtonIcon");
    drawMenuShareEvent.push(false);

    // Save drawing
    drawMenuTitleTab.push("Save drawing")
    drawMenuEventTab.push(    function(v,id, optionNumber){
	    var canvasName = $('#zoomSupport').find(".drawing").filter(":visible").attr("id");
	    var srcImage = $('#iframe' + canvasName.replace(/\D/g, "")).attr("src").replace(".png", "").replace(/^.*[\\\/]/, "");
	    document.getElementById(canvasName).toBlob(    function(blob) {
		    saveAs(blob, "drawing_"+ srcImage +".png");
		});
	});
    drawMenuIconClassAttributesTab.push("saveButtonIcon");
    drawMenuShareEvent.push(false);

    var DrawBlobs = new Map();	// maps blob IDs to drawing objects

    var getBlob = function (canvasName) {
	var deferred = Q.defer();
    
	var canvas = document.getElementById(canvasName);
	if ( $("#DrawSupport").length == 0) 
	    $("body").append('<div id="DrawSupport" style="width: '+canvas.width+'px; height: '+canvas.height+'px"></div>');

	canvas.toBlob( function(blob) {
	    // var canvasName = $('#zoomSupport').find(".drawing").filter(":visible").attr("id");
	    var nodeId=canvasName.replace(/drawCanvas/g, "");
	    
	    var thisDrawBlob=DrawBlobs.get(nodeId);
	    if ( thisDrawBlob ) {
		var newImg = thisDrawBlob.image;
		$('#'+newImg.id).remove();
		var OldUrl = thisDrawBlob.url;
		 
		// no longer need to read the blob so it's revoked
		window.URL.revokeObjectURL(OldUrl);
		
		// New blob
		var BlobUrl = window.URL.createObjectURL(blob);
		newImg.src = BlobUrl;
		$('#DrawSupport').append(newImg);
		thisDrawBlob.url = BlobUrl;
		thisDrawBlob.dataurl = canvas.toDataURL();
		$('#'+newImg.id).show();
	    } else {
		var newImg = document.createElement('img');
		BlobUrl = window.URL.createObjectURL(blob);
		
		newImg.id=canvasName+'_img';
		newImg.src = BlobUrl;
		$('#DrawSupport').append(newImg);
		
		DrawBlobs.set(nodeId,{
		    url: BlobUrl,
		    dataurl: canvas.toDataURL(),
		    nodeId: parseInt(nodeId),
		    image: newImg,
		    canvasName: canvasName,
		    listNodeImg: []
		});
	    }
	    thisDrawBlob=DrawBlobs.get(nodeId);	
	    deferred.resolve(thisDrawBlob);
	},'image/png');
	
	return deferred.promise;
    }

    var DrawNodeFun = function(nodeId,Id) {
	var Id=parseInt(Id);
	var LocImg="";

	var thisDrawBlob=DrawBlobs.get(nodeId);
	var canvasName=thisDrawBlob.canvasName;

	var DrawNodeId=canvasName+"_img_"+Id;
	if (thisDrawBlob.listNodeImg.indexOf(Id) > -1) {
	    $("#"+DrawNodeId).remove();
		    
	} else {
	    thisDrawBlob.listNodeImg.push(Id);
	}
	LocImg=$("#"+canvasName+"_img").clone().attr('id', DrawNodeId).appendTo($("#"+Id));
	LocImg.css({
		position: "absolute",
		    top: 0,
		    left: 0,
		    height: $('#'+canvasName+'_img').css('height'),
		    width: $('#'+canvasName+'_img').css('width'),
		    });

	var scaleX=(spread.X/ $('#'+canvasName+'_img').css('width').replace('px',''));
	var scaleY=(spread.Y/ $('#'+canvasName+'_img').css('height').replace('px',''));

	LocImg.css({'-webkit-transform': "scale("+scaleX+","+ scaleY +")",
		    '-webkit-transform-origin': '0 0',
		    '-moz-transform': "scale("+scaleX+","+ scaleY +")",
		    '-moz-transform-origin': '0 0',
		    '-o-transform': "scale("+scaleX+","+ scaleY +")",
		    '-o-transform-origin': '0 0',
		    '-ms-transform': "scale("+scaleX+","+ scaleY +")",
		    'transform': "scale("+scaleX+","+ scaleY +")",
		    'transform-origin': "0 0 0"});
    }

    var chunk_size=1024*64;
    var send_draw_data = function(data,nodeId,canvasName,offset,offsetEnd) {
	var datasend=data.slice(offset,offsetEnd+1).toString();
	
	var cdata={}
	cdata["room"]=my_session;
	cdata["nodeId"]=nodeId;
	cdata["offset"]=offset;
	cdata["offsetEnd"]=offsetEnd;
	cdata["data"]=datasend;
	socket.emit("uploadDraw", cdata, callback=function(sdata){
 	    //console.log("socket send draw part of "+canvasName+" from "+cdata.offset+" to "+cdata.offsetEnd);
	});
    }

    var send_DrawBlob = function(thisDrawBlob, canvasName, nodeId, allNodes) {
	var canvas = document.getElementById(canvasName);
	var ImageData=thisDrawBlob.dataurl;
	var lengthData=ImageData.length;
	var cdata={};
	var nbsend = parseInt(lengthData / chunk_size) + 1;
	cdata["room"]=my_session;
	cdata["nodeId"]=nodeId;
	cdata["canvasName"]=canvasName;
	cdata["length"]=lengthData;
	cdata["nbsend"]=nbsend;
	cdata["width"]=canvas.width;
	cdata["height"]=canvas.height;
	if (typeof allNodes == 'undefined') {
	    // emit Draw to all other clients of the session
	    socket.emit("drawBlob", cdata, callback=function(sdata){
 		console.log("socket send draw blob ", cdata);
	    });
	} else {
	    // emit Draw to all other clients of the session
	    cdata["allNodes"]="true";
	    socket.emit("drawBlob", cdata, callback=function(sdata){
 		console.log("socket send all clients draw blob ", cdata);
	    })
	}
	// Add progress bar
	// $('#buttonUnzoom').append('<div id="ProgressStatusZoom" class="progress-status"></div>')
	// $('#ProgressStatusZoom').append('<div id="myprogressBarZoom" class="progressBar" style="width: 0px"></div>')
	// $("#ProgressStatusZoom").show();
	// var sendProgress=0;
	// var updateProgressBarZoom = function() {
	//     if (sendProgress>=100) clearInterval(idProgress);
	//     $("#myprogressBarZoom").css({width: sendProgress+"%"});
	//     //	$("myprogressBarZoom").html(sendProgress  + '%');
	// };
	// var idProgress=setInterval(updateProgressBarZoom,1);

	for( var i=0; i<nbsend; i++ ) {
	    var offset=i*chunk_size;
	    var offsetEnd=Math.min(offset-1+chunk_size,lengthData-1)
	    send_draw_data(ImageData,nodeId,canvasName,offset,offsetEnd);
	    // sendProgress=parseInt((i+1)*100/nbsend);
	    // updateProgressBarZoom();
	}
	//$("#ProgressStatusZoom").remove();
	return nbsend
    }

    // Node drawing
    drawMenuTitleTab.push("Node drawing")
    drawMenuEventTab.push(    function(v,id, optionNumber){
	    var canvasName = $('#zoomSupport').find(".drawing").filter(":visible").attr("id");
	    var nodeId=canvasName.replace(/drawCanvas/g, "");
	    var thisDrawBlob=[];

	    getBlob(canvasName).then(function(thisDrawBlob) {

		try {
		    nbsend=send_DrawBlob(thisDrawBlob, canvasName, nodeId)
		} catch(err)  {
		    console.log("Error : init send draw "+err.toString())
		}
		return thisDrawBlob
	    }).then(function(thisDrawBlob) {
		var newImg = thisDrawBlob.image;
		console.log("blob",thisDrawBlob);
		
		newImg.onload = function() {
		    
		    DrawNodeFun(nodeId,nodeId);
		    $('#'+this.id).hide();
		};
		
		$('#buttonUnzoom').click();
		return thisDrawBlob
	    });
	});
    drawMenuIconClassAttributesTab.push("DrawOnNodeButtonIcon");
    drawMenuShareEvent.push(false);


    // Duplicate draw on other nodes
    drawMenuTitleTab.push("Duplicate draw on other nodes")
    drawMenuEventTab.push(    function(v,id, optionNumber){
	    var canvasName = $('#zoomSupport').find(".drawing").filter(":visible").attr("id");
	    var nodeId=canvasName.replace(/drawCanvas/g, "");

	    getBlob(canvasName).then(function(thisDrawBlob) {
		try {
		    nbsend=send_DrawBlob(thisDrawBlob, canvasName, nodeId, true)
		} catch(err)  {
		    console.log("Error : init send draw "+err.toString())
		}
		return thisDrawBlob
	    }).then(function(thisDrawBlob) {

		    var newImg = thisDrawBlob.image;
		console.log("blob",thisDrawBlob);

		    newImg.onload = function() {
			
			for(O in nodesByLoc)  {
			    DrawNodeFun(nodeId,O);
			}
		
			$('#'+this.id).hide();
		    };

		    $('#buttonUnzoom').click();
		return thisDrawBlob
		});
	});
    drawMenuIconClassAttributesTab.push("DrawOnAllNodesIcon");
    drawMenuShareEvent.push(false);

    // Share draws
    socket.on('receive_draw_img', function(sdatai){
     	console.log("receive_draw_img",sdatai);

    	var canvasName  = sdatai.canvasName;
    	var nodeId = sdatai.nodeId;
    	var offset=0;
    	var offsetend=0;
	$("#notifications").html("")
	$("#notifications").append('<div id="ProgressStatusUpload" class="progress-status">'+
				   '<div id="myprogressBarUp" class="progressBar" style="width: 0px"></div></div>')
	$("#ProgressStatusUpload").show();
		
	var sendProgress=0;
	var update_progressBarUp = function() {
	    if (sendProgress>100) clearInterval(idProgress);
	    $("#myprogressBarUp").css({width: sendProgress+"%"});
	    $("#myprogressBarUp").html(sendProgress + '%');
	};
	var idProgress=setInterval(update_progressBarUp,10);

	if ( $("#DrawSupport").length == 0) 
	    $("body").append('<div id="DrawSupport" style="width: '+sdatai.width+'px; height: '+sdatai.height+'px"></div>');

    	var data="";
    	socket.off('receive_draw_part').on('receive_draw_part', function(sdatap){

	    // $("#DrawSupport").show();
	    // $(".node").hide();
    	    // TODO Verify the right origin of the data ? nodeId + canvasName ?

	    receivedata=sdatap.data;
    	    if (offset == 0) {
    		data=receivedata;
    	    } else {
    		data=data+receivedata;		
	    }
	    offset=parseInt(sdatap.offset);
    	    offsetend=parseInt(sdatap.offsetEnd);
	    datalength=data.length;

	    sendProgress=parseInt((offsetend+1)*100/sdatai.length);
	    
    	    if (offsetend == sdatai.length-1) {
    		socket.off('receive_draw_part');
		
		sendProgress=101;

		if ( $('#'+canvasName+'_img').length == 0 )
		    $("#DrawSupport").append('<img id="'+canvasName+'_img" src=""'+
					     ' width='+sdatai.width+' height='+sdatai.height+'></img>')
		var newImg=$("#"+canvasName+"_img")[0];
		var thisDrawBlob=DrawBlobs.get(nodeId);
		
		if ( thisDrawBlob ) {
		    newImg = thisDrawBlob.image;
		    $("#"+newImg.id).remove();
		    var OldUrl = thisDrawBlob.url;
	    
		    // no longer need to read the blob so it's revoked
		    window.URL.revokeObjectURL(OldUrl);

		    newImg.src = data;
		    $("#DrawSupport").append(newImg);

		    $('#'+newImg.id).show();
		} else {
		    newImg.src = data;
		
		    DrawBlobs.set(nodeId,{
		    	url: "",
		    	dataurl: newImg.src,
		    	nodeId: parseInt(nodeId),
		    	image: newImg,
		    	canvasName: canvasName,
		    	listNodeImg: []
		    });
		}
		
		if ( $('#'+canvasName).length > 0 ) {
		    var canvas = document.getElementById(canvasName);
		    var ctx = canvas.getContext('2d');
		    ctx.drawImage(newImg, 0, 0);
		}
		
    		newImg.onload = function() {
    		    if (sdatai.allNodes) {
    			for(O in nodesByLoc)  {
    			    DrawNodeFun(nodeId,O);
    			}
    		    } else {
    			DrawNodeFun(nodeId,nodeId);
    		    }
    		}
		// $("#DrawSupport").hide();
		// $(".node").show();
		
		$("#ProgressStatusUpload").remove();
    	    }
	    offset=parseInt(sdatap.offsetEnd);
    	});
    });
	    
    // Close

    /** MasterSlave MENU
     * Functions :
     * - Apply MS after selection
     * - Select all nodes and zoom
     * - Help zoom
     */
 
    var MSMenuTitleTab = new Array();
    var MSMenuEventTab = new Array();
    var MSMenuIconClassAttributesTab = new Array();
    var MSMenuShareEvent = new Array();

    /** MasterSlave Menu
	After activation (the icon becomes white on black background), select node by clicking on it,
	First node is the master and lasts nodes are slave. 
	All mouse interactions on master are gathered on slaves. 
	click on the button on the upper-right to zoom and begin mode, then to unzoom. 
    */

    // Apply MS on selection
    MSMenuTitleTab.push("Apply MS on selection")
    MSMenuEventTab.push(    function( id, optionNumber){
	    // Zoomed div and Handlered div over it
	    var handleMaster,Handled;
	    // iframe of the Handled
	    var iframeHandled;
	    // number of the master
	    var iHandled;
 
	    // Variables for magnifyingGlass 
	    var nodeMSTab = me.getNodesToZoom();
	    var ratio =spread.Y/spread.X;
	    var initSpread = spread;
		    
	    if(nodeMSTab.length>0) {
		menuMS.css("visibility", "hidden");

		// We repeat first node because its div will be used as master.
		nodeMSTab=Array(nodeMSTab[0]).concat(nodeMSTab);
		if (parseBool(configBehaviour.onlyMasterMS))
		    configBehaviour.allMSShowMax=0;
		if (nodeMSTab.length > configBehaviour.allMSShowMax+1) {
		    nodeMSTab_=nodeMSTab.slice(0, configBehaviour.allMSShowMax+1);
		    me.magnifyingGlass(nodeMSTab_,ratio,initSpread);
		} else {
		    me.magnifyingGlass(nodeMSTab,ratio,initSpread);
		}			
			
		// We begin with first selected as Master
		handleMaster=$("#Zoomed"+0);
			
		// We create the listened div
		$("#zoomSupport").append('<div id=Handled class=handled></div>');
			
		iframeHandled=handleMaster.children("iframe");
		handleMaster.children(".info").html("MASTER Tile");
		handleMaster.children(".stickers_zone").remove()
		
		urlMaster=nodeMSTab[0].getJsonData().url;
		urlMasterPath=urlMaster.slice(0,urlMaster.search("vnc.html"));

		// We set the property of the iframe
		var HandledJQ=$("#Handled");
		HandledJQ.css({ 
			height : iframeHandled.css('height'),
			    width : iframeHandled.css('width'),
			    });
			
		// DOM path to this handled div
		Handled=$("#zoomSupport").children(".handled")[0];
			
		$('header').append("<div id=explain-StartMS>First node is duplicated to have the master to interact.</div>");
		$('#explain-StartMS').css({
			position : "fixed", 
			    backgroundColor : "green",
			    color : "black",
			    fontSize : 100,
			    left : "15%",
			    top : 0 ,
			    zIndex : 121
			    });
			
		// Start Master-Slave function
		function initMSList() {
		    // This function will work only for VNC connections
		    try {
			str_autoconnect="?autoconnect=1&"
			MSPath=urlMasterPath+"vnc_multi.html"+str_autoconnect+"NbRFB="+(nodeMSTab.length-1)+"&";
			for(i=1;i<nodeMSTab.length;i++) {
			    var urlNode=nodeMSTab[i].getJsonData().url;
			    urlNodeParam=urlNode.slice(urlNode.search("vnc.html")+"vnc.html".length+str_autoconnect.length);
			    NodeParams=urlNodeParam.split('&');
			    for (P in NodeParams) {
				thisparam=NodeParams[P].slice(0,NodeParams[P].search("="));
				switch(thisparam) {
				case("host"):
				case("port"):
				case("password"):
				case("path"):
				case("token"):
				case("encrypt"):
				    NodeParams[P]=NodeParams[P].replace("=",(i-1)+"=");
				case("autoconnect"):
				case("true_color"):
				    // suppress param
				}
			    }
			    MSPath=MSPath+NodeParams.join('&')+'&';
			}
			iframeHandled.attr("src",MSPath+"&true_color=1");
		    } catch(e) {
			console.log("Master-Slave function will work only for VNC connections.");
		    }
		}
			
 					
		// Start Master-Slave 
		initMSList();

		// unZoom function
		$('#buttonUnzoom').on({
			click : function(){
			    $('#explain-StartMS').remove();
				    
			    try {
				var	Handled=$("#zoomSupport").children(".handled")[0];
				Handled.remove();
			    } catch (err) {
			    }
			    menuMS.css("visibility", "visible");
				    
			    // for(O in nodesById)  { 
			    // 	me.removeNodeToZoom(O);
			    // }
			    // me.setZoomSelection(true);
			}
		    });
	    }
	});			
    MSMenuIconClassAttributesTab.push("expandZoomButtonIcon");
    MSMenuShareEvent.push(false);

    // Apply MS on all tiles
    MSMenuTitleTab.push("Apply MS on all tiles")
    MSMenuEventTab.push(    function(v, id, optionNumber){
	    me.resetNodesToZoom(); 					
	    var nodeMSTab = me.getNodesToZoom();
		    
	    for(O in nodesById)  { 
		nodeMSTab.push(nodesById[O]);
	    }
	    menuMS.children("[class*=expandZoomButtonIcon]").click();

	    for(O in nodesById)  { 
		me.removeNodeToZoom(O);
	    }
	    me.setZoomSelection(true);

	});
    MSMenuIconClassAttributesTab.push("AllMSButtonIcon");
    MSMenuShareEvent.push(false);

    // explain MS
    MSMenuTitleTab.push("Master-Slave explain area")    
    MSMenuEventTab.push(    function(v, id, optionNumber){
	});
    MSMenuIconClassAttributesTab.push("explain-MS");
    MSMenuShareEvent.push(false);

    /** ZOOM MENU
     * Functions :
     * - Disable or enable or zoom functions
     * - Apply zooming after selection
     * - Help zoom
     */

    /** Disable or enable other zoom functions
     */
    var ListZoomFunctions=["zoomNodes","zoom","MS","draw"];
    this.disableOtherZoom = function (myzoomfunction) {
	for (var otherZoom in ListZoomFunctions) {
	    var thisZoom=ListZoomFunctions[otherZoom];
	    if ( thisZoom != myzoomfunction )
		var thiszoom=thisZoom[0].toUpperCase()+thisZoom.substring(1);
		if ($(".close"+thisZoom+"ButtonIcon")[0]) {
		    $(".close"+thisZoom+"ButtonIcon").click();
		} else if ($(".close"+thiszoom+"ButtonIcon")[0]) {
		    $(".close"+thiszoom+"ButtonIcon").click();
		}
	}
    };
    
    /** Enable or enable other zoom functions
     */
    this.enableOtherZoom = function (myzoomfunction) {
	// for (var otherZoom in ListZoomFunctions) {
	//     var thisZoom=ListZoomFunctions[otherZoom];
	//     if ( thisZoom != myzoomfunction )
	// 	$(".disable"+thisZoom+"ButtonIcon").removeClass("disable"+thisZoom+"ButtonIcon").addClass(thisZoom+"ButtonIcon");
	// }
    };
    
    /** Zoom Global Menu functions 
	After activation (the icon becomes white on black background), select node by clicking on it, 
	click on the button on the upper-right to zoom, then to unzoom. 
    */

    var zoomMenuTitleTab = new Array();
    var zoomMenuEventTab = new Array();
    var zoomMenuIconClassAttributesTab = new Array();
    var zoomMenuShareEvent = new Array();

    // Apply Zoom button
    zoomMenuTitleTab.push("Apply zoom button")
    zoomMenuEventTab.push( function(v, id, optionNumber) {		

	    // Variables for magnifyingGlass 
	    var nodeZoomTab = me.getNodesToZoom();
	    var ratio =spread.Y/spread.X;
	    var initSpread = spread;

	    if(nodeZoomTab.length>0)  { 
		$("#menu"+id).css("visibility", "hidden");

		//$('#buttonUnzoom').hide();
		me.magnifyingGlass(nodeZoomTab,ratio,initSpread);
		// me.resetNodesToZoom();

		// unZoom function
		$('#buttonUnzoom').on({
			click: function(){		
				    
			    //console.log("click unzoom");
			    menuZoom.css("visibility", "visible");
			}
		    });
			
	    }
	});
    zoomMenuIconClassAttributesTab.push("expandZoomButtonIcon");
    zoomMenuShareEvent.push(false);

    zoomMenuTitleTab.push("Zoom explain area")    
    zoomMenuEventTab.push( function(v, id, optionNumber) {		
	});

    zoomMenuIconClassAttributesTab.push("explain-zoom");
    zoomMenuShareEvent.push(false);


    /** Zoom Global menu
     * List of implemented functions : 
     - Zoom on selected nodes
     - Master-slave interaction on selected nodes
     - show zoom Node fast zoom button to each node
    */

    var zoomGlobalMenuTitleTab = new Array();
    var zoomGlobalMenuEventTab = new Array();
    var zoomGlobalMenuIconClassAttributesTab = new Array();
    var zoomGlobalMenuShareEvent = new Array();

    // Zoom menu with selection
    zoomGlobalMenuTitleTab.push("Zoom menu with selection")
    zoomGlobalMenuEventTab.push(	(  function(){

		return function(v,id,optionNumber){

		    // for(O in nodesById)  { 
		    // 	nodesById[O].updateSelectedStatus(false);
		    // }

		    if(v==true)  { 
			//me.setZoomSelection(true); // To change the behaviour of a hitbox click, cf clickHB method // DEPRECATED ?
			// Deactivate other magnify menus
			me.disableOtherZoom("zoom")
			BlockDragAndDrop();

			for (O in nodesByLoc)
			    if (nodesByLoc[O].getNodeInViewportStatus()) {
				nodesByLoc[O].sub('').off();
				nodesByLoc[O].sub('hitbox').off("click").on("click", clickHBSelect);
				nodesByLoc[O].sub('hitbox').off("mouseenter");
			    }
			menuZoom.children('[class*=explain-zoom]')[0].innerText="Click on the left of the nodes to select them. Green nodes will be selected.";
			menuZoom.children('[class*=explain-zoom]').css({
				backgroundColor : "green",
				    color : "black",
				    fontSize : 100,
				    width: 2000,
				    });

			menuZoom.css("visibility", "visible");
			menuZoom.css("top", TagHeight+"px");

			$('#'+id+'option'+optionNumber).removeClass('zoomButtonIcon').addClass("closezoomButtonIcon");

		    } else { 

			// Activate other magnify menus
			me.enableOtherZoom("zoom")
			EnableDragAndDrop();

			me.setZoomSelection(false);
			me.resetNodesToZoom();
			$('#buttonUnzoom').click();
			//me.meshEventReStart();

			menuZoom.css("visibility", "hidden");

			$('#'+id+'option'+optionNumber).removeClass("closezoomButtonIcon").addClass("zoomButtonIcon");
		    }
		    return 0;
		};		
	    })());		

    zoomGlobalMenuIconClassAttributesTab.push("zoomButtonIcon");
    zoomGlobalMenuShareEvent.push(false);
	

    // MasterSlave Menu
    zoomGlobalMenuTitleTab.push("MasterSlave Menu")
    zoomGlobalMenuEventTab.push(	(function(){
 
 		return function(v,id,optionNumber){
 		    
		    me.setZoomSelection(true);
 
 		    // for(O in nodesById)  {
		    // 	nodesById[O].updateSelectedStatus(false);
		    // }
 
		    if(v==true) {
			//me.setZoomSelection(true); // To change the behaviour of a hitbox click, cf clickHB method // DEPRECATED ?
 
			// Deactivate other magnify menus
			me.disableOtherZoom("MS")
			BlockDragAndDrop();

			for (O in nodesByLoc)
			    if (nodesByLoc[O].getNodeInViewportStatus()) {
				nodesByLoc[O].sub('').off();
				nodesByLoc[O].sub('hitbox').off("click").on("click", clickHBSelect);
				nodesByLoc[O].sub('hitbox').off("mouseenter");
			    }

			menuMS.children('[class*=explain-MS]')[0].innerText="Click on the left of the nodes to select them. Click on left \"validate button\" or right \"ALL selected\" button.";
			menuMS.children('[class*=explain-MS]').css({
				backgroundColor : "green",
				    color : "black",
				    fontSize : 100,
				    width: 2800,
				    });			

			menuMS.css("visibility", "visible");
			menuMS.css("top", TagHeight+"px");

			$('#'+id+'option'+optionNumber).removeClass("MSButtonIcon").addClass("closeMSButtonIcon");

		    } else {

			// Activate other magnify menus
			me.enableOtherZoom("MS")
			EnableDragAndDrop();

			me.setZoomSelection(false);
			me.resetNodesToZoom();
			// We must replace iframes on their right place in the DOM !
			try {
			    var Handled=$("#zoomSupport").children(".handled")[0];
			    Handled.remove();
			} catch(err) {
			}
			$('#buttonUnzoom').click();
			//me.meshEventReStart();
			
			menuMS.css("visibility", "hidden");
			
			$('#'+id+'option'+optionNumber).removeClass("closeMSButtonIcon").addClass("MSButtonIcon");

		    };

		    return 0;
 		};		
	    }) ());		
 
    zoomGlobalMenuIconClassAttributesTab.push("MSButtonIcon");
    zoomGlobalMenuShareEvent.push(false);

    /** show zoom Node fast zoom button to each node */
    zoomGlobalMenuTitleTab.push("Show fast zoom button")
    zoomGlobalMenuEventTab.push( (    function(){

		return function(v, id, optionNumber){
		    if (v==true)  { 
			me.disableOtherZoom("zoomNodes")
			BlockDragAndDrop();

			$('.zoomNodeButtonIcon').show();
			$('#'+id+'option'+optionNumber).removeClass('zoomNodesButtonIcon').addClass('closeZoomNodesButtonIcon');
		    } else { 
			// Activate other magnify menus
			me.enableOtherZoom("zoomNodes")
			EnableDragAndDrop();

			$('.zoomNodeButtonIcon').hide();
			$('#'+id+'option'+optionNumber).removeClass("closeZoomNodesButtonIcon").addClass("zoomNodesButtonIcon");
		    }
		};

	    })());
    zoomGlobalMenuIconClassAttributesTab.push("zoomNodesButtonIcon");
    zoomGlobalMenuShareEvent.push(false);

    /** State of tiles menu
     * List of implemented functions : 

     - Show OnOff button
     - Show node info
     */

    // State Menu Global
    
    var stateGlobalMenuTitleTab = new Array();
    var stateGlobalMenuEventTab = new Array();
    var stateGlobalMenuIconClassAttributesTab = new Array();
    var stateGlobalMenuShareEvent = new Array();    
    
    // Show OnOff button
    stateGlobalMenuTitleTab.push("Show OnOff button")
    stateGlobalMenuEventTab.push( (    function(){

		return function(v, id, optionNumber){
		    if (v==true)  { 
			for (O in nodesByLoc)
			    if (nodesByLoc[O].getNodeInViewportStatus())
				nodesByLoc[O].getHtmlNode().children(".onoff").css({display : "inline"});
			$('#'+id+'option'+optionNumber).removeClass('OnOffButtonIcon').addClass('closeOnOffButtonIcon');
		    } else { 
			for (O in nodesByLoc)
			    if (nodesByLoc[O].getNodeInViewportStatus())
				nodesByLoc[O].getHtmlNode().children(".onoff").css({display : "none"});
			$('#'+id+'option'+optionNumber).removeClass("closeOnOffButtonIcon").addClass("OnOffButtonIcon");

		    }
		};

	    })());

    stateGlobalMenuIconClassAttributesTab.push("OnOffButtonIcon");
    stateGlobalMenuShareEvent.push(true);
    
    /** show QR code link to each node */
    stateGlobalMenuTitleTab.push("Show QR code link")
    stateGlobalMenuEventTab.push( (    function(){

		return function(v, id, optionNumber){
		    if (v==true)  { 
			$('.qrcode').show();
			$('#'+id+'option'+optionNumber).removeClass('QRcodeButtonIcon').addClass('closeQRcodeButtonIcon');
		    } else { 
			$('.qrcode').hide();
			$('#'+id+'option'+optionNumber).removeClass("closeQRcodeButtonIcon").addClass("QRcodeButtonIcon");

		    }
		};

	    })());

    stateGlobalMenuIconClassAttributesTab.push("QRcodeButtonIcon");
    stateGlobalMenuShareEvent.push(true);

    /** Show node info */
    stateGlobalMenuTitleTab.push("Show node info")
    stateGlobalMenuEventTab.push( (    function(){

		return function(v, id, optionNumber){
		    if (v==true)  { 
			for (O in nodesByLoc)
			    if (nodesByLoc[O].getNodeInViewportStatus())
				nodesByLoc[O].getHtmlNode().children(".info").css({visibility : "visible", display : "inline" });
			$('#'+id+'option'+optionNumber).removeClass('showInfoButtonIcon').addClass('closeShowInfoButtonIcon');
		    } else { 
			if(!! configBehaviour.alwaysShowInfo)  { 
			    for (O in nodesByLoc)
				if (nodesByLoc[O].getNodeInViewportStatus())
				    nodesByLoc[O].getHtmlNode().children(".info").css({visibility : "hidden"});
			}
			$('#'+id+'option'+optionNumber).removeClass("closeShowInfoButtonIcon").addClass("showInfoButtonIcon");

		    }
		};

	    })());

    stateGlobalMenuIconClassAttributesTab.push("showInfoButtonIcon");
    stateGlobalMenuShareEvent.push(true);
    
    /** Management menu
     * List of implemented functions : 

     - Draws on tile management 
     - Save work session (at the moment only the post-its)
     - Options menu
     - help frame
     */
        
    var managementGlobalMenuTitleTab = new Array();
    var managementGlobalMenuEventTab = new Array();
    var managementGlobalMenuIconClassAttributesTab = new Array();
    var managementGlobalMenuShareEvent = new Array();

    /** Draws on tile management */

    // Share modification of draw in Draws Management Menu.
    emit_ModifDraws=function(action,nodeId) {
	    cdata={"room":my_session,"action":action,"nodeId":nodeId};
	    socket.emit("modif_draws", cdata, callback=function(sdata){
 		console.log("socket send modif_draws ", cdata);				
	    });
    }
    
    socket.on('receive_SuppressDraw',function(sdata){
	var thisblob=DrawBlobs.get(sdata.nodeId.toString());
	var newImg=thisblob.image;
	var canvasName=thisblob.canvasName;
	for (ind in thisblob.listNodeImg) {
	    Id=thisblob.listNodeImg[ind];
	    DrawNodeId=canvasName+"_img_"+Id;
	    $("#"+DrawNodeId).remove();
	}
	DrawBlobs.delete(thisblob.nodeId.toString());
	$('#'+newImg.id).remove();
	$('#draws'+thisblob.nodeId).remove();
    });

    socket.on('receive_HideDraw',function(sdata){
	var thisblob=DrawBlobs.get(sdata.nodeId.toString());
	var canvasName=thisblob.canvasName;
	for (ind in thisblob.listNodeImg) {
	    Id=thisblob.listNodeImg[ind];
	    DrawNodeId=canvasName+"_img_"+Id;
	    $("#"+DrawNodeId).hide();
	}
	$('input[name=drawOtherNodes'+thisblob.nodeId+']').val('yes').attr("checked",true);
    });
    
    socket.on('receive_ShowDraw',function(sdata){
	var thisblob=DrawBlobs.get(sdata.nodeId.toString());
	var canvasName=thisblob.canvasName;
	for (ind in thisblob.listNodeImg) {
	    Id=thisblob.listNodeImg[ind];
	    DrawNodeId=canvasName+"_img_"+Id;
	    $("#"+DrawNodeId).show();
	}
	$('input[name=drawOtherNodes'+thisblob.nodeId+']').val('no').attr("checked",false);
    });
    
    managementGlobalMenuTitleTab.push("Draws management")
    managementGlobalMenuEventTab.push( (    function(){

		return function(v, id, optionNumber){
   		    if (v==true)  { 
   			$('header').append("<div id=DrawsMenu class=option-draws></div>");
			$('#DrawsMenu').css({
				backgroundColor : "SkyBlue",
				    color : "black",
				    fontSize : 50,
				    left: 500,
				    width: 1000,
				    zIndex: 801
				    });
   			// maps blob IDs to drawing objects
   			DrawBlobs.forEach(function(thisblob) { 
			    $('#DrawsMenu').append("<div id='draws"+thisblob.nodeId+"'> </div>");
   			    $('#draws'+thisblob.nodeId).append("<input type='checkbox' id='drawNode"+thisblob.nodeId+"' name='drawNode"+thisblob.nodeId+"' value='no'> supress Node "+thisblob.nodeId+" | </input>");
   			    $('#draws'+thisblob.nodeId).append("<input type='checkbox' id='drawOtherNodes"+thisblob.nodeId+"' name='drawOtherNodes"+thisblob.nodeId+"' value='no'> Hide all clone "+ thisblob.listNodeImg.length+"</br></input>");
			    //$('input[name=drawNode'+thisblob.nodeId+'][value=yes]').attr("checked", true);
   			    $('#drawNode'+thisblob.nodeId).off("change").on({
   				change : function() {
				    // Checked : delete the blob and all pictures on tiles.
				    emit_ModifDraws("SuppressDraw",thisblob.nodeId);
				    window.URL.revokeObjectURL(thisblob.url);
				}
   			    });
			    //$('input[name=drawOtherNodes'+thisblob.nodeId+'][value=yes]').attr("checked", true);
   			    $('#drawOtherNodes'+thisblob.nodeId).off("change").on({
   				change : function() {
				    if (!! $('input[name=drawOtherNodes'+thisblob.nodeId+']').attr("checked")) {
					// Checked : Hide all pictures of this blob on tiles.
					emit_ModifDraws("HideDraw",thisblob.nodeId);
				    } else {
					// unChecked : Show all pictures of this blob on tiles.
					emit_ModifDraws("ShowDraw",thisblob.nodeId);
				    }
				}
   			    });
   			});
   			$('#'+id+'option'+optionNumber).removeClass('DrawsButtonIcon').addClass('closeDrawsButtonIcon');

   		    } else { 
   			$('header').children("#DrawsMenu").remove();
   			$('#'+id+'option'+optionNumber).removeClass("closeDrawsButtonIcon").addClass("DrawsButtonIcon");
   		    }
		};

		})() );

    managementGlobalMenuIconClassAttributesTab.push("DrawsButtonIcon");
    managementGlobalMenuShareEvent.push(true);
    
    /** Save working session : post its and position for each node will be copied to a .js file. */
    managementGlobalMenuTitleTab.push("Save working session")
    managementGlobalMenuEventTab.push(    function(v,id,optionNumber){
	// Concatenate json data
	idFinalLocation=0;
	for(O in nodesByLoc)  { 	
	    var id=nodesByLoc[O].getId();
	    if (nodesByLoc[O].getOnOffStatus()) {
		// Save positions
		nodesByLoc[O].getJsonData().IdLocation = nodesByLoc[O].getIdLocation();
		idFinalLocation++;
		// Save usernotes
		nodesByLoc[O].getJsonData().userNotes = nodesByLoc[O].getComment();
		// Save tags
		nodesByLoc[O].getJsonData().tags = nodesByLoc[O].getNodeTagList();
	    }
	}

	// Ask for save all tiles or just visibles ones (default)
	$('#notifications').html('<div id=saveTiles height="10%" width="50%"></div>');
	$('#saveTiles').append('<form style="font-size: 45px"> Save all tiles or just visible ones (default) ? &nbsp;&nbsp;'
				  + '<input type="checkbox" id="allTiles" value="no" ></input>&nbsp;&nbsp;'
				  + '<button id="submitTiles" name="submitTiles" class="btn btn-info" style="font-size: 40px"> Submit</button>&nbsp;&nbsp;'
			       + '</form>');
	var saveAllTiles=false;
	$('#allTiles').off("change").on({
   	    change : function() {
		saveAllTiles=$('input[name=allTiles]').attr("checked");
	    }
	});
	$('#submitTiles').off("click").on("click",function() {
	    $('#saveTiles').remove();
	    
	    // Reconstruct another nodes.js with the same structure
	    var temp = "{\"nodes\": [XXX] }";
	    var id=0;

	    for(O in nodesByLoc)  { 

		if (saveAllTiles || nodesByLoc[O].getOnOffStatus()) {
	    	    id=nodesByLoc[O].getId();
	    	    //console.log(id);
		    
	    	    var temp3 ="{{***}}";

	    	    for(W in nodesByLoc[O].getJsonData())  {
 			if (W == "tags" ) {
			    var ListTags=new Array();
			    nodesByLoc[O].getNodeTagList().forEach(function(currentValue) {
				if (currentValue in globalFloatingTags) {
				    var ft=nodesByLoc[O].getFloatingTag()
				    ListTags.push("'{"+currentValue+","+ft[currentValue]["m"]+","+ft[currentValue]["val"]+","+ft[currentValue]["M"] + "}'") }
				else {
				    ListTags.push("'"+currentValue + "'") }
			    })
			    var mytext = "\""+W+"\""+" : "+"["+ListTags.toString().replace(/\'/g,'\"')+"], {***}"
			} else if ( W == "comment") {
			    // Don't save old comment because user may have modified it in postit. 
			    var mytext = "{***}";
			} else if ( W == "userNotes") {
			    comment=nodesByLoc[O].getJsonData()["userNotes"].toString().replace(/\"/g,"'")
			    var mytext = "\"comment\""+" : "+"\""+comment+"\""+", {***}"
			    // } else if ( W == "IdLocation") {
			    //     var mytext = "\""+W+"\""+" : "+"\""+nodesByLoc[0].getIdLocation().toString()+"\""+",\n {***}";
			} else {
	    		    var mytext = "\""+W+"\""+" : "+"\""+nodesByLoc[O].getJsonData()[W].toString().replace(/\"/g,"'").replace(/\n/g,"")+"\""+", {***}";
			}
	    		temp3=temp3.replace("{***}",mytext);
	    	    }
	    	    temp3=temp3.replace(", {***}","");
	    	    temp=temp.replace("XXX",temp3+",XXX");
		}
	    }
	    // Save the file with a clear name (date and time, name of the project) 
	    temp=temp.replace(",XXX","");
	    // tempFile = "var text_ = \n     "+temp+";\nvar jsDataTab = text_.nodes;";
	    tempFile=temp;
	    
	    var sessionDate = new Date();
	    var strDate=sessionDate.toLocaleDateString({day: "2-digit", month: "2-digit"}).replace(/\//g, "-") + "_" + sessionDate.toLocaleTimeString("fr-FR").replace(/:/g, "-")
	    //var fileName = my_session + "_" + "tiles_" + strDate + ".js"; 
	    //var file = new File([tempFile], fileName, {type: "text/plain;charset=utf-8"},{ autoBom: false });
	    var fileName = my_session + "_" + "tiles_" + strDate + ".json"; 
	    
	    // socket save new session ??
	    $('#notifications').html('<div id=saveValidate height="10%" width="50%"></div>');
	    // TODO method POST with
	    //<form method="POST">
	    $('#saveValidate').append('<form style="font-size: 45px"> New suffix for save '+my_session+'&nbsp;&nbsp;'
				      + '<input type=text id="newSuffix" value="'+strDate+'" style="width:20%"></input>&nbsp;&nbsp;'
				      + 'Change description : <input type=text id="newDescr" value="'+my_description+'" style="width:50%"></input>&nbsp;&nbsp;'
				      +'<button id="submitSave" name="submitSave" class="btn btn-info" style="font-size: 40px"> Submit</button>&nbsp;&nbsp;'
				      +'<button id="submitCancel" name="submitCancel" class="btn btn-info" style="font-size: 40px"> Cancel</button></form>');
	    $('#submitSave').off("click").on("click",function() {
		//saveAs(file);
		download([tempFile], fileName,"text/plain;charset=utf-8")

		new_suffix=$('#newSuffix').val();
		new_description=$('#newDescr').val();
		new_room=my_session+'_'+new_suffix;
		cdata ={"room":my_session, "NewSuffix": new_suffix,"NewDescription": new_description,"Session": temp }
		console.log("Save session : "+new_room);
		socket.emit("save_Session", cdata);
		$('#saveValidate').remove();

		$('#notifications').html('<div id=gotoNewRoom height="10%" width="50%" style="font-size:75"></div>');
		$('#gotoNewRoom').append('Goto new room ?<br>'		                     
					 + '<input type="text" id="gNRnew_room" name="new room" value="'+ new_room +'" style="width:40%"></input>&nbsp;&nbsp;'
					 +'<button id="ChangeRoomYes" name="ChangeRoomYes" class="btn btn-info" style="font-size: 40px">Yes</button>&nbsp;'
					 +'<button id="ChangeRoomNo" name="ChangeRoomNo" class="btn btn-info" style="font-size: 40px">No</button>');

		$('#ChangeRoomYes').off("click").on("click",function() {
		    new_room=$('#gNRnew_room').val();
		    cdata ={"room":my_session, "NewRoom": new_room }
		    $('#gGnewroom').val(new_room);
		    socket.emit("deploy_Session", cdata);
		});
		
		$('#ChangeRoomNo').off("click").on("click",function() {
		    $('#gotoNewRoom').remove();
		});
	    });
	    $('#submitCancel').off("click").on("click",function() {
		$('#saveValidate').remove();
	    });
	});
    });
    managementGlobalMenuIconClassAttributesTab.push("saveButtonIcon");
    managementGlobalMenuShareEvent.push(false);

    /** Options menu
	- How the selection of iframes is done, but ... it shall be widened in the future
	-  */
    managementGlobalMenuTitleTab.push("Option menu")
    managementGlobalMenuEventTab.push(    function(v, id, optionNumber){
	    if(v == true)  { 
		$('header').append("<div id=options class='dropbtn'></div>");
		$("#options").css({//GLOBALCSS 
			position : "fixed", 
			    top : 0, 
			    left: parseInt($(me.menu.getHtmlMenuSelector()).css("width")), 
			    height: "100%",
			    zIndex: 902,	
			    width :window.innerWidth - parseInt($(me.menu.getHtmlMenuSelector()).css("width")), // To have the upper right part of the screen
			    //backgroundColor : "white", // TO DO : unify color style with the help menu + set color change for the wall
			    //color : "black",
			    fontSize : 100
			    });

		$('#options').append("<div id=options-zone></div>");
		$('#options-zone').append("<div id=options-menus class=option-group></div>");

		// Menus behaviour
		//$('#options-zone').append("<div id=options-menus class=option-group></div>");
		//$('#options-menus').append("<div id=options-menus-label class=label>Menus</div>");
		$('#options-menus').append('<div id=dropdownglobal class="drop-left-menu" ></div>');
		$('#dropdownglobal').css({
		    position: 'absolute',
		    top: 40,
		    left: 200,
		    width: 100,
		    height: 100,
		    zIndex: 130,
		});

		$('#options-menus').append("<div id=options-global-menu-label class='label'>Share global menu</div>");
		var thisMenuShareEvent=me.menu.getMenuShareEvent();
		var thisIconTab=me.menu.getMenuIconClassAttributesTab();
		var LocalMenus=Array();
		var GlobalMenuLabelState=false;
		var SubmenuLabelState=false;
		var SubmenusLabelState={};

		for (var theOption in thisIconTab) {
		    $('#options-global-menu-label')
			.append("<div id='shareDivMenu_"+thisIconTab[theOption]+"' style='font-size:100'></div>");
		    $("#shareDivMenu_"+thisIconTab[theOption]).hide()
			.append("</br><input type='checkbox' id='shareMenu_"+thisIconTab[theOption]+"' name='shareMenu_"+thisIconTab[theOption]+"' value='yes' >"+
				thisIconTab[theOption].replace("GlobalMenu","Menu").replace("ButtonIcon",""));
		    $('input[name=shareMenu_'+thisIconTab[theOption]+']').attr("checked",thisMenuShareEvent[theOption]);
		    if (thisIconTab[theOption].search("GlobalMenu") > -1)
			LocalMenus.push(thisIconTab[theOption])
		}
		
		$('#dropdownglobal').on({
		    click : function(e) {
			if (GlobalMenuLabelState) {
			    GlobalMenuLabelState=false;
			    $('#dropdownglobal').removeClass("drop-down-menu").addClass("drop-left-menu");
			    for (var theOption in thisIconTab) {
				$("#shareDivMenu_"+thisIconTab[theOption]).hide();
			    }
			} else {
			    GlobalMenuLabelState=true;
			    $('#dropdownglobal').removeClass("drop-left-menu").addClass("drop-down-menu");
			    for (var theOption in thisIconTab) {
				$("#shareDivMenu_"+thisIconTab[theOption]).show();
			    }
			}
		    }
		});
		
		$('#options-menus').append('<br><br><div id=dropdownsubm class="drop-left-menu"></div>');
		$('#dropdownsubm').css({
		    position: 'relative',
		    top: 80,
		    left: 200,
		    width: 100,
		    height: 100,
		    zIndex: 130,
		});
		$('#options-menus').append("<div id=options-submenus-label class='label' style='font-size:95'>Share sub-menus</div>");
		for (var locMenu in LocalMenus) {
		    var menuname=LocalMenus[locMenu].replace("GlobalMenuButtonIcon","Global");
		    var thismenu=subMenusGlobal.filter(menu=>menu.getId()==menuname)[0];
		    var thismenuShareEvent=thismenu.getMenuShareEvent();
		    var thisiconTab=thismenu.getMenuIconClassAttributesTab();

		    $('#options-submenus-label').append('<br><div id="dropdownsubm_'+menuname+'" class="drop-left-menu"></div>');
		    $('#dropdownsubm_'+menuname).css({
			position: 'relative',
			top: 80,
			left: 240,
			width: 100,
			height: 100,
			zIndex: 130,
			transform: "scale(0.75)"
		    }).hide();
		    
		    $('#options-submenus-label').append("<div id='shareDivSubmenu_"+menuname+"' style='font-size:85'>"+menuname+"</div>");
		    $("#shareDivSubmenu_"+menuname).hide();
		    SubmenusLabelState[menuname]=false;
		    
		    for (var theOption in thisiconTab) {
		    	$("#shareDivSubmenu_"+menuname)
			    .append("<div id=options-submenu-"+menuname+"-"+thisiconTab[theOption]+" ></div>");
			$("#options-submenu-"+menuname+"-"+thisiconTab[theOption]).hide()
		    	    .append("<br><input type='checkbox' id='shareMenu_"+thisiconTab[theOption]+"' name='shareMenu_"+thisiconTab[theOption]+"' value='yes'>"+
		    		    thisiconTab[theOption].replace("ButtonIcon",""));
			$('input[name=shareMenu_'+thisiconTab[theOption]+']').attr("checked",thismenuShareEvent[theOption]);
		    }
		    
		    $('#dropdownsubm_'+menuname).on({
		    	click : function(e) {
			    var menuname=this.id.replace("dropdownsubm_","");
			    var thismenu=subMenusGlobal.filter(menu=>menu.getId()==menuname)[0];
			    var thisiconTab=thismenu.getMenuIconClassAttributesTab();
		    	    if (SubmenusLabelState[menuname]) {
		    		SubmenusLabelState[menuname]=false;
				$('#dropdownsubm_'+menuname).removeClass("drop-down-menu").addClass("drop-left-menu");
		    		for (var theOption in thisiconTab) {
				    $("#options-submenu-"+menuname+"-"+thisiconTab[theOption]).hide()
		    		}
		    	    } else {
		    		SubmenusLabelState[menuname]=true;
				$('#dropdownsubm_'+menuname).removeClass("drop-left-menu").addClass("drop-down-menu");
		    		for (var theOption in thisiconTab) {
				    $("#options-submenu-"+menuname+"-"+thisiconTab[theOption]).show();
		    		}
		    	    }
		    	}
		    });
		}

		
		$('#dropdownsubm').on({
		    click : function(e) {
			if (SubmenuLabelState) {
			    SubmenuLabelState=false;
			    $('#dropdownsubm').removeClass("drop-down-menu").addClass("drop-left-menu");
			    for (var locMenu in LocalMenus) {
				var menuname=LocalMenus[locMenu].replace("GlobalMenuButtonIcon","Global");
				$('#dropdownsubm_'+menuname).hide();
				$("#shareDivSubmenu_"+menuname).hide();
			    }
			} else {
			    SubmenuLabelState=true;
			    $('#dropdownsubm').removeClass("drop-left-menu").addClass("drop-down-menu");
			    for (var locMenu in LocalMenus) {
				var menuname=LocalMenus[locMenu].replace("GlobalMenuButtonIcon","Global");
				$('#dropdownsubm_'+menuname).show();
				$("#shareDivSubmenu_"+menuname).show();
			    }
			}
		    }
		});

		setColorTheme(configColors.colorTheme);	

		$('#options-zone').append("<div id=options-look class=option-group></div>");

		// Color theme 
		$('#options-look').append("<div id=options-color-theme-label class=label>Color theme</div>");
		$('#options-look').append("<form id=options-color-theme-form>");
		$('#options-look').append("<input type='radio' name='color-theme-radio' value='dark'/>Dark<br />");
		$('#options-look').append("<input type='radio' name='color-theme-radio' value='light'/>Light<br />");
		$('#options-look').append("</form><br>");
		$('input[name=color-theme-radio][value=' + configColors.colorTheme + ']').attr("checked", true);

		// Help tooltip => Option NOT USED in Menu.js because only defined at startup
		// $('#options-look').append("<div id=options-tooltip-label class=label>Tooltip</div>");
		// $('#options-look').append("<input type='checkbox' name=enable-tooltip value="+ configBehaviour.tooltip +">Enable Tooltip<br /><br />");
		// $('input[name=enable-tooltip]').attr("checked",configBehaviour.tooltip);

		// Opacity slider
		$('#options-look').append("<div id=options-opacity-label class=label>Opacity</div>");
		$('#options-look').append("<input id=opacitySlider type='range' name=opacitySlider min=0 max=100 value= " + 
					     configBehaviour.opacity*100 + " oninput='opacitySliderOutputId.value=opacitySlider.value.toString()+ \"%\"'>");		
		$('#options-look').append("<output name=opacitySliderOutput id=opacitySliderOutputId for=opacitySlider "+
					     "style='font-size: 80px; padding: 20px; padding-top: 5px; padding-bottom: 5px;'>"+
					  configBehaviour.opacity*100 +"%</output><br /><br />");
		$('#opacitySlider').change(function () {
			var val = ($(this).val() - $(this).attr('min')) / ($(this).attr('max') - $(this).attr('min'));
				
			$(this).css('background-image',
				    '-webkit-gradient(linear, left top, right top, '
				    + 'color-stop(' + val + ', rgb(255, 0, 0)), '
				    + 'color-stop(' + val + ', rgb(0, 255, 0))'
				    + ')'
				    );
		    });
		//$('#opacitySliderOutputId').css('background-image', '');

		// Primary Zoom Slider
		$('#options-look').append("<div id=options-primaryZoomSlider-label class=label>Global Zoom Slider</div>");
		$('#options-look').append("<input type='checkbox' name=enable-primaryZoom value="+ configBehaviour.primaryZoomSlider +">Enable primary Zoom Slider<br />");
		if (parseBool(configBehaviour.primaryZoomSlider))
		    $('input[name=enable-primaryZoom]').attr("checked",configBehaviour.primaryZoomSlider);
		
		// Primary Zoom Slider
		$('#options-look').append("<div id=options-globalVerticalSlider-label class=label>Global Vertical Slider</div>");
		var gVS=false;
		$('#options-look').append("<input type='checkbox' name=enable-globalVertical value="+gVS+">Enable browser vertical slider<br />");
		if (parseBool(gVS))
		    $('input[name=enable-globalVertical]').attr("checked",gVS);
		
		// Spread
		$('#options-zone').append("<div id=options-spread class=option-group></div>");
		$('#options-spread').append("<div id=options-spread-label class=label>Tile size</div>");
		$('#options-spread').append("<input type='checkbox' name=spread-keepratio value="+ configBehaviour.defaultKeepRatio +">Keep ratio<br />");
		if (parseBool(configBehaviour.defaultKeepRatio))
		    $('input[name=spread-keepratio]').attr("checked",configBehaviour.defaultKeepRatio);

		$('#options-spread').append("X: <input id=spreadX name=spreadX type='number' value=" +spread.X +">px   ");
		$('#options-spread').append("Y: <input id=spreadY name=spreadY type='number' value=" +spread.Y +">px <br />");
		$('#options-spread').append("Number of columns:</br><input id=colNumber name=colNumber type='number' value=" +numOfColumns+ "><br />");
		$('#options-spread').append("Space Between </br>Columns:<input id=spaceBetweenColumns name=spaceBetweenColumns type='number' value=" +gapBetweenColumns+ "><br />");
		$('#options-spread').append("Lines:<input id=spaceBetweenLines name=spaceBetweenLines type='number' value=" +gapBetweenLines+ "><br />");

		var clickKR = function(){
		    if ($('input[name=spread-keepratio]').is(":checked"))  { 
			//console.log("KR checked");
			$('input[name=spreadX]').off("change").on({
				change : function(){
				    $('input[name=spreadX]').val($('input[name=spreadX]').val().replace(/[^0-9.]/g, ''))
				    //console.log("changeX");
				    var ratioX = $('input[name=spreadX]').val()/spread.X;
				    //console.log(ratioX);
				    $('input[name=spreadY]').val(spread.Y*ratioX);
				}
			    });
			$('input[name=spreadY]').off("change").on({
				change : function(){
				    $('input[name=spreadY]').val($('input[name=spreadY]').val().replace(/[^0-9.]/g, ''))
				    //console.log("changeY");
				    var ratioY = $('input[name=spreadY]').val()/spread.Y;
				    //console.log(ratioY);
				    $('input[name=spreadX]').val(spread.X*ratioY);
				}
			    });
		    } else { 
			//console.log("KR unchecked");
		    }
		};

		$('input[name=spread-keepratio]').off("click").on({
			click : clickKR
			    });
		if(configBehaviour.defaultKeepRatio)  { // Simulate first click to check the box if default behaviour means it should be checked
		    $('input[name=spread-keepratio]').click();
		}

		// Always show info
		$('#options-zone').append("<div id=options-info class=option-group></div>");
		$('#options-info').append("<div id=options-showinfo-label class=label>Informations</div>");
		$('#options-info').append("<input type='checkbox' id='showinfo-cb' name='showinfo-cb' value="+configBehaviour.alwaysShowInfo+">Always show</input>");
		if (parseBool( configBehaviour.alwaysShowInfo))
		    $('input[name=showinfo-cb]').attr("checked", configBehaviour.alwaysShowInfo);
		// Info style
		$('#options-info').append("<div id=options-info-font-label class=label>Font</div>");
		$('#options-info').append("<select id=options-info-font-select></select>");
		for (var it = 0;it<configBehaviour.infoFonts.length;it++)  { 
		    $('#options-info-font-select').append("<option value='"+it+"'>"+configBehaviour.infoFonts[it].split(",")[0]+"</option>");
		    if(it==configBehaviour.defaultFontIndex)  { 
			$('#options-info-font-select').val(it);
		    }
		}
		$('#options-info').append("<div id=options-info-size-label class=label>Size</div>");
		$('#options-info').append("<input id=infoSize name=infoSize type='number' value="+ parseInt($('.info').css("font-size"))  +"><h1> less than "+configBehaviour.maxInfoFontSize+"</h1>");

		// Drag and drop behaviour
		$('#options-zone').append("<div id=options-dragdrop class=option-group></div>");
		$('#options-dragdrop').append("<div id=options-dragdrop-label class=label>Drag & drop</div>");
		$('#options-dragdrop').append("<input type='checkbox' id='show-only-border-cb' name='show-only-border-cb' value="+configBehaviour.moveOnlyABorder+">Show only the border</br></input>");
		if (parseBool( configBehaviour.moveOnlyABorder))
		    $('input[name=show-only-border-cb]').attr("checked", configBehaviour.moveOnlyABorder);
		$('#options-dragdrop').append("<input type='checkbox' id='move-on-menu-item-cb' name='move-on-menu-item-cb' value="+configBehaviour.moveOnMenuOption+">Enable in menu items</br></input>");
		if (parseBool( configBehaviour.moveOnMenuOption))
		    $('input[name=move-on-menu-item-cb]').attr("checked", configBehaviour.moveOnMenuOption);
		$('#options-dragdrop').append("<input type='checkbox' id='move-on-grid-cb' name='move-on-grid-cb' value="+configBehaviour.moveOnGrid+">Move on a grid</br></br></input>");
		if (parseBool( configBehaviour.moveOnGrid))
		    $('input[name=move-on-grid-cb]').attr("checked", configBehaviour.moveOnGrid);
		$('#options-dragdrop').append("<input type='checkbox' id='showAnimationsLineColSwap' name='showAnimationsLineColSwap' value="+configBehaviour.showAnimationsLineColSwap+">Animate moves</br></input>");
		if (parseBool( configBehaviour.showAnimationsLineColSwap))
		    $('input[name=showAnimationsLineColSwap]').attr("checked", configBehaviour.showAnimationsLineColSwap);
		$('#options-dragdrop').append("<br>Speed of animations:</br><input id=AnimationSpeed name=AnimationSpeed type='number' value=" +configBehaviour.animationSpeed+ "></br>");

		// Zoom Nodes behaviour
		$('#options-zone').append("<div id=options-zoom class=option-group></div>");
		$('#options-zoom').append("<div id=options-sharedZoomNodes-label class=label>Shared zoom nodes</div>");
		$('#options-zoom').append("<input type='checkbox' name=enable-sharedzoomnodes value="+ configBehaviour.sharedZoomNodes +">Enable shared zoom nodes<br /></br>");
		if (parseBool(configBehaviour.sharedZoomNodes))
		    $('input[name=enable-sharedzoomnodes]').attr("checked",configBehaviour.sharedZoomNodes);
		
		$('#options-zoom').append("<input type='checkbox' name=enable-sharedSliderzoom value="+ configBehaviour.sharedSliderZoom +">Enable shared slider zoom<br /></br>");
		if (parseBool(configBehaviour.sharedSliderZoom))
		    $('input[name=enable-sharedSliderzoom]').attr("checked",configBehaviour.sharedSliderZoom);
		
		// master-slave behaviour
		$('#options-zoom').append("<div id=options-masterslave-label class=label>Parallel interaction</div>");
		$('#options-zoom').append("<br>Number of tiles showed:</br><input id=allMSShowMax name=allMSShowMax type='number' value=" +configBehaviour.allMSShowMax+ "></br>");
		$('#options-zoom').append("<br>Only MASTER in MS mode:</br><input id=onlyMasterMS name=onlyMasterMS type='checkbox' value=" +configBehaviour.onlyMasterMS+ "></br>");
		if (parseBool(configBehaviour.onlyMasterMS))
		    $('input[name=onlyMasterMS]').attr("checked",configBehaviour.onlyMasterMS);

		$('#options-zone').append("<div id=options-touch class=option-group></div>");
		// Touch behaviour
		$('#options-touch').append("<div id=options-touch-label class=label>Touchable device</div>");
		if (touchok) {

		    $('#options-touch').append("<br>Speed of touch:</br><input id=touchSpeed name=touchSpeed type='number' value=" +configBehaviour.touchSpeed+ "></br>");
		    $('#options-touch').append("<input type='checkbox' id='touchon-window' name='touchon-window' value="+configBehaviour.touchonWindow+">Touch on window gesture</input></br>");
		    if (parseBool( configBehaviour.touchonWindow))
		        $('input[name=touchon-window]').attr("checked", configBehaviour.touchonWindow);			    
		}
		$('#options-touch').append("<input type='checkbox' id='smooth-rotation' name='smooth-rotation' value="+configBehaviour.smoothRotation+">Smooth rotation</input>");
		if (parseBool( configBehaviour.smoothRotation))
		    $('input[name=smooth-rotation]').attr("checked", configBehaviour.smoothRotation);
		
		$('#options-touch').append("<br>Speed of rotation:</br><input id=RotInc name=RotInc type='number' step='0.1' value=" +configBehaviour.RotationSpeed+ "></br>");

		// Button to save and exit the options menu
		$('#options').append("<div id=buttonApply title='Apply for this browser'></div>");

		// Button cancel modifications
		$('#options').append("<div id=buttonCancel title='Cancel changes'></div>");

		// Button to save config in a file
		$('#options').append("<div id=buttonSave title='Apply and save options to a file'></div>");

		// Button to share config to all clients in room
		$('#options').append("<div id=buttonShare title='Apply and share to other clients in session'</div>");
		
		$('#'+id+'option'+optionNumber).attr('class', $('#'+id+'option'+optionNumber).attr('class').replace('optionsButtonIcon', 'closeOptionsButtonIcon'));

		// Get all values
		ApplyParameters = function() {
		    var tempColors = "'colors': {***}";
		    // var tempJsonData = "'jsonData': {***}";
		    var tempBehaviour = "'behaviour': {***}";
		    // var tempTagBehaviour = "'tagBehaviour': {***}";
		    // var tempCSSProperties = "'cssProperties': {***}";

		    if(configColors.colorTheme != $('input[name=color-theme-radio]').filter(':checked').val())  { 
			configColors.colorTheme = $('input[name=color-theme-radio]').filter(':checked').val();
			setColorTheme(configColors.colorTheme);
		    }
		    tempColors=tempColors.replace("***","'colorTheme':'"+configColors.colorTheme+"'"+", ***");

		    // Help tooltip => Option NOT USED in Menu.js because only defined at startup
		    // configBehaviour.tooltip = $('input[name=enable-tooltip]').is(":checked");
		    // tempBehaviour=tempBehaviour.replace("***","'tooltip': '"+configBehaviour.tooltip+"', ***");
		    
		    if(configBehaviour.opacity*100 != $('#opacitySlider').val())  { 
			configBehaviour.opacity = Math.max($('#opacitySlider').val()/100, 0.1);
			for (O in nodesById)  { 
			    nodesById[O].setNodeOpacity(configBehaviour.opacity);
			}
		    }
		    tempBehaviour=tempBehaviour.replace("***","'opacity':"+configBehaviour.opacity+", ***");

		    configBehaviour.primaryZoomSlider = $('input[name=enable-primaryZoom]').is(":checked");
		    if (parseBool( configBehaviour.primaryZoomSlider )) {
			$('#primarySliderLabel').show();
			$('#primarySlider').show();
			$('#primarySlider').click();
		    } else {
			$('#primarySliderLabel').hide();
			$('#primarySlider').hide();
			$('#primaryparent').css("transform","")
			$('#primaryparent').css("transform-origin","")
		    }
		    
		    var gVS = $('input[name=enable-globalVertical]').is(":checked");
		    if (parseBool(gVS))
			document.body.setAttribute('style','overflow:hidden auto;');
		    else
			document.body.setAttribute('style','overflow:hidden;');
			
		    var hasSpreadChanged = false;
		    if(spread.X != $('input[name=spreadX]').val())  { 
			if ( $('input[name=spreadX]').val() == "")
			    $('input[name=spreadX]').val(spread.X)
			//console.log("change X, new", $('input[name=spreadX]').val());
			hasSpreadChanged = true;
		    }
		    if(spread.Y != $('input[name=spreadY]').val())  { 
			if ( $('input[name=spreadY]').val() == "")
			    $('input[name=spreadY]').val(spread.Y)
			//console.log("change Y, new", $('input[name=spreadY]').val());
			hasSpreadChanged = true;
		    }

		    if(hasSpreadChanged)  { 
			$('input[name=spreadX]').val($('input[name=spreadX]').val().replace(/[^0-9.]/g, ''))
			$('input[name=spreadY]').val($('input[name=spreadY]').val().replace(/[^0-9.]/g, ''))
			var newSpread = {
			    X : parseInt($('input[name=spreadX]').val()),
			    Y : parseInt($('input[name=spreadY]').val())
			    
			};
			me.updateSpread(newSpread);
			
			temp3="'spread': { 'X':"+newSpread.X+",  'Y':"+newSpread.Y+"}";
			tempBehaviour=tempBehaviour.replace("***",temp3+", ***");
		    }

		    //console.log(parseInt($('input[name=colNumber]').val()));
		    numOfColumns = parseInt($('input[name=colNumber]').val());
                    tempBehaviour=tempBehaviour.replace("***","'maxNumOfColumns': "+numOfColumns+", ***");

		    gapBetweenColumns = parseInt($('input[name=spaceBetweenColumns]').val());
                    tempBehaviour=tempBehaviour.replace("***","'spaceBetweenColumns': "+gapBetweenColumns+", ***");

		    gapBetweenLines = parseInt($('input[name=spaceBetweenLines]').val());
                    tempBehaviour=tempBehaviour.replace("***","'spaceBetweenLines': "+gapBetweenLines+", ***");

	            maxNumOfColumns=numOfColumns;
		    mesh.globalLocationProvider();
		    
		    configBehaviour.alwaysShowInfo = $('input[name=showinfo-cb]').is(":checked");
		    tempBehaviour=tempBehaviour.replace("***","'alwaysShowInfo': '"+configBehaviour.alwaysShowInfo+"', ***");

		    if(parseInt($('.info').css("font-size"))!=$('#infoSize').val())  { 
			$('.info').css("font-size",  Math.min($('#infoSize').val(), configBehaviour.maxInfoFontSize) + "px");
			configBehaviour.defaultInfoFontSize = $('.info').css("font-size");

			tempBehaviour=tempBehaviour.replace("***","'defaultInfoFontSize': '"+configBehaviour.defaultInfoFontSize+"', ***");
		    }
		    configBehaviour.defaultFontIndex = $('#options-info-font-select').val();
		    $('.info').css("font-family", configBehaviour.infoFonts[configBehaviour.defaultFontIndex]);

		    tempBehaviour=tempBehaviour.replace("***","'defaultFontIndex': "+configBehaviour.defaultFontIndex+", ***");

		    configBehaviour.moveOnlyABorder = $('input[name=show-only-border-cb]').is(":checked");
		    tempBehaviour=tempBehaviour.replace("***","'moveOnlyABorder': '"+configBehaviour.moveOnlyABorder+"', ***");
		    configBehaviour.moveOnMenuOption = $('input[name=move-on-menu-item-cb]').is(":checked");
                    tempBehaviour=tempBehaviour.replace("***","'moveOnMenuOption': '"+configBehaviour.moveOnMenuOption+"', ***");
		    configBehaviour.moveOnGrid = $('input[name=move-on-grid-cb]').is(":checked");
                    tempBehaviour=tempBehaviour.replace("***","'moveOnGrid': '"+configBehaviour.moveOnGrid+"', ***");
		    configBehaviour.showAnimationsLineColSwap = $('input[name=showAnimationsLineColSwap]').is(":checked");
                    tempBehaviour=tempBehaviour.replace("***","'showAnimationsLineColSwap': '"+configBehaviour.showAnimationsLineColSwap+"', ***");
		    
		    configBehaviour.animationSpeed = $('#AnimationSpeed').val();
                    tempBehaviour=tempBehaviour.replace("***","'animationSpeed': "+configBehaviour.animationSpeed+", ***");

		    configBehaviour.sharedZoomNodes = $('input[name=enable-sharedzoomnodes]').is(":checked");
		    tempBehaviour=tempBehaviour.replace("***","'sharedZoomNodes': '"+configBehaviour.sharedZoomNodes+"', ***");
		    
		    configBehaviour.sharedSliderZoom = $('input[name=enable-sharedSliderzoom]').is(":checked");
		    tempBehaviour=tempBehaviour.replace("***","'sharedSliderZoom': '"+configBehaviour.sharedSliderZoom+"', ***");
		    
		    configBehaviour.allMSShowMax = $('#allMSShowMax').val();
                    tempBehaviour=tempBehaviour.replace("***","'allMSShowMax': "+configBehaviour.allMSShowMax+", ***");
		    
		    configBehaviour.onlyMasterMS = $('#onlyMasterMS').val();
                    tempBehaviour=tempBehaviour.replace("***","'onlyMasterMS': "+configBehaviour.onlyMasterMS+", ***");
		    
		    if (touchok) {
			configBehaviour.touchSpeed = $('#touchSpeed').val();
			tempBehaviour=tempBehaviour.replace("***","'touchSpeed': "+configBehaviour.touchSpeed+", ***");

			configBehaviour.touchonWindow = $('#touchon-window').val();
			if (parseBool(configBehaviour.touchonWindow)) {
			    document.body.setAttribute('style','overflow:auto;');			    
			} else {
			    document.body.setAttribute('style','overflow:hidden;');
			}
			tempBehaviour=tempBehaviour.replace("***","'touchonWindow': "+configBehaviour.touchonWindow+", ***");
		    }

		    configBehaviour.smoothRotation = $('input[name=smooth-rotation]').is(":checked");
		    tempBehaviour=tempBehaviour.replace("***","'smoothRotation': '"+configBehaviour.smoothRotation+"', ***");
		    if (parseBool(configBehaviour.smoothRotation)) {
			configBehaviour.RotationSpeed=$('#RotInc').val();
			tempBehaviour=tempBehaviour.replace("***","'RotationSpeed': '"+configBehaviour.smoothRotation+"', ***");
			RotInc=parseFloat(configBehaviour.RotationSpeed); //for a smooth touchmove rotation
		    } else {
			// for a turn over with only touchstart / touchend (no touchmove) events
			RotInc=180; 
		    }

		    temp3="'shareMenu': { ";
		    tempBehaviour=tempBehaviour.replace("***",temp3+" ***");
		    
		    for (var theOption in thisIconTab) {
			ThisMenuShared=$('input[name=shareMenu_'+thisIconTab[theOption]+']').is(":checked");
			me.menu.setMenuShareEvent(theOption, ThisMenuShared);
			tempBehaviour=tempBehaviour.replace("***","'"+thisIconTab[theOption]+"': '"+ThisMenuShared+"', ***");
		    }
		    for (var locMenu in LocalMenus) {
			var menuname=LocalMenus[locMenu].replace("GlobalMenuButtonIcon","Global")
			var thismenu=subMenusGlobal.filter(menu=>menu.getId()==menuname)[0];
			var thisiconTab=thismenu.getMenuIconClassAttributesTab();
			for (var theOption in thisiconTab) {
			    ThisMenuShared=$('input[name=shareMenu_'+thisiconTab[theOption]+']').is(":checked");
			    thismenu.setMenuShareEvent(theOption, ThisMenuShared);
			    tempBehaviour=tempBehaviour.replace("***","'"+thisiconTab[theOption]+"': '"+ThisMenuShared+"', ***");
			}
		    }
		    
		    temp3="}";
		    tempBehaviour=tempBehaviour.replace(", ***",temp3+", ***");
		    
		    var tempConfigJson="{"
			+ tempColors.replace(", ***","").replace("***","")+","
			// + tempJsonData.replace(",\n ***","").replace("***","")+",\n"
			+ tempBehaviour.replace(", ***","").replace("***","")
			// + tempTagBehaviour.replace(",\n ***","").replace("***","")+",\n"
			// + tempCSSProperties.replace(",\n ***","").replace("***","")+"\n"
			+ "}";

		    return tempConfigJson.replaceAll("'",'"');
		}

		
		// Interactions
		$('#buttonApply').off("click").on({

			click : function(){
			    ApplyParameters();
			    $('#buttonCancel').click();
			}
		    });

		$('#buttonCancel').off("click").on('click',function() { 
		    $('#'+id+'option'+optionNumber).click();
		});

		$('#buttonSave').off("click").on({
			click : function(){				
			    ConfigJson = ApplyParameters();
			    
			    var sessionDate = new Date();
			    var strDate=sessionDate.toLocaleDateString({day: "2-digit", month: "2-digit"}).replace(/\//g, "-") + "_" + sessionDate.toLocaleTimeString("fr-FR").replace(/:/g, "-")
			    var fileName = my_session + "_" + "Config_" + strDate + ".json"; 
			    //var file = new File([ConfigJson], fileName, {type: "text/plain;charset=utf-8"},{ autoBom: false });
			    //saveAs(file);
			    download([ConfigJson], fileName, {type: "text/plain;charset=utf-8"})
			    addBlink(this)

			    // Force save config in DB too.
			    cdata ={"room":my_session, "Config": ConfigJson.replaceAll("'",'"') }
			    console.log("Share config : "+ConfigJson);
			    // used to deploy config but not on the user that have emited the signal.
			    myOwnConfig=true;
			    socket.emit("share_Config", cdata);
			}
		});
		
		$('#buttonShare').off("click").on({
			click : function(){				
			    ConfigJson = ApplyParameters();
			    
			    cdata ={"room":my_session, "Config": ConfigJson.replaceAll("'",'"') }
			    console.log("Share config : "+ConfigJson);
			    // used to deploy config but not on the user that have emited the signal.
			    myOwnConfig=true;
			    socket.emit("share_Config", cdata);
			    addBlink(this)
			}
		});
		
	    } else {
		$('#options').remove();
		$('#options-content-select').remove();
		$('#'+id+'option'+optionNumber).removeClass("closeOptionsButtonIcon").addClass("optionsButtonIcon");
	    }
	});

    managementGlobalMenuIconClassAttributesTab.push("optionsButtonIcon");
    managementGlobalMenuShareEvent.push(false);


    // Update parameters for options
    UpdateParameters = function(configJson) {
	var tempColors = configJson.colors;
	// var tempJsonData = configJson.jsonData;
	var tempBehaviour = configJson.behaviour;
	// var tempTagBehaviour = configJson.tagBehaviour;
	// var tempCSSProperties = configJson.cssProperties;

	if (tempColors.hasOwnProperty('colorTheme')) {
	    configColors.colorTheme = tempColors.colorTheme
	    setColorTheme(configColors.colorTheme);
	}

	// Help tooltip => Option NOT USED in Menu.js because only defined at startup
	// if(tempBehaviour.hasOwnProperty('tooltip'))
	//     configBehaviour.tooltip = $.parseJSON(tempBehaviour.tooltip);

	if(tempBehaviour.hasOwnProperty('opacity')) {
	    configBehaviour.opacity = tempBehaviour.opacity;
	    for (O in nodesById)  { 
		nodesById[O].setNodeOpacity(configBehaviour.opacity);
	    }
	}

	if(tempBehaviour.hasOwnProperty('spread'))  { 
	    var newSpread = {
		X : parseInt(tempBehaviour.spread.X),
		Y : parseInt(tempBehaviour.spread.Y)
		
	    };
	    me.updateSpread(newSpread);			
	}

        if(tempBehaviour.hasOwnProperty('maxNumOfColumns'))
	    numOfColumns = tempBehaviour.maxNumOfColumns;
	
        if(tempBehaviour.hasOwnProperty('spaceBetweenColumns'))
	    gapBetweenColumns = tempBehaviour.spaceBetweenColumns
        if(tempBehaviour.hasOwnProperty('spaceBetweenLines'))
	    gapBetweenLines = tempBehaviour.spaceBetweenLines
	    
	maxNumOfColumns=numOfColumns;
	mesh.globalLocationProvider();

	if(tempBehaviour.hasOwnProperty('alwaysShowInfo'))
	    configBehaviour.alwaysShowInfo = $.parseJSON(tempBehaviour.alwaysShowInfo);

	if(tempBehaviour.hasOwnProperty('defaultInfoFontSize'))  {
	    configBehaviour.defaultInfoFontSize = tempBehaviour.defaultInfoFontSize;
	    $('.info').css("font-size",configBehaviour.defaultInfoFontSize) 
	}
	if(tempBehaviour.hasOwnProperty('defaultFontIndex'))  { 
	    configBehaviour.defaultFontIndex = tempBehaviour.defaultFontIndex;
	    $('.info').css("font-family", configBehaviour.infoFonts[configBehaviour.defaultFontIndex]);
	}

	if(tempBehaviour.hasOwnProperty('moveOnlyABorder'))
	    configBehaviour.moveOnlyABorder = $.parseJSON(tempBehaviour.moveOnlyABorder);

	if(tempBehaviour.hasOwnProperty('moveOnMenuOption'))
	    configBehaviour.moveOnMenuOption = $.parseJSON(tempBehaviour.moveOnMenuOption);

	if(tempBehaviour.hasOwnProperty('moveOnGrid'))
	    configBehaviour.moveOnGrid = $.parseJSON(tempBehaviour.moveOnGrid);

        if(tempBehaviour.hasOwnProperty('showAnimationsLineColSwap'))
	    configBehaviour.showAnimationsLineColSwap = $.parseJSON(tempBehaviour.showAnimationsLineColSwap);
		    
        if(tempBehaviour.hasOwnProperty('animationSpeed'))
	    configBehaviour.animationSpeed = tempBehaviour.animationSpeed;
		    
        if(tempBehaviour.hasOwnProperty('allMSShowMax'))
	    configBehaviour.allMSShowMax = tempBehaviour.allMSShowMax;
	
        if(tempBehaviour.hasOwnProperty('onlyMasterMS'))
	    configBehaviour.onlyMasterMS = tempBehaviour.onlyMasterMS;
	
	if (touchok) {

            if(tempBehaviour.hasOwnProperty('touchSpeed'))
		configBehaviour.touchSpeed = tempBehaviour.touchSpeed;
            if(tempBehaviour.hasOwnProperty('touchonWindow'))
		configBehaviour.touchonWindow = tempBehaviour.touchonWindow;
	}			

	configBehaviour.smoothRotation = false;
        if(tempBehaviour.hasOwnProperty('smoothRotation'))
	    configBehaviour.smoothRotation = $.parseJSON(tempBehaviour.smoothRotation);

	if (parseBool(configBehaviour.smoothRotation)) {
            if(tempBehaviour.hasOwnProperty('RotationSpeed'))
		configBehaviour.RotationSpeed =  $.parseJSON(tempBehaviour.RotationSpeed);
	    RotInc=parseFloat(configBehaviour.RotationSpeed); //for a smooth touchmove rotation
	} else {
	    // for a turn over with only touchstart / touchend (no touchmove) events
	    RotInc=180; 
	}
				    
    }

    /** Help icon : 
     */

    var initHelp=null;

    managementGlobalMenuTitleTab.push("Show help page")
    managementGlobalMenuEventTab.push(    function(v, id, optionNumber){
	    if (v==true)  { 
		//var support = document.getElementById("helpframe");

		if (initHelp == null)  { // First time opening the help menu: Help page will be loaded
		    htmlPrimaryParent.prepend($('#helpSupport'));	
		    $('#helpSupport').css({ // TO BE CONTINUED !
			    position : "absolute",
				//top : parseInt($('#header').css('height')),
				top : 0, 
				//padding : "100px",
				left : parseInt($(me.menu.getHtmlMenuSelector()).css("width")),
				zIndex : 750,
				height : "100%",
				width : "100%",
				backgroundColor : "black",
				opacity : 1
				});


		    $('#helpframe').attr("height","30%").attr("width","30%").css({
			    height: "30%",
				width : "30%"
		    });
		    
		    console.log(helpPath);
		    $('#helpSupport').append('<div id=buttonClosehelp class=unzoomButtonIcon></div>');
		    $('#helpSupport').append("<div id=helpSliderLabel style='background-image: none; color: white; background-color: black; font-size: 80px; padding: 20px; padding-top: 5px; padding-bottom: 5px;'>Zoom</div>");
		    $('#buttonClosehelp').css({
			position : "fixed", 
			top : 0 ,
			left : parseInt($(me.menu.getHtmlMenuSelector()).css("width")),
			height : 200,
			width : 200,
			zIndex : 802,	
			backgroundColor: "rgba(0, 0, 0, 0.5)"
		    });
		    $('#buttonClosehelp').off("click").on('click',function() { 
			$('#helpSupport').hide();	
			$('#'+id +'option'+optionNumber).removeClass("closeHelpButtonIcon").addClass("helpButtonIcon")
		    });
		    
		    $('#helpSliderLabel').css({
			position: "fixed",
			fontSize : "150px",
			left : parseInt($(me.menu.getHtmlMenuSelector()).css("width"))
			    +parseInt($('#buttonClosehelp').css("width")),
			top: 10,
			//color: "white",
			zIndex: 802,
			padding: "0px 50px",
			width : "600px",
			height : "200px"
			//backgroundColor: "rgba(0, 0, 0, 0.5)"
		    });

		    $('#helpSliderLabel').append("<input id=helpSlider type='range' name=helpSlider min="+window.devicePixelRatio*100+" max="+5*window.devicePixelRatio*100+" value= " + 
						 3*window.devicePixelRatio*100 + ">");

		    $('#helpSlider').css({
			position : "fixed", 
			top: parseInt($('#helpSliderLabel').css("height"))/2,
			left : (parseInt($('#helpSliderLabel').css("width"))
				+parseInt($('#buttonClosehelp').css("width")))*1.1,
			//width : 30/100 * parseInt($('header').css("width"))
			width: parseInt($('header').css("width"))/2 - parseInt($(me.menu.getHtmlMenuSelector()).css("width")),
			//padding : parseInt($('#helpSliderLabel').css("height"))/2,
		    });
		    
		    $('#helpSlider').change(function () {
			    var val = ($(this).val() - $(this).attr('min')) / ($(this).attr('max') - $(this).attr('min'));
				
			    $(this).css('background-image',
					'-webkit-gradient(linear, left top, right top, '
					+ 'color-stop(' + val + ', rgb(255, 0, 0)), '
					+ 'color-stop(' + val + ', rgb(0, 255, 0))'
					+ ')'
					);
			});

		    var val = ($("#helpSlider").val() - $("#helpSlider").attr('min')) / ($("#helpSlider").attr('max') - $("#helpSlider").attr('min'));
		    $('#helpSlider').css('background-image',
					 '-webkit-gradient(linear, left top, right top, '
					 + 'color-stop(' + val + ', rgb(255, 0, 0)), '
					 + 'color-stop(' + val + ', rgb(0, 255, 0))'
					 + ')'
					 );


		    $('#helpframe').css({
			    position: "fixed",
				top : parseInt($('#helpSliderLabel').css("height"))
				});

		    $('#helpSlider').off("click").on({
			    click : function(e){
				var newZoom = $('#helpSlider').val();
				var ratio = newZoom/(window.devicePixelRatio*100);
				$('#helpframe').css("-moz-transform","scale("+ratio+")").css("-webkit-transform","scale("+ratio+")").css("transform-origin", "0 0 0");
			    }
			});

		    $('#helpSlider').click();
		    //$('#helpSupport').load("doc/user_doc_EN.html");

		    setColorTheme(configColors.colorTheme); // First time: set colors	
		    $('#helpSupport').show();
			
		    initHelp="ok";
		} else // Simply show the previous (hidden since) help page.
		    {
			$('#helpSupport').show();
		    }	

		$('#'+id+'option'+optionNumber).removeClass("helpButtonIcon").addClass("closeHelpButtonIcon");
	    } else
		$('#buttonClosehelp').click();
	});
    managementGlobalMenuIconClassAttributesTab.push("helpButtonIcon");
    managementGlobalMenuShareEvent.push(false);

    /** Cancel menu
     - Undo last operation (Ctrl+Z)
     - Redo last operation (Ctrl+Y)
     */
    
    var cancelGlobalMenuTitleTab = new Array();
    var cancelGlobalMenuEventTab = new Array();
    var cancelGlobalMenuIconClassAttributesTab = new Array();
    var cancelGlobalMenuShareEvent = new Array();

    // Cancel last movement
    cancelGlobalMenuTitleTab.push("Cancel last movement")
    cancelGlobalMenuEventTab.push((    function(){

		return function(v){
		    if(!(nodesOldPositions.length-stepBack == -1))  { // ie nodesOldPositions.length != 0, ie there is/are movement(s) to cancel			
			if(stepBack==1)  { 
			    //console.log("stepback == 1");
			    me.savePositions();
			    stepBack++;
			}

			var back = function(){

			    var u = 0;

			    for(u=0;u<nodesByLoc.length;u++)  { 	
				me.switchLocation(me.getNode(nodesOldPositions[nodesOldPositions.length-stepBack][u]),nodesByLoc[u],true,false);
			    }
			    // If the last movement was a "block movement", ie column or line swap, undo the
			    // swap with only one click
			    if (nodesOldPositions[nodesOldPositions.length - stepBack][nodesByLoc.length])  { 
				stepBack ++;
				back();	
			    }
			}

			if(v==true)  { 	
			    back();
			} else { 		
			    back();
			}

			stepBack++;

		    }	

		};
	    })());

    cancelGlobalMenuIconClassAttributesTab.push("moveBackButtonIcon");
    cancelGlobalMenuShareEvent.push(true);
    
    /** Define keyboard shortcuts Ctrl+Z and Alt+Z to undo last movement */

    // var ctrlpress = false;
    // var altpress = false;
    // var sizeMenuEventTab = menuEventTab.length-1;
    // $("body").on({
    // 	    keydown : function(e){
    // 		//CTRL
    // 		if(e.keyCode==17)  { 
    // 		    ctrlpress=true;

    // 		    $("body").on({

    // 			    keydown : function(e){
    // 				//Z
    // 				if(e.keyCode==90 && ctrlpress==true)  { 

    // 				    menuGlobal.children(menuGlobal.attr("id").replace("menu","")+'option'+sizeMenuEventTab).click();//MARK
    // 				}
    // 			    },
    // 				keyup : function(e){
    // 				//CTRL
    // 				if(e.keyCode==17)  { 
    // 				    ctrlpress=false;
    // 				}
    // 			    }				
    // 			});
    // 		} //alt
    // 		// else 
    // 		// if(e.keyCode==18)
    // 		// {
    // 		//     altpress=true;

    // 		//     $("body").on({

    // 		//	keydown : function(e){
    // 		//	    //Z
    // 		//	    if(e.keyCode==90 && altpress==true)
    // 		//	    {

    // 		//		menuGlobal.children(menuGlobal.attr("id").replace("menu","")+'option'+sizeMenuEventTab).click();
    // 		//	    }
    // 		//	},
    // 		//	keyup : function(e){
    // 		//	    //ALT
    // 		//	    if(e.keyCode==18)
    // 		//	    {
    // 		//		altpress=false;
    // 		//	    }
    // 		//	}				
    // 		//     });
    // 		// }
    // 	    }
    // 	});


    /** Re-do last cancelled action */
    cancelGlobalMenuTitleTab.push("Redo last cancelled")
    cancelGlobalMenuEventTab.push((    function(){


		return function(v){

		    var stepForward = 1-stepBack; // It was 2-stepBack in Yacouba's code, and caused an error when trying to undo movements at the beginning, when they weren’t any (stepForward = 2-1 = 1, the loop was entered, but nodesOldPositions[nodes….length + 1] didn’t exist).
		    //console.log(stepForward, stepBack);	
		    if(stepForward<0 && stepForward + nodesOldPositions.length >= 0)  { 



			var forward = function(){

			    var u = 0;

			    //console.log(nodesOldPositions.length+stepForward);
			    for(u=0;u<nodesByLoc.length;u++)  { 	
				me.switchLocation(me.getNode(nodesOldPositions[nodesOldPositions.length+stepForward][u]),nodesByLoc[u],true,false);
			    }
			    // If the last undone movement was a block move, we want to detect it and re-do
			    // it in one click
			    if (stepForward + 1 <= -1)  { // Condition on length : we want the "nodesOldPositions.length + stepForward +1"-th element, this index has to be smaller than "nodesOldPositions.length - 1"
				var boolCurrIdx = nodesOldPositions[nodesOldPositions.length+stepForward][nodesByLoc.length];
				var boolNextIdx = nodesOldPositions[nodesOldPositions.length+stepForward+1][nodesByLoc.length];
				//console.log(boolCurrIdx, boolNextIdx);
				if (boolNextIdx  || boolCurrIdx)  { 
				    //console.log("detected block");
				    stepBack --;
				    stepForward = 1-stepBack;
				    //console.log(stepBack, stepForward);

				    if(stepForward<0 && stepForward >= -nodesOldPositions.length)  { // Ensure no forbidden operations / access to unaccessible index in the array
					forward();
				    }
				}
			    } else { 
				console.log("not in range (forward)");
			    }
			}

			if(v==true)  { 	
			    forward();
			} else { 		
			    forward();
			}

			stepBack--;
		    }
		};
	    })());

    cancelGlobalMenuIconClassAttributesTab.push("moveForwardButtonIcon");
    cancelGlobalMenuShareEvent.push(true);
    
    /** Keyboard shortcuts Ctrl+Y or Alt+Y to re-do last cancelled action. */

    // var ctrlpress = false;
    // //var altpress = false;
    // var sizeMenuEventTab2 = menuEventTab.length-1;
    // $("body").on({
    // 	    keydown : function(e){
    // 		//CTRL
    // 		if(e.keyCode==17)  { 
    // 		    ctrlpress=true;

    // 		    $("body").on({

    // 			    keydown : function(e){
    // 				//Y
    // 				if(e.keyCode==89 && ctrlpress==true)  { 

    // 				    menuGlobal.children(menuGlobal.attr("id").replace("menu","")+'option'+sizeMenuEventTab2).click();
    // 				}
    // 			    },
    // 				keyup : function(e){
    // 				//CTRL
    // 				if(e.keyCode==17)  { 
    // 				    ctrlpress=false;
    // 				}
    // 			    }				
    // 			});
    // 		} // alt
    // 		// else 
    // 		// if(e.keyCode==18)
    // 		// {
    // 		//     altpress=true;

    // 		//     $("body").on({

    // 		//	keydown : function(e){
    // 		//	    //Y
    // 		//	    if(e.keyCode==89 && altpress==true)
    // 		//	    {
    // 		//		menuGlobal.children(menuGlobal.attr("id").replace("menu","")+'option'+sizeMenuEventTab2).click();

    // 		//	    } 
    // 		//	},
    // 		//	keyup : function(e){
    // 		//	    //ALT
    // 		//	    if(e.keyCode==18)
    // 		//	    {
    // 		//		altpress=false;
    // 		//	    }
    // 		//	}				
    // 		//     });
    // 		// } 
    // 	    }
    // 	});

    /** Updown menu
     - Move up all lines and place first line on last one
     - Move down all lines and place last line on first
    */    

    var updownGlobalMenuTitleTab = new Array();
    var updownGlobalMenuEventTab = new Array();
    var updownGlobalMenuIconClassAttributesTab = new Array();
    var updownGlobalMenuShareEvent = new Array();

    // Move up all lines and place first line on last one
    updownGlobalMenuTitleTab.push("Move up all lines and place first line on last one")
    updownGlobalMenuEventTab.push(    function(v, id, optionNumber){
		moveMesh("up");
	});
    updownGlobalMenuIconClassAttributesTab.push("upArrowButtonIcon");
    updownGlobalMenuShareEvent.push(true);
    
    // Move down all lines and place last line on first
    updownGlobalMenuTitleTab.push("Move down all lines and place last line on first")
    updownGlobalMenuEventTab.push(    function(v, id, optionNumber){
		moveMesh("down");
	});
    updownGlobalMenuIconClassAttributesTab.push("downArrowButtonIcon");
    updownGlobalMenuShareEvent.push(true);

    /** GLOBAL MENU	
     * List of implemented functions : 

     - Search/Filter option
     - Clear all selections
     - Next "Off" tiles move up
     - Only if touchable browser : Show rotate button on each node.
     - Refresh button
     - Tag menu : Zoom on selection, Master-Slave mode, zoom on one node.
     - Management menu : manage of overlay draws, save session, options, help frame. 
     - Info on node menu : OnOff buttons, QRcodes, title information.
     - Node menu : transparency, text on nodes, draw mode, sort lines or columns 
     - Cancel Global Menu
     - Up/Down on lines menu
    */
    var menuTitleTab = new Array();
    var menuEventTab = new Array();
    var menuIconClassAttributesTab = new Array();
    var menuShareEvent = new Array();

    /** Filter node through tags and zoom on filtered nodes
	- Launch a simple research 
	-> type the keyword in the search bar and press enter : 
	the matching nodes will move to the top of the grid, the other ones will stay at the bottom and become darker.
	- Launch a multiple research 
	-> type the keywords in the search bar, using the symbol "&" as separator ("pressure&heat" to search for both terms) : 
	a legend with different colors will be shown at the top of the screen.
	- Clean search : click on the Eraser icon on the upper-right corner.
	This filter use Jquery UI modules : autocompletes, see https://jqueryui.com/autocomplete/ for details
    */
    // Filter node through tags and zoom on filtered nodes
    menuTitleTab.push("Filter node through tags and zoom on filtered nodes")
    menuEventTab.push(    function(v,id,optionNumber){

	    me.savePositions();	
	    // Variable for the magnifyingGlass function
	    var ratio =spread.Y/spread.X;
	    var initSpread = spread;

	    if(v==true)  { 	
		var numOfFilter= 0;

		$('header').css({height : 250 /*GLOBALCSS ?*/, width : htmlPrimaryParent.css("width")});
		_allowDragAndDrop = false;

		// Creation of the search bar
		$('header').append("<div id=search></div>");
		$("#search").css({ //GLOBALCSS
			position :"fixed", 
			    top : 0 , 
			    left :  parseInt($(me.menu.getHtmlMenuSelector()).css("width")), // +100/* .split("px")[0] */ , 
			    height : 100, 
			    width : 800, 
			    backgroundColor : "black", 
			    fontSize : 50, 
			    color : "white"
			    });

		$("#search").append("<label for=filter>Filter: </label>").append("<input id=filter type=text>").css({ 
			position : "fixed" ,
			    top : 210, 
			    left :  parseInt($(me.menu.getHtmlMenuSelector()).css("width")), 
			    zIndex : 131
			    });
		$("#filter").css({ 
			top : 205, 
			    left :  parseInt($(me.menu.getHtmlMenuSelector()).css("width")), 
			    height : 80, 
			    width : 800, 
			    fontSize : 70,
			    zIndex : 131

			    });
		$('filter').draggable();
		// Add a button to clean the legend
		$('header').append("<div id=brush class=brushButtonIcon></div>");
		$("#brush").css({ // GLOBALCSS !
			position : "fixed",
			    height : 200, 
			    width : 200,
			    top : 0, 
			    left : parseInt($(me.menu.getHtmlMenuSelector()).css("width")),
			    zIndex : 802,
			    });
		var left_ = parseInt($(me.menu.getHtmlMenuSelector()).css("width")) + parseInt($('#brush').css("width"));
		//var width_ = parseInt($('header').css("width"))-left_-50;
		var width_ = window.innerWidth - left_;

		// Creation of the div $(#blackboard) containing the legend
		$('header').append("<div id=blackboard></div>");			
		$("#blackboard").css({ // GLOBALCSS ?
			position :"fixed",
			    height : "200px" , 
			    width : width_, 
			    top : 0, 
			    left  : left_,
			    zIndex : 149, 
			    display : "flex",/*  flexDirection: "column", */
			    flexWrap: "wrap"/* , marginTop : 20 */});




		// Autocomplete : see https://jqueryui.com/autocomplete/ for details
		$( "#search" ).off("autocompleteselect").on( "autocompleteselect", function( event, ui ) {

			document.getElementById("filter").value = ui.item.value;
		    });

		// Set user interaction
		$("#search").off("tap focusin").on("tap focusin",			 

			function(){

			    $("#search").off("keydown").on({	

				    keydown : function(e){ // TO DO : replace with keypresses ?
					$('#internal_warning').remove();
					if(e.keyCode == 13)  { 
					    var nodeZoomTab = new Array();
					    var text_ = $('#filter').val();	
					    // Substitution if the user writes "&&" or "&&&" instead of "&", or spaces
					    text_=text_.replace('&&','&').replace('&&','&').replace(' ','');
					    var textTab = text_.split("&"); // Builds a tab with the different tags or filters
					    var e=0;

					    for(e=0;e<textTab.length;e++)  { 
						text_=textTab[e];
						var nodesbis=nodesById;
						var w=0;

						if(appliedFilters.indexOf(text_)==-1)  { 
						    // TO DO : study influence of nodes/nodesbis in the loops ?
						    // TO DO : what happens when too many filters ?	
						    for(O in nodesbis)  { 
							if(me.hasTag(nodesbis[O],text_))  { 
							    nodeZoomTab.push(nodesById[O]);
							    me.switchLocation(nodesbis[O],nodesByLoc[w],false,true);
							    nodesbis[O].getHtmlNode().css({
								    opacity : 1
									});
							    nodesbis[O].getStickers().addSticker(text_,colorFilterStickersTab[numOfFilter],true);
							    w++;
							}
						    }

						    if(w>0)  { // At least one node fits
							$("#blackboard").append('<div id='+text_+' >'+text_+'</div>');
							//console.log(text_);
							$("#"+text_).css({ // GLOBALCSS
								width : width_/colorFilterStickersTab.length, 
								    height : 100, 
								    fontSize : 100, 
								    border : 25, 
								    backgroundColor : colorFilterStickersTab[numOfFilter]
								    });
							numOfFilter++;
						    } else {
							$("#blackboard").append('<div id=internal_warning class="legend-warning">Filter not found on those tiles</div>');
						    }

						    var filtered = w;	
						    while(w<nodesByLoc.length)  { 											
							nodesByLoc[w].getHtmlNode().css({
								opacity : 0.5
								    });
							w++;
						    }

						    appliedFilters.push(text_);
						    $('.stickers_zone').css("visibility", "visible");

						    // To zoom on filtered nodes
						    // Disabled by Yacouba because there were too many filtered nodes through some queries
						    // TO DO : find an upper bound to zoom on the nodes if there are not so many nodes
						    // if(filtered<4) // more complex, should take into account how many nodes are filtered
						    // with each filter
						    /* $("#"+text_).on('dblclick',function(){			

						       me.magnifyingGlass(nodeZoomTab,ratio,initSpread);		

						       }); */

						} else { 

						}											
					    }

					    // Load the nodes provided by the search which are outside the screen and not yet loaded 
					    // depends on "chargeAllContentOnStart" and "distance_from_the_bottom_for_loading")
					    if(chargeAllContentOnStart==false)  { 
						me.computeNumColumns();
						for(O in nodesById ){
						    node = nodesById[O];
						    if( node.getLoadedStatus() == false && mesh.locationProvider(node.getIdLocation()).getY()<window.innerHeight  )  { 
							//console.log(node.getmLocation().getnX());
							ratio=mesh.loadContent(node.getId());
							node.setLoadedStatus(true);
						    }
						}
					    }
					}
				    }


				});
			});
		$("#search").off("focusout").on({
			    focusout : function(){

			    $("#search").off('keydown');									

			}
		    });


		$( "#filter" ).autocomplete({

			source: suggestion_list

			    });	

		$('#brush').off("click").on({		

			click : function()  { 
			    var buffer=0;

			    while(appliedFilters.length>0)  { 
				buffer=appliedFilters.pop();

				// for(O in nodesById)  { 
				//     nodesById[O].removeElementFromNodeTagList(buffer);
				// }

				numOfFilter--;
			    }

			    $('#blackboard').children().remove();
					    
			    for (O in nodesByLoc)
				if (nodesByLoc[O].getNodeInViewportStatus()) {
				    nodesByLoc[O].sub('stickers_').css("visibility", "hidden");
				    nodesByLoc[O].sub('').css({
					opacity : 1
				    });
				}
			}

		    });	
		// Replace icons		    
		$('#'+id+'option'+optionNumber).attr('class',$('#'+id+'option'+optionNumber).attr('class').replace('searchButtonIcon','closeSearchButtonIcon'));		
	    } else { 	
		$("#brush").click();
		$('#blackboard').remove();
		$("#filter").remove();
		$("filter").remove();
		$("#search").remove();
		$("#brush").remove();
		$('#'+id+'option'+optionNumber).attr('class',$('#'+id+'option'+optionNumber).attr('class').replace('closeSearchButtonIcon','searchButtonIcon'));	

	    }		
	});	

    menuIconClassAttributesTab.push("searchButtonIcon");
    menuShareEvent.push(false)

    // /** Share selection to other participants in session. */
    // menuTitleTab.push("Share selection")
    // menuEventTab.push(    function(v,id,optionNumber){
	
    // 	$('#'+id+'option'+optionNumber).removeClass('selectionButtonIcon').addClass('closeSelectionButtonIcon');
    // 	var listSelectionIds = [];
    // 	var listSelectionTiles=me.getSelectedNodes()
    // 	for(O in listSelectionTiles)  { 
    // 	    listSelectionIds.push(listSelectionTiles[O].getId());
    // 	}
    //  	console.log("share_Selection",listSelectionIds);
    // 	var cdata ={"room":my_session, "Selection": "["+listSelectionIds.toString()+"]" }
    // 	socket.emit("share_Selection", cdata);

    // 	$('#'+id+'option'+optionNumber).removeClass('closeSelectionButtonIcon').addClass('selectionButtonIcon');
    // });
    // menuIconClassAttributesTab.push("selectionButtonIcon");
    // menuShareEvent.push(false);
    
    /** Clear selection to all participants in session. */
    menuTitleTab.push("Clear selection")
    menuEventTab.push(    function(v,id,optionNumber){
	
	$('#'+id+'option'+optionNumber).removeClass('clearSelectionButtonIcon').addClass('closeClearSelectionButtonIcon');
	for(O in nodesById)  { 
	    nodesById[O].updateSelectedStatus(false);
	}
	me.setZoomSelection(false);
	me.resetNodesToZoom();
	$('#'+id+'option'+optionNumber).removeClass('closeClearSelectionButtonIcon').addClass('clearSelectionButtonIcon');
	addBlink($('#'+id+'option'+optionNumber));
    });
    menuIconClassAttributesTab.push("clearSelectionButtonIcon");
    menuShareEvent.push(true);

    /** Show next tiles. */
    var nextList=[];
    var IntervalClearSelection=100;
    var IntervalCloseTagMenu=100;
    var IntervalCloseTagButton=100;
    var IntervalSelectOffStickers=100;
    var IntervalShareSelection=100;
    var IntervalAddNextTag=300;
    var IntervalCloseSelectTag=100;
    var IntervalSelectionToTag=100;
    var IntervalApplyToTag=200;
    var IntervalcheckCloseSelectTag=100;
    var IntervalCloseSelect=100;
    var IntervalAlignTag=100;
    var IntervalCloseAll=300;

    menuTitleTab.push("Show next tiles.")
    menuEventTab.push(    function(v,id,optionNumber){
	
	$('#'+id+'option' + optionNumber).removeClass('nextTilesButtonIcon').addClass('closeNextTilesButtonIcon');

	if ($('#'+globalTagsList[0]).position() == undefined)
	    $('.tagsGlobalMenuButtonIcon').click()

	me.setSelectTags(true);
	$('.clearSelectionButtonIcon').click();

	if (nextList.length == 0) {
	    var numberOff=$('.Off').length;
	    var numberOn=$('.On').length;
	    // Select next "Off" tiles with max number "On" or "Off" if it is lower
	    var numberToView=Math.min(numberOn,numberOff)
	}
	    
	// All functions for this page salection
	// to AddOnTagsPage
	funApplyNewTag_CloseMenuButtonIcon=function(newtag) {
	    var checkApplyNewTag = setInterval(function() {
		if ( $('.'+newtag).length > 0 ) {
		    clearInterval(checkApplyNewTag);
		    $('.closeSelectTagMenuButtonIcon').click();
		}
	    }, IntervalApplyToTag)
	}

	funEndselectionToTag_taglegendclick=function(newtag) {
	    var checkEndselectionToTag = setInterval(function() {
		if ( $('.closeSelectionToTagButtonIcon').length) {
		    clearInterval(checkEndselectionToTag);
		    $('#tag-legend>#'+newtag).click();
		    funApplyNewTag_CloseMenuButtonIcon(newtag);
		}
	    }, IntervalSelectionToTag)
	}

	funEndaddPageTag_selectionToTagButtonIcon = function(newtag) {
	    var checkEndaddPageTag = setInterval(function() {
		if (receive_Add_Tag) {
		    clearInterval(checkEndaddPageTag);
		    addBlink($('.selectionToTagButtonIcon'));
		    $('.selectionToTagButtonIcon').click()
		    funEndselectionToTag_taglegendclick(newtag);
		}
	    }, IntervalAddNextTag)
	}

	funCloseSelectTag_emitnewTag = function(page) {
	    var checkCloseSelectTag = setInterval(function() {
		if ($('.selectTagButtonIcon').length) {
		    clearInterval(checkCloseSelectTag);
		    var newtag="Page"+page;
 		    console.log("New On page ", newtag);
		    emit_newTag(id+'option'+optionNumber,newtag);
		    
		    funEndaddPageTag_selectionToTagButtonIcon(newtag)
		}
	    }, IntervalCloseSelectTag)
	}

	funEndshareSelectionOn_closeSelectTag = function(page) {
	    var checkEndshareSelectionOn = setInterval(function() {
		if (receive_deploy_Selection) {
		    clearInterval(checkEndshareSelectionOn);
		    
		    addBlink($('.closeSelectTagButtonIcon'));
		    $('.closeSelectTagButtonIcon').click();
		    
		    funCloseSelectTag_emitnewTag(page);
		}
	    }, IntervalShareSelection)
	}

	funEndselectOnStickers_listSelectionIds = function(page) {
	    var checkEndselectOnStickers= setInterval(function() {
		if ( me.getSelectedNodes().length > 0) {
		    clearInterval(checkEndselectOnStickers);
		    
		    var selectedNodes=me.getSelectedNodes().filter(node=>{if (node.getNodeTagList().indexOf("On") > -1) return node});
		    
		    addBlink($('.closeSelectTagButtonIcon'))
		    me.setSelectTags(false);
		    
    		    var listSelectionIds = [];
    		    var listSelectionTiles=me.getSelectedNodes();
    		    for(O in listSelectionTiles)  { 
    			listSelectionIds.push(listSelectionTiles[O].getId());
    		    }
     		    //console.log("share_Selection",listSelectionIds);
		    receive_deploy_Selection=false;
    		    var cdata ={"room":my_session, "Selection": "["+listSelectionIds.toString()+"]" }
    		    socket.emit("share_Selection", cdata);
		    
		    funEndshareSelectionOn_closeSelectTag(page);
		}
	    }, IntervalSelectOffStickers)
	}
	
	funselectTagButton_taglegendOn = function(page) {
	    var checkselectTagButton = setInterval(function() {
		if ($('.closeSelectTagButtonIcon').length) {
		    clearInterval(checkselectTagButton);
		    
		    $('#tag-legend>#On').click();
		    addBlink($('#tag-legend>#On'));
     		    console.log("Selection On");
		    
		    funEndselectOnStickers_listSelectionIds(page);
		}
	    }, IntervalCloseTagButton)
	}

	funselectTagMenu_selectTagButtonIcon = function(page) {
	    var checkselectTagMenu = setInterval(function() {
		if ($('.closeSelectTagMenuButtonIcon').length) {
		    clearInterval(checkselectTagMenu);
		    if ($('.closeSelectTagButtonIcon').length == 0)
			$('.selectTagButtonIcon').click();
			    
		    funselectTagButton_taglegendOn(page);
		}
	    }, IntervalCloseTagMenu)
	}

	funAddOnTagsPage = function(page) {
	    var checkEndcloseTagsGlobalMenu=setInterval(function() {
		if ($('.closeTagsGlobalMenuButtonIcon').length ) {
		    clearInterval(checkEndcloseTagsGlobalMenu);
		    
		    if ($('.closeSelectTagMenuButtonIcon').length == 0)
			$('.selectTagMenuButtonIcon').click();
		    $('.clearSelectionButtonIcon').click()
		    addBlink($('.clearSelectionButtonIcon'));

		    funselectTagMenu_selectTagButtonIcon(page);
		}
	    }, IntervalClearSelection)
	}
	
	//funAddOnTagsPage(nextList.length);

	//
	// All functions for Next page iteration
	//
	funCloseAll = function() {
	    var checkCloseAll = setInterval(function() {
		if ( EndOfGroupping) {
		    clearInterval(checkCloseAll);
		    // HowTo/NeedTo Wait for click on new tag here ?
		    $('.closeAlignTagButtonIcon').click();
		    $('.clearSelectionButtonIcon').click();	
		}
	    }, IntervalCloseAll)	    
	}
	
	funEndalignTag = function(newtag) {
	    var checkEndalignTag = setInterval(function() {
		if ( $('.closeAlignTagButtonIcon').length ) {
		    clearInterval(checkEndalignTag);
		    EndOfGroupping=false;
		    $('#tag-legend>#'+newtag).click();
		    
		    funCloseAll();
		    $('#'+id+'option'+optionNumber).removeClass('closeNextTilesButtonIcon').addClass('nextTilesButtonIcon');
		    
		}
	    }, IntervalAlignTag)
	}

	funCloseSelect = function(newtag) {
	    var checkCloseSelect = setInterval(function() {
		if ( $('.selectTagMenuButtonIcon').length ) {
		    clearInterval(checkCloseSelect);
		    $('.alignTagButtonIcon').click();
		    addBlink($('.alignTagButtonIcon'));
		    
		    funEndalignTag(newtag);
		}
	    }, IntervalCloseSelect)
	}

	//,funnext
	funApplyNewTag = function(newtag) {
	    var checkApplyNewTag = setInterval(function() {
		if ( $('.'+newtag).length > 0 ) {
		    clearInterval(checkApplyNewTag);
		    $('.closeSelectTagMenuButtonIcon').click();
		    
		    funCloseSelect(newtag);
		}
	    }, IntervalApplyToTag)
	}

	funEndselectionToTag = function(newtag) {
	    var checkEndselectionToTag = setInterval(function() {
		if ( $('.closeSelectionToTagButtonIcon').length) {
		    clearInterval(checkEndselectionToTag);
		    $('#tag-legend>#'+newtag).click();
		    
		    funApplyNewTag(newtag);
		}
	    }, IntervalSelectionToTag)
	}

	funEndaddNextTag = function(newtag) {
	    var checkEndaddNextTag = setInterval(function() {
		if (receive_Add_Tag) {
		    clearInterval(checkEndaddNextTag);
		    addBlink($('.selectionToTagButtonIcon'));
		    $('.selectionToTagButtonIcon').click()
		    
		    funEndselectionToTag(newtag);
		}
	    }, IntervalAddNextTag)
	}

	funCloseSelectTag = function(newtag) {
	    var checkCloseSelectTag = setInterval(function() {
		if ($('.selectTagButtonIcon').length) {
		    clearInterval(checkCloseSelectTag);
		    var newtag="Next"+nextList.length;
		    nextList.push(newtag);
 		    console.log("Next add New Tag ", newtag);
		    emit_newTag(id+'option'+optionNumber,newtag);
		    
		    funEndaddNextTag(newtag)
		}
	    }, IntervalCloseSelectTag)
	}

	funEndshareSelectionOff = function() {
	    var checkEndshareSelectionOff = setInterval(function() {
		if (receive_deploy_Selection) {
		    clearInterval(checkEndshareSelectionOff);
		    
		    addBlink($('.closeSelectTagButtonIcon'));
		    $('.closeSelectTagButtonIcon').click();
		    
		    funCloseSelectTag();
		}
	    }, IntervalShareSelection)
	}

	funEndselectOffStickers = function() {
	    var checkEndselectOffStickers = setInterval(function() {
		if ( me.getSelectedNodes().length > 0) {
		    clearInterval(checkEndselectOffStickers);
		    
		    // Correction from previous Next selection and still Off tiles.
		    //var selectedNodes= me.getSelectedNodes();
		    //for (O in selectedNodes) { var node=selectedNodes[O]; console.log(node.getNodeTagList()) }
		    //var selectedNodes= me.getSelectedNodes(); selectedNodes.filter(node=>{ console.log("Off" in node.getNodeTagList()); if ("Off" in node.getNodeTagList()) node })
		    var selectedNodes=me.getSelectedNodes().filter(node=>{if (node.getNodeTagList().indexOf("Off") > -1) return node});
		    //.slice(0,numberToView);
		    
		    addBlink($('.selectTagButtonIcon'))
		    me.setSelectTags(false);
		    
    		    var listSelectionIds = [];
    		    var listSelectionTiles=me.getSelectedNodes();
    		    for(O in listSelectionTiles)  { 
    			listSelectionIds.push(listSelectionTiles[O].getId());
    		    }
     		    //console.log("share_Selection",listSelectionIds);
		    receive_deploy_Selection=false;
    		    var cdata ={"room":my_session, "Selection": "["+listSelectionIds.toString()+"]" }
    		    socket.emit("share_Selection", cdata);
		    
		    
		    funEndshareSelectionOff();
		}
	    }, IntervalSelectOffStickers)
	}

	funselectTagButton = function() {
	    var checkselectTagButton = setInterval(function() {
		if ($('.closeSelectTagButtonIcon').length) {
		    clearInterval(checkselectTagButton);
		    
		    if (nextList.length < 1) {
			//funAddOnTagsPage(0);
			$('#tag-legend>#Off').click();
			addBlink($('#tag-legend>#Off'));
     			console.log("Selection Off");
		    } else {
			//funAddOnTagsPage(nextList.length);
			var oldtag="Next"+(nextList.length-1);
			// sans les On ! ou intersection oldtag et Off actuel
			$('#tag-legend>#'+oldtag).click();
			addBlink($('#tag-legend>#'+oldtag));
     			console.log("Selection "+oldtag);
		    }
		    
		    funEndselectOffStickers();
		}
	    }, IntervalCloseTagButton)
	}
	
	funselectTagMenu = function() {
	    var checkselectTagMenu = setInterval(function() {
		if ($('.closeSelectTagMenuButtonIcon').length) {
		    clearInterval(checkselectTagMenu);
		    if ($('.closeSelectTagButtonIcon').length == 0)
			$('.selectTagButtonIcon').click();
		    
		    funselectTagButton();
		}
	    }, IntervalCloseTagMenu)
	}

	funEndcloseTagsGlobalMenu = function() {
	    var checkEndcloseTagsGlobalMenu = setInterval(function() {
		if ($('.closeTagsGlobalMenuButtonIcon').length ) {
		    clearInterval(checkEndcloseTagsGlobalMenu);
		    
		    // We can't click on SelectTagMenu and .tagsMenuSelectButton
		    // because nodes tagged off are not identically distributed to all clients.
		    // Then we use here internal function setSelectTags and share_Selection after.
		    if ($('.closeSelectTagMenuButtonIcon').length == 0)
			$('.selectTagMenuButtonIcon').click();
		    $('.clearSelectionButtonIcon').click()
		    addBlink($('.clearSelectionButtonIcon'));
		    
		    //funAddOnTagsPage(nextList.length)

		    //funnext.pop()()
		    funselectTagMenu();
		}
	    }, IntervalClearSelection)
	}

	// List of call functions for show Next tiles 
	funnext=new Array(funEndalignTag,funCloseSelect);	

	// Run first node for show Next tiles 
	funEndcloseTagsGlobalMenu();
    });
    menuIconClassAttributesTab.push("nextTilesButtonIcon");
    menuShareEvent.push(false);

    /** Show rotate button on each node */
    menuTitleTab.push("Show rotate button")
    menuEventTab.push( (    function(){

    	    return function(v, id, optionNumber){
    		if (v==true)  { 
    		    $('.rotate').show();
    		    $('#'+id+'option'+optionNumber).removeClass('RotateButtonIcon').addClass('closeRotateButtonIcon');
    		} else { 
    		    $('.rotate').hide();
    		    $('#'+id+'option'+optionNumber).removeClass("closeRotateButtonIcon").addClass("RotateButtonIcon");

    		}
    	    };

    	})());

    menuIconClassAttributesTab.push("RotateButtonIcon");
    menuShareEvent.push(false);
    
    
    /** Refresh button: 
	designed to reset nodes when something goes wrong 
	(reload their content, remove draggable classes).
    **/
	
    // Refresh all nodes
    menuTitleTab.push("Refresh all nodes")
    menuEventTab.push(    function (v){
	    if (v==true)  { 
		refreshNodes();
	    } else { 
		refreshNodes();
	    }
	});

    menuIconClassAttributesTab.push("refreshButtonIcon");
    menuShareEvent.push(true);
    
    /** Tags: opens tag menu and let the user manipulate tags
     */
    // Tag menu
    menuTitleTab.push("Tag menu")
    menuEventTab.push(    function(v, id, optionNumber){
	    if (v == true)  { 
		for (O in nodesByLoc)  { 
		    if (nodesByLoc[O].getNodeInViewportStatus()) { 
			nodesByLoc[O].sub('hitbox').off("click"); 
			if (!!configBehaviour.moveOnMenuOption)  { 
			    nodesByLoc[O].sub('').off(); 
			}
			nodesByLoc[O].sub('hitbox').on("click", clickHBTag);
		    }
		}
		menuTags.css("visibility", "visible");
		// Legend :
		var left_ = Math.max(parseInt($(me.menu.getHtmlMenuSelector()).css("width")), 
				     //parseInt($(me.menu.getHtmlMenuSelector()).css("width")) + 
				     parseInt($(me.tagMenu.getHtmlMenuSelector()).css("width"))); // To adapt with the menu in the corner
		try {
		    var width_= parseInt($('#home').position().left)-250 -left_;
		} catch(err) {
		    var width_= parseInt($('header').css('width')) - left_ -600 /*- parseInt($('body').prop("scrollwidth"))*/; // 600 is for the three buttons on the right
		}

		var tmp = document.getElementById("tag-legend");
		if (tmp == null)  { 
		    // Init tag-legend
		    menuTags.append('<div id=tag-legend class=legend scrollable="yes"></div>');

		    $('#tag-legend').css({//GLOBALCSS
			    position : "relative",
				height : 200,
				width : width_,
				top : 0,
				left : left_,
				display : "flex",
				flexWrap : "wrap",
				zIndex : 149
				});
			// Add notif zone (bottom of the screen?)
		        $('body').append('<div id=tag-notif class=tag-notif></div>');
		        $('#tag-notif').text("click on an icon then a color to use tags.");
		} else { 
		    $('#tag-legend').show();
			$('#tag-notif').show();
		    $('.stickers_zone').css("visibility", "visible");
						
		}

		// Pre-load some tags (depending on configuration)
		if (typeof(computedTagsList) == "undefined")  { 
		    computedTagsList = [];
		}
		if (computedTagsList.length == 0)  { 
		    if (configTagsBehaviour.showAll)  { 
			computedTagsList = globalTagsList.sort();
		    }
		    else if (configTagsBehaviour.selectionMethod =="frequency")  { 
			// Calculations on the dico
			var tagHisto = new Array ();
			var temp = 0;
			for (var k=0;k<globalTagsList.length;k++)  { 	
			    for (var i=0;i<me.getCardinal();i++)  { 
				if(me.hasTag(nodesByLoc[i],globalTagsList[k]))  { 
				    temp +=1;
				}
			    }
			    tagHisto[k]=temp;
			    temp = 0;
			}
			var maxValues = new Array();
			var index = -1;
			for(var k=0;k<Math.min(configTagsBehaviour.numOfTagsToShow, globalTagsList.length);k++)  { 
			    maxValues[k] = $.inArray(Math.max.apply(null, tagHisto), tagHisto);
			    computedTagsList.push(globalTagsList[maxValues[k]]);

			    tagHisto[maxValues[k]] = - (k+1); // To register the used indices
			    if (computedTagsList.length <= colorTagStickersTab.length)  { 
				attributedTagsColorsArray[computedTagsList[computedTagsList.length-1]] = colorTagStickersTab[computedTagsList.length-1];
			    } else if (computedTagsList.length<(colorTagStickersTab.length + colorFilterStickersTab.length-2))  { 
				attributedTagsColorsArray[computedTagsList[computedTagsList.length-1]] = 
				    colorFilterStickersTab[computedTagsList.lengthk-colorTagStickersTab.length];
			    } else { 
				attributedTagsColorsArray[computedTagsList[computedTagsList.length-1]] = 
				    "rgb("+Math.floor(Math.random()*255) + ", " + Math.floor(Math.random()*255)+ ", " + Math.floor(Math.random()*255)+")";
			    }
			    for(O in nodesByLoc)  { 
				if(me.hasTag(nodesByLoc[O], computedTagsList[k]) )  { 
				    var color = attributedTagsColorsArray[computedTagsList[k]];
				    nodesByLoc[O].getStickers().addSticker(computedTagsList[k], false, color);
				}

			    }
			}
		    }
		    else if(configTagsBehaviour.selectionMethod == "alphabet")  { 
			computedTagsList = globalTagsList.slice(0, configTagsBehaviour.numOfTagsToShow);
		    }
					
		    // Build legend
		    if ($('#tag-legend').children(".tag").length<computedTagsList.length)  { 
			// Check length: if a tag is already in the legend, there’s no need in putting it up again (TO DO: refine the test…)
			for(k=0;k<computedTagsList.length;k++)  { 

			    var ck=computedTagsList[k]
			    if (ck=="")  { 
				break;
			    }
			    if ( ck in globalFloatingTags ) {
				var symb=globalFloatingTags[ck]["symb"]
				$('#tag-legend').append('<div id =' + ck + ' class=tag>'+ck +" "+ symb +'</div>');
				ComputedTag=$('#' + ck);
				ComputedTag.css({
				    'background': 'linear-gradient(to right,'+globalFloatingTags[ck]["cm"]+','+globalFloatingTags[ck]["cM"]+')'
				});
			    } else {
				$('#tag-legend').append('<div id =' + ck + ' class=tag>' + ck + '</div>');
				ComputedTag=$('#' + ck);
				ComputedTag.css({
				    backgroundColor : attributedTagsColorsArray[ck]
				});
			    }
			    if ( ComputedTag.position().top+ComputedTag.height() > $("#tag-legend").height() ) {
				$("#tag-legend").css({height: ComputedTag.position().top + ComputedTag.height()+10});
			    }

			}
			for (O in nodesByLoc)
			    if (nodesByLoc[O].getNodeInViewportStatus())
				nodesByLoc[O].sub('stickers_').show();
		    }
		    TagHeight=($("#tag-legend").height());
		    if ( my_user != "Anonymous" ) {
			TopPP=TagHeight;
			htmlPrimaryParent.css("marginTop",TopPP+"px");;
			ppot=TopPP;
		    }

		    // for debugging : add tag with initial grid order
		    if (debugPos) {
			for(O in nodesByLoc)  { 
		    	    me.AddNewTag("pos"+nodesByLoc[O].getId());
		    	    nodesByLoc[O].getStickers().addSticker("pos"+nodesByLoc[O].getId(), attributedTagsColorsArray["pos"+nodesByLoc[O].getId()],false);
		    	    nodesByLoc[O].addElementToNodeTagList("pos"+nodesByLoc[O].getId());
			}
		    }
		    for(O in nodesByLoc)  { 
			nodesByLoc[O].getStickers().updateStickers();
		    }
		}
		$('.stickers_zone').css("visibility", "visible");
			


		$('.tag').off("click").on({
			click : clickTagInLegend
			    });

		$('.sticker').off("click").on({
			click : clickSticker
			    });
			
		$('#'+id+'option'+optionNumber).removeClass('tagsGlobalMenuButtonIcon').addClass('closeTagsGlobalMenuButtonIcon');

	    } else { 	
		me.tagMenu.closeAllOptions();
		menuTags.css("visibility", "hidden");
		$('#tag-notif').hide();
		// for (var i=0; i<tagMenuEventTab.length;i++)  { 
		//     var tmp_class = $('#'+id+'option'+i).attr("class").match(/\w+ButtonIcon/g)[0];
		//     var isNotClosed = tmp_class.match("close"); 
		//     if (isNotClosed)  { 
		// 	var new_class = tmp_class.replace("close", "");
		// 	new_class = new_class[0].toLowerCase() + new_class.slice(1);
		// 	menuTags.children('#'+id+'option'+i).removeClass(tmp_class).addClass(new_class);
		//     }
		// }
		//console.log(menuTags.children());
		$('.stickers_zone').css("visibility", "hidden");
		$('#tag-legend').hide();
		if(currentSelectedTag != "")  { 
		    $('#'+currentSelectedTag).css("outlineStyle", "none");
		}
		currentSelectedTag = "";
		$('#new-tag').remove();
		$('#add-tag').remove();
		//??
		$('new-tag').remove();	
		me.meshEventReStart();

		// If numerous tags, restore initial grid/legend position
		// if (computedTagsList.length>10) {

		//     TopPP=($("#tag-legend").height())
		//     htmlPrimaryParent.css("marginTop",TopPP+"px");
		//     //htmlPrimaryParent.css("margin", "0px 0px 0px 300px");
		// }
		$('#'+id+'option'+optionNumber).removeClass('closeTagsGlobalMenuButtonIcon').addClass('tagsGlobalMenuButtonIcon');

	    }
	});
    menuIconClassAttributesTab.push('tagsGlobalMenuButtonIcon');
    menuShareEvent.push(true)
    
    // Action menu

    menuTitleTab.push("All action functions Menu")
    menuEventTab.push(    function(v, id, optionNumber){
	if(v==true)  { 
	    menuActionGlobal
		.css("top", (function(){
		    return menuGlobal.position()["top"]+$('.actionGlobalMenuButtonIcon').position()["top"];
		})() )
		.css("left",menuGlobal.position()["left"]+menuGlobal.width())
		.css("visibility", "visible");

	    BlockDragAndDrop();
	    
	    for (O in nodesByLoc)
		if (nodesByLoc[O].getNodeInViewportStatus()) {
		    nodesByLoc[O].sub('').off();
		    nodesByLoc[O].sub('hitbox').off("click").on("click", clickHBSelect);
		    nodesByLoc[O].sub('hitbox').off("mouseenter");
		}
	    me.resetNodesToZoom();
	    me.setZoomSelection(true);
	    $('#'+id+'option'+optionNumber).removeClass('actionGlobalMenuButtonIcon').addClass('closeActionGlobalMenuButtonIcon');
	} else { 
	    me.actionGlobalMenu.closeAllOptions();
	    menuActionGlobal.css("visibility", "hidden");
	    me.setZoomSelection(false);
	    for (O in nodesByLoc)
		if (nodesByLoc[O].getNodeInViewportStatus()) 
		    nodesByLoc[O].sub('hitbox').off("click").on("click", clickHB);
	    $('#'+id+'option'+optionNumber).removeClass('closeActionGlobalMenuButtonIcon').addClass('actionGlobalMenuButtonIcon');
	}
    });
    menuIconClassAttributesTab.push("actionGlobalMenuButtonIcon");
    menuShareEvent.push(false);
    
    // Zoom Global Menu
    menuTitleTab.push("All zoom functions Menu")
    menuEventTab.push(    function(v, id, optionNumber){
	if(v==true)  { 
	    menuZoomGlobal
		.css("top", (function(){
		    return menuGlobal.position()["top"]+$('.zoomGlobalMenuButtonIcon').position()["top"];
		})() )
		.css("left",menuGlobal.position()["left"]+menuGlobal.width())
		.css("visibility", "visible");
	    $('#'+id+'option'+optionNumber).removeClass('zoomGlobalMenuButtonIcon').addClass('closeZoomGlobalMenuButtonIcon');
	} else { 
	    me.zoomGlobalMenu.closeAllOptions();
	    menuZoomGlobal.css("visibility", "hidden");
	    $('#'+id+'option'+optionNumber).removeClass('closeZoomGlobalMenuButtonIcon').addClass('zoomGlobalMenuButtonIcon');
	}
    });
    menuIconClassAttributesTab.push("zoomGlobalMenuButtonIcon");
    menuShareEvent.push(false);
    
    // Management menu

    menuTitleTab.push("All management functions Menu")
    menuEventTab.push(    function(v, id, optionNumber){
	if(v==true)  { 
	    menuManagementGlobal
		.css("top",menuGlobal.position()["top"]+menuGlobal.height())
		.css("left",menuGlobal.position()["left"])
		.css("visibility", "visible");
	    $('#'+id+'option'+optionNumber).removeClass('managementGlobalMenuButtonIcon').addClass('closeManagementGlobalMenuButtonIcon');
	} else { 
	    me.managementGlobalMenu.closeAllOptions();
	    menuManagementGlobal.css("visibility", "hidden");
	    $('#'+id+'option'+optionNumber).removeClass('closeManagementGlobalMenuButtonIcon').addClass('managementGlobalMenuButtonIcon');
	}
    });
    menuIconClassAttributesTab.push("managementGlobalMenuButtonIcon");
    menuShareEvent.push(false);
    
    // State of tiles Menu
    menuTitleTab.push("All state of tile functions")
    menuEventTab.push(    function(v, id, optionNumber){
	if(v==true)  { 
	    menuStateGlobal
		.css("top", (function(){
		    return menuGlobal.position()["top"]+$('.stateGlobalMenuButtonIcon').position()["top"];
		})() )
		.css("left",menuGlobal.position()["left"]+menuGlobal.width())
		.css("visibility", "visible");
	    $('#'+id+'option'+optionNumber).removeClass('stateGlobalMenuButtonIcon').addClass('closeStateGlobalMenuButtonIcon');
	} else { 
	    // We want to keep state info on demand.
	    //me.stateGlobalMenu.closeAllOptions();
	    menuStateGlobal.css("visibility", "hidden");
	    $('#'+id+'option'+optionNumber).removeClass('closeStateGlobalMenuButtonIcon').addClass('stateGlobalMenuButtonIcon');
	}
    });
    menuIconClassAttributesTab.push("stateGlobalMenuButtonIcon");
    menuShareEvent.push(false);

    // Display/Hide the node menu
    menuTitleTab.push("Display/Hide the node menu")
    menuEventTab.push(    function(v,id,optionNumber){
        if (executeAtEndComplete) {
	    if(v==true)  { 	
		if (!!configBehaviour.moveOnNodeMenuOption)  { 
		    for (O in nodesByLoc)
			if (nodesByLoc[O].getNodeInViewportStatus()) {
			    nodesByLoc[O].sub('').off();
			    nodesByLoc[O].sub('hitbox').off();
			}
		}

		for (O in nodesByLoc)
		    if (nodesByLoc[O].getNodeInViewportStatus())
			nodesByLoc[O].getHtmlNode().children(".nodemenu").css({visibility : "visible"});

		$('#'+id+'option'+optionNumber).attr('class',$('#'+id+'option'+optionNumber).attr('class').replace('nodeMenuButton','closeNodeMenuButton'));
	    } else { 	
		var nodeId =0;

		for (O in nodesByLoc)
		    if (nodesByLoc[O].getNodeInViewportStatus()) {
			var p =0 ;
			var mymenu=nodesByLoc[O].getNodeMenu();
			for(p=0;p<mymenu.getEventSelectedTab().length;p++)  { 
			    if(mymenu.getEventSelectedTab()[p]==true)  { 
				$("#menu"+mymenu.getId()+">#option"+p).click();
				//console.log("obscure if condition in NodeMenu");
			    }
			}
			$("#menu"+mymenu.getId()).css({visibility : "hidden"});
		    }


		me.meshEventReStart();
		$('#'+id+'option'+optionNumber).attr('class',$('#'+id+'option'+optionNumber).attr('class').replace('closeNodeMenuButton','nodeMenuButton'));
	    }
	}
    });
    menuIconClassAttributesTab.push("nodeMenuButtonIcon");
    menuShareEvent.push(true);

    // Cancel Global Menu
    
    menuTitleTab.push("cancel/redo Menu")
    menuEventTab.push(    function(v, id, optionNumber){
	if(v==true)  { 
	    menuCancelGlobal
		.css("top", (function(){
		    return menuGlobal.position()["top"]+$('.cancelGlobalMenuButtonIcon').position()["top"];
		})() )
		.css("left",menuGlobal.position()["left"]+menuGlobal.width())
		.css("visibility", "visible");
	    $('#'+id+'option'+optionNumber).removeClass('cancelGlobalMenuButtonIcon').addClass('closeCancelGlobalMenuButtonIcon');
	} else { 
	    me.cancelGlobalMenu.closeAllOptions();
	    menuCancelGlobal.css("visibility", "hidden");
	    $('#'+id+'option'+optionNumber).removeClass('closeCancelGlobalMenuButtonIcon').addClass('cancelGlobalMenuButtonIcon');
	}
    });
    menuIconClassAttributesTab.push("cancelGlobalMenuButtonIcon");
    menuShareEvent.push(false);

    // Updown Global Menu
    
    menuTitleTab.push("up/down Menu")
    menuEventTab.push(    function(v, id, optionNumber){
	if(v==true)  { 
	    menuUpdownGlobal
		.css("top", (function(){
		    return menuGlobal.position()["top"]+$('.updownGlobalMenuButtonIcon').position()["top"];
		})() )
		.css("left",menuGlobal.position()["left"]+menuGlobal.width())
		.css("visibility", "visible");
	    $('#'+id+'option'+optionNumber).removeClass('updownGlobalMenuButtonIcon').addClass('closeUpdownGlobalMenuButtonIcon');
	} else { 
	    menuUpdownGlobal.css("visibility", "hidden");
	    $('#'+id+'option'+optionNumber).removeClass('closeUpdownGlobalMenuButtonIcon').addClass('updownGlobalMenuButtonIcon');
	}
    });
    menuIconClassAttributesTab.push("updownGlobalMenuButtonIcon");
    menuShareEvent.push(false);

    /** Here is created a tab menuIconClassAttributesTab related to the parameters menuIconClassAttributesTab_ of the Menu constructor (see below)
	This table contains the name of the class which allows to give some backgroundImage to the various buttons
    */
    
    this.menu = new Menu("Global",$('header'),menuTitleTab,menuEventTab,menuIconClassAttributesTab,menuShareEvent,{
	    position : "fixed",
	    top : $('#notifications').height(),
	    left : 0,
	    visible : "visible",
	    classN : "super",
	    height : 200, //GLOBAL + TO DO : adapt it to the size of the screen
	    width : 200,
	    rightMargin :0,
	    orientation : "V"
	});
    menuGlobal=$('#menuGlobal');

    subMenusGlobal=Array();
    
    this.tagMenu = new Menu("tagsGlobal", $('header'), tagMenuTitleTab, tagMenuEventTab, tagMenuIconClassAttributesTab, tagMenuShareEvent,{
	    position : "fixed",
	    top : 0,
	    left : parseInt($(me.menu.getHtmlMenuSelector()).css('width')), //parseInt(window.innerWidth) - tagMenuEventTab.length*200,
	    visible : 'hidden',
	    classN : 'tag',
	    height : 200,
	    width : 200,
	    rightMargin :0,
	    //borderStyle : "solid",
	    //borderWidth : "5px", 
	    //borderColor : "green",
	    orientation : "H",
	    zIndex : 149

	});
    menuTags=$('#menutagsGlobal');
    subMenusGlobal.push(this.tagMenu);
    
    this.actionGlobalMenu = new Menu("actionGlobal", $('header'), actionGlobalMenuTitleTab, actionGlobalMenuEventTab, actionGlobalMenuIconClassAttributesTab, actionGlobalMenuShareEvent,{
	    position : "fixed",
	    top : parseInt($(me.menu.getHtmlMenuSelector()).css('height')),
	    left : parseInt($(me.menu.getHtmlMenuSelector()).css('width')),
	    visible : 'hidden',
	    classN : 'action',
	    height : 200,
	    width : 200,
	    rightMargin :0,
	    backgroundColor: "rgba(0, 0, 0, 0.6)",
	    //borderStyle : "solid",
	    //borderWidth : "5px", 
	    //borderColor : "green",
	    orientation : "H",
	    zIndex : 149

	});
    menuActionGlobal=$('#menuactionGlobal');
    subMenusGlobal.push(this.actionGlobalMenu);
    
    this.zoomGlobalMenu = new Menu("zoomGlobal", $('header'), zoomGlobalMenuTitleTab, zoomGlobalMenuEventTab, zoomGlobalMenuIconClassAttributesTab, zoomGlobalMenuShareEvent,{
	    position : "fixed",
	    top : parseInt($(me.menu.getHtmlMenuSelector()).css('height')),
	    left : parseInt($(me.menu.getHtmlMenuSelector()).css('width')),
	    visible : 'hidden',
	    classN : 'zoom',
	    height : 200,
	    width : 200,
	    rightMargin :0,
	    backgroundColor: "rgba(0, 0, 0, 0.6)",
	    //borderStyle : "solid",
	    //borderWidth : "5px", 
	    //borderColor : "green",
	    orientation : "H",
	    zIndex : 149

	});
    menuZoomGlobal=$('#menuzoomGlobal');
    subMenusGlobal.push(this.zoomGlobalMenu);
    
    this.managementGlobalMenu = new Menu("managementGlobal", $('header'), managementGlobalMenuTitleTab, managementGlobalMenuEventTab, managementGlobalMenuIconClassAttributesTab, managementGlobalMenuShareEvent,{
	    position : "fixed",
	    top : parseInt($(me.menu.getHtmlMenuSelector()).css('height')),
	    left : parseInt($(me.menu.getHtmlMenuSelector()).css('left')),
	    visible : 'hidden',
	    classN : 'manage',
	    height : 200,
	    width : 200,
	    rightMargin :0,
	    backgroundColor: "rgba(0, 0, 0, 0.6)",
	    //borderStyle : "solid",
	    //borderWidth : "5px", 
	    //borderColor : "green",
	    orientation : "V",
	    zIndex : 149

	});
    menuManagementGlobal=$('#menumanagementGlobal');
    subMenusGlobal.push(this.managementGlobalMenu);
    
    this.stateGlobalMenu = new Menu("stateGlobal", $('header'), stateGlobalMenuTitleTab, stateGlobalMenuEventTab, stateGlobalMenuIconClassAttributesTab, stateGlobalMenuShareEvent,{
	    position : "fixed",
	    top : parseInt($(me.menu.getHtmlMenuSelector()).css('height')),
	    left : parseInt($(me.menu.getHtmlMenuSelector()).css('width')),
	    visible : 'hidden',
	    classN : 'state',
	    height : 200,
	    width : 200,
	    rightMargin :0,
	    backgroundColor: "rgba(0, 0, 0, 0.6)",
	    //borderStyle : "solid",
	    //borderWidth : "5px", 
	    //borderColor : "green",
	    orientation : "H",
	    zIndex : 149

	});
    menuStateGlobal=$('#menustateGlobal');
    subMenusGlobal.push(this.stateGlobalMenu);
    
    this.cancelGlobalMenu = new Menu("cancelGlobal", $('header'), cancelGlobalMenuTitleTab, cancelGlobalMenuEventTab, cancelGlobalMenuIconClassAttributesTab, cancelGlobalMenuShareEvent,{
	    position : "fixed",
	    top : parseInt($(me.menu.getHtmlMenuSelector()).css('height')),
	    left : parseInt($(me.menu.getHtmlMenuSelector()).css('width')),
	    visible : 'hidden',
	    classN : 'cancel',
	    height : 200,
	    width : 200,
	    rightMargin :0,
	    backgroundColor: "rgba(0, 0, 0, 0.6)",
	    //borderStyle : "solid",
	    //borderWidth : "5px", 
	    //borderColor : "green",
	    orientation : "H",
	    zIndex : 149

	});
    menuCancelGlobal=$('#menucancelGlobal');
    subMenusGlobal.push(this.cancelGlobalMenu);
    
    this.updownGlobalMenu = new Menu("updownGlobal", $('header'), updownGlobalMenuTitleTab, updownGlobalMenuEventTab, updownGlobalMenuIconClassAttributesTab, updownGlobalMenuShareEvent,{
	    position : "fixed",
	    top : parseInt($(me.menu.getHtmlMenuSelector()).css('height')),
	    left : parseInt($(me.menu.getHtmlMenuSelector()).css('width')),
	    visible : 'hidden',
	    classN : 'updown',
	    height : 200,
	    width : 200,
	    rightMargin :0,
	    backgroundColor: "rgba(0, 0, 0, 0.6)",
	    //borderStyle : "solid",
	    //borderWidth : "5px", 
	    //borderColor : "green",
	    orientation : "H",
	    zIndex : 149

	});
    menuUpdownGlobal=$('#menuupdownGlobal');
    subMenusGlobal.push(this.updownGlobalMenu);

    var menutagsGlobaljs=document.getElementById("menutagsGlobal");
    this.drawMenu = new Menu("Draw", $('header'), drawMenuTitleTab, drawMenuEventTab, drawMenuIconClassAttributesTab, drawMenuShareEvent,{
	    position : "fixed",
	    top : 0,
 	    left : menutagsGlobaljs.offsetLeft+$('#menutagsGlobal').width(),
	    visible : 'hidden',
	    classN : 'draw',
	    height : 200,
	    width : 200,
	    rightMargin :0,
	    //borderStyle : "solid",
	    //borderWidth : "5px", 
	    //borderColor : "green",
	    orientation : "H",
	    zIndex : 801

	});
    menuDraw=$('#menuDraw');
    
    this.zoomMenu = new Menu("Zoom", $('header'), zoomMenuTitleTab, zoomMenuEventTab, zoomMenuIconClassAttributesTab, zoomMenuShareEvent, {
	    position : "fixed",
	    top : 0,
	    left : menutagsGlobaljs.offsetLeft+$('#menutagsGlobal').width(),
	    visible : 'hidden',
	    classN : 'zoomAction',
	    height : 200,
	    width : 200,
	    rightMargin :0,
	    //borderStyle : "solid",
	    //borderWidth : "5px", 
	    //borderColor : "green",
	    orientation : "H",
	    zIndex : 801

	});
    menuZoom=$('#menuZoom');
    
    this.MSMenu = new Menu("MS", $('header'), MSMenuTitleTab, MSMenuEventTab, MSMenuIconClassAttributesTab, MSMenuShareEvent, {
	    position : "fixed",
	    top : 0,
	    left : menutagsGlobaljs.offsetLeft+$('#menutagsGlobal').width(),
	    visible : 'hidden',
	    classN : 'masterslave',
	    height : 200,
	    width : 200,
	    rightMargin :0,
	    //borderStyle : "solid",
	    //borderWidth : "5px", 
	    //borderColor : "green",
	    orientation : "H",
	    zIndex : 801

	});
    menuMS=$('#menuMS');	

    this.tagAlignOrderTagsMenu = new Menu("AlignOrderTags", $('header'), tagAlignOrderTagsMenuTitleTab, tagAlignOrderTagsMenuEventTab, tagAlignOrderTagsMenuIconClassAttributesTab, tagAlignOrderTagsMenuShareEvent,{
	    position : "fixed",
	    top : 100,
	    left : parseInt($(me.menu.getHtmlMenuSelector()).css('width')), //parseInt(window.innerWidth) - tagMenuEventTab.length*200,
	    visible : 'hidden',
	    classN : 'tagalignOrdertags',
	    height : 200,
	    width : 200,
	    rightMargin :0,
	    backgroundColor: "rgba(0, 0, 0, 0.5)",
	    //borderStyle : "solid",
	    //borderWidth : "5px", 
	    //borderColor : "green",
	    orientation : "V",
	    zIndex : 150

	});
    menuAlignOrderTags=$('#menuAlignOrderTags');

    this.tagHideTagsMenu = new Menu("HideTags", $('header'), tagHideTagsMenuTitleTab, tagHideTagsMenuEventTab, tagHideTagsMenuIconClassAttributesTab, tagHideTagsMenuShareEvent,{
	    position : "fixed",
	    top : 100,
	    left : parseInt($(me.menu.getHtmlMenuSelector()).css('width')), //parseInt(window.innerWidth) - tagMenuEventTab.length*200,
	    visible : 'hidden',
	    classN : 'taghidetags',
	    height : 200,
	    width : 200,
	    rightMargin :0,
	    backgroundColor: "rgba(0, 0, 0, 0.5)",
	    //borderStyle : "solid",
	    //borderWidth : "5px", 
	    //borderColor : "green",
	    orientation : "V",
	    zIndex : 150

	});
    menuHideTags=$('#menuHideTags');

    this.tagSelectionMenu = new Menu("SelectionTags", $('header'), tagSelectionMenuTitleTab, tagSelectionMenuEventTab, tagSelectionMenuIconClassAttributesTab, tagSelectionMenuShareEvent,{
	    position : "fixed",
	    top : 100,
	    left : parseInt($(me.menu.getHtmlMenuSelector()).css('width')), //parseInt(window.innerWidth) - tagMenuEventTab.length*200,
	    visible : 'hidden',
	    classN : 'tagselect',
	    height : 200,
	    width : 200,
	    rightMargin :0,
	    backgroundColor: "rgba(0, 0, 0, 0.5)",
	    //borderStyle : "solid",
	    //borderWidth : "5px", 
	    //borderColor : "green",
	    orientation : "V",
	    zIndex : 150

	});
    menuSelectionTags=$('#menuSelectionTags');

    this.tagManagementMenu = new Menu("ManagementTags", $('header'), tagManagementMenuTitleTab, tagManagementMenuEventTab, tagManagementMenuIconClassAttributesTab, tagManagementMenuShareEvent,{
	    position : "fixed",
	    top : 100,
	    left : parseInt($(me.menu.getHtmlMenuSelector()).css('width')), //parseInt(window.innerWidth) - tagMenuEventTab.length*200,
	    visible : 'hidden',
	    classN : 'tagmanage',
	    height : 200,
	    width : 200,
	    rightMargin :0,
	    backgroundColor: "rgba(0, 0, 0, 0.5)",
	    //borderStyle : "solid",
	    //borderWidth : "5px", 
	    //borderColor : "green",
	    orientation : "V",
	    zIndex : 150

	});
    menuManagementTags=$('#menuManagementTags');
    
    //******select column and line******//	

    //--getter 
    this.getcolumnSelected = function(){
	return columnSelected;
    };

    /**give table nodes*/	

    //--getter
    this.getlineSelected = function(){	
	return lineSelected;
    };

    //--setter 
    this.setcolumnSelected = function(number){
	columnSelected = number;
    };

    /**give table nodes*/	

    //--setter
    this.setlineSelected = function(number){	
	lineSelected = number ;
    };	

    //******columns******//

    /**give a node of a certain id*/

    //--getter 
    this.getNumOfColumns = function(){
	return numOfColumns;
    };

    /**give table nodes*/	

    //--setter
    this.setNodes = function(){	
	return nodesById;
    };

    //******heighttable and widthtable******//

    //--getter 
    this.getHeightTab = function(){
	return heightTab;
    };

    //--getter
    this.getWidthTab = function(){	
	return widthTab;
    };


    //--setter 
    this.setHeightTab = function(index,value){
	heightTab[index]=value;
    };

    //--setter
    this.setWidthTab = function(index,value){	
	widthTab[index]=value;
    };


    //--update, apply to all elements the changement of spread
    this.updateSpread = (    function(){
	    var initialSpread=spread;
	    var scale =1;
	    //console.log(initialSpread, newSpread);
	    return function(newSpread,id){

			
		var scaleX=(newSpread.X/ initialSpread.X);
		var scaleY=(newSpread.Y/ initialSpread.Y);
		scale = (scaleX + scaleY)/2;
		//console.log("scale", scaleX, scaleY, scale);
		if(typeof id == 'undefined' || typeof id != 'number' || (id < 0) || !(id < nodeCardinal))  { 
		    spread=newSpread;
		    for(O in nodesById)  { 
			nodesById[O].updateHW(spread.Y,spread.X);

		    }
		    $('.selection').css({height : spread.Y,  width : spread.X});
		    $('iframe').height(spread.Y).width(spread.X);
		    // $('iframe').css( '-webkit-transform', "scale("+scaleX+","+ scaleY +")");
		    // $('iframe').css( '-moz-transform', "scale("+scaleX+","+ scaleY +")");
		    // OnOff with just spread.Y ?
		    $('.onoff').css("height",parseInt(spread.Y*0.1)).css("width",parseInt(spread.Y*0.1)).css("left",-parseInt(spread.Y*0.1)).css("z-index", 161);
		    $('.hitbox').css("height", parseInt(spread.Y*0.9)).css("top",parseInt(spread.Y*0.1));
		    $('.info').css("font-size", Math.min(configBehaviour.maxInfoFontSize,parseInt(configBehaviour.defaultInfoFontSize*scale)));

		    for(O in nodesById)  { 	
			if(ColumnStyle=="static") // Why are the two parts of this condition the same?!

			    {
				//var marginleft = (parseInt($('#'+nodesById[O].getId()).css("width"))-widthTab[nodesById[O].getId()]*scale)/2;
				var node=nodesById[O];
				me.setLocation(node,node.getIdLocation(),false).done(updateNode(node));
				//var margintop = (parseInt($('#'+nodesById[O].getId()).css("height"))-heightTab[nodesById[O].getId()]*scale)/2;

				$('#iframe'+nodesById[O].getId()).css({marginTop : 0 , marginLeft : 0   });				
			    }
			else // "dynamic" ColumnStyle
			    {
				//var marginleft = (parseInt($('#'+nodesById[O].getId()).css("width"))-widthTab[nodesById[O].getId()]*scale)/2;
				var node=nodesById[O];
				me.setLocation(node,node.getIdLocation(),false).done(updateNode(node));
				//var margintop = (parseInt($('#'+nodesById[O].getId()).css("height"))-heightTab[nodesById[O].getId()]*scale)/2;
				$('#iframe'+nodesById[O].getId()).css({marginTop : 0,marginLeft : 0 });	
			    }


		    }
		    $('.stickers_zone').css("left", spread.X);
		    //console.log($('.info').css("font-size"));
		    configBehaviour.defaultInfoFontSize = $('.info').css("font-size");
		    //console.log(configBehaviour.defaultInfoFontSize);

		} else { 
		    spread=newSpread;

		    nodesById["node"+id].updateHW(spread.Y,spread.X);

		    // ?? Global functions for update spread for one tile ?? 
		    $('.selection').css({height : spread.Y,  width : spread.X});
		    $('iframe').height(spread.Y).width(spread.X);
		    //$('iframe').css( '-webkit-transform', "scale("+scaleX+","+ scaleY +")");
		    //$('iframe').css( '-moz-transform', "scale("+scaleX+","+ scaleY +")");
		    $('.onoff').css("height",parseInt(spread.Y*0.1)).css("width",parseInt(spread.Y*0.1)).css("left",-parseInt(spread.Y*0.1));
		    $('.hitbox').css("height", parseInt(spread.Y*0.9)).css("top",parseInt(spread.Y*0.1));
		    //console.log(parseInt($('.info').css("font-size")));
		    $('.info').css("font-size", Math.min(configBehaviour.maxInfoFontSize,parseInt(configBehaviour.defaultInfoFontSize*scale)));
		    //console.log(parseInt($('.info').css("font-size")));

		    if(ColumnStyle=="static")  { 
			var marginleft = (parseInt($('#'+nodesById["node"+id].getId()).css("width"))-widthTab[nodesById["node"+id].getId()]*scale)/2;
			var node=nodesById["node"+id];
			me.setLocation(node,node.getIdLocation(),false).done(updateNode(node));
			var margintop = (parseInt($('#'+nodesById["node"+id].getId()).css("height"))-heightTab[nodesById["node"+id].getId()]*scale)/2;

			$('#iframe'+nodesById["node"+id].getId()).css({marginTop : 0 , smarginLeft : 0   });

		    } else { 
			var marginleft = (parseInt($('#'+nodesById["node"+id].getId()).css("width"))-widthTab[nodesById["node"+id].getId()]*scale)/2;
			var node=nodesById["node"+id];
			me.setLocation(node,node.getIdLocation(),false).done(updateNode(node));
			var margintop = (parseInt($('#'+nodesById["node"+id].getId()).css("height"))-heightTab[nodesById["node"+id].getId()]*scale)/2;
			$('#iframe'+nodesById["node"+id].getId()).css({marginTop : margintop,marginLeft : marginleft   });	
		    }	
		    $('.stickers_zone').css("left", spread.X);
		    //console.log($('.info').css("font-size"));
		    configBehaviour.defaultInfoFontSize = $('.info').css("font-size");
		    //console.log(configBehaviour.defaultInfoFontSize);
		} 
	    };


	})();

    this.getSpread = function(){
	return spread;
    };

    //******cardinal******//

    //--getter	
    this.getCardinal = function(){	
	return nodeCardinal;
    };

    //--setter	
    this.setCardinal = function(n){	
	nodeCardinal = n;
    };


    //******nodes******//

    /**give a node of a certain id*/

    //--getter 
    this.getNode = function(id){
	return nodesById["node"+id];
    };

    /**give table nodes*/	

    //--getter
    this.getNodes = function(){	
	return nodesById;
    };


    /**give table nodesByLoc*/	

    //--getter
    this.getNodesByLoc = function(){	
	return nodesByLoc;
    };

    //--setter
    setNodesByLoc = function(idLocation,node){	
	nodesByLoc[idLocation]=node;
    };



    //******location******//

    var widthScreen = htmlPrimaryParent.width();
    this.computeNumColumns = function(newNumOfColumns){
	// Test if newNumOfColumns has been given as parameter
	newNumOfColumns = newNumOfColumns || false;
		
	if (newNumOfColumns !=false)  { 
	    numOfColumns = Math.min(newNumOfColumns, maxNumOfColumns);
	} else { 	
	    widthScreen = htmlPrimaryParent.width();
	    //console.log("processing num of columns from spread and screen size");
	    numOfColumns =
		Math.min(
		    Math.max(
			Math.floor((widthScreen-parseInt($(me.menu.getHtmlMenuSelector()).css("width")))/(spread.X+borderSize)),
			1),
		    maxNumOfColumns);
	}
    };
	
    /** This function provides a mlocation of the node
	when you submit an idLocation*/

    //--find  node mlocation
    this.mlocationProvider = function(node_idLocation){		
	var nX =node_idLocation%numOfColumns ;
	var nY = Math.floor(node_idLocation/numOfColumns);
	return (new MLocation(nX,nY));
    };

    /**This function provide a location of the node
       ...
    */	

    var ppol=primaryparent.offsetLeft;
    var ppot=$(".main-legend-zone").height();
    //primaryparent.offsetTop;
    //--find  node location
    this.locationProvider = function(node_idLocation){

	var temp = me.mlocationProvider(node_idLocation);
	var nX =temp.getnX();
	var nY =temp.getnY();
	// var x = nX*(spread.X+gapBetweenColumns)+ (nX)*borderSize+htmlPrimaryParent.offset().left;
	var x = nX*(spread.X + gapBetweenColumns + borderSize)+ppol;
	//var y = nY*(spread.Y+gapBetweenLines)+ (nY)*borderSize+htmlPrimaryParent.offset().top;
	var y = nY*(spread.Y + gapBetweenLines + borderSize)+ppot;
	return (new Location(x,y));
    };

    //--find all node location
    this.globalLocationProvider = function(){ 

	for(O in nodesById)  { 	
	    if(!$('#' + nodesById[O].getId()).hasClass("transparentNode")) { // Transparent nodes have sometimes to remain superposed
		nodesById[O].setLocation(me.locationProvider(nodesById[O].getIdLocation()),false);
		setNodesByLoc(nodesById[O].getIdLocation(),nodesById[O]);
	    } else {
		$('#'+nodesById[O].getId()).css("z-index", 899);
		//console.log("getting new z-index at ", $('#'+nodesById[O].getId()).css("z-index"));
	    }
			
	}
		
    };


    // Change location of a node and update nodesByLoc table
    this.setLocation = function(node, IdLoc, boolAnimation, animationSpeed) {
	boolAnimation = boolAnimation || false;
	animationSpeed = animationSpeed || configBehaviour.animationSpeed;
	node.setLocation(me.locationProvider(IdLoc),boolAnimation,animationSpeed);
	setNodesByLoc(node.getIdLocation(),node);
	return $.Deferred().resolve();
    }
    var updateNode = function(node) {
	// Force wait end of animation to asynchronusly detect
	if (node.getNodeInViewportStatus()) {
	    node.setOnOffStatus(true);
	    node.updateUrl();
	}
    }
    
    //--Switch position between two nodes

    this.switchLocation = function(node1,node2,boolAnimation,boolSavePosition, boolBlockMove){
	boolBlockMove = boolBlockMove || false;
	if(boolSavePosition==true)
	    me.savePositions(boolBlockMove);
	var tampon = node1.getIdLocation();

	node1.setIdLocation(node2.getIdLocation());
	node2.setIdLocation(tampon);

	//if($('#' + node1.getId()).hasClass("transparentNode") || $('#' + ListMoveNodes[NodeM-1]).hasClass("transparentNode")) {
	//console.log("don’t swap, transparent");
	//} else {

	node1.setLocation(me.locationProvider(node1.getIdLocation()),boolAnimation,configBehaviour.animationSpeed);
	node2.setLocation(me.locationProvider(node2.getIdLocation()),boolAnimation,configBehaviour.animationSpeed);	


	setNodesByLoc(node2.getIdLocation(),node2);
	setNodesByLoc(node1.getIdLocation(),node1);
	node1.setNodeInViewportStatus();
	node2.setNodeInViewportStatus();
    }

    //--A node gets the position of another one
    //  and all the columns will be shifted and all the lines to the initial position
    this.switchLocationShiftColumnLine = function(node1,node2,boolAnimation,boolSavePosition){

	var lineDrag   =this.mlocationProvider( node1.getIdLocation() ).getnY();
	var columnDrag =this.mlocationProvider( node1.getIdLocation() ).getnX();
	var lineDrop   =this.mlocationProvider( node2.getIdLocation() ).getnY();
	var columnDrop =this.mlocationProvider( node2.getIdLocation() ).getnX();

	this.setlineSelected( lineDrop );
	this.setcolumnSelected( columnDrop );

	//console.log(lineDrag, lineDrop, columnDrag, columnDrop);


	// Ces commentaires rappellent que l'on devra optimiser l'algo 
	//   si les images à déplacer sont lourdes (Jupyter, vnc ?)
	// SaveNode=node1;
	// node1.setJsonDataUrl("")
	// node1.setLoadedStatus(false)
	// me.loadContent(node1.getId());
	// node1.setLoadedStatus(true)

	var ListMoveNodes= [];
	var nX = [];
	var nY = [];

	for(O in this.getNodesByLoc()) {
	    nX[O]=this.mlocationProvider( this.getNodesByLoc()[O].getIdLocation()).getnX();
	    nY[O]=this.mlocationProvider( this.getNodesByLoc()[O].getIdLocation()).getnY();
	}

	if ( lineDrag > lineDrop ) {
	    if ( columnDrag > columnDrop ) {

		for(O in this.getNodesByLoc()) {
			    
		    if (nX[O] == columnDrop && lineDrag > nY[O] && !(nY[O] < lineDrop) ) {
			this.getNodesByLoc()[O].getHtmlNode().css({
				boxShadow: "0 0 0 10px blue"});//GLOBALCSS
			ListMoveNodes.push(this.getNodesByLoc()[O])
				
		    } else if ( !(nX[O] < columnDrop) && nY[O] == lineDrag && !(nX[O] > columnDrag) ) {
			this.getNodesByLoc()[O].getHtmlNode().css({
				boxShadow: "0 0 0 10px red"});//GLOBALCSS
			ListMoveNodes.push(this.getNodesByLoc()[O])
		    }
		}
			
	    } else {
			
		for(O in this.getNodesByLoc()){
		    if (nX[O] == columnDrop && lineDrag > nY[O] && !(nY[O] < lineDrop) ) {
			this.getNodesByLoc()[O].getHtmlNode().css({
				boxShadow: "0 0 0 10px blue"});
			ListMoveNodes.push(this.getNodesByLoc()[O])
		    }
		}

		ReverseList=[]
		for(O in this.getNodesByLoc()) {
		    if ( !(nX[O] < columnDrag) && nY[O] == lineDrag && !(nX[O] > columnDrop) ) {
			this.getNodesByLoc()[O].getHtmlNode().css({
				boxShadow: "0 0 0 10px red"});
			ReverseList=[this.getNodesByLoc()[O]].concat(ReverseList)
		    }
		}
		ListMoveNodes=ListMoveNodes.concat(ReverseList)
	    }
		    
	} else {
	    //( lineDrag <= lineDrop ) 
	    if ( columnDrag > columnDrop ) {
			
		ReverseList=[]
		for(O in this.getNodesByLoc())  {
		    if (nX[O] == columnDrop && (nY[O] > lineDrag) && !(lineDrop < nY[O]) ) {
			this.getNodesByLoc()[O].getHtmlNode().css({
				boxShadow: "0 0 0 10px blue"});
			ReverseList=[this.getNodesByLoc()[O]].concat(ReverseList)
		    } 
			    
		}

		for(O in this.getNodesByLoc()) {
		    if ( !(nX[O] < columnDrop) && nY[O] == lineDrag && !(nX[O] > columnDrag) ) {
			this.getNodesByLoc()[O].getHtmlNode().css({
				boxShadow: "0 0 0 10px red"});
			ListMoveNodes.push(this.getNodesByLoc()[O])
		    }
		}
		ListMoveNodes=ReverseList.concat(ListMoveNodes)
			
	    } else {
		//( lineDrag <= lineDrop )
		// ( columnDrag <= columnDrop )
			
		ReverseList=[]
		for(O in this.getNodesByLoc()) {
		    if (nX[O] == columnDrop && (nY[O] > lineDrag) && !(lineDrop < nY[O]) ) {
			this.getNodesByLoc()[O].getHtmlNode().css({
				boxShadow: "0 0 0 10px blue"});
			ReverseList=[this.getNodesByLoc()[O]].concat(ReverseList)
		    } 
			    
		}
			
		ReverseList2=[]
		for(O in this.getNodesByLoc()) {
		    if ( !(nX[O] < columnDrag) && nY[O] == lineDrag && !(nX[O] > columnDrop) ) {
			this.getNodesByLoc()[O].getHtmlNode().css({
				boxShadow: "0 0 0 10px blue"});
			ReverseList2=[this.getNodesByLoc()[O]].concat(ReverseList2)
		    } 
			    
		}
		ListMoveNodes=ReverseList.concat(ReverseList2)
			
	    }
	}

	for(NodeM=ListMoveNodes.length-1; NodeM > 0;NodeM--) {
	    //console.log("swapping nodes : ", node1.getId(), ListMoveNodes[NodeM-1].getId());
	    node1.setIsMoving(true);
	    this.switchLocation(node1,ListMoveNodes[NodeM-1],configBehaviour.showAnimationsLineColSwap,true);
	    ListMoveNodes[NodeM-1].getHtmlNode().css({
		    boxShadow: ""});
	}
	node1.getHtmlNode().css({
		boxShadow: ""});
	node1.updateSelectedStatus(false);

	// node1.setJsonDataUrl(SaveNode.getJsonData().url)
	// node1.setLoadedStatus(false)
	// me.loadContent(node1.getId())
	// node1.setLoadedStatus(true)

    } // End switchLocationShiftColumnLine


    //******selectedNode******//

    //--add node on  selectedtable
    addSelectedNode = function(node){	
	selectedNodes.push(node);	
    }

    //--remove node on  selectedtable
    removeSelectedNode = function(node){	
	selectedNodes.splice(selectedNodes.indexOf(node),1);
    };

    //--getter node selected status table
    this.getSelectedNodes = function(){
	return selectedNodes;
    };

    //******nodesToToggle******//

    //--add node to toggle 
    addNodeToToggle = function(node){	
	nodesToToggle.push(node);	
    }

    //--remove node to toggle
    removeNodeToToggle = function(node){	
	nodesToToggle.splice(nodesToToggle.indexOf(node),1);
    };

    //--getter node selected status table
    this.getNodesToToggle = function(){
	return nodesToToggle;
    };

    //******Border size******//

    //--getter
    this.getBorderSize = function(){	
	return borderSize;
    };



    //******nodes******//
    me.computeNumColumns();

    /**Here the table of nodes is filled*/
    nodesById = (    function(){

	    var node = [];
	    var nodes_ = [];
	    var temp = []; // utility ?

	    for(i=0;i<nodeCardinal;i++)  { 
		temp = new Location(); // utility ?
		node = new Tile(this);
		nodes_["node"+node.getId()]=node;
		nodesByLoc[node.getIdLocation()]=node;
	    }
	    globalTagsList.sort();

	    return nodes_;
	}());


    //******nodesOldPosition*******//


    this.savePositions = function(boolBlockMove){
	boolBlockMove = boolBlockMove || false;

	if(stepBack>1)  { 
	    while(stepBack > 1)  { 
		stepBack--;
		nodesOldPositions.pop();
	    }
	}

	var indice = nodesOldPositions.length;

	nodesOldPositions[indice] = new Array();

	var u = 0;

	for(u=0;u<nodesByLoc.length;u++)  { 
	    nodesOldPositions[indice][u]=nodesByLoc[u].getId();
	}
	nodesOldPositions[indice].push(boolBlockMove); // The last element of the layer says if it’s part of a block move or not
	    
	    
    };

    //******extra method******//

    /**this methods return true 
       when the input word is find on metadata of the node data 
       these metadata are on the jsondata added on the creation of the node,
       particularly on the "comments"
    */
    this.hasTag = function(node,word){
	    
	if(node.getJsonData().comment.search(word)>-1 ||  node.getNodeTagList().indexOf(word)>-1) 
	    // Adapted to search in "comment" field of the nodes.js, and in the "nodeTagList" (which can be modified during a session)
	    return true;
	else
	    return false;			
	    
    };

    /**this methods return true 
       when the input word is find on metadata of the node data 
       these metadata are floating tag on the jsondata added on the creation of the node
    */
    this.hasFloatingTag = function(node,word){
	return node.getFloatingTag().hasOwnProperty(word)
    };

    /** Manage node size **/
    this.changeNodeSize = function(){

	var X_ = (parseInt($("body").prop("scrollWidth")))/(maxNumOfColumns);
	// To be checked for new version .... 
	ratio = spread.X/((parseInt($("body").prop("scrollWidth"))-(maxNumOfColumns-1)*gapBetweenColumns- X_)/maxNumOfColumns);
	//mesh.updateSpread({X : spread.X/ratio , Y : spread.Y/ratio});
	me.computeNumColumns();
    };

    /** Manage menu size TODO **/
    // Inspired by this.changeNodeSize, may need some adaptations
    /*this.changeMenuSize = function(){
      var X_ = (parseInt($('body').prop("scrollWidth")))/(maxNumOfColumns);
      ratio = spread.X/((parseInt($('body').prop("scrollWidth"))-(maxNumOfColumns - 1)* )) }; */



    /**Put node above other node on the screen ( increase zindex )*/
    putOnTop = function(nodeId){
	    
	for ( O in nodesById)  { 		
	    if(!(nodesById[O].getId()==nodeId))  { 
		putDown(nodesById[O].getId());
	    } else { 
		$("#"+nodesById[O].getId()).css("z-index",100);
	    }
	}
    };
    /**Put node under other node on the screen ( decrease zindex )*/
    putDown = function(nodeId){
	if($('#'+nodeId).attr("class").match("transparentNode"))  { 
	    //console.log("dont put down");
	    $("#"+nodeId).css("z-index",100);
	} else { 
	    $("#"+nodeId).css("z-index",3);
	}
    };

    /**Here we load the iframe content on a given node*/
    this.loadContent = (    function(){
	    
	    var maxH = -1;
	    var maxW = -1;
	
	    return function (nodeId)  { 
		var node = nodesById["node"+nodeId];
		var hnode=node.getHtmlNode();
		var ratio = 1;
		if ($("#iframe"+nodeId).length == 0) {
		    hnode.append('<iframe id=iframe'+node.getId()+' scrolling = "yes" src="" frameborder=0 height = "'+  
				  hnode[0].clientHeight + 'px" width = "' + hnode[0].clientWidth + 'px" style="display=none"></iframe>');
		}
		var widthtab = [];
		var heighttab =[];
		
		(    function(){
		    
		    var id=node.getId();
		    var iframe = $('#iframe'+id);
		    iframe.onload = function(){
			widthtab[id] = this.width;
			heighttab[id] = this.height;	
			mesh.setWidthTab(id,this.width);
			mesh.setHeightTab(id,this.height);	

			if(maxH<heighttab[id] || maxW<widthtab[id]){
						    
			    if(maxH<heighttab[id])
				maxH = heighttab[id];
			    
			    if(maxW<widthtab[id])
				maxW = widthtab[id];
			    
			    iframe.height(heighttab[id]).width(widthtab[id]).css(zIndex,101 /*marginLeft : marginleft , marginTop : margintop  }*/ );
			    //iframe.attr("src",this.src);
			    if(ColumnStyle=="static"){
				var W = (parseInt($("body").prop("scrollWidth")))/(maxNumOfColumns);
				ratio = maxW/((parseInt($("body").prop("scrollWidth"))-(maxNumOfColumns-1)*gapBetweenColumns- W)/maxNumOfColumns);
			    }
			    //console.log(ratio);
			    //mesh.updateSpread({X : maxW/ratio , Y : maxH/ratio});
			    //mesh.globalLocationProvider();
			} else { 
			    iframe.height(heighttab[id]).width(widthtab[id]) /*.css({zIndex:101, marginLeft : marginleft , marginTop : margintop  } )*/;
			    mesh.changeNodeSize();
			    
			};

		    }

		    node.updateUrl();
		    //$(".temporaire").remove(); Not used anywhere else in script2 ?!

		    // We need to return it because on function startLoading only visible nodes will be loaded
		    
		} ());

		return ratio;
		
	    };
	})(); // End loadContent
	
    this.loadHitbox = (    function(){ // Load hitboxes (if visible ?) and their behaviour
	    return function(nodeId)  { 
		//console.log("loadingHB");
		var HB = $('#hitbox'+nodeId);
		var id = nodeId;
		HB.css({
			height: spread.Y, 
			    width: 60, // GLOBAL !
			    left: -60,
			    zIndex: 102, 
			    position: 'absolute', 
			    });

	    };
	})();

    var SetOff = function(id) {
	var node=$('#'+id);
	var OOF = $('#onoff'+id);
	var node2= nodesById["node"+id];
	OOF.css('background-color', "red");
	node.children("iframe").hide();
	node2.setLoadedStatus(false);
    }

    var SetOn = function(id) {
	var node=$('#'+id);
	var OOF = $('#onoff'+id);
	var node2= nodesById["node"+id];
	OOF.css('background-color', "green");
	node2.setLoadedStatus(true);
	mesh.loadContent(id);
	node.children("iframe").show();
	node2.updateUrl()
    }

    
    /** Here we load all the nodes or only those visible on screen*/
    this.startLoading = function()  { 
	// Creation of the mesh, loading image data
	//waypoints are the object which can detect when a object are entering on screen
	// see http://imakewebthings.com/waypoints/ for details
	var waypoint = new Array();
	var ratio = 1;

	if(configBehaviour.showInfoAtLoading)  { 
	    for (O in nodesByLoc)
		if (nodesByLoc[O].getNodeInViewportStatus())
		    nodesByLoc[O].getHtmlNode().children(".info").css({visibility : "visible"});	
	    $(".showInfoButtonIcon").removeClass('showInfoButtonIcon').addClass('closeShowInfoButtonIcon');
	}

	me.computeNumColumns();
	for(O in nodesById){

	    var id = O.replace("node","");
	    var node = mesh.getNode(id);
	    var ratio = 1;

	    if( node.getLoadedStatus() == false && 
		node.getNodeInViewportStatus() )  { 
			
		ratio=mesh.loadContent(node.getId());
		SetOn(id);
		mesh.loadHitbox(node.getId());
	    }
	    else if(node.getLoadedStatus() == false)  { 
			    
		var id = node.getId();
		//remember : http://imakewebthings.com/waypoints/ for details
		//#005-2
		//offset : parseInt(window.innerHeight) + distance_from_the_bottom_for_loading ,
		waypoint[id] =	new Waypoint({
				
			offset : 'bottom-in-view' ,
			element: document.getElementById(''+node.getId()),
				
			handler: (    function(){
					
				var id = node.getId();
				return function(direction) {
					    
				    ratio = mesh.loadContent(id);
				    mesh.loadHitbox(id);
				    waypoint[id].destroy();
				    node.setLoadedStatus(true);
					    
				};
					
			    })()
		    });
	    }
	}

	spread = mesh.getSpread();
	mesh.updateSpread({X : spread.X/ratio , Y : spread.Y/ratio});

	//* Dynamic icons for actionGlobal menu    
	for ( var TS in json_actions) {
	    for ( var thisAction in json_actions[TS]) {
		var FuncName=json_actions[TS][thisAction][0];
		var IconName=json_actions[TS][thisAction][1];
		var ButtonDiv=$(".optionfromactionGlobal").filter("."+TS+"_"+IconName+"ButtonIcon")
		if (ButtonDiv.children().length == 0) {
		    ButtonDiv.append('<i class="material-icons" style="position:relative; top:100px; color:'+
				$('.'+TS).css("background-color")+'; -moz-transform:scale(8);-webkit-transform:scale(8)">'+
				IconName+'</i>')
		}
	    }}
	
    }; // End startLoading

    /**Here all the native (without menu event) event are implemented*/
    this.meshEventStart = function(){
	// Reset events
	$('.hitbox').off(); 
	$('.node').off(); 
	$('.qrcode').on({
	    click : me.clickQRcode
	});
	
	_allowDragAndDrop = true;
	touchspeed = configBehaviour.touchSpeed; // speed of touch move;

	this.meshEventReStart = function(){
	    setTimeout(function() {
		if (touchok) 
		    htmlPrimaryParent.off();

		for (O in nodesByLoc)  { 
		    if (nodesByLoc[O].getNodeInViewportStatus()) { 
			nodesByLoc[O].sub('qrcode').off();
			nodesByLoc[O].sub('handle').off();
			nodesByLoc[O].sub('rotate').off();
			
			nodesByLoc[O].sub('hitbox').off(); 
			nodesByLoc[O].sub('onoff').off();
			nodesByLoc[O].sub('').off(); 
		    }
		} 
		_allowDragAndDrop = true;

		if (touchok) 
		    htmlPrimaryParent.on(touchhandleEvent);

		for (O in nodesByLoc)  { 
		    if (nodesByLoc[O].getNodeInViewportStatus()) { 
			nodesByLoc[O].sub('onoff').on(OOFEvent);
			nodesByLoc[O].sub('handle').on(handleEvent);
			nodesByLoc[O].sub('rotate').on(rotateEvent);
			nodesByLoc[O].sub('hitbox').on(HBEvent);
			nodesByLoc[O].sub('').on(NodeEvent);
			nodesByLoc[O].setLoadedStatus(true);			
			
			nodesByLoc[O].sub('qrcode').on({
			    click : clickQRcode
			});
		    }
		}
	    }, 100);
	}

	this.setDraggable = function(targetNode_, boolBorder, boolTransparent){
	    //console.log("in set draggable border "+boolBorder+", transp "+boolTransparent);
	    if (! $('#' + targetNode_).hasClass("ui-draggable")) {
		//console.log("setDraggable "+targetNode_);
		$('#'+targetNode_).css("z-index", 999);
		$('#handle'+targetNode_).addClass("drag-handle-dragging");
		if (boolTransparent)  { 
		    console.log("set draggable transp ", boolTransparent);
		} else if(boolBorder) {
		    console.log("set draggable border ", boolBorder);
		    $('#' + targetNode_).children("iframe").hide(); //attr("src", "about:blank");
		    $('#' + targetNode_).css("background-color", "transparent");
		    $('#' + targetNode_).css("border", "10px solid white");
		}
		putOnTop(targetNode_); 
		$('#'+targetNode_).draggable();
		$('#' + targetNode_).off("mouseleave");
		if (parseBool(configBehaviour.moveOnGrid)) {
		    $('#' + targetNode_).draggable("option", "grid", [spread.X + gapBetweenColumns, spread.Y + configBehaviour.gapBetweenLines]);
		}
		$('#' + targetNode_).off("mouseup").on("mouseup", function(e){
		    
			me.dropNode(targetNode_);
			refreshNodes(targetNode_);
			me.globalLocationProvider();
			//e.stopPropagation(); // Or the "mousedown/mouseup"
		    });
	    }


	};

	this.unsetDraggable = function(targetNode_, boolBorder, boolTransparent){ // Called in "dropNode", not to be used as stand-alone
			
	    boolBorder = boolBorder || configBehaviour.moveOnlyABorder;
	    //console.log("in unset draggable",targetNode_,  $('#'+targetNode_).hasClass("ui-draggable"));

	    boolTransparent = boolTransparent || $('#'+targetNode_).attr("class").match("transparentNode");

	    if($('#' + targetNode_).hasClass("ui-draggable")) {
		$('#' + targetNode_).draggable("destroy");
	    } else {
		//alert("this node wasn't even draggable!'")
		//console.log("Warning : node " + targetNode_ + " wasn't draggable");
	    }
	    if (boolTransparent) {
		$('#'+targetNode_).css("z-index", 899);
		//console.log("getting new z-index at ", $('#'+targetNode_).css("z-index"));
	    } else {
		$('#'+targetNode_).css("z-index", 3);
	    }
	    if (boolBorder) {
		if (nodesByLoc[targetNode_].getLoadedStatus()) {
		    $('#' + targetNode_).css("background-color", "white");
		    $('#' + targetNode_).css("border-display", "none");
		    me.loadContent(targetNode_);
		}
	    }
			
	    //$('#hitbox' + targetNode_).css("background-color", "black");
	    $('#handle'+targetNode_).removeClass("drag-handle-dragging");

	    //console.log(me.getSelectedNodes());

	};

	this.dropNode = function(targetNode_){
	    var node = me.getNode(targetNode_);
	    //console.log("dropNode "+targetNode_);
	    node.updateLocFromHtmlNode();		
	    var nodeX = node.getLocation().getX();
	    var nodeY = node.getLocation().getY();
	    me.RealdropNode(targetNode_, nodeX, nodeY);	    
	    $('#'+targetNode_).addClass("NotSharedAgain");
	    cdata={"room":my_session, "id":targetNode_, "posX":nodeX , "posY":nodeY };
	    socket.emit("move_tile", cdata, callback=function(sdata){
		//console.log("socket send move_tile", sdata);	
	    });
	};
	    
	this.RealdropNode = function(targetNode_, newPosX, newPosY){
	    var node = me.getNode(targetNode_);
	    //console.log("dropNode "+targetNode_);
	    node.updateLocFromHtmlNode();		
	    var nodeX = newPosX;
	    var nodeY = newPosY;
	    var i = 0;

	    allocate = false;
	    for(i = 0 ; i < nodeCardinal ; i++) {
		if(i != node.getId()) {
		    var tmpNodeLoc = nodesById["node" + i].getLocation();
		    var tmpNodeX = tmpNodeLoc.getX();
		    var tmpNodeY = tmpNodeLoc.getY();
		    var v = nodeX - tmpNodeX;
		    var w = nodeY - tmpNodeY;

		    if((v>-spread.X/targetSize && w>-spread.Y/targetSize) && (v<spread.X/targetSize && w<spread.Y/targetSize)) { 
			//console.log("found "+ nodesById["node"+i].getId()+ " -> ("+ $('#' + node.getId()).attr("class")+")");
			if($('#'+node.getId()).hasClass("transparentNode")) { // Drop on corresponding tile
			    me.setLocation(node,tmpNodeLoc);
			    allocate = true;

			} else { // Drop besides the tile
			    me.switchLocationShiftColumnLine(node,nodesById["node"+i],true,true);
			    allocate = true;
			    node.updateSelectedStatus(false);
			}
			break;
		    }
		}
	    }

	    if (allocate == false) { // ie node not dropped, no corresponding tile found
		me.setLocation(node,node.getIdLocation(),false,50);
	    }

	};

	socket.on('receive_move', function(sdata){
	    //console.log("receive_move",sdata);

	    var newPosX = sdata["posX"];
	    var newPosY = sdata["posY"];
	    var tileID = parseInt(sdata["id"]);
	    //console.log("2 receive_move", sdata["session_id"], $('#'+tileID), newPosX, newPosY);
	    if ( ! $('#'+tileID).hasClass("NotSharedAgain") )
		me.RealdropNode(tileID, newPosX, newPosY);
	    else
		$('#'+tileID).removeClass("NotSharedAgain");
	});


	var dragAndDrop = function(targetNode_){

	    //console.log("dragAndDrop"+targetNode_);
	    // Don’t trigger if an option is selected
	    if (!_allowDragAndDrop) {
		$('node').filter('.ui-draggable').draggable("destroy");
		//console.log("Don’t move: drag and drop not allowed here");
		//return -1;
	    } else {
		var targetNode = targetNode_;
		var node = mesh.getNode(targetNode);
		var _isNodeTransparent = ($('#' + targetNode).hasClass("transparentNode") == true);
		mesh.setDraggable(targetNode, configBehaviour.moveOnlyABorder, _isNodeTransparent);
	    }
	};

	// Group tags along a pattern
	var groupTags = function(pattern_) {
	    var Nodes = nodesByLoc;
	    var NodesByLoc = nodesByLoc;
	    //console.log("grouping", pattern_);
	    var w = 0;
	    for (O in Nodes)  { 
		if (mesh.hasTag(Nodes[O], pattern_))  { 
		    mesh.switchLocation(Nodes[O], NodesByLoc[w], false, true)	
			}
	    }
	};

	// Behaviour when mouse is over a node
	var mouseEnterFunction = function () {
		
	    var node = mesh.getNode(this.id);
	    node.updateHtmlNodeState(1);
	    if ($('node').filter('.ui-draggable').length == 0) { // No draggable nodes to keep on top
		putOnTop(node.getId());
		var HB=$('#hitbox'+node.getId());
		var HBcolor = HB.css('background-color');
		if(HBcolor != colorHBselectedRGB && HBcolor != colorHBtoZoomRGB)  { // Keep the color only if the node has been selected or zoomed 
		    HB.css("background-color", colorHBonfocus);
		}
	    }
	    if (_allowDragAndDrop) {
		//console.log("from mouseEnterFunction")
		//dragAndDrop(this);
	    } else {
		//console.log("Drag and drop not allowed :'(");
	    }
	};

	// When the mouse leaves the node : no border anymore, only a change in color on the HB ! 
	var mouseLeaveFunction  = function () {
	    //console.log("mouseLeaveFunction");
	    for (O in nodesByLoc)
		if (nodesByLoc[O].getNodeInViewportStatus()) {
		    nodesByLoc[O].sub('').off("mouseup");
		}
	    var node = mesh.getNode(this.id);
	    var HBcolor = $('#hitbox'+node.getId()).css('background-color');
	    if(HBcolor != colorHBselectedRGB && HBcolor != colorHBtoZoomRGB)  { // Keep the color only if the node has been selected or zoomed 	
		$('#hitbox'+node.getId()).css('background-color', colorHBdefault);
	    }
		    
		    
	    if(node.getState()==3)  { // 3 == drag and drop achieved
		node.draggable("destroy")
		mesh.loadContent(this.id);
	    }
		    
	    node.updateHtmlNodeState(0);
	    putDown(node.getId());
	};
	    
	//When a mouse click on a node
	// -> First the node is colored in red
	// -> the node color back to normal 
	var clickFunction = function () {
		
	    //console.log("click function");
	    var node = mesh.getNode(this.id);
	    if (node.getState() == 0) {
	    for (O in nodesByLoc)
		if (nodesByLoc[O].getNodeInViewportStatus()) {
		    nodesByLoc[O].sub('').off("mouseup");
		}
		node.updateHtmlNodeState(1);
		//console.log($('.transparentNode').length);
		if ($('.transparentNode').length==0)  { 
		    //console.log("put on top");
		    putOnTop(node.getId());
		}
		else {
		    // What if one node is transparent ?
		}

		//var HT=node.getHtmlNode(); // Not used anywhere else ?!
		//if(me.getSelectedNodes().length<1)
		//if(me.getSelectedNodes().length<1 && !($(mesh.menu.getHtmlMenuSelector()).children("[class*=close]").length > 0 && !configBehaviour.moveOnMenuOption && !configBehaviour.alwaysShowInfo))
		//{
		//console.log("click, dont drag");
		//dragAndDrop(this);
		//}
		//else if ($('.closeTransparentButtonIcon').length > 0)
		//{
		//console.log("exception : transparency");
		////dragAndDrop(this);
		//}
	    } else { 
		for (O in nodesByLoc)
		    if (nodesByLoc[O].getNodeInViewportStatus()) {
			nodesByLoc[O].sub('').off("mouseup");
		    }
		node.updateHtmlNodeState(0);
		putDown(node.getId());
	    }
	};

	    
	// Behaviour when a node is selected : red solid border
	var dblclickFunction = function() {
		
	    var node = mesh.getNode(this.id); // TO DO : how to be sure/consider each case (selected/node/iframe/id) ?

	    if(node.getSelectedStatus()==false)
		node.updateSelectedStatus(true);
	    else
		node.updateSelectedStatus(false);

	    if(selectedNodes.length>2)  { // More than two nodes : the first one is unselected
		selectedNodes[0].updateSelectedStatus(false);
	    }
	    else if (selectedNodes.length == 2)  { // Two nodes : they switch position (switchLocation) or are placed besides (switch LocationShiftColumnLine)
		me.switchLocationShiftColumnLine(selectedNodes[0],selectedNodes[1],true,true)
		// me.switchLocation(selectedNodes[0],selectedNodes[1],true,true)
		selectedNodes[0].updateSelectedStatus(false);
		//selectedNodes[1].updateSelectedStatus(true);

	    }
	};


	var NodeEvent = {

	    mouseenter: mouseEnterFunction ,

	    mouseleave: mouseLeaveFunction,

	    click: clickFunction,

	    dblclick: dblclickFunction

	};
	   
	$('.node').on(NodeEvent);

	var clickOnOff = function(){
	    if (emit_click("onoff",this.id))
		return
	    var id = this.id.replace("onoff", "");
	    var node = nodesById["node"+id];
	    if(	node.getOnOffStatus() ) {
		SetOff(id);
	    } else {
		SetOn(id);
	    }
	}
		
	var OOFEvent = {
	    click: clickOnOff
	};

	$('.onoff').on(OOFEvent);
		
	clickHB = function(){
	    //console.log("Hitbox " + id + " clicked");
	    if((me.getZoomSelection() == false) && (currentSelectedTag == ""))  { // Default behaviour : not selecting nodes for a zoom, not in tag mode
		var HB = $('#'+this.id);
		//console.log(this.id, HB);
		var id = this.id.replace("hitbox", "");
		var HBcolor = HB.css('background-color');
		if(HBcolor == colorHBselectedRGB)  { // Check if the node is already selected
		    HB.css({backgroundColor : colorHBonfocus}); // Return to focused state only
		} else { 	
		    HB.css({backgroundColor : colorHBselected}); // Select node
		}
		if(me.getNodesToToggle().length == 0)  { 
		    addNodeToToggle(id);
		}
		else if(me.getNodesToToggle().length == 1)  { 
		    var nodesToToggle = me.getNodesToToggle();
		    if(id!=nodesToToggle[0]) {
			addNodeToToggle(id);
			var node1 = me.getNode(nodesToToggle[0]);
			var node2 = me.getNode(nodesToToggle[1]);
			me.switchLocationShiftColumnLine(node1,node2,true,true);
			$('#hitbox'+nodesToToggle[0]).css('background-color', colorHBdefault);
			$('#hitbox'+nodesToToggle[1]).css('background-color', colorHBdefault);
			nodesToToggle.splice(0,2);
			nodesToToggle.splice(0,2);
		    } else { 
			console.log("This node is already stored");
		    }
		} else { 
		    console.log("Problem with nodesToToggle, its length shouldn’t exceed 2 !");
		}
	    }	
	    else if (me.getZoomSelection() == true)  { 
		console.log("Select Zoom with hitbox.");
		clickHBSelect(id=this.id);
	    }
	    else if (currentSelectedTag !="")  { 
		console.log("Add Tag with hitbox.");
		clickHBTag(id=this.id);
	    }



	};

	nodeSelect = function(node,HB) {
	    if(node.getSelectedStatus()==false) { 
		node.updateSelectedStatus(true); 
		me.addNodeToZoom(node); 
		HB.css({backgroundColor : colorHBtoZoom}); 
	    } else { 
		node.updateSelectedStatus(false);
		me.removeNodeToZoom(node);							
		HB.css({backgroundColor : colorHBdefault});
	    }					
	}
	
	clickHBSelect = function(id__){
	    if (typeof this.id == 'undefined')
		var id_ = id__;
	    else
		var id_ = this.id;
	    //console.log("click HBZoom");
	    var HB = $('#' + id_);
	    try {
		var id = id_.replace("hitbox", ""); 
		//console.log(this.id, id, HB); 
		var node = me.getNode(id);
		nodeSelect(node,HB)
	    } catch(e) {
		console.log("Error in clickHBSelect.");
	    }
	};

	clickHBTag = function(id__){
	    if (typeof this.id == 'undefined')
		var id_ = id__;
	    else
		var id_ = this.id;
	    //console.log("click HBTag", this);
	    if (emit_click("hitbox",id_))
		return
	    var HB = $('#' + id_);
	    if(currentSelectedTag != "")  { 
		var id = id_.replace("hitbox", "");
		var node = me.getNode(id);
		node.getStickers().addSticker(currentSelectedTag, attributedTagsColorsArray[currentSelectedTag],true);
		addBorderBlink($("#iframe"+id),attributedTagsColorsArray[currentSelectedTag])
		node.addElementToNodeTagList(currentSelectedTag);
		$('.sticker').off();
		$('.sticker').on({
			click : clickSticker
			    });
		$('#tag-notif').text("Added tag " + currentSelectedTag + " to tile " + id);
	    } else {
		$('#tag-notif').text("No tag currently selected, you may need to click on a tag in the legend to select it, or to create a new one?");
	    }
	};


	var HBEvent = {

	    //mouseenter: mouseEnterHB ,
	    click: clickHB/*,

dblclick: dblclickFunction*/

	};
	$('.hitbox').on(HBEvent);

	var mouseEnterHandle = function(e){
	    if ($("#" + this.id).ontouchstart == undefined) {
		$("#" + this.id).off("mouseleave");
		$("#" + this.id).off("mouseup");
		//console.log("enter", this.id);
		if($('#' + this.id).hasClass("drag-handle-on")) {
		    for (O in nodesByLoc)
			if (nodesByLoc[O].getNodeInViewportStatus()) {
			    nodesByLoc[O].sub('').off("mouseenter");
			}
		    $('#'+this.id).css('-webkit-transform','scale(2)').css('-moz-transform','scale(2)');
		    var nodeToDrag = this.id.replace("handle", "");
		    if(_allowDragAndDrop && $('.node').filter('.ui-draggable').length == 0) {
			// To adapt for multiple draggable tiles at the same time
			//console.log(nodeToDrag);
			$("#" + this.id).on("mousedown", function(e){
				dragAndDrop(nodeToDrag);
			    })
			    } 

		    $("#" + this.id).on("mouseup", function(e){
			    var nodeToDrop = this.id.replace("handle", "");
			    me.dropNode(nodeToDrop);
			    $('#'+this.id).css('-webkit-transform','scale(1)').css('-moz-transform','scale(1)');
			    refreshNodes(nodeToDrop);
			    me.globalLocationProvider();
			    me.meshEventReStart();
			    
			    $("#" + this.id).on("mouseleave", function(e){
				var nodeToDrop = this.id.replace("handle", "");
				refreshNodes(nodeToDrop);
				me.meshEventReStart();
				$('#'+nodeToDrag).on(NodeEvent);
			    });
			    $("#" + this.id).off("mousedown");
			    $("#" + this.id).on("mousedown", function(e){
			    $('#'+nodeToDrag).on(NodeEvent);
			    $("#" + this.id).mouseenter();
			});
			$('#'+nodeToDrag).on(NodeEvent);
		    }).on("mouseleave", function(e){
			$('#'+this.id).css('-webkit-transform','scale(1)').css('-moz-transform','scale(1)');
		    });
		}
		if ($('.node').filter('.ui-draggable').length == 0)
		    for (O in nodesByLoc)
			if (nodesByLoc[O].getNodeInViewportStatus()) {
			    nodesByLoc[O].sub('').on("mousenter");
			}
	    }
	    
	};

	var handleEvent = {
	    mouseenter: mouseEnterHandle,
	};
	if (!touchok) {
	    console.log("No Touch.");
	};
	$('.handle').on(handleEvent);

	var mouseEnterRotate = function(e){
	    if ($("#" + this.id).ontouchstart == undefined) {
		var RotateBut=$("#" + this.id);
		RotateBut.off("mousedown");
		RotateBut.off("mouseup");
		RotateBut.off("mousemove");
		RotateBut.off("mouseleave");
		RotateBut.off("mouseenter");
		RotateBut.off("dblclick");

		var id = this.id.replace("rotate", "");

		var node = mesh.getNode(id);
		var nodeToRotate=$('#' + id);
		
		var rotstate_angle = 0.;
		var rotate_ok=false
		
		RotateBut.on("mousedown", function(e){
		    rotate_ok=true
		    RotateBut.css('-webkit-transform','scale(2)').css('-moz-transform','scale(2)');
		});
		
		RotateBut.on("mousemove", function(e){
		    if (rotate_ok) {
			
			rotstate_angle = node.getNodeAngle();
			if (!! configBehaviour.smoothRotation) {
			    if ( rotstate_angle > 340 || rotstate_angle < 20) 
				rotstate_angle=0;
			    else if ( rotstate_angle > 70 && rotstate_angle < 110) 
				rotstate_angle=90;
			    else if ( rotstate_angle > 160 && rotstate_angle < 200) 
				rotstate_angle=180;
			    else if ( rotstate_angle > 250 && rotstate_angle < 290) 
				rotstate_angle=270;
			} else {
			    rotstate_angle = rotstate_angle+RotInc;
			    if (rotstate_angle > 360) 
				rotstate_angle=RotInc;
			}
			node.setNodeAngle(rotstate_angle);
			
			nodeToRotate.css({ '-webkit-transform': 'rotate('+rotstate_angle+'deg)',
					   '-moz-transform': 'rotate('+rotstate_angle+'deg)',
					   '-o-transform': 'rotate('+rotstate_angle+'deg)',
					   '-ms-transform': 'rotate('+rotstate_angle+'deg)',
					   'transform': 'rotate('+rotstate_angle+'deg)'
					 });
			e.stopPropagation();
		    };
		}).on("mouseup", function(e){
		    if (rotate_ok) {
			rotate_ok=false
			
			RotateBut.off("mousemove");
			RotateBut.off("mouseleave");
			RotateBut.off("mouseup");
			
			RotateBut.on("mouseleave", function(e){

			    RotateBut.css('-webkit-transform','scale(0.5)').css('-moz-transform','scale(0.5)');
			    e.stopPropagation();
			});		    
			e.stopPropagation();
			RotateBut.on("mouseenter",mouseEnterRotate)
		    };
		}).on("dblclick", function(e){
		    node.setNodeAngle(0);
			
		    nodeToRotate.css({ '-webkit-transform': 'rotate('+0+'deg)',
				       '-moz-transform': 'rotate('+0+'deg)',
				       '-o-transform': 'rotate('+0+'deg)',
				       '-ms-transform': 'rotate('+0+'deg)',
				       'transform': 'rotate('+0+'deg)'
				     });
		    e.stopPropagation();
		});
	    };
	};

	var rotateEvent = {
	    mouseenter: mouseEnterRotate,
	};
	$('.rotate').on(rotateEvent);
	
	// multi-touch support
	if (touchok) {
	    var dragging = new Map();	// maps touch IDs to drag state objects
	    var rotating = new Map();

	    //	$(".handle").addClass("drag-handle-on");
	    //$(".handle").addClass("drag-handle-dragging");//.removeClass("drag-handle-on");
		    
	    $('.node').on("mouseleave");
	    $('.node').on("mouseup");

	    var touchstartHandle = function (ev) {
		// alert("touchstart");
		//alert("ev.changedTouches.length"+ev.changedTouches.length);
		var hastouched=false;

		for (var i = 0; i < ev.changedTouches.length; i++) {
		    var touch = ev.changedTouches[i];
		    var targetid=touch.target.id;
		    if  (targetid.indexOf('handle') >= 0 && _allowDragAndDrop ) {
			$('.handle').off();
			var id = targetid.replace("handle", "");
			//var node = mesh.getNode(id);
			var nodeToDrag=$('#' + id);
			var thishandle=$('#'+touch.target.id);
			thishandle.addClass("drag-handle-dragging");

			for (O in nodesByLoc)
			    if (nodesByLoc[O].getNodeInViewportStatus()) {
				nodesByLoc[O].sub('').off("mouseenter");
			    }
			nodeToDrag.off("mouseleave");

			var rect = {
			    top: parseInt(nodeToDrag[0].style.top.replace('px','')),
			    left: parseInt(nodeToDrag[0].style.left.replace('px','')),
			};
			//console.log("touchstart i "+i+" targetid "+targetid+" rect "+rect.top +" "+rect.left );
			dragging.set(touch.identifier, {
				target: touch.target,
				    top: rect.top,
				    left: rect.left,
				    prevX: touch.pageX,
				    prevY: touch.pageY,
				    });
			// for (var [key, value] of dragging) {
			//     console.log("dragging : "+key + " = {" + value.left+", "+value.top+", "+value.prevX+", "+value.prevY+"}");
			// }

			//nodeToDrag[0].style.background='red';
			hastouched=true;
			// } else {
			// 	console.log("touchstart err i "+i+" targetid "+targetid);
			$('#'+targetid).css('-webkit-transform','scale(2)').css('-moz-transform','scale(2)');
		    } else if (targetid.indexOf('rotate') >= 0) {
			var id = targetid.replace("rotate", "");
			var nodeToDrag=$('#' + id);
			var node = mesh.getNode(id);
			var centerX = nodeToDrag[0].style.left.replace('px','')+(nodeToDrag[0].style.width.replace('px','')/2);
			var centerY = nodeToDrag[0].style.top.replace('px','')+(nodeToDrag[0].style.height.replace('px','')/2);
			rotating.set(touch.identifier, {
				target: touch.target,
				    angle: node.getNodeAngle(),
				    centerX: centerX,
				    centerY: centerY,
				    });
			//console.log("centerX : "+rotating.get(touch.identifier).centerX+" centerY : "+rotating.get(touch.identifier).centerY);
			console.log("centerX : "+centerX+" centerY : "+centerY);
			$('#'+targetid).css('-webkit-transform','scale(2)').css('-moz-transform','scale(2)');
		    }
		}
		if  (hastouched) {
		    hastouched=false;
		    //     ev.preventDefault();
		}
	    };
		    
	    var touchmoveHandle = function (ev) {
		for (var i = 0; i < ev.changedTouches.length; i++) {
		    // for each moved touch, see if we have a corresponding dragstate 
		    var touch = ev.changedTouches[i];
		    var targetid=touch.target.id;
		    var dragstate = dragging.get(touch.identifier);
		    var rotstate = rotating.get(touch.identifier);
		    // for (var [key, value] of dragging) {
		    // 	console.log(key + " = {" + value.left+", "+value.top+", "+value.prevX+", "+value.prevY+"}");
		    // }
		    if  (targetid.indexOf('handle') >= 0 && _allowDragAndDrop && dragstate) {
			var id = targetid.replace("handle", "");
			var node = mesh.getNode(id);
			var nodeToDrag=$('#' + id);
			var thishandle=$('#'+touch.target.id);
			dragstate.left = parseInt(dragstate.left)+touchspeed*(touch.pageX - dragstate.prevX);
			dragstate.top  = parseInt(dragstate.top)+touchspeed*(touch.pageY - dragstate.prevY);
			nodeToDrag.css({left: dragstate.left+'px',
				    top: dragstate.top+'px'});
			//nodeToDrag[0].style.background='green';
				
			// if (touch.screenX == dragstate.prevX && touch.screenY == dragstate.prevY) {
			//     thishandle.off("touchmove");
			//     thishandle.on("touchend");
			// } else {				
			//     //update cursor position
			dragstate.prevX = touch.pageX;
			dragstate.prevY = touch.pageY;
			// }
			// console.log("touchmoveFunction screenX "+ dragstate.prevX +" left "+dragstate.left+
			// 	    " screenY " + dragstate.prevY + " top "+dragstate.top );
			// dragstate.prevX = dragstate.left;
			// dragstate.prevY = dragstate.top;
			ev.stopPropagation();
		    }
		    else if (targetid.indexOf('rotate') >= 0 && rotstate && configBehaviour.smoothRotation) {
			var id = targetid.replace("rotate", "");
			var node = mesh.getNode(id);
			var nodeToDrag=$('#' + id);
			var thishandle=$('#'+touch.target.id);

			rotstate.angle = rotstate.angle+RotInc;
			if (rotstate.angle > 360) 
			    rotstate.angle=RotInc;

			console.log(id+" move rotstate.angle : "+rotstate.angle);
			node.setNodeAngle(rotstate.angle);

			nodeToDrag.css({ '-webkit-transform': 'rotate('+rotstate.angle+'deg)',
				    '-moz-transform': 'rotate('+rotstate.angle+'deg)',
				    '-o-transform': 'rotate('+rotstate.angle+'deg)',
				    '-ms-transform': 'rotate('+rotstate.angle+'deg)',
				    'transform': 'rotate('+rotstate.angle+'deg)'
				    });
			//transform-origin: 50% 50%, (ou center center)
		    }
		}
		//ev.preventDefault()
	    }

		    

	    var touchendHandle = function (ev) {
		//console.log("touchend");
		var hastouched=false;
		// for each touch that ended, reset the dragstate
		for (var i = 0; i < ev.changedTouches.length; i++) {
		    var touch = ev.changedTouches[i];
		    var dragstate = dragging.get(touch.identifier);
		    var rotstate = rotating.get(touch.identifier);
		    var targetid=touch.target.id;
		    if  (targetid.indexOf('handle') >= 0 && _allowDragAndDrop && dragstate) {
			var thishandle=$('#'+touch.target.id);
			var id = targetid.replace("handle", "");
			var nodeToDrag=$('#' + id);
			//console.log("touchend i "+i+" targetid "+targetid+" length "+ev.changedTouches.length);

			//nodeToDrag[0].style.background='blue';
			// nodeToDrag.removeClass("ui-draggable-dragging");

			me.dropNode(id);
			me.globalLocationProvider();

			// for (var [key, value] of dragging) {
			//     console.log("dragging : "+key + " = {" + value.left+", "+value.top+", "+value.prevX+", "+value.prevY+"}");
			// }
			dragging.delete(touch.identifier);
			//		    $(thishandle).removeClass("drag-handle-on");
			$(thishandle).removeClass("drag-handle-dragging");

			hastouched=true;

			nodeToDrag.on("mouseleave");
			if (dragging.size == 0)
			    for (O in nodesByLoc)
				if (nodesByLoc[O].getNodeInViewportStatus()) {
				    nodesByLoc[O].sub('').on("mouseenter");
				}

			$('#'+targetid).css('-webkit-transform','scale(1)').css('-moz-transform','scale(1)');
		    } else if (targetid.indexOf('rotate') >= 0 && rotstate) {
			var id = targetid.replace("rotate", "");
			var node = mesh.getNode(id);
			var nodeToDrag=$('#' + id);

			if (!! configBehaviour.smoothRotation) {
			    if ( rotstate.angle > 340 || rotstate.angle < 20) 
				rotstate.angle=0;
			    else if ( rotstate.angle > 70 && rotstate.angle < 110) 
				rotstate.angle=90;
			    else if ( rotstate.angle > 160 && rotstate.angle < 200) 
				rotstate.angle=180;
			    else if ( rotstate.angle > 250 && rotstate.angle < 290) 
				rotstate.angle=270;
			} else {
			    rotstate.angle = rotstate.angle+RotInc;
			    if (rotstate.angle > 360) 
				rotstate.angle=RotInc;
			}

			console.log(id+" end rotstate.angle : "+rotstate.angle);
			node.setNodeAngle(rotstate.angle);

			nodeToDrag.css({ '-webkit-transform': 'rotate('+rotstate.angle+'deg)',
				    '-moz-transform': 'rotate('+rotstate.angle+'deg)',
				    '-o-transform': 'rotate('+rotstate.angle+'deg)',
				    '-ms-transform': 'rotate('+rotstate.angle+'deg)',
				    'transform': 'rotate('+rotstate.angle+'deg)'
				    });

			// var tx=rotstate.centerX - (nodeToDrag[0].style.left.replace('px','')+(nodeToDrag[0].style.width.replace('px','')/2));
			// var ty=rotstate.centerY - (nodeToDrag[0].style.top.replace('px','')+(nodeToDrag[0].style.height.replace('px','')/2));
			// nodeToDrag.css({ '-webkit-transform': 'translate('+tx+'px,'+ty+'px)',
			// 		 '-moz-transform': 'translate('+tx+'px,'+ty+'px)',
			// 		 '-o-transform': 'translate('+tx+'px,'+ty+'px)',
			// 		 '-ms-transform': 'translate('+tx+'px,'+ty+'px)',
			// 		 'transform': 'translate('+tx+'px,'+ty+'px)'
			// 	       });
				    
			rotating.delete(touch.identifier);
			$('#'+targetid).css('-webkit-transform','scale(1)').css('-moz-transform','scale(1)');
		    }
		}
		if  (hastouched) {
		    me.meshEventReStart();
		    //ev.stopPropagation();
		    //ev.preventDefault();
		    hastouched=false;
		}
	    };
		    
	    var touchhandleEvent = {
		touchstart: touchstartHandle,
		touchmove: touchmoveHandle,
		touchend: touchendHandle,
	    }

	    htmlPrimaryParent.on(touchhandleEvent);
	}

	// zoomNodecodes : on click, Zoom 
	this.clickzoomNode = function(){

	    if ( configBehaviour.sharedZoomNodes && emit_click("zoomNodeButtonIcon",this.id))
		return

	    //console.log("zoomNode clicked", this.id);
	    var id = this.id.replace("zoomNode", "");

	    var node = me.getNode(id);

	    // Variables for magnifyingGlass 
	    var nodeZoomTab = new Array();
	    nodeZoomTab.push(node);
	    var ratio =spread.Y/spread.X;
	    var initSpread = spread;

	    for (O in nodesByLoc)
		if (nodesByLoc[O].getNodeInViewportStatus()) {
		    nodesByLoc[O].sub('').off();
		    nodesByLoc[O].sub('hitbox').off("click").on("click", clickHBSelect);
		    nodesByLoc[O].sub('hitbox').off("mouseenter");
		}
	    _allowDragAndDrop = false;
 
	    me.magnifyingGlass(nodeZoomTab,ratio,initSpread);
	    if ( configBehaviour.sharedZoomNodes )
		$('#buttonUnzoom').on('click',function(){ emit_click("unzoomButtonIcon","buttonUnzoom") } )
	};

	this.init_click_zoomNode = function() {
	    $('.zoomNodeButtonIcon').on({
		click : me.clickzoomNode
	    });
	}
	
	// QRcodes : on click, Zoom 
	clickQRcode = function(){
	    //console.log("QRcode clicked", this.id);
	    if (emit_click("qrcode",this.id))
		return
	    var splittedId = this.id.split("qrcode");
	    var nodeId = splittedId.pop();	    
	    var divnode = $('#'+nodeId);
	    var node = nodesById["node"+nodeId];
	    var theqrcode = node.getQRcode();
	    var thisqrcode = $('#qrcode'+nodeId);
	    var qrcodeZoom=theqrcode.getZoom();
		    
	    if (qrcodeZoom) {
		thisqrcode.css({
		    position : "absolute",
		    top : parseInt(divnode.css("height"))-50,
		    left : parseInt(divnode.css("width"))-50,
		    width : 130,
		    height : 130,
		    zIndex : 111,
		});				
		thisqrcode.css('-webkit-transform','scale('+1.+')').css('-moz-transform','scale('+1.+')');
		$('#qqrcode'+nodeId).css({
		    zIndex : 199,
		});				
		theqrcode.setZoom(false);
	    } else {
		thisqrcode.css('-webkit-transform','scale('+400./130+')').css('-moz-transform','scale('+400./130+')');
		thisqrcode.css({
			position : "absolute",
			top : parseInt(divnode.css("height"))-200,
		        left : parseInt(divnode.css("width"))-200,
			zIndex : 999,
		    });
		$('#qqrcode'+nodeId).css({
			zIndex : 999,
			    });				
		theqrcode.setZoom(true);
	    }
	    $('#iqrcode'+nodeId).css({
		    width : thisqrcode.css("width"),
		    height : thisqrcode.css("height"),
		});				
	    $('#qqrcode'+nodeId).css({
		    top : -parseInt(thisqrcode.css("height"))*1.1,
			width : parseInt(thisqrcode.css("width")),
			height : parseInt(thisqrcode.css("height")),
			});				
	};
	
	//when the window is reloaded...
	$( window ).resize(    function() {

		if(ColumnStyle=="static")  { 
		    mesh.changeNodeSize();
		}
		else if(ColumnStyle=="dynamic" && numOfColumns==maxNumOfColumns)  { 	
		    me.computeNumColumns();
		    mesh.globalLocationProvider();
		    mesh.changeNodeSize();
		} else { 
		    me.computeNumColumns();
		    mesh.globalLocationProvider();
		}
		    
	    }) 

    }; // End meshEventStart

};
    })
