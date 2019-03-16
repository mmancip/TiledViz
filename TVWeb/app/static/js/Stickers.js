/** Here is define the stickers used to mark the node after a research/applciations of a filter
    ->id of the node concerned 
    ->htmltag of this node $("#node"+id)*/
$(document).ready(    function (){
    ColorSticker = function(k) {
	if (k<colorTagStickersTab.length)  { 
	    return colorTagStickersTab[k];
	}
	else if (k<(colorTagStickersTab.length + colorFilterStickersTab.length))  { 
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
	    
	    this.updateStickers = function()  { 
		//console.log("updating stickers");
		$('#stickers_'+id).children(".sticker").remove();
		var it = 0;
		while (it < stickerTab.length)  { 
		    var text_ = stickerTab[it][0];
		    var color = stickerTab[it][1];
		    //console.log(text_, color);

		    var thisSticker = $('#stickers_'+id).children(".sticker")[it];
		    
		    $('#stickers_'+id).append("<div id='" +text_ + "_" + id +"' class='"+text_+ " sticker'" + "></div>");
		    $('#'+ text_ + "_" +id).css({
			    classN : "sticker",
				backgroundColor : color,
				top : 50*it+"px",		
		    }).off("click").on({
			click : clickSticker
		    });
		    it++;
		}
	    }	

	    /* addSticker tests if the sticker is already present, if not, add it to the stickerTab and updates the stickers to make the new one appear */

	    this.addSticker = function(text_, color)  { 
		var found =0;
		for (var i=0;i<stickerTab.length;i++)  { 
			
		    if (stickerTab[i][0]==text_ && stickerTab[i][1] == color)  { 
			found = 1;		
			break;
		    }
		}
		if (found==0)  { 
		    stickerTab.push([text_, color]);
		}
		this.updateStickers();
	    }

	    this.removeSticker = function(text_)  { 
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
		this.updateStickers();	
	    }

	    this.createSticker = function(text_, color)  { 
		if($('#stickers_'+id).children("."+text_).length == 0)  { 			
		    $('#stickers_'+id).append("<div id='" + text_ + "_" + id +"' class='"+text_+ " sticker'" + "></div>");
		    //console.log($('#stickers_'+id).children(".sticker").length, numOfTags);
		    $('#'+ text_ + "_" +id).css({
			    classN : "sticker",
				backgroundColor : color,
				top : 50*($('#stickers_'+id).children(".sticker").length-1)+"px",
				});
		} else { 
		    //console.log("Sticker already exists");
		}

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
