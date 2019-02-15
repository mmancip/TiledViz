TVWeb is the web interface for TiledWiz.




# Structure

```

app/
	static/
		dist/ # Bootstrap, jQuery, other frameworks files (css, js)
			css/
			js/
			webfonts/ # To use with fontawesome (css in ../css)
		css/ # My CSS files
		js/ # My JS files
		images/
			icons/
		favicon.ico # To be displayed
	templates/
		base.html # Imports (js/css) + block "additional scripts"
		base_simple.html # Classic page
		base_forms.html # Page suited for forms templates
		base_grid.html # Page with menu on the left, legend space at the top, grid space in the middle
		main.html # Filling
		grid.html # Filling
	__init__.py # SocketIO(app, host) is *here*
	forms.py # Implementation of various forms to be later embedded (as imports)
	routes.py # Routes, template rendering, event processing (socketio)
	models.py # Data models (ie database content management)
tvweb.py # Only imports app (no code here), main file in regard to variable definition: export FLASK_APP=tvweb.py
config.py # Non-critical parameters (critical ones should never be written in this repo)
requirements.txt # Packages listed to be installed through pip on the web server
```

# Conventions
## Naming
Socket.io communications:
* Server-side: data received from the client will be named `cdata`, data sent to the client will be named `sdata`
* Client-side: data received from the server will be named `sdata`, data sent to the server will be named `cdata`
