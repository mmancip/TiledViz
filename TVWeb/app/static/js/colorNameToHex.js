function getHexColor(colorStr) {
    var a = document.createElement('div');
    a.style.color = colorStr;
    var colors = window.getComputedStyle( document.body.appendChild(a) ).color.match(/\d+/g).map(function(a){ return parseInt(a,10); });
    document.body.removeChild(a);
    return (colors.length >= 3) ? '#' + (((1 << 24) + (colors[0] << 16) + (colors[1] << 8) + colors[2]).toString(16).substr(1)) : false;
}


function getRGBColor (colorStr) {
    var colorHex=getHexColor(colorStr);
    return [parseInt(colorHex.slice(1,3),16),
	    parseInt(colorHex.slice(3,5),16),
	    parseInt(colorHex.slice(5,7),16)]
}

function colourNameToHex(colorStr)
{
    return getHexColor(colorStr)
}

function InterpolColor(m,val,M,cm,cM) {
    var s =  ( val - m ) / (M - m);
    var cval = [ parseInt(s * ( cM[0] - cm[0] ) + cm[0]),
		 parseInt(s * ( cM[1] - cm[1] ) + cm[1]),
		 parseInt(s * ( cM[2] - cm[2] ) + cm[2]) ];
    return cval
}

