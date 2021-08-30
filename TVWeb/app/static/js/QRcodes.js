
/** Here is define the QR used to get URI of the inner source of the node with an external device
    ->id of the node concerned 
*/
$(document).ready(    function (){
        QRcodes = function(id,jsonData)  { 
	    $('#'+id).append("<div id=qrcode"+ id +" class='qrcode'></div>");

	    var qrcodeZoom = false;
	    this.getZoom = function() {
		return qrcodeZoom;
	    }
	    this.setZoom = function(newZoom) {
		qrcodeZoom=newZoom;
	    }

	    var qrcodediv=$('#qrcode'+id);
	    
	    qrcodediv.css({
		    position : "absolute",
			top : parseInt($('#'+id).css("height"))-50,
			left : parseInt($('#'+id).css("width"))-50,
			width : 130,
			height : 130,
			zIndex : 111,
		
			});

	    nodeUrl=jsonData.url;
	    if(nodeUrl!='undefined') {
		var qrcodeimg = new QRCode(document.getElementById("qrcode"+id), {
		    id:"iqrcode"+id,
		    text: nodeUrl,
		    width:qrcodediv[0].clientWidth,
		    height:qrcodediv[0].clientHeight,
		    colorDark : "#000000",
		    colorLight : "#ffffff",
		    correctLevel : QRCode.CorrectLevel.H
		});
	    } else {
		qrcodediv.append('<div id="iqrcode'+id+'>No Qrcode</div>');
		var qrcodeimg=$('#iqrcode'+id);
	    }
	    
	    qrcodediv.append("<div id=qqrcode"+ id +" ></div>");
	    $('#qqrcode'+id).css({
		    position : "relative",
			top : -parseInt(qrcodediv.css("height"))*1.05,
			left : 0,
			width : parseInt(qrcodediv.css("width")),
			height : parseInt(qrcodediv.css("height")),
			zIndex : 112,
		
			});
	    
	    $('#qrcode'+id).hide();

	};


})
