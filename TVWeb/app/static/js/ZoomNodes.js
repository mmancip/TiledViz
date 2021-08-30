/** Here is define the zoom on each node used to fast zoom on a node
 */
$(document).ready(    function (){
     zoomNodes = function(id)  { 
	 $('#'+id).append("<div id=zoomNode"+ id +" scrolling = 'no' class='zoomNodeButtonIcon'></div>");

	 var zoomNodediv=$('#zoomNode'+id);
	    
	 zoomNodediv.css({
		 position : "absolute",
		     top : parseInt($('#'+id).css("height"))-50,
		     left : parseInt($('#'+id).css("width"))-50,
		     width : 105,
		     height : 105,
		     padding: 5,
		     zIndex : 112,
		     });
	    
	 zoomNodediv.hide();
     };
    })
