/** Here is define the stickers used to mark the node after a research/applciations of a filter
    ->id of the node concerned 
    ->htmltag of this node $("#node"+id)*/
$(document).ready(    function (){

    ListSymbols=["&#x2295","&#x2296","&#x2297","&#x2298","&#x2299","&#x229a","&#x229b","&#x229c","&#x229d",
		 "&#x2460","&#x2460","&#x2461","&#x2462","&#x2463","&#x2464","&#x2465","&#x2466","&#x2467","&#x2468","&#x2469",
		 "&#x2660","&#x2660","&#x2661","&#x2662","&#x2663","&#x2664","&#x2665","&#x2666","&#x2667"]

    rgbFromStr =  function (rgbStr) {
	return Array.from(rgbStr.replace("rgb(","").replace(")","").split(','), x => parseInt(x))
    }
    
    ColorSticker = function(k, floatingTag) {
	if ( typeof(floatingTag) != "undefined" ) {
	    var val=parseFloat(floatingTag["val"]);
	    var m = parseFloat(floatingTag["m"]);
	    var M = parseFloat(floatingTag["M"]);
	    if ( k < ListSymbols.length ) {
		var symb=ListSymbols[k]
	    } else {
		var symb=""
	    }
	    
	    if ( k<colorTagStickersTab.length-1 )  {
		var cm=getRGBColor(colorTagStickersTab[k]);
		var cM=getRGBColor(colorTagStickersTab[colorTagStickersTab.length-k+1]);
		
		cval=InterpolColor(m,val,M,cm,cM)
	    } else if (k<(colorTagStickersTab.length + colorFilterStickersTab.length - 1 ))  {
		var cm=getRGBColor(colorFilterStickersTab[k   -colorTagStickersTab.length]);
		var cM=getRGBColor(colorFilterStickersTab[colorTagStickersTab.length + colorFilterStickersTab.length - k+1]);
		
		cval=InterpolColor(m,val,M,cm,cM)
	    }
	    return {"cm":"rgb("+cm[0]+","+cm[1]+","+cm[2]+")",
		    "cval":"rgb("+cval[0]+","+cval[1]+","+cval[2]+")",
		    "cM":"rgb("+cM[0]+","+cM[1]+","+cM[2]+")",
		    "symb": symb}
	} else if (k<colorTagStickersTab.length)  { 
	    return colorTagStickersTab[k];
	} else if (k<(colorTagStickersTab.length + colorFilterStickersTab.length))  { 
	    return colorFilterStickersTab[k-colorTagStickersTab.length];
	} else { 
	    return "rgb("+Math.floor(Math.random()*255) + ", " + Math.floor(Math.random()*255)+ ", " + Math.floor(Math.random()*255)+")";
	}
    };

    newTag_conformance = function(tmpNewTag) {
	tmpNewTag = tmpNewTag.replace(/\s[+]\s/g, "_and_");
	var forbiddenCharacters = ["'", "(", ")", " + ", " ", ".", ",", '"', "@", "+", "/", "*", "=", "%", ":", "__"]; // TO DO: create a function, to also use with the filters?
	var replacementCharacters = ["", "", "", "_and_","_", "_", "_", "", "_at_", "_", "_", "_", "_", "_", "", "_"];

	for(var i=0; i<forbiddenCharacters.length; i++)  { 
	    while($.inArray(forbiddenCharacters[i], tmpNewTag)!=-1)  { 
		tmpNewTag = tmpNewTag.replace(forbiddenCharacters[i],replacementCharacters[i]);
	    }
	}
	tmpNewTag = tmpNewTag.replace(/_+$/g, ""); // Trailing underscores
	tmpNewTag = tmpNewTag.replace(/_+/g, "_"); // Multiple underscores
	return tmpNewTag;
    };    
    
	Stickers = function(id, htmlSupport)  { 
	
	    var numOfTags = 0;
	    var nodeId=id;
	    
	    $('#'+id).append("<div id=stickers_"+ id +" class=stickers_zone></div>");

	    $('#stickers_'+id).css({
		    position : "absolute",
			//position : "fixed",
			top : 0,
			left : parseInt($('#'+id).css("width")),
			width : 50,
			height : parseInt($('#'+id).css("height")),
			zIndex : 110,

			});

	    getStickers = function()  { 
		return this;
	    }

	    this.getNodeId = function() { 
		return nodeId;
	    }

	    var stickerTab = [];
	    this.getStickerTab = function()  {
		return stickerTab.toString();
	    }
	    this.resetStickerTab = function()  {
		$('#stickers_'+id).children(".sticker").remove();
		return stickerTab = [];
	    }
	    
	    this.updateStickers = function(reset)  {
		if (typeof(reset) != "undefined")
		    $('#stickers_'+id).children(".sticker").remove();
		    
		//console.log("updating stickers");
		var it = $('#stickers_'+id).children(".sticker").length;
		while (it < stickerTab.length)  {
		    var thisstickerTab=stickerTab[it];
		    
		    var text_ = thisstickerTab[0];
		    var color = thisstickerTab[1];
		    //console.log(text_, color);

		    var idSticker = text_ + "_" + id;

		    $('#stickers_'+id).append("<div id='" +idSticker +"' title='"+text_ +"' class='"+text_+ " sticker' " + "name='"+idSticker+"_"+it+"' ></div>");
		    $('#'+idSticker).css({
			classN : "sticker",
			backgroundColor : color,
			top : 50*it+"px",		
		    });
		    $('#stickers_'+id).on('mouseover',function() {
			if (configBehaviour.tooltip) {
		    	    $(this).append('<div id=tooltip class="tooltipfrom'+id
		    			   +' fg-tooltip ui-widget ui-widget-content ui-corner-all" style="font-size: 40px"></div>');
		    	    var tooltip=$('#tooltip');
		    	    tooltip.html($(this).attr("title"));
			    $(this).attr("title","");
		    	    tooltip.append('<div class="fg-tooltip-pointer-down ui-widget-content"><div class="fg-tooltip-pointer-down-inner"></div></div></div>');
			    tooltip.css("top","-180px");
			    
		    	    tooltip.fadeIn('500');
		    	    tooltip.fadeTo('10',10);
			}
		    }).on('mouseout',function() {
			if (configBehaviour.tooltip) {
			    $(this).attr("title",$(this).children('div#tooltip').text());
		    	    $(this).children('div#tooltip').remove();
			}
		    })

		    if ( thisstickerTab.length > 2 ) {

			$('#'+idSticker).html(thisstickerTab[2]);
			var val=thisstickerTab[5];
			$('#'+idSticker).attr('title',val);
			
			$('#'+idSticker).on({
			    mouseenter: function() {
				var idSticker=this.id;
				var id=idSticker.replace(/.*_(\D*)/,"$1");
				var it=$('#'+idSticker).attr("name").replace(/.*_(\D*)/,"$1");
				var thisstickerTab=stickerTab[it];
				var color = thisstickerTab[1];
				var cval=rgbFromStr(color);
				var cm=thisstickerTab[3];
				var cM=thisstickerTab[4];
				// $('#'+idSticker).removeClass("sticker");
				var stickerscale=2;
				$('#'+idSticker).css({
				    width : 100,
				    zIndex : 999,
				    background : 'linear-gradient(to right,'+cm+','+cM+')' 
				});
				$('#'+idSticker).css('-webkit-transform','scale('+stickerscale+')').css('-moz-transform','scale('+stickerscale+')');
				$('#'+idSticker).append("<div id='stick"+idSticker+"' style='color:white' >|</div>");
				cm=rgbFromStr(cm);
				cM=rgbFromStr(cM);
				var s=0;
				var n=0;
				if (cM[0] - cm[0] != 0) {
				    s= s+(cval[0] -cm[0]) / (cM[0] - cm[0]);
				    n=n+1;
				}
				if (cM[1] - cm[1] != 0) {
				    s= s+(cval[1] -cm[1]) / (cM[1] - cm[1]);
				    n=n+1;
				}
				if (cM[2] - cm[2] != 0) {
				    s= s+(cval[2] -cm[2]) / (cM[2] - cm[2]);
				    n=n+1;
				}
				s=s/n * parseInt($('#'+idSticker).css("width"))
				$('#stick'+idSticker).css({
				    position: "absolute",
				    top :-10,
				    left : parseInt(s)
				})
			    },
				
			    mouseleave: function() {
				var idSticker=this.id;
				var id=idSticker.replace(/.*_(\D*)/,"$1");
				var it=$('#'+idSticker).attr("name").replace(/.*_(\D*)/,"$1");
				var thisstickerTab=stickerTab[it];
			    	var color = thisstickerTab[1];
				$('#'+idSticker).css('-webkit-transform','scale('+1.+')').css('-moz-transform','scale('+1.+')');
				$('#'+idSticker).css({
				    width : 50,
			    	    background : color
				});
			    	$('#'+idSticker).children().remove();
			    }
			});
		    }
		    
		    $('#'+idSticker).off("click").on({
			click : clickSticker
		    });
		    it++;
		}
	    }	

	    /* addSticker tests if the sticker is already present, if not, add it to the stickerTab and updates the stickers to make the new one appear */

	    this.addSticker = function(text_, color, updateAll, outColors, val)  { 
		var found =0;
		for (var i=0;i<stickerTab.length;i++)  { 
			
		    if (stickerTab[i][0]==text_ && stickerTab[i][1] == color)  { 
			found = 1;		
			break;
		    }
		}
		if (found==0)  {
		    if (typeof(outColors) != "undefined") {
			stickerTab.push([text_, outColors["cval"], outColors["symb"], outColors["cm"], outColors["cM"], val]);
		    } else {
			stickerTab.push([text_, color]);
		    }
		}
		if (updateAll)
		    this.updateStickers(true);
	    }

	    this.removeSticker = function(text_,updateAll)  { 
		var color = attributedTagsColorsArray[text_];
		var found = false;
		var index = -1;
		for (var i=0;i<stickerTab.length;i++)  { 
			
		    if (stickerTab[i][0]==text_ && stickerTab[i][1] == color)  { 
			found = true;		
			index = i;
			break;
		    }
		}
		if (found)  { 
		    stickerTab.splice(index, 1);
		}
		if (updateAll)
		    this.updateStickers(true);
	    }

	    this.colorSticker = function(text_, color)  { 
		if($('#stickers_'+id).children("."+text_).length != 0)  { 				
		    var it = 0;
		    while (it < stickerTab.length)  { 
			if ( text_ == stickerTab[it][0] ) {
			    stickerTab[it][1] = color;
			    break;
			}
			it++;
		    }
		    
		    $('#'+ text_ + "_" +id).css({
			backgroundColor : color,
		    });
		}
	    }
	}
    })
