# thanatos
Python script to fix errant processes running on a ROCKS/SLURM cluster

Thanatos is the Greek god of death. I thought that fitting name since we are searching for processes that should have been killed a long time ago and really probably need to die

This script works by calling a few ROCKS builtin commands to find which users are running processes on which nodes in the cluster. We exclude all management nodes. At Missouri S&T (my home institution) we have two login nodes and one head node. We then check to see which users have jobs started in SLURM and which nodes have been allocated to those jobs. 

The model for how to kill processes that don’t belong is based on the Ansys Fluent cleanup script (which is really a terrible way for Ansys to have coded their method of killing processes, but it works quite well here). Basically if we find a user who has processes running on a compute node but does not have a corresponding job in SLURM, we ssh to that node and kill all processes associated with the UID. 

Provisions are made for system accounts, obviously root and postfix aren’t going to be running a cluster job, but they will still have processes running and they need to stay running for Linux to do its job. We start with a base list of all the system type accounts I could find with a quick `ps aux` but since the UID of all system accounts is 500 or under, if I find a UID running a process under 500, I add it’s name to the list of users to ignore and then don’t kill it’s process. 

=== WHAT YOU ACTUALLY WANT TO KNOW ===

-Dependences-
python 2.7, 
python hostlist, 
ROCKS Cluster, 
SLURM 15 (or greater) Scheduler and Resource Manager (may work with older SLURM but not tested)

-How to run-
Create a bash script that runs thanatos.py. Modify it to do whatever logging you would like, we just copy the cleanup script that is created to a separate log file if it’s larger than one line (the line that deletes the cleanup script). Place this script in a CRON job. Watch your cluster run much smoother because it’s not wasting resources running processes that should have died long ago. Yes folks, it’s that simple.

-Notes-
Every so often ROCKS will have a blip where it can’t ssh properly into a node to tell me what processes are running on it. This will cause CRON/BASH to freak out a little but has never ended processes that it shouldn’t. Since this isn’t doing anything other than notifying me that it couldn’t run that line, I haven’t tried to fix that bug, but if it bothers you and you’d like to modify my code, send me a pull request and I’ll release it to the wild. 

Obviously this is free software, and you get what you pay for. I make no claim that it won’t harm your cluster, but it’s been running great on the Missouri S&T Forge cluster for a good long while now (over a month as of writing this README, thats nearly 1000 runs of this program) and nothing has broken. Also this being free software, that means I’m not charging you for it. If you’d like to use it I’m cool with that, but if you modify it let me know. If it’s a cool mod I’d like to add it to my code. If you like what you see, hit me up at nickegg1018@gmail.com. I feel like I’m a pretty decent cluster admin and I’m always looking for new and exciting roles to fill. Thanks! 
