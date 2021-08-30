TiledViz is designed to be a client-server version of TileViz, our small-multiple and
generic data visualisation tool.

With TiledViz, you can use secure connection to watch remote VNC stream from
computing machine with TiledViz.

On host, the job is TiledViz Secure (TVSecure.py).
Flask is running inside TVSecure then you don't need to run its docker container
mannually.

After reading INSTALL doc and running install.sh script, you can run launch_TiledViz
script run this TVSecure tool.


You must download TiledViz also on your HPC machine in order to build HPC
visualization dockers.
You have some examples with Mageia7 and Ubuntu 18.04 in TVConnection directory.
You may want GPU acceleration inside this container then GLX extension is required.
Take care of x11-driver-video-nvidia390 or x11-driver-vidio-nvidia-current package to
be able to use you Nvidia GPU already installed in the shared kernel of the HPC node. 
You can try TiledTest CASE with glxgears to test GLX extension.

Those HPC containers musn't be shared between users because it will contain your own id_rsa key.
You can put your rsa ssh public key in ${HOME}/.ssh/authorized_key for redirection of
VNC stream on your frontend with good rights.

This represent a security breach because docker containers will be shared on HPC machine between users.
For a more robust chain, you can ask root for http frontend machine to create a generic account and
get a ssh key to export VNC stream through ssh to this generic account.
See also step 10 for the configuration of this host.

Thoses containers are launched (in test_job.py for example) on the HPC machine.
You may use TVConnections/Swarm/launch_dockers script.


For TiledViz client browser, best usage comes with a scale factor at 0.25 to watch all
tiles in a full view.

You can adjust list of scale factor with google-chrome using dev tools on page
chrome://settings/?search=zoom
Inspect page zoom chooser element with Developper tool.
Look at zoomLevel list and copy/paste on element. Then change the value and print.
It will be saved in ".config/google-chrome/default/Current Session" binary file.

On Mozilla Firefox you just have to go on  about:config
and get the list 
toolkit.zoomManager.zoomValues


7. Use debug option in web Connection form.

If you want to build your own TiledViz cases, you may read
TVConnection/TVConnections.py
because it contains initialization and functions for calling in case job. 

This debug option may stop the connection script before you launch your own job then
you can test it manualy.

You may use os.system('/cat_between #Line1 #Line2 file.py') to display and copy/paste
parts of your script in the ipython prompt.

You can either have python sources of your functions already loaded with this command
print(inspect.getsource(myfun))
on ipython prompt.
