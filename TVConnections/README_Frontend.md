TVConnection is launched from tvconnections.sh in connection docker to manage password to Frontend of HPC machine.

It creates VNC secure flux with TVSecure in secure host
and a communication socket with the client browser through Flask server with action.json list of actions.

It launchs the script job.

Generic functions for all cases :
"tileNum" is the number of a tile in a TileSet and "tileId" is a string for its Id given by containerId(tileNum+1).

* Get_client_IP: return the IP of a client 
* tunnel : launch /opt/tunnel_ssh for activating the secure tunnel of VNC stream.
* vnc : launch the vnc server with /opt/vnccommand script.
* init_wmctrl : call a global wmctrl call to list all windows in the tile.
* clear_VNC : send clear-all command to the vnc server if it appears problems with keyboard interaction.
* changeSize : change tile resolution.
* fullscreenThisApp : toggle fullscreen option for a window.
* showThisGUI : toggle above a window.
* clickPoint : send a click event on a given position.

* kill_all_containers : this function must be defined in all case script for killing all containers.

Action sur les conteneurs :
grabwin
kill_ssh
launch_command
launch_dockers
launch_tunnels
launch_vncviewer
launch_Wall
launch_x11vnc
replace_init_window
rescale_docker
stop_dockers

Client-serveur VMD :
analyse_newNoeuds.py
UDP_2_multi_TCP.py

Actions globales : 
build_mageia_git
build_WebRTC_git
all_dockers_images
all_dockers_ps
all_dockers_rm
all_dockers_stop
all_services_docker_restart
mydocker-join
mydocker-swarm
stop_all_dockers
clear_images

On GPU computation nodes :
* All informations on GPU devices on the node
nvidia-smi
or mode detailed
nvidia-smi -q
* with ls hardware you can search "3D controller" :
lshw -xml

* we need to create /dev/nvidia# with # in GPUlist=[0-4] for example
for gpu in GPUlist; do
    nvidia-modprobe --create-nvidia-device-file=$gpu
done
#mknod /dev/nvidia0 c 195 0
mknod /dev/nvidiactl c 195 255
mknod /dev/nvidia-uvm c 241 0
mknod /dev/nvidia-uvm-tools c 241 1
mknod /dev/nvidia-modset c 195 254
chmod 666 /dev/nvidiactl /dev/nvidia-uvm /dev/nvidia-uvm-tools /dev/nvidia-modset

Docker with Swarm :
Must install docker on each node, build and copy mageainvidia (for example) image on
each node (or pull a Xvnc system from a hub).

Build mageia docker (used in TiledTest scripts) for example.
* Copy some authorized keys to your frontend in TVConnections/mageianvidia/ssh (to make secure tunneling of vnc stream) 
* Build container :
  docker build -t mageianvidia -f TVConnections/mageianvidia/Dockerfile .
  
Singularity :
Change rights with X launch on nodes
/etc/pam.d/xserver
 #auth       required  pam_console.so
 auth       sufficient pam_permit.so
 account    sufficient pam_permit.so
because of the creation of /tmp/.X#-lock lock file and /tmp/.X11-unix/X# socket on
the host for nvidia acceleration inside the container.

On the forwarding frontend
 if you use OpenSSH sshd server, the server's GatewayPorts option needs to be enabled.
