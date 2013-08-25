import wx
import wxPython.wx
import wx.grid as gridlib
import os
import ConfigParser
import sys
import logging
import copy
import ast
import datetime
import time
import subprocess

import boto.ec2
from boto.ec2.connection import EC2Connection

class EC2_Functionality():
    def __init__(self, logLevel=logging.CRITICAL, logger=None):
        """ Helper class to talk to EC2.

        :param logLevel: Verbosity level of this command (DEBUG|INFO|WARNING|CRITICAL).
        :type logLevel: logging.logLevel
        :param logger: Optionally specificy a logger. Useful for multithreading.
        :type logger: logging logger

        """
        if logger is None:
            #- Create the logger:
            self.log = logging.getLogger(__name__)
            self.log.handlers = []
            ch = logging.StreamHandler()
            ch.setFormatter(logging.Formatter('%(message)s'))
            self.log.addHandler(ch)
            self.log.setLevel(logLevel)
            self.identityFile = None
        else:
            self.log = logger

        #- OK, now connect to the region:
        self.connectToRegion()

    def connectToRegion(self):
        #- Connect to us-east-1 region:
        if 'AWS_ACCESS_KEY' in os.environ and 'AWS_SECRET_KEY' in os.environ:
            self.conn = EC2Connection(os.environ['AWS_ACCESS_KEY'],
                                      os.environ['AWS_SECRET_KEY'])
        else:
            #- Maybe you can connect with the credentials in ~/.boto or with IAM Role:
            self.conn = EC2Connection()
        self.log.critical('Connected to Region: ' + self.conn.region.name)

    def createTags(self, resource_ids=[], dict_of_tags={}, logger=None):
        """ This function creates tags on resource ID.

        :param resource_ids: A list of AWS resource IDs.
        :type resource_ids: list of strings
        :param dict_of_tags: A dict of tags.
        :type dict_of_tags: dict
        :param logger: Optionally specificy a logger. Useful for multithreading.
        :type logger: logging logger

        """
        if logger is None:
            logger = self.log
        logger.critical('Creating Tags: ' + str(dict_of_tags) + 'on resource IDs: ' + str(resource_ids))
        image = self.conn.create_tags(resource_ids, dict_of_tags)


    def getInstanceById(self, instanceId, logger=None):
        """ This function returns an instance object based on an instance AWS ID.

        :param imageId: The AWS Instance ID.
        :type imageId: string
        :param logger: Optionally specificy a logger. Useful for multithreading.
        :type logger: logging logger
        :return: boto instance object

        """
        if logger is None:
            logger = self.log
        logger.critical('Finding instance ' + instanceId + '... ')
        reservations = self.conn.get_all_instances(instance_ids=[instanceId])
        for reservation in reservations:
            for instance in reservation.instances:
                if instance.id == instanceId:
                    logger.critical('Returning instance ' + instanceId + '... ')
                    return instance
        return None

    def getAllInstances(self):
        """ This function returns a list of all instance objects.

        :return: list of boto instance objects

        """
        return [i for r in self.conn.get_all_instances() for i in r.instances]


    def terminateInstanceById(self, instanceId, logger=None):
        """ This function terminates an instance by it's AWS ID.

        :param instanceId: AWS Instance ID that you wish to terminate.
        :type instanceId: string
        :param logger: Optionally specificy a logger. Useful for multithreading.
        :type logger: logging logger

        """
        if logger is None:
            logger = self.log
        logger.critical('\nTerminating Instance: ' + instanceId)
        instance = self.getInstanceById(instanceId)
        if instance is None:
            logger.critical('***Error: Instance not found: ' + instanceId)
        else:
            while instance.state != 'terminated':
                instance.terminate()
                instance.update()
                if instance.state == 'shutting-down':
                    break
                logger.critical('Waiting for terminated state. Currently: ' + instance.state)
                time.sleep(10)
        logger.critical('Instance ' + instanceId + ' is terminated or is terminating!')

class AdditionalInfoDialog(wx.Dialog):
    def __init__ (self, parent, ID, title, instanceObj):
        import inspect
        print inspect.getargspec(wx.Dialog.__init__)
        wx.Dialog.__init__(self, parent=parent,
                                         pos=wx.DefaultPosition, size=(850,500),
                                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        xposKey = 25
        xposValue = 160
        height = 20
        yStartOfText = 20
        heading = wx.StaticText(self, -1, 'Additional Info on Instance', (xposKey, 15))
        heading.SetFont(font)
        instance_attrs = ["id", "groups", "private_dns_name", "state", "previous_state",
                          "key_name", "instance_type", "launch_time", "image_id", "placement", "kernel", "ramdisk",
                          "architecture", "hypervisor", "virtualization_type", "product_codes", "ami_launch_index",
                          "monitored", "monitoring_state", "spot_instance_request_id", "subnet_id", "vpc_id",
                          "private_ip_address", "ip_address", "platform", "root_device_name", "root_device_type",
                          "block_device_mapping", "state_reason", "interfaces", "ebs_optimized", "instance_profile"]

        wx.StaticLine(self, -1, (xposKey, 40), (300,1))
        i = 1
        bflip = False
        for attr in instance_attrs:
            rcolumn = 0
            if bflip is False:
                bflip = True
                rcolumn = 380
                i = i + 1
            else:
                bflip = False
            #wx.StaticText(self, -1, attr, (xposKey + rcolumn, yStartOfText + i * height), style=wx.ALIGN_RIGHT)
            t = wx.TextCtrl(parent=self, id=-1, size=(135,-1), pos=(xposKey + rcolumn, yStartOfText + i * height), style=wx.TE_READONLY|wx.BORDER_NONE)
            t.SetValue(attr)
            if attr == 'instance_profile':
                val = getattr(instanceObj, attr)
                if val is not None:
                    val = val['arn'][val['arn'].find('/')+1:]
            elif attr == 'groups':
                val = getattr(instanceObj, attr)
                if val is not None:
                    strval = ''
                    for group in val:
                        print group.name + ':' + group.id
                        strval = strval + group.name + ','
                    if strval != '':
                        if strval[-1] == ',':
                            strval = strval[:-1]
                    val = strval
            else:
                val = str(getattr(instanceObj, attr))
            #wx.StaticText(self, -1, str(val), (xposValue + rcolumn, yStartOfText + i * height))
            t = wx.TextCtrl(parent=self, id=-1, size=(200,-1), pos=(xposValue + rcolumn, yStartOfText + i * height), style=wx.TE_READONLY|wx.BORDER_NONE)
            t.SetValue(str(val))

        i = i + 2
        wx.Button(self, 1, 'OK', (140, yStartOfText + i * height), (60, 30))
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=1)

    def OnOk(self, event):
        self.Close()

class MyForm(wx.Frame):

    def getMaxName(self, instance):
        if 'Name' in instance.tags.keys():
            return len(instance.tags['Name'])
        else:
            return 0

    def getMaxTag(self, instance):
        tags_minus_name = instance.tags.copy()
        if 'Name' in instance.tags.keys():
            del tags_minus_name['Name']
        return len(str(tags_minus_name))

    def createDictFromIni(self):
        configfile = os.path.join(os.path.dirname(__file__), 'ec2_gui.ini')
        config = ConfigParser.RawConfigParser()
        ret_sshFileDict = {}
        ret_credentialsDict = {}
        ret_usersDict = {}
        if os.path.exists(configfile):
            config.read(configfile)
            sshFileSections = filter(lambda k: k.startswith('SSH_FILE-'), config.sections())
            credentialSections = filter(lambda k: k.startswith('CREDENTIALS-'), config.sections())
            userSections = filter(lambda k: k.startswith('USER-'), config.sections())

            for section in sshFileSections:
                ret_sshFileDict[section] = {}
                ret_sshFileDict[section]['SSH_FILE'] = config.get(section, 'SSH_FILE')
                ret_sshFileDict[section]['DISPLAY'] = config.get(section, 'DISPLAY')

            for section in credentialSections:
                ret_credentialsDict[section] = {}
                ret_credentialsDict[section]['AWS_ACCESS_KEY'] = config.get(section, 'AWS_ACCESS_KEY')
                ret_credentialsDict[section]['AWS_SECRET_KEY'] = config.get(section, 'AWS_SECRET_KEY')
                ret_credentialsDict[section]['SSH_CMD'] = config.get(section, 'SSH_CMD')
                
            for section in userSections:
                ret_usersDict[section] = {}
                ret_usersDict[section]['NAME'] = config.get(section, 'NAME')
                ret_usersDict[section]['DISPLAY'] = config.get(section, 'DISPLAY')

        else:
            dlg = wx.MessageDialog(None, 'Could not find ini file!' \
                                         'See README.txt for more details.', "Error", wx.OK|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            sys.exit(1)

        return ret_sshFileDict, ret_credentialsDict, ret_usersDict

    def __init__(self):
        #- Read the a config:
        self.ret_sshFileDict, self.ret_credentialsDict, self.ret_usersDict = self.createDictFromIni()
        self.selected_row = 0
        self.selected_col = 0

        #- Get the instances:
        self.reverseSort = True

        credentials = [key for key in self.ret_credentialsDict.keys()]
        self.setCredentialsBasedOnComboBoxSelection(credentials[0])
        self.refreshEc2List()

        #- Initialize the window:
        wx.Frame.__init__(self, None, wx.ID_ANY, "Grid with Popup Menu", size=(1100,300))

        # Add a panel so it looks correct on all platforms
        self.panel = wx.Panel(self, wx.ID_ANY)

        num_of_columns = 6
        self.grid = gridlib.Grid(self.panel)
        self.grid.CreateGrid(len(self.all_instances), num_of_columns)

        # Add the click events:
        self.grid.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.handler_onRightClick)
        self.grid.Bind(gridlib.EVT_GRID_LABEL_LEFT_DCLICK, self.handler_onRowDClick)
        self.grid.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.handler_onRowClick)
        self.grid.Bind(gridlib.EVT_GRID_CELL_CHANGE, self.handler_onCellChange)

        #- Get the size of column based on largest text in column:
        f = self.panel.GetFont()
        dc = wx.WindowDC(self.panel)
        dc.SetFont(f)
        buff = 'WWW'

        #- Set the Columns:
        if len(self.all_instances) == 0:
            max_name_len = 'W'*10
            max_dns_name = 'W'*10
            max_tags = 'W'*10
            max_id = 'W'*10
            max_private_dns_name = 'W'*10
            max_state = 'W'*10
        else:
            i = max(self.all_instances, key=self.getMaxName)
            if 'Name' in i.tags.keys():
                max_name_len = i.tags['Name']
            else:
                max_name_len = buff
            
            max_dns_name = max(self.all_instances, key=lambda x: len(x.dns_name)).dns_name
            max_tags = str(max(self.all_instances, key=self.getMaxTag).tags)
            max_id = max(self.all_instances, key=lambda x: len(x.id)).id
            max_private_dns_name = max(self.all_instances, key=lambda x: len(x.private_dns_name)).private_dns_name
            max_state = max(self.all_instances, key=lambda x: len(x.state)).state

        self.columns = {}
        self.columns["Name"] = {'col_id':0, 'ins_attr':'tags["Name"]','col_size':dc.GetTextExtent(max_name_len + buff)[0]}
        self.columns["public-dns"] = {'col_id':1, 'ins_attr':'dns_name','col_size':dc.GetTextExtent(max_dns_name + buff)[0]}
        self.columns["tags"] = {'col_id':2, 'ins_attr':'tags','col_size':dc.GetTextExtent(max_tags + buff)[0]}
        self.columns["ID"] = {'col_id':3, 'ins_attr':'id','col_size':dc.GetTextExtent(max_id + buff)[0]}
        self.columns["private-dns"] = {'col_id':4, 'ins_attr':'private_dns_name','col_size':dc.GetTextExtent(max_private_dns_name + buff)[0]}
        self.columns["state"] = {'col_id':5, 'ins_attr':'state','col_size':dc.GetTextExtent(max_state + buff)[0]}

        #- Set the colors of the rows based on instance state:
        self.state_colors = {}
        self.state_colors['running'] = 'green'
        self.state_colors['terminated'] = 'red'
        self.state_colors['shutting-down'] = 'orange'
        self.state_colors['pending'] = 'yellow'
        self.state_colors['stopped'] = 'grey'

        for col_name, val in self.columns.items():
            self.grid.SetColLabelValue(val['col_id'], col_name)
            self.grid.SetColSize(val['col_id'], val['col_size'])

        self.refreshGrid()

        #- Create the toolbar and all its widgets:
        toolbar = self.CreateToolBar()

        #- Pull down for credentials:
        cb_credentials = wx.ComboBox(toolbar, value=credentials[0], pos=(50, 30), choices=credentials, style=wx.CB_READONLY)
        cb_credentials.Bind(wx.EVT_COMBOBOX, self.handler_onComboBoxCredentialsSelect)

        #- Pull down for user:
        sshFiles = [v['DISPLAY'] for k,v in self.ret_sshFileDict.items()]
        cb_sshFiles = wx.ComboBox(toolbar, value=sshFiles[0], pos=(50, 30), choices=sshFiles, style=wx.CB_READONLY)
        self.setSshFileBasedOnComboBoxSelection(sshFiles[0])
        cb_sshFiles.Bind(wx.EVT_COMBOBOX, self.handler_onComboBoxSSHFilesSelect)        
        
        #- Pull down for ssh pem/ppk files:
        userSelection = [v['DISPLAY'] for k,v in self.ret_usersDict.items()]
        cb_UserSelection = wx.ComboBox(toolbar, value=userSelection[0], pos=(50, 30), choices=userSelection, style=wx.CB_READONLY)
        self.setUserFileBasedOnComboBoxSelection(userSelection[0])
        cb_UserSelection.Bind(wx.EVT_COMBOBOX, self.handler_onComboBoxUserSelect)

        #- Refresh button:
        qtool = toolbar.AddLabelTool(wx.ID_ANY, 'Refresh', wx.Bitmap(os.path.join(os.path.dirname(__file__), 'refresh.png')))
        toolbar.AddSeparator()
        self.Bind(wx.EVT_TOOL, self.refreshButton, qtool)

        #- Text Search:
        self.search = wx.SearchCtrl(toolbar, size=(150,-1))
        self.search.Bind(wx.EVT_TEXT, self.handler_onTextEnteredInSearchField)
        
        #- Now add all widgets to toolbar:
        toolbar.AddControl(self.search)
        toolbar.AddSeparator()
        toolbar.AddControl(cb_credentials)
        toolbar.AddSeparator()
        toolbar.AddControl(cb_sshFiles)
        toolbar.AddSeparator()
        toolbar.AddControl(cb_UserSelection)

        toolbar.Realize()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.grid, 1, wx.EXPAND, num_of_columns)
        self.panel.SetSizer(sizer)

        #- Handle Right click menu stuff:
        #- (note: if you change the text here, you'll have to update handler_onRightClick)
        menu_titles = [ "Connect to Instance", "Terminate", "Aditional Info"]

        self.menu_title_by_id = {}
        for title in menu_titles:
            self.menu_title_by_id[ wx.NewId() ] = title

        self.search_text = ''

    def handler_onComboBoxUserSelect(self, e):
        self.setUserFileBasedOnComboBoxSelection(e.GetString())
        
    def handler_onComboBoxSSHFilesSelect(self, e):
        self.setSshFileBasedOnComboBoxSelection(e.GetString())

    def setSshFileBasedOnComboBoxSelection(self, text):
        self.sshFileSelected = text
        
    def setUserFileBasedOnComboBoxSelection(self, text):
        self.userSelected = text
        
    def handler_onComboBoxCredentialsSelect(self, e):
        self.setCredentialsBasedOnComboBoxSelection(e.GetString())
        self.doRefreshButtonCommands()

    def setCredentialsBasedOnComboBoxSelection(self, text):
        self.credentialsSelected = text
        os.environ['AWS_ACCESS_KEY'] = self.ret_credentialsDict[text]['AWS_ACCESS_KEY']
        os.environ['AWS_SECRET_KEY'] = self.ret_credentialsDict[text]['AWS_SECRET_KEY']

    def refreshEc2List(self):
        print '------------refreshing ec2 list'
        self.g_ec2 = EC2_Functionality()
        
        self.all_instances = self.g_ec2.getAllInstances()
        self.filtered_list = copy.deepcopy(self.all_instances)
        self.makeAllVisible()

    def refreshButton(self, event):
        #- When you click on the refresh button, this code gets executed:
        self.doRefreshButtonCommands()

    def doRefreshButtonCommands(self):
        self.refreshEc2List()
        self.refreshGrid()
        self.DoSearch(self.search_text)

    def handler_onCellChange(self, evt):
        value = self.grid.GetCellValue(evt.GetRow(), evt.GetCol())
        print 'value: ', value
        for k,v in self.columns.items():
            if v['col_id'] == evt.GetCol():
                print 'column modified: ' + k + '. instance ID: ' + str(self.filtered_list[evt.GetRow()].id)
                self.g_ec2.createTags(resource_ids=[str(self.filtered_list[evt.GetRow()].id)], dict_of_tags=ast.literal_eval(value))
                break

    def handler_onTextEnteredInSearchField(self, evt):
        self.search_text = self.search.GetValue()
        self.DoSearch(self.search_text)

    def makeAllVisible(self):
        print '----------making all visible'
        for i in self.all_instances:
            i.visible = True

    def DoSearch(self, text):
        print 'Search text: ' + text
        self.makeAllVisible()
        ordered_search_strings = filter(None, text.strip().split(' '))
        for ordered_search in ordered_search_strings:
            for i in self.all_instances:
                #- Hide the instances where this ordered_search does not appear:
                if ordered_search.lower() not in i.dns_name.lower() and \
                   ordered_search.lower() not in i.private_dns_name.lower() and \
                   ordered_search.lower() not in i.state.lower() and \
                   not any( ordered_search.lower() in k for k in [el.lower() for el in i.tags.keys()] ) and \
                   not any( ordered_search.lower() in k for k in [el.lower() for el in i.tags.values()] ) and \
                   ordered_search.lower() not in [el.lower() for el in i.tags.values()] and \
                   ordered_search.lower() not in i.id.lower():
                    i.visible = False

        self.refreshGrid()

    def refreshGrid(self):
        print '\n\n\n------------refresh grid'
        self.grid.ClearGrid()
        current, new = (self.grid.GetNumberRows(), len(self.all_instances))

        if new < current:
            #- Delete rows:
            self.grid.DeleteRows(0, current-new, True)

        if new > current:
            #- append rows:
            self.grid.AppendRows(new-current)

        for i in range(len(self.all_instances)):
            for col_name, val in self.columns.items():
                self.grid.SetCellBackgroundColour(i, val['col_id'], 'white')

        self.filtered_list = filter(lambda x: x.visible is True, self.all_instances)
        for i in range(len(self.filtered_list)):
            for col_name, val in self.columns.items():
                col_val = ''
                if col_name == 'Name':
                    if 'Name' in self.filtered_list[i].tags.keys():
                        col_val = self.filtered_list[i].tags['Name']
                if hasattr(self.filtered_list[i], val['ins_attr']):
                    col_val = getattr(self.filtered_list[i], val['ins_attr'])
                self.grid.SetCellValue(i, val['col_id'], str(col_val))
                #- Set color based on state:
                if self.filtered_list[i].state in self.state_colors:
                    self.grid.SetCellBackgroundColour(i, val['col_id'], self.state_colors[self.filtered_list[i].state])

    def handler_onRowClick(self, event):
        print 'column clicked!'

    def handler_onRowDClick(self, event):
        if self.reverseSort is False:
            self.reverseSort = True
        else:
            self.reverseSort = False

        col = event.GetCol()
        if col == 0:
            self.all_instances.sort(key=lambda x: '' if 'Name' not in x.tags else x.tags['Name'], reverse=self.reverseSort)
        elif col == 1:
            self.all_instances.sort(key=lambda x: x.dns_name, reverse=self.reverseSort)
        elif col == 2:
            self.all_instances.sort(key=lambda x: str(x.tags), reverse=self.reverseSort)
        elif col == 3:
            self.all_instances.sort(key=lambda x: x.id, reverse=self.reverseSort)
        elif col == 4:
            self.all_instances.sort(key=lambda x: x.private_dns_name, reverse=self.reverseSort)
        elif col == 5:
            self.all_instances.sort(key=lambda x: x.state, reverse=self.reverseSort)

        self.refreshGrid()

    def handler_onRightClick(self, event):
        self.selected_row = event.GetRow()

        self.grid.SetSelectionBackground(wx.NamedColour('blue'))
        self.grid.SelectRow(self.selected_row, False) # True if the selection should be expanded
        self.grid.Refresh()

        ### 2. Launcher creates wxMenu. ###
        menu = wxPython.wx.wxMenu()
        for (id,title) in self.menu_title_by_id.items():
            ### 3. Launcher packs menu with Append. ###
            menu.Append( id, title )
            ### 4. Launcher registers menu handlers with EVT_MENU, on the menu. ###
            wxPython.wx.EVT_MENU( menu, id, self.MenuSelectionCb )

        ### 5. Launcher displays menu with call to PopupMenu, invoked on the source component, passing event's GetPoint. ###
        self.PopupMenu( menu )
        menu.Destroy() # destroy to avoid mem leak

    def MenuSelectionCb( self, event ):
        operation = self.menu_title_by_id[ event.GetId() ]
        if operation == 'Connect to Instance':
            # Re-read the ini file:
            self.ret_sshFileDict, self.ret_credentialsDict, self.ret_usersDict = self.createDictFromIni()
            #- Based on the ssh pulldown, get the value:
            ssh_file = None
            for k,v in self.ret_sshFileDict.items():
                if self.sshFileSelected == v['DISPLAY']:
                    ssh_file = v['SSH_FILE']
                    break
            #- Based on the user pulldown, get the value:
            name = None
            for k,v in self.ret_usersDict.items():
                if self.userSelected == v['DISPLAY']:
                    name = v['NAME']
                    break
            #- Modify the cmd, based on the pulldowns:
            cmd = self.ret_credentialsDict[self.credentialsSelected]['SSH_CMD']
            cmd = cmd.replace('%DNS_NAME%', self.filtered_list[self.selected_row].dns_name)
            cmd = cmd.replace('%SSH_FILE%', ssh_file)
            cmd = cmd.replace('%NAME%', name)
            print cmd
            #DETACHED_PROCESS = 0x00000008
            #subprocess.Popen(cmd,shell=False,stdin=None,stdout=None,stderr=None,close_fds=True,creationflags=DETACHED_PROCESS)
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        if operation == 'Terminate':
            # Terminate Instance
            str_contents = 'Are you sure you want to delete this instance?'
            dlg = wx.MessageDialog(None, str_contents, "Notice", wx.YES_NO | wx.ICON_QUESTION)
            result = dlg.ShowModal() == wx.ID_YES
            dlg.Destroy()
            if result is True:
                self.g_ec2.terminateInstanceById(instanceId=self.filtered_list[self.selected_row].id)
                time.sleep(1)
                self.doRefreshButtonCommands()
        if operation == 'Aditional Info':
            dlg = AdditionalInfoDialog(parent=None, ID=0, title="Info", instanceObj=self.filtered_list[self.selected_row])
            dlg.ShowModal()
            dlg.Destroy()


# Run the program
if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = MyForm().Show()
    app.MainLoop()
