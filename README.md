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
