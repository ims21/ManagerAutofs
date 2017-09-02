#
#  Manager Autofs
#
VERSION = "1.28"
#
#  Coded by ims (c) 2017
#  Support: openpli.org
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# for localized messages
from . import _

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Button import Button
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigIP, ConfigInteger, ConfigText, getConfigListEntry, ConfigYesNo, NoSave, ConfigSelection, ConfigPassword
from Tools.BoundFunction import boundFunction
from Screens.ChoiceBox import ChoiceBox
from Components.Sources.List import List
from shutil import copyfile
import enigma
import skin
import os

config.plugins.mautofs = ConfigSubsection()
# parameters for auto.master file
config.plugins.mautofs.enabled = NoSave(ConfigYesNo(default = False))
config.plugins.mautofs.mountpoint = NoSave(ConfigText(default = "/mnt/remote", visible_width = 30, fixed_size = False))
config.plugins.mautofs.autofile = NoSave(ConfigText(default = "remote", visible_width = 30, fixed_size = False ))
config.plugins.mautofs.ghost = NoSave(ConfigYesNo(default = False))
#config.plugins.mautofs.timeout = NoSave(ConfigYesNo(default = False))
#choicelist = [("", _("no"))]
#for i in range(0, 1000, 10):
#	choicelist.append(("%d" % i, "%d" % i))
#config.plugins.mautofs.delay = NoSave(ConfigSelection(default="", choices=choicelist))
cfg = config.plugins.mautofs

MASTERFILE="/etc/auto.master"

def hex2strColor(argb):
	out = ""
	for i in range(28,-1,-4):
		out += "%s" % chr(0x30 + (argb>>i & 0xf))
	return out

dC = "\c%s" % hex2strColor(int(skin.parseColor("#00999999").argb()))
eC = "\c%s" % hex2strColor(int(skin.parseColor("foreground").argb()))
yC = "\c%s" % hex2strColor(int(skin.parseColor("yellow").argb()))
fC = "\c%s" % hex2strColor(int(skin.parseColor("foreground").argb()))

class ManagerAutofsMasterSelection(Screen):
	skin = """
		<screen name="ManagerAutofsMasterSelection" position="center,center" size="680,605" backgroundColor="#00000000">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on"/>
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on"/>
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on"/>
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on"/>
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1"/>
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1"/>
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1"/>
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1"/>
			<widget source="list" render="Listbox" position="5,60" size="670,500" backgroundColor="#00000000" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
				{"templates":
					{"default": (25,[
							MultiContentEntryText(pos = (5, 6), size = (10, 25), font=1, flags = RT_HALIGN_LEFT, text = 0), # index 0 is the status
							MultiContentEntryText(pos = (50, 3), size = (250, 25), font=0, flags = RT_HALIGN_LEFT, text = 1), # index 1 is the name
							MultiContentEntryText(pos = (300, 3), size = (250, 25), font=0, flags = RT_HALIGN_LEFT, text = 2), # index 1 is the autofile
						])
					},
					"fonts": [gFont("Regular", 18),gFont("Regular", 12)],
					"itemHeight": 25
				}
				</convert>
			</widget>
			<widget name="status" position="50,560" zPosition="10" size="660,20" font="Regular;18" backgroundColor="#00000000" halign="left" valign="center"/>
			widget name="statusbar" position="50,580" zPosition="10" size="660,20" font="Regular;22" backgroundColor="#00000000" halign="left" valign="center"/>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session

		self.data = ''
		self.container = enigma.eConsoleAppContainer()
		self.container.appClosed.append(self.appClosed)
		self.container.dataAvail.append(self.dataAvail)
		self["status"] = Label()
		self["statusbar"] = Label()

		self["shortcuts"] = ActionMap(["SetupActions","OkCancelActions","ColorActions","MenuActions"],
		{
			"ok": self.menu,
			"cancel": self.keyClose,
			"red": self.keyClose,
			"green": self.keyOk,
			"blue": self.changeMasterRecordStatus,
			"yellow": self.editAutofile,
			"menu": self.menu,
		}, -1)

		self.list = []
		self["list"] = List(self.list)
		if not self.selectionChanged in self["list"].onSelectionChanged:
			self["list"].onSelectionChanged.append(self.selectionChanged)

		self["key_red"] = Button(_("Close"))
		self["key_green"] = Button(_("Ok"))
		self["key_blue"] = Button("")
		self["key_yellow"] = Button(_("Edit auto file"))

		self.msgNM=None
		self.onShown.append(self.setWindowTitle)

		if os.path.exists(MASTERFILE):
			copyfile(MASTERFILE, MASTERFILE+"_bak")
		else:
			f = open(MASTERFILE, "w")
			f.write("%s%s /etc/auto.%s %s\n" % ("" if cfg.enabled.value else "#", cfg.mountpoint.value, cfg.autofile.value, "--ghost" if cfg.ghost.value else ""))
			f.close()

		self.onLayoutFinish.append(self.readMasterFile)

	def setWindowTitle(self):
		self.setTitle(_("Manager Autofs v.%s - use %sMenu%s or %sOK%s on record") % (VERSION, yC,fC,yC,fC))

	def readMasterFile(self):
		# 0 - status 1 - mountpoint 2 - autofile 3 - ghost
		self.list = []

		for line in open( MASTERFILE, "r"):
			line = line.replace('\n','')
			if '#' in line:
				status = ("disabled")
				line = line[1:]
			else:
				status = ("enabled")
			line = status + ' ' + line
			m = line.split(' ')

			self.list.append(('x' if m[0] == "enabled" else '', m[1], m[2], m[3]))

		self['list'].setList(self.list)

	def selectionChanged(self):
		self.clearTexts()
		sel = self["list"].getCurrent()
		if sel:
			if sel[0] == "x":
				text = _("Disable")
			else:
				text = _("Enable")
			self["key_blue"].setText(text)
			self["status"].setText("%s%s %s %s" % ("" if sel[0] == "x" else "#",sel[1],sel[2],sel[3]))

	def keyClose(self):
		self.restartAutofs()
		self.close()

	def keyOk(self):
		self.saveMasterFile()
		self.restartAutofs()
		self.close()

	def clearTexts(self):
		self.MessageBoxNM()
		self["statusbar"].setText("")

	def saveMasterFile(self):
		fo = open( MASTERFILE, "w")
		for x in self.list:
			fo.write("%s%s %s %s\n" % ("" if x[0] == "x" else "#", x[1], x[2], x[3]))
		fo.close()

	def menu(self):
		menu = []
		buttons = []
		text = _("Select operation:")
		sel = self["list"].getCurrent()
		if sel:
			recordname = "%s" % (sel[1].split('/')[2])
			autoname = "%s" % sel[2].split('/')[2]
			menu.append(((_("Edit record:") + "  %s%s%s" % (yC,recordname,fC)),0))
			buttons = ["4"]
		menu.append((_("Add record"),1))
		menu.append(((_("Remove record:") + "  %s%s%s" % (yC,recordname,fC)),2))
		buttons += ["1", "8"]
		if sel:
			menu.append(((_("Edit -") + " %s%s%s" % (yC,autoname,fC)),10))
			menu.append(((_("Add line - ") + " %s%s%s" % (yC,autoname,fC)),11))
			menu.append(((_("Remove -") + " %s%s%s" % (yC,autoname,fC)),12))
			buttons += ["yellow", "", ""]
#		menu.append((_("Reload autofs"),13))
#		buttons += ["green"]
		menu.append((_("Reload autofs with GUI restart"),14))
		buttons += ["red"]

		self.session.openWithCallback(self.menuCallback, ChoiceBox, title=text, list=menu, keys=buttons)

	def menuCallback(self, choice):
		if choice is None:
			return
		sel = self["list"].getCurrent()
		if sel:
			if choice[1] == 0:
				self.editMasterRecord()
			elif choice[1] == 1:
				self.addMasterRecord()
			elif choice[1] == 2:
				self.removeMasterRecord()
			elif choice[1] == 10:
				self.editAutofile()
			elif choice[1] == 11:
				self.addAutofileLine()
			elif choice[1] == 12:
				self.removeAutofile()
#			elif choice[1] == 13:
#				self.restartAutofs()
			elif choice[1] == 14:
				def callback(value=False):
					if value:
						self.restartAutofs(restartGui=True)
				self.session.openWithCallback(callback, MessageBox, _("Really reload autofs and restart GUI?"), type=MessageBox.TYPE_YESNO, default=False)
			else:
				return

	def restartAutofs(self, restartGui=False):
		if os.path.exists('/etc/init.d/autofs'):
			cmd = '/etc/init.d/autofs reload'
			if restartGui:
				cmd += '; killall enigma2'
			if self.container.execute(cmd):
				print "[ManagerAutofs] failed to execute"
				self.showOutput()
		else:
			self.MessageBoxNM(True, _("Autofs is not installed!"), 5)

	def appClosed(self, retval):
		print "[ManagerAutofs] done:", retval
		if retval:
			txt = _("Failed")
		else:
			txt = _("Done")
		self.showOutput()
		self.data = ''
		self["statusbar"].setText(txt)
	def dataAvail(self, s):
		self.data += s
		print "[ManagerAutofs]", s.strip()
		self.showOutput()
	def showOutput(self):
		self["status"].setText(self.data)

	def changeMasterRecordStatus(self):
		curr = self["list"].getCurrent()
		if curr:
			index = self["list"].getIndex()
			self.changeItemStatus(index, curr)

	def addMasterRecord(self):
		def callbackAdd(change=False):
			if change:
				mountpoint = "/mnt/%s" % cfg.mountpoint.value
				autofile = "/etc/auto.%s" % cfg.autofile.value
				enabled =  cfg.enabled.value and "x" or ""
				ghost = cfg.ghost.value and "--ghost" or ""
				add = (enabled, mountpoint, autofile, ghost)
				self.addItem(add)
		self.session.openWithCallback(boundFunction(callbackAdd), ManagerAutofsMasterEdit, None)

	def editMasterRecord(self):
		def callbackEdit( index, change = False):
			if change:
				mountpoint = "/mnt/%s" % cfg.mountpoint.value
				autofile = "/etc/auto.%s" % cfg.autofile.value
				enabled =  cfg.enabled.value and "x" or ""
				ghost = cfg.ghost.value and "--ghost" or ""
				edit = (enabled, mountpoint, autofile, ghost )
				self.changeItem(index, edit)
		sel = self["list"].getCurrent()
		if sel:
			index = self["list"].getIndex()
			self.session.openWithCallback(boundFunction(callbackEdit, index), ManagerAutofsMasterEdit, sel)

	def removeMasterRecord(self):
		def callbackRemove(index, autofile, retval=False):
			if retval > 1:	# remove auto file - must be removed before than record due valid "sel" in list!!!
				if os.path.exists(autofile):
					bakName = autofile + "_del"
					os.rename(autofile, bakName)
			if retval:	# remove record
				self.removeItem(index)

		sel = self["list"].getCurrent()
		if sel:
			index = self["list"].getIndex()
			record = sel[1]
			autofile = sel[2]
			removing = [(_("Nothing"), False), (_("Record %s only") % record, 1), (_("Record %s and its file %s") % (record, autofile), 2) ]
			self.session.openWithCallback(boundFunction(callbackRemove, index, autofile), MessageBox, _("What all do You want to remove?"), type=MessageBox.TYPE_YESNO, default=False, list=removing)

	def changeItemStatus(self, index, data):
		if data[0] == "x":
			status = ""
		else:
			status = "x"
		self.changeItem(index, (status,data[1],data[2],data[3]))

	def changeItem(self, index, new):
		self["list"].modifyEntry(index,(new[0], new[1], new[2], new[3]))

	def addItem(self, new):
		self.list.append((new[0], new[1], new[2], new[3]))

	def removeItem(self, index):
		self.list.pop(index)
		self["list"].updateList(self.list)

	def addAutofileLine(self):
		sel = self["list"].getCurrent()
		if sel:
			name = sel[2]
			self.session.open(ManagerMultiAutofsAutoEdit, name)

	def editAutofile(self):
		def callBackSingle(name,text=""):
			if text:
				self.backupFile(name,"bak")
				self.saveFile(name, text)
		sel = self["list"].getCurrent()
		if sel:
			name = sel[2]
			lines = self.getAutoLines(name)
			data = ""
			if lines == 1:		# single line
				line = open(name, "r").readline()
				data = line.replace('\n','').strip()
				self.session.openWithCallback(boundFunction(callBackSingle, name), ManagerAutofsAutoEdit, name, data, False)
			elif lines > 1:		# multi
				self.session.open(ManagerMultiAutofsAutoEdit, name)
			elif lines == -1:	# missing
				self.session.openWithCallback(boundFunction(callBackSingle, name), ManagerAutofsAutoEdit, name, data, True)
			else:			# empty
				self.session.openWithCallback(boundFunction(callBackSingle, name), ManagerAutofsAutoEdit, name, data, True)

	def backupFile(self, name, ext):
		if os.path.exists(name):
			os.rename(name, "%s_%s" % (name,ext))

	def saveFile(self, name, data):
		fo = open(name, "w")
		fo.write("%s\n" % data)
		fo.close()

	def getAutoLines(self, name):
		nr = 0
		if not os.path.exists(name):
			return -1
		for mline in open(name, "r"):
			mline = mline.replace('\n','')
			if mline:
				nr += 1
		return nr

	def removeAutofile(self):
		def callBack(name, value=False):
			if value:
				if os.path.exists(name):
					bakName = name + "_del"
					os.rename(name, bakName)
		sel = self["list"].getCurrent()
		if sel:
			name = sel[2]
			self.session.openWithCallback(boundFunction(callBack, name), MessageBox, _("Really remove autofile '%s'?" % name), type=MessageBox.TYPE_YESNO, default=False)


	def MessageBoxNM(self, display=False, text="", delay=0):
		if self.msgNM:
			self.session.deleteDialog(self.msgNM)
			self.msgNM = None
		else:
			if display and self.session is not None:
				self.msgNM = self.session.instantiateDialog(NonModalMessageBoxDialog, text=text, delay=delay)
				self.msgNM.show()

class ManagerAutofsMasterEdit(Screen, ConfigListScreen):
	skin = """
		<screen position="center,center" size="560,220">
			<ePixmap name="red" position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue" position="420,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget  name="key_red" position="0,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="red" font="Regular;20" transparent="1"/>
			<widget  name="key_green" position="140,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="green" font="Regular;20" transparent="1"/>
			<widget  name="key_yellow" position="280,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="yellow" font="Regular;20" transparent="1"/>
			<widget  name="key_blue" position="420,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="blue" font="Regular;20" transparent="1"/>
			<widget name="text" position="5,40" size="550,20" font="Regular;16" halign="left" valign="center"/>
			<widget name="config" position="5,65" size="550,150" scrollbarMode="showOnDemand"/>
		</screen>"""

	def __init__(self, session, pars):
		Screen.__init__(self, session)
		if pars:
			text = _("Manager Autofs - edited record: %s") % pars[1].split('/')[2]
		else:
			text = _("Manager Autofs - create new record")

		self.setTitle(text)
		self.pars = pars
		self["text"] = Label()

		self["key_red"] = Button(_("Close"))
		self["key_green"] = Button(_("Ok"))

		self.list = [ ]
		self.onChangedEntry = [ ]
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)		

		self["actions"] = ActionMap(["SetupActions","OkCancelActions","ColorActions"],
			{
			"ok":		self.keyOk,
			"cancel":	self.keyClose,
			"green":	self.keyOk,
			"red":		self.keyClose,
			 }, -1)

		self.createConfig()
		self.actualizeString()

	def createConfig(self):
		self.setDefault()

		self.list = [ ]

		if self.pars:
			if self.pars[0] == "x":
				cfg.enabled.value = True
			cfg.mountpoint.value = self.pars[1].split('/')[2]
			cfg.autofile.value = self.pars[2].split('.')[1]
			if self.pars[3] == "--ghost":
				cfg.ghost.value = True
#			if self.pars[4] == "--timeout":
#				cfg.timeout.value = True
		else:
			cfg.mountpoint.value = cfg.mountpoint.value.split('/')[2]

		self.list.append(getConfigListEntry(_("enabled"), cfg.enabled))
		self.list.append(getConfigListEntry(_("mountpoint name"), cfg.mountpoint))
		self.list.append(getConfigListEntry(_("auto.name"), cfg.autofile))
		self.list.append(getConfigListEntry(_("ghost"), cfg.ghost))
#		self.list.append(getConfigListEntry(_("timeout"), cfg.ghost))
#		if cfg.timeout.value:
#			self.list.append(getConfigListEntry(_("delay"), cfg.delay))

		self["config"].list = self.list
		self["config"].setList(self.list)

	def setDefault(self):
		cfg.enabled.value = cfg.enabled.default
		cfg.mountpoint.value = cfg.mountpoint.default
		cfg.autofile.value = cfg.autofile.default
		cfg.ghost.value == cfg.ghost.default

	def changedEntry(self):
		self.actualizeString()
	
	def actualizeString(self):
		string = "#" if not cfg.enabled.value else ""
		string += "/mnt/%s" % cfg.mountpoint.value
		string += " "
		string += "auto.%s" % cfg.autofile.value
		string += " "
		string += "--ghost" if cfg.ghost.value else ""
		self["text"].setText(string)

	def keyOk(self):
		#save file
		self.close(True)

	def keyClose(self):
		self.close()

# parameters for selected auto. file
config.plugins.mautofs.localdir = NoSave(ConfigText(default = "dirname", visible_width = 30, fixed_size = False))
config.plugins.mautofs.fstype = NoSave(ConfigSelection(default="cifs", choices=[("cifs","cifs"),("nfs","nfs") ]))
config.plugins.mautofs.rw = NoSave(ConfigYesNo(default=False))
config.plugins.mautofs.user = NoSave(ConfigText(default="root", fixed_size=False))
config.plugins.mautofs.passwd = NoSave(ConfigPassword(default="password", fixed_size=False))

config.plugins.mautofs.useddomain = NoSave(ConfigYesNo(default=False))
config.plugins.mautofs.domain = NoSave(ConfigText(default="domain.local", fixed_size=False))
config.plugins.mautofs.noperm = NoSave(ConfigYesNo(default=False))

config.plugins.mautofs.ip = NoSave(ConfigIP(default=[192,168,1,100]))
config.plugins.mautofs.remotedir = NoSave(ConfigText(default = "dirname", visible_width = 30, fixed_size = False))
config.plugins.mautofs.noatime = NoSave(ConfigYesNo(default=True))
config.plugins.mautofs.noserverino = NoSave(ConfigYesNo(default=True))
config.plugins.mautofs.sec = NoSave(ConfigSelection(default = "", choices = [("", _("no")),("ntlm", "ntlm"),("ntlm2", "ntlm2") ]))
config.plugins.mautofs.iocharset = NoSave(ConfigSelection(default="utf8", choices=[("", _("no")),("utf8", "utf8"),("1250", "1250") ]))
config.plugins.mautofs.rsize = NoSave(ConfigSelection(default="", choices=[("", _("no")),("4096", "4096"),("8192", "8192"),("16384", "16384"),("32768", "32768") ]))
config.plugins.mautofs.wsize = NoSave(ConfigSelection(default="", choices=[("", _("no")),("4096", "4096"),("8192", "8192"),("16384", "16384"),("32768", "32768") ]))

class ManagerAutofsAutoEdit(Screen, ConfigListScreen):
	skin = """
		<screen position="center,center" size="560,520">
			<ePixmap name="red" position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue" position="420,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget  name="key_red" position="0,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="red" font="Regular;20" transparent="1"/>
			<widget  name="key_green" position="140,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="green" font="Regular;20" transparent="1"/>
			<widget  name="key_yellow" position="280,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="yellow" font="Regular;20" transparent="1"/>
			<widget  name="key_blue" position="420,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="blue" font="Regular;20" transparent="1"/>
			<widget name="text" position="5,42" size="550,56" font="Regular;14" halign="left" valign="center"/>
			<widget name="config" position="5,100" size="550,400" scrollbarMode="showOnDemand"/>
		</screen>"""

	def __init__(self, session, filename, line, new=False):
		Screen.__init__(self, session)
		self.setTitle(_("Manager Autofs - edited autofile: %s") % filename)
		self.session = session
		self.new = new
		self["text"] = Label("")
		self.autoName = filename
		
		self["key_red"] = Button(_("Close"))
		self["key_green"] = Button(_("Ok"))
		
		self.list = [ ]
		self.onChangedEntry = [ ]
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)		

		self["actions"] = ActionMap(["SetupActions","OkCancelActions","ColorActions"],
			{
#			"ok":		self.keyOk,
			"cancel":	self.keyClose,
			"green":	self.keyOk,
			"red":		self.keyClose,
#			"yellow":	self.keyEdit,
#			"blue": 	self.keyAdd,
			 }, -1)

		if self.new:
			self.setDefaultPars()
		else:
			self.parseParams(line)
		self.createConfig()

	def createConfig(self):
		self.list = [ ]

		self.list.append(getConfigListEntry(_("local directory"), cfg.localdir))
		self.list.append(getConfigListEntry(_("fstype"), cfg.fstype))
		self.list.append(getConfigListEntry(_("rw"), cfg.rw))
		self.list.append(getConfigListEntry(_("user"), cfg.user))
		self.list.append(getConfigListEntry(_("password"), cfg.passwd))
		self.useddomain = _("domain")
		self.list.append(getConfigListEntry(self.useddomain, cfg.useddomain))
		if cfg.useddomain.value:
			self.list.append(getConfigListEntry(_("domain name"), cfg.domain))
			self.list.append(getConfigListEntry(_("noperm"), cfg.noperm))
		self.list.append(getConfigListEntry(_("noatime"), cfg.noatime))
		self.list.append(getConfigListEntry(_("noserverino"), cfg.noserverino))
		self.list.append(getConfigListEntry(_("ip"), cfg.ip))
		self.list.append(getConfigListEntry(_("remote directory"), cfg.remotedir))
		self.list.append(getConfigListEntry(_("security"), cfg.sec))
		self.list.append(getConfigListEntry(_("iocharset"), cfg.iocharset))
		self.list.append(getConfigListEntry(_("rsize"), cfg.rsize))
		self.list.append(getConfigListEntry(_("wsize"), cfg.wsize))

		self["config"].list = self.list
		self["config"].setList(self.list)

		self.fillString()

	def changedEntry(self):
		if self["config"].getCurrent()[0] == self.useddomain:
			self.createConfig()
		self.fillString()

	def fillString(self):
		self["text"].setText(self.actualizeString())

	def actualizeString(self):
		string = cfg.localdir.value
		string += " "
		string += "-fstype=%s," % cfg.fstype.value
		string += "rw," if cfg.rw.value else ""
		string += "user=%s," % cfg.user.value
		string += "password=%s," % cfg.passwd.value
		string += ("domain=%s," % cfg.domain.value) if cfg.useddomain.value else ""
		string += "noperm," if cfg.noperm.value else ""
		string += "noatime," if cfg.noatime.value else ""
		string += "noserverino," if cfg.noserverino.value else ""
		string += ("iocharset=%s," % cfg.iocharset.value) if cfg.iocharset.value else ""
		string += ("rsize=%s," % cfg.rsize.value) if cfg.rsize.value else ""
		string += ("wsize=%s," % cfg.wsize.value) if cfg.wsize.value else ""
		string += ("sec=%s," % cfg.sec.value) if cfg.sec.value else ""
		string += " "
		ip = "%s.%s.%s.%s" % (tuple(cfg.ip.value))
		string += "://%s/%s" % (ip, cfg.remotedir.value)
		return string

	def writeFile(self):
		if not self.new:
			bakName = self.autoName + "_bak"
			os.rename(self.autoName, bakName)
		fo = open(self.autoName, "w")
		fo.write("%s\n" % self["text"].getText())
		fo.close()

	def keyOk(self):
#		self.writeFile()
		self.close(self["text"].getText())

	def keyClose(self):
		self.close()

	def parseParams(self, line):
		if line:
			self["text"] = Label("%s" % line)
			parts = line.split()
			self.parse(parts)

	def setDefaultPars(self):
		# set default pars before parsing line
		cfg.localdir.value = cfg.localdir.default
		cfg.ip.value = cfg.ip.default
		cfg.remotedir.value = cfg.remotedir.default
		cfg.fstype.value = cfg.fstype.default
		cfg.user.value = cfg.user.default
		cfg.passwd.value = cfg.passwd.default
		cfg.sec.value = cfg.sec.default
		cfg.iocharset.value = cfg.iocharset.default
		cfg.rsize.value = cfg.rsize.default
		cfg.wsize.value = cfg.wsize.default
		cfg.useddomain.value = cfg.useddomain.default
		cfg.domain.value = cfg.domain.default
		cfg.noperm.value = cfg.noperm.default
		cfg.noatime.value = cfg.noatime.default
		cfg.noserverino.value = cfg.noserverino.default

	def parse(self, parts):
		self.setDefaultPars()
		# parse line
		for x in parts[1].split(','):
#			print x
			if "-fstype" in x:
				cfg.fstype.value=x.split('=')[1]
			elif "user" in x:
				cfg.user.value=x.split('=')[1]
			elif "password" in x:
				cfg.passwd.value=x.split('=')[1]
			elif "sec" in x:
				cfg.sec.value=x.split('=')[1]
			elif "iocharset" in x:
				cfg.iocharset.value=x.split('=')[1]
			elif "rsize" in x:
				cfg.rsize.value=x.split('=')[1]
			elif "wsize" in x:
				cfg.wsize.value=x.split('=')[1]
			elif "domain" in x:
				cfg.useddomain.value = True
				cfg.domain.value=x.split('=')[1]
			elif hasattr(x, "rw"):
				cfg.fstype.value=True
			elif hasattr(x, "noperm"):
				cfg.noperm.value=True
			elif hasattr(x, "noatime"):
				cfg.noatime.value=True
			elif hasattr(x, "noserverino"):
				cfg.noserverino.value=True
			else:
				pass
		# dir name
		cfg.localdir.value = parts[0].strip()
		# ip and shared remote dir
		remote = parts[2].split('/')
		cfg.ip.value = self.convertIP(remote[2])
		cfg.remotedir.value = remote[3]

	def convertIP(self, ip):
		strIP = ip.split('.')
		ip = []
		for x in strIP:
			ip.append(int(x))
		return ip

class ManagerMultiAutofsAutoEdit(Screen):
	skin = """
		<screen name="ManagerMultiAutofsAutoEdit" position="center,center" size="680,400" backgroundColor="#00000000">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on"/>
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on"/>
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on"/>
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on"/>
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1"/>
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1"/>
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1"/>
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1"/>
			<widget source="list" render="Listbox" position="5,40" size="670,320" backgroundColor="#00000000" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
				{"templates":
					{"default": (40,[
							MultiContentEntryText(pos = (5, 0), size = (660, 24), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 0 is the name
							MultiContentEntryText(pos = (5, 24), size = (660, 15), font=1, flags = RT_HALIGN_LEFT, text = 1), # index 1 is the description
						])
					},
					"fonts": [gFont("Regular", 22),gFont("Regular", 12)],
					"itemHeight": 40
				}
				</convert>
			</widget>
			<widget name="info" position="5,380" zPosition="10" size="660,15" font="Regular;11" backgroundColor="#00000000" halign="left" valign="center"/>
		</screen>"""

	def __init__(self, session, name = None):
		Screen.__init__(self, session)
		self.session = session
		self.name = name

		self["shortcuts"] = ActionMap(["SetupActions","OkCancelActions","ColorActions"],
		{
			"ok": self.keyEdit,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keyOk,
			"yellow": self.keyAdd,
			"blue": self.keyErase,
		}, -1)

		self.list = []
		self["list"] = List(self.list)
		if not self.selectionChanged in self["list"].onSelectionChanged:
			self["list"].onSelectionChanged.append(self.selectionChanged)

		self["key_red"] = Label(_("Close"))
		self["key_green"] = Label("Ok")
		self["key_yellow"] = Label(_("Add"))
		self["key_blue"] = Label(_("Erase"))

		self["info"] = Label("")

		self.onShown.append(self.setWindowTitle)
		self.onLayoutFinish.append(self.readFile)

	def setWindowTitle(self):
		self.setTitle(_("Autofs file: %s") % self.name)

	def readFile(self):
		if self.name:
			self.list = []
			for x in open(self.name, "r"):
				line = x.replace('\n','').strip()
				if line:
					p = line.split()
					name = p[0]
					self.list.append((name, line))

			self['list'].setList(self.list)

	def selectionChanged(self):
		current = self["list"].getCurrent()
		if current:
			self["info"].setText("%s" % current[1])

	def keyEdit(self):
		current = self["list"].getCurrent()
		if current:
			index = self["list"].getIndex()
			def callBackWriteLine(index, text=""):
				if text:
					name = text.split()[0]
					self.changeItem(index, (name, text))
			self.session.openWithCallback(boundFunction(callBackWriteLine, index), ManagerAutofsAutoEdit, current[0], current[1], False)

	def keyOk(self):
		self.backupFile(self.name,"bak")
		self.saveFile(self.name)
		self.close()

	def keyAdd(self):
		def callBackAdd(text=""):
			if text:
				name = text.split()[0]
				self.addItem((name, text))
		self.session.openWithCallback(boundFunction(callBackAdd), ManagerAutofsAutoEdit, _("New"), "", True)

	def keyErase(self):
		def callbackErase(value=False):
			if value:
				index = self["list"].getIndex()
				self.removeItem(index)
		name = self["list"].getCurrent()[0]
		self.session.openWithCallback(callbackErase, MessageBox, _("Really erase record: '%s'?") % name, type=MessageBox.TYPE_YESNO, default=False)

	def backupFile(self, name, ext):
		os.rename(name, "%s_%s" % (name,ext))

	def saveFile(self, name):
		fo = open(name, "w")
		for data in self.list:
			fo.write("%s\n" % data[1])
		fo.close()

# has no effect for autofs if is record commented
	def disableItem(self, index, data):
		if data[1][0] != "#":
			line = "#" + data[1]
			self.changeItem(index, (data[0], line))

	def enableItem(self, index, data):
		if data[1][0] == "#":
			line = data[1][1:]
			self.changeItem(index, (data[0], line))

	def changeItemStatus(self, index, data):
		if data[1][0] == "#":
			line = data[1][1:]
		else:
			line = "#" + data[1]
		self.changeItem(index, (data[0], line))
#
	def changeItem(self, index, new):
		self["list"].modifyEntry(index,(new[0], new[1]))

	def addItem(self, new):
		self.list.append((new[0], new[1]))

	def removeItem(self, index):
		self.list.pop(index)
		self["list"].updateList(self.list)

	def keyCancel(self):
		self.close()

class NonModalMessageBoxDialog(Screen):
	skin="""
		<screen name="NonModalMessageBoxDialog" position="center,center" size="470,120" backgroundColor="#00404040" zPosition="2" flags="wfNoBorder">
			<widget name="message" position="center,center" size="460,110" font="Regular;20" valign="center" halign="center"/>
		</screen>
	"""
	def __init__(self, session, text="", delay=0):
		Screen.__init__(self, session)
		self.text = text
		self.delay = delay
		self["message"]=Label()

		self.timer = enigma.eTimer()
		self.timer.callback.append(self.timerLoop)

		self.onLayoutFinish.append(self.timerStart)

	def timerStart(self):
		self["message"].setText(self.text)
		self.timer.start(1000, True)

	def timerLoop(self):
		self.delay -= 1
		if self.delay > 0:
			self.timer.start(1000, True)
		else:
			self.session.deleteDialog(self)