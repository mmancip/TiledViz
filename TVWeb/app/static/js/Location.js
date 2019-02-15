$(document).ready(    function (){
	/** This function provides an unique ID to each node created
	 */
	nodeIdProvider = (    function() {

		var i = -1;

		return function(){
		    i++;
		    return i;
		};
	    })();

	/** This object will help us to manage node coordinates
	    The equivalence between node coordinates as an JS obect and html convention : 
	    X <-> Left 
	    Y <-> Top
	    ------------> X
	    |
	    |
	    |
	    |
	    V
	    Y
	*/
	Location = function(x,y) {

	    (    function(){

		if(x==undefined)
		    x=0;
		if(y==undefined)
		    y=0
			})();

	    var X = x;
	    var Y = y;

	    this.getX = function(){

		return X;
	    }

	    this.getY = function(){

		return Y;
	    }

	    this.getXY = function(){

		return [X,Y];
	    }

	    this.setX = function(x){

		X=x;
	    }

	    this.setY = function(y){

		Y=y;
	    }

	    this.setXY = function(x,y){

		setX(x);
		setY(y);
	    }

	}

	/** This object will help us to manage node coordinates
	    MLocation give the location of an node on the mesh 
	    So the coordinates are integer only
	    (0,0)-(1,0)-(2,0)-...
	    (0,1)-(1,1)-(2,1)-...
	    (0,2)-(1,2)-(2,2)-...
	*/
	MLocation = function(nx,ny) {	


	    (    function(){

		if(nx==undefined)
		    nx=0;
		if(ny==undefined)
		    ny=0
			})();

	    var nX = nx;
	    var nY = ny;

	    this.getnX = function(){

		return nX;
	    }

	    this.getnY = function(){

		return nY;
	    }

	    this.getnXY = function(){

		return [nX,nY];
	    }

	    setnX = function(nx){

		nX=nx;
	    }

	    setnY = function(ny){

		nY=ny;

	    }

	    setnXY = function(nx,ny){

		setX(nx);
		setY(ny);
	    }




	    };
    })
