$(document).ready(    function (){
    
	setColorTheme = function(colorTheme)  { 
	    if (colorTheme == "light")  { 
		$('#options').css({
			backgroundColor : "white",
			color : "black"
		    });

		$('#buttonSave').css({
			backgroundColor : "lightgray",
			    color : "black"
			    });

		var cssThemeLink = document.createElement("link");
		cssThemeLink.href = "doc/doc_style_light.css";
		cssThemeLink.rel = "stylesheet";
		cssThemeLink.type = "text/css";


	    }
	    else if (colorTheme == "dark")  { 
		$('#options').css({
			backgroundColor : "black",
			color : "white"
		    });
		$('#buttonSave').css({
			backgroundColor : "darkgray",
			    color : "lightgray"
			    });
	    }

	    var temp = $('#helpframe').attr("src");
	    $('#helpframe').attr("src", "").attr("src", temp); // To reload the help iframe

	    $('#helpframe').on('load', (    function(){
			$('#helpframe').contents().find("head").append($('<link rel="stylesheet" href="./doc_style_'+colorTheme+'.css">'));
		    }));
	    //document.getElementById("helpframe").reload();
	};
    })
