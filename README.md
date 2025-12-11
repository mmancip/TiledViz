TiledViz is designed to be a client-server for small-multiple and generic data visualisation tool.

With TiledViz, you can use secure connection to watch remote VNC streams from
computing machine and metadata for each element of ensemble from a database.

On host, the job is TiledViz Secure (TVSecure.py). It is a secured scheduler of web micro-services.
Flask is running inside TVSecure then you don't need to run its docker container
mannually.

After reading INSTALL doc and running install.sh script, you can run launch_TiledViz
script run this TVSecure tool.


You must download TiledViz also on your HPC machine in order to build HPC
visualization dockers.
You have some examples with Mageia8 and Ubuntu 18.04 in TVConnection directory.
You may want GPU acceleration inside this container then GLX extension is required.
If you want to use your own client container, take care of x11-driver-vidio-nvidia-current package to
be able to use you Nvidia GPU already installed in the shared kernel of the HPC node. 
You can try TiledTest CASE with glxgears to test GLX extension.
One can use Singularity client containers as well whith tools in Singularity directory.

Thoses containers are launched (in test_job.py for example) on the HPC machine.
You may use TVConnections/Swarm/launch_dockers script.

Using docker on HPC machine represent a security breach because one user with docker rights can escaladate to root.

With a new connection a special ssh id is created and propagated to user chain of frontends and use in HPC containers to exchange secured data and RPC (VNC) streams to be share by other invited users in the secured web session.

For TiledViz client browser, best usage comes with a scale factor at 0.25 to watch all
tiles in a full view of the visualization grid.

You can adjust list of scale factor with google-chrome using dev tools on page
chrome://settings/?search=zoom
Inspect page zoom chooser element with Developper tool.
Look at zoomLevel list and copy/paste on element. Then change the value and print.
It will be saved in ".config/google-chrome/default/Current Session" binary file.

On Mozilla Firefox you just have to go on  about:config
and get the list 
toolkit.zoomManager.zoomValues


1. Use debug option in web Connection form.

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

2. Problems on some OS

Some gvfs versions gives full memory with Connections docker and
udisks2-volume-monitor service. You can deactivate this behaviour with 
> systemctl --user stop gvfs-udisks2-volume-monitor.service
> systemctl --user mask gvfs-udisks2-volume-monitor.service

Some new Dockerd version limit system in containers.
This blocks connections to x11vnc server for TVConnection client.
One must change /etc/docker/daemon.json by added
```
    "default-ulimits": {
       "nofile": {
          "Hard": 1048576,
          "Name": "nofile",
          "Soft": 1048576
        }
    }
```

3. SSL and server deployment

Give SERVER_NAME.DOMAIN web server string available in a DNS service.  
Give SSL public then private available keys complete path in server at install stage in a readable directory.
Thoses variables are asked in the installation step on a web server.

4. Logger

Change level (from WARNING to DEBUG) interactively :
> docker exec -u flaskusr -it flaskdock bash -c 'echo DEBUG > /tmp/logfifo'

Size of server log:
> docker inspect --format='{{.LogPath}}' flaskdock | xargs sudo du -sh

5. ssh version
Switch to ed25519.

As per the release notes for OpenSSH 7.6:

Refuse RSA keys <1024 bits in length and improve reporting for keys that do not meet this requirement.

So it's likely that the key you're trying to import is too short (weak). Your best bet is to generate a new key.
