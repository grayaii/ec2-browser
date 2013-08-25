## ec2-browser ##


This is a python script that allows you to browse, connect, search, terminate your ec2 instances across multiple accounts.

### How to Use ###
You can either run it with python or with pythonw (if you run it with python, you'll see all the print statements, which can be helpful in debugging):
    
    python ec2_gui.pyw
    python2 ec2_gui.pyw

### Requirements ###

#### boto ####
You need boto, which is needed to talk to AWS.  There are number of ways to install boto.  I prefer this way:

    git clone https://github.com/boto/boto.git
    cd boto
    python setup.py install

#### ec2_gui.ini ####
You also need to create a file called **ec2_gui.ini**.  This file contains the information that will be populated in the pulldowns of the GUI.

Here is an example of 2 accounts, 2 login users, and 2 ssh pem files.

Basically the ini file has 3 sections:

- [USER-*]
- [SSH_FILE-*]
- [CREDENTIALS-*]

Where "*" is whatever text you want to put there.
	
	[USER-EC2-USER]
	NAME=ec2-user
	DISPLAY=ec2-user
	
	[USER-ROOT]
	NAME=root
	DISPLAY=root(for centos)

	[SSH_FILE-ACCOUNTA]
	SSH_FILE=c:\\\\Users\\\\alex.gray\\\\Documents\\\\devOpsQa.pem
	DISPLAY=c:\Users\alex.gray\Documents\devOpsQa.pem
	
	[SSH_FILE-ACCOUNTB]
	SSH_FILE=c:\\\\Users\\\\alex.gray\\\\Documents\\\\alex.gray.pem
	DISPLAY=c:\Users\alex.gray\Documents\alex.gray.pem
	
	[CREDENTIALS-ACCOUNTA]
	AWS_ACCESS_KEY=ABC123
	AWS_SECRET_KEY=XYZ123
	#SSH_CMD=c:\utilities\kitty.exe -ssh -i %SSH_FILE% %NAME%@%DNS_NAME% 
	SSH_CMD=C:\Utilities\Mobatek\MobaXterm\MobaXterm.exe -newtab "ssh %NAME%@%DNS_NAME% -p 22 -i %SSH_FILE%"
	
	[CREDENTIALS-ACCOUNTB]
	AWS_ACCESS_KEY=DEF123
	AWS_SECRET_KEY=WXY123
	SSH_CMD=C:\Utilities\Mobatek\MobaXterm\MobaXterm.exe -newtab "ssh %NAME%@%DNS_NAME% -p 22 -i %SSH_FILE%"

**Note:** I use 4 backslashes in my SSH_FILE entry because that is what [MobaXterm](http://mobaxterm.mobatek.net/), the free tool that I use to connect my ec2 machines.  I used putty or kitty before, but I like MobaXterm.
