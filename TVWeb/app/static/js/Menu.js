/**Menu class

   they are two kind of menu :  - a local menu attached to a node 
   - a global menu attached to the mesh

       
   For local menu : 

   id -> the id of the node 
   htmlSupport -> the htmltag of the node   >$('#'+id)<

   For global menu : 

   id -> choose 999
   htmlSupport -> the htmltag of the header  >$('header')<

   menuEventTab_ -> 

   The size of menuEventTab_ determine the number of menu button 
   The function on menuEventTab_ determine what happens when the users click on the options menu 
   When the users click on the first button menuEventTab_(0) is called 
   When the users click on the second  button menuEventTab_(1) is called etc.
       
   See declaration of Menu for the node and the mesh to know what 
   must be the forms of the function on menuEventTab_
       
       
   menuIconClassAttributesTab_ ->    this table contains the name of the class which allow to give some backgroundImage at the options button
   menuIconClassAttributesTab_ size must be the twice bigger than menuEventTab_ because for eashoptions there is two icon (activate/desactivate)

*/
$(document).ready(    function (){
    Menu = function(id,htmlSupport,menuTitleTab_,menuEventTab_,menuIconClassAttributesTab_,menuShareEvent_,parameters)  { 

	    var id=id;
	    var menuEventTab = menuEventTab_;
	    var numOfEvents = menuEventTab.length;
	    var menuShareEvent = menuShareEvent_;
	    var eventSelectedTab= new Array();

	    this.getId = function() {
	       return id;
	    };
	
	    this.getEventSelectedTab = function(){
	    
		return eventSelectedTab;
	    };

	    this.getMenuIconClassAttributesTab = function(){
	    
		return menuIconClassAttributesTab_;
	    };
		
	    this.getMenuShareEvent = function(){
	    
		return menuShareEvent;
	    };
		
	    this.setMenuShareEvent = function(option_, menuShareEvent_){
	    
		menuShareEvent[option_] = menuShareEvent_;
	    };
	

	    if(typeof parameters == 'undefined'){



		var parameters = {
		
		    position : "absolute",
		    top : 0,
		    left : 0,
		    visible : "hidden",
		    classN : "",
		    height : 100,
		    width : 100,
		    margin : "0px 0px 0px 0px", 
		    rightMargin : 0, 
		    backgroundColor: "rgba(0, 0, 0, 0.0)",
		    //borderStyle : "solid",
		    //borderSize : "20px",
		    //borderColor : "blue",
		    orientation : "H", // Default H for horizontal, V would be for vertical
		    zIndex : 150

		}

	    }

	    var position_= parameters.position;     
	    var top_=parameters.top;
	    var left_=parameters.left;
	    var visible = parameters.visible;
	    var class_ =parameters.classN;
	    var height_=parameters.height;
	    var width_=parameters.width;
	    var src_unselect = "unselectdefault100";
	    var backgroundColor_ = parameters.backgroundColor;
	    var borderStyle_ = parameters.borderStyle;
	    var borderWidth_ = parameters.borderWidth;
	    var borderColor_ = parameters.borderColor;
	    var orientation_ = parameters.orientation;
	    var margin_ = parameters.margin;
	    var rightMargin_ = parameters.rightMargin;
	    var zIndex_ = parameters.zIndex;
	    var menubox_ = true;
	    if (typeof parameters.menubox != 'undefined') {
		menubox_ = parameters.menubox;
	    }
	    var touchok=('ontouchstart' in document);
	    var touchspeed = configBehaviour.touchSpeed; // speed of touch move;

	    if (orientation_ == "V")  { 
		var H = 0;
		var V = 1;
	    } else { 
		var H = 1;
		var V = 0;
	    }

	    this.buildHtmlMenu = function(){	    
	    
		htmlSupport.append('<div id=menu'+id+' class='+class_+'menu></div>');
		// Calculations here to be used in global menu CSS
		var HandleDecalTop=0;
		var HandleDecalLeft=0;
		if (menubox_) {
		    HandleDecalTop=Math.max(parseInt(height_/2),90);
		    HandleDecalLeft=Math.max(parseInt(width_/2),70);
		}

		var myMenu=$("#menu"+id);					
		myMenu.css({
			position : position_,
			    top : 0+top_,
			    left : 0+left_,
			    height : (V*numOfEvents+1*H)*height_+V*HandleDecalTop, // V*numOfEvents gives the total height (in elements), if the menu is not vertical (ie it’s horizontal), we count an element in height
			    width : (H*numOfEvents+1*V)*(width_+rightMargin_)+H*HandleDecalLeft, // Same as height
			    //backgroundColor : 'red',
			    visibility : visible,
			    zIndex : zIndex_,
			    margin : margin_
			    });

		for(optionNumber=0;optionNumber<numOfEvents;optionNumber++)  { 	
		    eventSelectedTab.push(false);
		    myMenu.append('<div id='+id+'option'+optionNumber+' class=optionfrom'+id+' title="'+menuTitleTab_[optionNumber]+'" ></div>');
		    var Option=$('#'+id+'option'+optionNumber);
		
		    Option.addClass(menuIconClassAttributesTab_[optionNumber]).addClass(myMenu.attr("class")+"Button");

		    Option.css({
			    position :'absolute',
				top : optionNumber*height_*V+HandleDecalTop*V,
				left : (optionNumber)*(width_+rightMargin_)*H+HandleDecalLeft*H,
				height : height_,
				width : width_,
				//backgroundColor : 'red'  ,
				zIndex: 130,
			        backgroundColor: backgroundColor_,
				//borderStyle : borderStyle_,
			//borderWidth: borderWidth_,
				//borderColor : borderColor_,
		    
				});


		    Option.on('mouseover',function() {
			if (configBehaviour.tooltip) {
		    	$(this).append('<div id=tooltip class="tooltipfrom'+id
		    		       +' fg-tooltip ui-widget ui-widget-content ui-corner-all" style="font-size: 40px"></div>');
		    	var tooltip=$('#tooltip');
		    	tooltip.html($(this).attr("title"));
			$(this).attr("title","");
		    	if (orientation_ == "V") {
		    	    tooltip.append('<div class="fg-tooltip-pointer-down ui-widget-content"><div class="fg-tooltip-pointer-down-inner"></div></div></div>');
			    tooltip.css("top","-180px");
		    	} else { 
		    	    tooltip.append('<div class="fg-tooltip-pointer-up ui-widget-content"><div class="fg-tooltip-pointer-down-inner"></div></div></div>');
			    tooltip.css("top","240px");
		    	}
		    	tooltip.fadeIn('500');
		    	tooltip.fadeTo('10',10);
			}
			if (touchok) {
			    $('#'+this.id).css('-webkit-transform','scale(1.5)').css('-moz-transform','scale(1.5)');
			}
		    }).on('mouseout',function() {
			if (configBehaviour.tooltip) {
			$(this).attr("title",$(this).children('div#tooltip').text());
		    	$(this).children('div#tooltip').remove();
			}
			if (touchok) {
			    $('#'+this.id).css('-webkit-transform','scale(1)').css('-moz-transform','scale(1)');
			}
		    })

		    $('#'+id+'option'+optionNumber).on({
		    
		    // 	    mouseleave : function(e){
			
		    // 		//e.stopPropagation(); 
			
		    // 	    },
		    
		    
		    
		    // 		mouseenter : function(e){
			
		    // 		//e.stopPropagation(); 
			
		    // 	    },
		    
		    
		    
				click : function(e){
			
				    var optionNumber = parseInt(this.id.replace(this.parentNode.id.replace("menu","")+'option',''));	
				    var id = this.className.match(/optionfrom\w+/g)[0].replace('optionfrom','');

			
				if (menuShareEvent[optionNumber] && ! $('#'+id+'option'+optionNumber).hasClass("NotSharedAgain")) {
				    cdata={"room":my_session,"Menu":id,"optionNumber":optionNumber,"optionButton":menuIconClassAttributesTab_[optionNumber]};
				    socket.emit("click_Menu", cdata, callback=function(sdata){
 					console.log("socket send Menu ", cdata);				
				    });
				    return;
				}
				if(eventSelectedTab[optionNumber]==false)  { 	
				    if ( this.className.match(/disable/) == null ) {
					// Loop on menu items to leave currently selected one	
					if(only_one_option==true)  { 
					    var p = 0; 
					    
					    for(p=0;p<eventSelectedTab.length;p++)  { 
						if(p!=optionNumber && eventSelectedTab[p]==true)  { 
						    eventSelectedTab[p]=false;
						    menuEventTab[p](eventSelectedTab[p],id,p);	
						}
					    }
					} 
					eventSelectedTab[optionNumber]=true;
					//$('#menu'+id+'>#option'+optionNumber).css({backgroundColor : 'rgb(125,126,142)'});
					// Send reference to the options to allow users to change apparence if the default behavior is not convenient
					menuEventTab[optionNumber](eventSelectedTab[optionNumber],id,optionNumber);
					    
					// if(this.className.match(/(supermenu|NodeMenu|Tag|Rotate|OnOff|QRcode|Info|efresh)/g) != null || id < 999) { 
					//     // Regex to select "Info" and "NodeMenu" options; id<999 means: allow when nodeMenu is open
					//     EnableDragAndDrop();
					// } else {
					//     BlockDragAndDrop();
					// }
				    }
				} else { 
				    eventSelectedTab[optionNumber]=false;
				    menuEventTab[optionNumber](eventSelectedTab[optionNumber],id,optionNumber);	

				    EnableDragAndDrop();
				}
				//console.log(this.className, this.className.match("ranspa"), this.className.match("nfo"), _allowDragAndDrop);
			    }
			
			
			}); 
		
		}
		
		if (menubox_) {
		    var classes = myMenu.attr('class');
		    classes = 'ui-draggable  ' +classes;
		    myMenu.attr('class', classes);

		    //HandleDecalLeft=parseInt(HandleDecalLeft*1.5);

		    myMenu.append('<div id=MenuBox'+id+'></div>');
		    var MenuBox=$('#MenuBox'+id);
		    MenuBox.append('<div id=handleMenu'+id+' class=menu-handle-off ></div>');
		    if (orientation_ == "V")  {
			var MenuBoxWidth=width_;
			var MenuBoxHeight=HandleDecalTop;
		    } else { 
			var MenuBoxWidth=HandleDecalLeft;
			var MenuBoxHeight=height_;
		    }

		    MenuBox.css({
			    position :'absolute',
			    top : 0,
			    left : 0,
			    height : MenuBoxHeight,
			    width : MenuBoxWidth,
			    //backgroundColor : 'red'  ,
			    zIndex: 130,
			    //borderStyle : borderStyle_,
			    //borderWidth: borderWidth_,
			    //borderColor : borderColor_,
			    
			    });
		    var HandleMenu=$('#handleMenu'+id);
		    var HandleMenuDraggable=false;
		
		    HandleMenu.css({
			    position :'absolute',
			    top : 0,
			    left : 0,
			    height : HandleDecalTop,
			    width : HandleDecalLeft,
			    zIndex: 130,
			    });

		    if (touchok) {
			var draggingMenu = new Map();	// maps touch IDs to drag state objects
			touchstartMenuHandle = function (ev) {
			    for (var i = 0; i < ev.changedTouches.length; i++) {
				var touch = ev.changedTouches[i];
				var targetid=touch.target.id;
				if  (targetid.replace("handleMenu", "") == id ) {
				    var rect = {
					top: parseInt(myMenu.css('top').replace('px','')),
					left: parseInt(myMenu.css('left').replace('px','')),
				    };
				    HandleMenu.removeClass("menu-handle-off").addClass("menu-handle-on");
				    draggingMenu.set(touch.identifier, {
					    target: touch.target,
						top: rect.top,
						left: rect.left,
						prevX: touch.pageX,
						prevY: touch.pageY,
						});

				    //$('#'+targetid).css({'width': parseInt($('#'+targetid).css('width'))*2+'px','height': parseInt($('#'+targetid).css('height'))*2+'px'});
				    $('#'+targetid).css('-webkit-transform','scale(2)').css('-moz-transform','scale(2)');

				}
			    }
			    //ev.stopPropagation();
			};

			touchmoveMenuHandle = function (ev) {
			    for (var i = 0; i < ev.changedTouches.length; i++) {
				var touch = ev.changedTouches[i];
				var targetid=touch.target.id;
				var dragstate = draggingMenu.get(touch.identifier);
				if  (targetid.replace("handleMenu", "") == id  && dragstate) {
				    HandleMenu.removeClass("menu-handle-on").addClass("menu-handle-dragging");
				    dragstate.left += touchspeed*(touch.pageX - dragstate.prevX);
				    dragstate.top  += touchspeed*(touch.pageY - dragstate.prevY);
				    myMenu.css({left: dragstate.left+'px',
						top: dragstate.top+'px'});
				    dragstate.prevX = touch.pageX;
				    dragstate.prevY = touch.pageY;
				}
			    }
			    ev.preventDefault()
			};

			touchendMenuHandle = function (ev) {
			    for (var i = 0; i < ev.changedTouches.length; i++) {
				var touch = ev.changedTouches[i];
				var targetid=touch.target.id;
				if  (targetid.replace("handleMenu", "") == id ) {
				    draggingMenu.delete(touch.identifier);
				    HandleMenu.removeClass("menu-handle-on").removeClass("menu-handle-dragging").addClass("menu-handle-off");
				    $('#'+targetid).css('-webkit-transform','scale(1)').css('-moz-transform','scale(1)');
				}
			    }
			};

			HandleMenu.on({
				touchstart: touchstartMenuHandle,
				touchmove: touchmoveMenuHandle,
				touchend: touchendMenuHandle,
			    });

		    } else {
			var HandleLeave = function(e){
			    HandleMenu.removeClass("menu-handle-on").removeClass("menu-handle-dragging").addClass("menu-handle-off");
			    //e.stopPropagation(); 
			}
			var HandleEnter = function(e){
			    HandleMenu.removeClass("menu-handle-off").addClass("menu-handle-on");
			    
			    //e.stopPropagation(); 
			}
			
			HandleMenu.on({
			
				mouseleave : HandleLeave,
				
				mouseenter : HandleEnter,
				
				click : function(e){
				    if (HandleMenuDraggable) {
					HandleMenuDraggable=false;
					myMenu.draggable("destroy");
					HandleMenu.on("mouseenter",HandleEnter);
					HandleMenu.on("mouseleave",HandleLeave);
				    } else {
					HandleMenu.removeClass("menu-handle-on").addClass("menu-handle-dragging");
					myMenu.draggable();
					HandleMenu.off("mouseenter");
					HandleMenu.off("mouseleave");
					HandleMenuDraggable=true;
				    }
				}
			    });
		    }

		    MenuBox.append('<div id=dropdown ></div>');
		    var DropDown=$('#MenuBox'+id+'>#dropdown');
		    if (orientation_=='V') {
			DropDown.addClass("drop-down-menu");
			DropDown.css({
				position :'absolute',
				top : 0,
				width : width_-HandleDecalLeft,
				left : HandleDecalLeft,
				height : HandleDecalTop,
				zIndex: 130,
				});
 		    } else {
			DropDown.addClass("drop-right-menu");
			DropDown.css({
				position :'absolute',
				top : HandleDecalTop,
				width : HandleDecalLeft,
				left : 0,
				height : height_-HandleDecalTop,
				zIndex: 130,
				});
		    }
		    var DropDownState=true;
		    DropDown.on({

			    click : function(e){
				if (DropDownState) {
				    for(optionNumber=0;optionNumber<numOfEvents;optionNumber++)  { 	
					var Option=$('#'+id+'option'+optionNumber);
					Option.hide();
				    }
				    DropDownState=false;
				    if (orientation_=='V') {
					DropDown.removeClass("drop-down-menu").addClass("drop-left-menu");
				    } else {
					DropDown.removeClass("drop-right-menu").addClass("drop-down-menu");
				    }
				} else {
				    for(optionNumber=0;optionNumber<numOfEvents;optionNumber++)  { 	
					var Option=$('#'+id+'option'+optionNumber);
					Option.show();
				    }
				    DropDownState=true;
				    if (orientation_=='V') {
					DropDown.removeClass("drop-left-menu").addClass("drop-down-menu");
				    } else {
					DropDown.removeClass("drop-down-menu").addClass("drop-right-menu");
				    }
				}
			    }
			});
		}

		$('#menu'+id).on({ // Is this really useful ? To check, but it seems impossible to click on a menu, 
			// since the menu options are on it (higher z-index), and their event defined above, + all events only trigger "stopPropagation", ie "do nothing"
			// When commenting the whole thing, the menu behaviour doesn’t change
			
			mouseleave : function(e){
			    
			    e.stopPropagation(); 
			    
			},
			
			
			
			mouseenter : function(e){
			    
			    e.stopPropagation(); 
			    
			},
			
			
			dblclick : function(e){
			    
			    e.stopPropagation();
			},
			
			click : function(e){
			    
			    e.stopPropagation();
			}
		    
		    });
		
	    };

	    this.buildHtmlMenu();


	    this.getHtmlMenuSelector = function(){
		return '#menu'+id;
	    
	    };

	    this.closeAllOptions = function(){		
		var myMenu=$("#menu"+id);					
		for(optionNumber=0;optionNumber<numOfEvents;optionNumber++)  { 		
		    var tmp_class = $('#'+id+'option'+optionNumber).attr("class").match(/\w+ButtonIcon/g)[0];
		    var isNotClosed = tmp_class.match("close"); 
		    if (isNotClosed)  { 
			$('#'+id+'option'+optionNumber).click();
		    }
		}
	    };
	
	};

    })
