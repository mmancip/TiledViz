/** Here is define the stickers used to mark the node after a research/applciations of a filter
    ->id of the node concerned 
    ->htmltag of this node $("#node"+id)*/
$(document).ready(    function (){
	Stickers = function(id, htmlSupport)  { 
	
	    var numOfTags = 0;
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

	    var stickerTab = [];
	    this.updateStickers = function()  { 
		//console.log("updating stickers");
		$('#stickers_'+id).children(".sticker").remove();
		for (var it = 0;it<stickerTab.length;it++)  { 
			
		    var text_ = stickerTab[it][0];
		    var color = stickerTab[it][1];
		    //console.log(text_, color);
		    $('#stickers_'+id).append("<div id='" +text_ + "_" + id +"' class='"+text_+ " sticker'" + "></div>");
		    $('#'+ text_ + "_" +id).css({
			    classN : "sticker",
				backgroundColor : color,
				top : 50*it+"px",		
				});
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
	}
    })
