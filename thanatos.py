#!/bin/python
#thanatos.py
#The specific purpose of this program is to search for Fluent processes that shouldn't be running anymore and kill them. Turns out that it's not just Fluent that's causing this problem and it will really find any processes that don't have a SLURM job associated with them
#The broad way this actually works is by calling squeue with some switches that only give us the user and node they're running on and figuring out who has legitmate
#  jobs running. Once we know who's actually supposed to be running we then look at what nodes have
#  processes running by users who aren't supposed to have any processes running on that node and kill them. (The processes, not the users)
#
# Nicholas J Eggleston
# 04 May 2016
# Rev 1.1

import hostlist
import subprocess
import pwd

USER_ID_CONST = 0
NODE_CONST = 1
SYSTEM_RESERVED_UID_LIMIT = 500
NODE_DONT_CHECK = ["login-44-0", "login-44-1", "nic-p2"]
USERS_DONT_CHECK = ["USER", "root", "down", "68", "munge", "postfix", "dbus", "haldaemon", "nobody", "ntp", "rpc", "rpcuser"]
#REGEX = re.compile("([\w]+[-\d]{3,5})(\[[-\d,]+\]){0,1}") #We only needed this line before we found the 'hostlist' library. Now this is obsolete and really just here in case we need it again later

def main():
	currentlyRunningProcessesDict = {} #Blank dictionary for good times later.
	currentlyRunningJobsDict = {} #Another blank dictionary, also for good times even later

	#Now we need to find out who is running on what nodes
	#	 In one shot this gives us a list of all the nodes (which is semi dynamic) as well as the name of everyone that is listed to have running processes
	#  We need to do this step first because we don't want to have a process start before we collect data on who's supposed to be running, otherwise we'll kill
	#  legitimate processes...I think that makes English sense.
	whosRunningNow = subprocess.check_output(["rocks", "run", "host", "collate=true", "\"ps -e -o user | sort | uniq\""])
	nodesAndNames = whosRunningNow.split('\n')

	for line in nodesAndNames:
		if line != '': #For some reason the last element in nodesAndNames is just a blank, and it screws things up, hence this
			temp = line.split(':')
			node = temp[0].rstrip(': ') #Get rid of the colon and the space
			user = temp[1].strip().rstrip() #Get rid of any leading and trailing whitespace
			try:
				if pwd.getpwnam(user).pw_uid <= SYSTEM_RESERVED_UID_LIMIT: #If we run across some system account that I didn't catch and put in the array, add it and then don't go any further with that user
					USERS_DONT_CHECK.append(user)
					continue
			except KeyError: #Something screwy happened, we probably found a header. Don't care, carry on.
				continue
			
			if node not in NODE_DONT_CHECK:
				if user not in USERS_DONT_CHECK: #We don't want to know about those users, or the nodes they're associated with if they're the only users on that node
					if node not in currentlyRunningProcessesDict: #This is a node we've not yet encountered
						currentlyRunningProcessesDict[node] = [user]
					else:
						if user not in currentlyRunningProcessesDict[node]: #We don't want duplicates of the username in this dictionary
							currentlyRunningProcessesDict[node].append(user)

	#In this section we figure out who has legitimate cause to be running on what nodes by having the scheduler tell us what it's allowed to run and where
	#Now we're against the clock, since jobs start and stop all the time, we need the most accurate list of who's running and where we can get so we don't cancel processes we shouldn't be cancelling
	cleanupscript = open('cleanupscript.sh', 'w')
	biglist = subprocess.check_output(["squeue", "-h", "-o", "%u:%N"]) #calling squeue with these flags gets you of an output of username:nodename where that user currently has a job running on that node

	splitlist = biglist.split('\n')

	for item in splitlist: 
		if item != '': #The output of squeue ends with a newline, making the last element equal to '', this is aggrivating but this is how we deal with it
			smalllist = item.split(':')
			userId = smalllist[USER_ID_CONST]
			nodelist =  smalllist[NODE_CONST]
			if userId != '' and nodelist != '': #If a job is in queue but not running, it has no node assigned, this is where we deal with that
				#The hostlist package is brought in because squeue gives us goofy crap like aleksandr-43-[15-16,18],edrcompute-43-1,grethor-20-[8,11] and we need to translate all that each into its own nodename
				for derp in hostlist.expand_hostlist(nodelist): #Yes, I made a variable named 'derp', you'll have to deal with it
					if derp not in currentlyRunningJobsDict: #This is a node we've not yet encountered
						currentlyRunningJobsDict[derp] = [userId]
					else:
						if userId not in currentlyRunningJobsDict[derp]: #We don't want duplicates of the username in this dictionary
							currentlyRunningJobsDict[derp].append(userId)

	#And here is the grand finale!
	#  Here we compare the list of who is running processes on the node, to who is actually supposed to be running a job
	for node in currentlyRunningProcessesDict:
		for user in currentlyRunningProcessesDict[node]:
			try:
				if user not in currentlyRunningJobsDict[node]:
					cleanupscript.write("ssh " + node + " \"pkill -9 -u " + user + "\"\n")
			except KeyError: #Basically what has happened here is the user has a node allocated to them, but they're currently not running processes on it, since that's legit we'll just ignore it
				#cleanupscript.write("Error with: " + node + "\n") #This is now in comments because BASH wants to execute it as a command and clearly that's not possible. Once we get better logging in place we can reenable this
				continue

	cleanupscript.write("rm -f cleanupscript.sh\n")
	cleanupscript.close()


if __name__ == "__main__":
	main()

