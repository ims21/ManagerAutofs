#
#  Manager Autofs
#
VERSION = 1.10
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
from Components.ChoiceList import ChoiceList, ChoiceEntryComponent
from Tools.BoundFunction import boundFunction
from Screens.ChoiceBox import ChoiceBox
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
		<screen name="ManagerAutofsMasterSelection" title="Select auto mount file with OK" position="fill" flags="wfNoBorder">
			<panel name="PigTemplate"/>
			<panel name="ButtonTemplate_RGYB"/>
			<panel name="TextTemplate"/>
			<widget name="list" position="780,100" size="1110,912" scrollbarMode="showOnDemand"/>
		</screen>
	"""
	def __init__(self, session, *args):
		Screen.__init__(self, session)
		self.session = session
		self.setTitle(_("ManagerAutofs v.%s - use %sMenu%s or %sOK%s on record") % (VERSION, yC,fC,yC,fC))

		self.data = ''
		self.container = enigma.eConsoleAppContainer()
		self.container.appClosed.append(self.appClosed)
		self.container.dataAvail.append(self.dataAvail)
		self["status"] = Label()
		self["statusbar"] = Label()

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Edit master record"))
		self["key_yellow"] = Button(_("Edit auto file"))

		self["list"] = ChoiceList(list=[ChoiceEntryComponent('',((_("Reading auto.master file - Please wait...")), "Waiter"))])

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "KeyboardInputActions", "MenuActions"],
		{
			"ok": self.menu,
			"cancel": boundFunction(self.close, None),
			"red": boundFunction(self.close, None),
			"green": self.editMasterRecord,
			"yellow": self.editAutofile,
			"up": self.keyUp,
			"down": self.keyDown,
			"left": self.keyLeft,
			"right": self.keyRight,
			"upRepeated": self.keyUp,
			"downRepeated": self.keyDown,
			"leftRepeated": self.keyLeft,
			"rightRepeated": self.keyRight,
			"menu": self.menu,
		}, -1)
		self.msgNM=None
		self.onLayoutFinish.append(self.readMasterFile)

	def keyLeft(self):
		self.clearTexts()
		self["list"].instance.moveSelection(self["list"].instance.pageUp)

	def keyRight(self):
		self.clearTexts()
		self["list"].instance.moveSelection(self["list"].instance.pageDown)

	def keyUp(self):
		self.clearTexts()
		self["list"].instance.moveSelection(self["list"].instance.moveUp)

	def keyDown(self):
		self.clearTexts()
		self["list"].instance.moveSelection(self["list"].instance.moveDown)

	def clearTexts(self):
		self.MessageBoxNM()
		self["status"].setText("")
		self["statusbar"].setText("")

	def readMasterFile(self, edit=None, action=None):
		# 0 - status 1 - mountpoint 2 - autofile 3 - ghost
		list = []
		self.masterList = []

		m = None
		fi = open( MASTERFILE, "r")
		for line in fi:
			line = line.replace('\n','')
			if '#' in line:
				status = ("disabled")
				color = dC
				line = line[1:]
			else:
				status = ("enabled")
				color = eC
			line = status + ' ' + line
			m = line.split(' ')
			if not action and edit: 	# change record's parameters
				if m[1] == edit[1] and m[2] == edit[2]:
					m = edit
			if action == "remove" and edit: # remove record
				if m[1] == edit[1] and m[2] == edit[2]:
					continue
			list.append(ChoiceEntryComponent('',('{0:}{1:40}{2:30}'.format(color, m[1], m[2]), m[1], m[2], m[3], m[0])))
			self.masterList.append((m[0], m[1], m[2], m[3]))
		fi.close()
		if edit and action == "new": 		# add new record
			if edit[0] == "disabled":
				color = dC
			else:
				color = eC
			list.append(ChoiceEntryComponent('',('{0:}{1:40}{2:30}'.format(color, edit[1], edit[2]), edit[1], edit[2], edit[3], edit[0])))
			self.masterList.append((edit[0], edit[1], edit[2], edit[3]))
		self["list"].setList(list)

	def saveMasterFile(self):
		fo = open( MASTERFILE, "w")
		for x in self.masterList:
			fo.write("%s%s %s %s\n" % ("" if x[0]=="enabled" else "#", x[1], x[2], x[3]))
		fo.close()

	def menu(self):
		menu = []
		buttons = []
		text = _("Select operation:")
		sel = self["list"].l.getCurrentSelection()
		if sel:
			recordname = "%s" % (sel[0][1].split('/')[2])
			autoname = "%s" % sel[0][2].split('/')[2]
			menu.append((_("Edit - %s%s%s" % (yC,recordname,fC)),0))
			buttons = ["4"]
		menu.append((_("Add"),1))
		menu.append((_("Remove"),2))
		buttons += ["1", "8"]
		if sel:
			menu.append((_("Edit - %s%s%s" % (yC,autoname,fC)),10))
			buttons += ["yellow"]
		menu.append((_("Reload autofs"),13))
		menu.append((_("Reload autofs with restart GUI"),14))
		buttons += ["green", "red"]

		self.session.openWithCallback(self.menuCallback, ChoiceBox, title=text, list=menu, keys=buttons)

	def menuCallback(self, choice):
		if choice is None:
			return
		sel = self["list"].l.getCurrentSelection()
		if sel is None:
			return
		if choice[1] == 0:
			self.editMasterRecord()
		elif choice[1] == 1:
			self.addMasterRecord()
		elif choice[1] == 2:
			self.removeMasterRecord()
		elif choice[1] == 10:
			self.editAutofile()
		elif choice[1] == 13:
			self.restartAutofs()
		elif choice[1] == 14:
			self.restartAutofs(restart=True)
		else:
			return

	def restartAutofs(self, restart=False):
		cmd = '/etc/init.d/autofs reload'
		if restart:
			cmd += '; killall enigma2'
		if self.container.execute(cmd):
			print "[ManagerAutofs] failed to execute"
			self.showOutput()

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

	def addMasterRecord(self):
		def callback(change=False):
			if change:
				add = ""
				mountpoint = "/mnt/%s" % cfg.mountpoint.value
				autofile = "/etc/auto.%s" % cfg.autofile.value
				enabled =  cfg.enabled.value and "enabled" or "disabled"
				ghost = cfg.ghost.value and "--ghost" or ""
				add = (enabled, mountpoint, autofile, ghost)
				self.readMasterFile(edit=add, action="new")
				self.saveMasterFile()
		self.session.openWithCallback(boundFunction(callback), ManagerAutofsMasterEdit, None)

	def editMasterRecord(self):
		def callback(change=False):
			if change:
				edit = ""
				mountpoint = "/mnt/%s" % cfg.mountpoint.value
				autofile = "/etc/auto.%s" % cfg.autofile.value
				enabled =  cfg.enabled.value and "enabled" or "disabled"
				ghost = cfg.ghost.value and "--ghost" or ""
				edit = (enabled, mountpoint, autofile, ghost)
				self.readMasterFile(edit=edit)
				self.saveMasterFile()
		sel = self["list"].l.getCurrentSelection()
		if sel is None:
			return
		self.session.openWithCallback(boundFunction(callback), ManagerAutofsMasterEdit, sel)

	def removeMasterRecord(self):
		def callback(change=False):
			if change:
				rm = ""
				mountpoint = sel[0][1]
				autofile = sel[0][2]
				enabled = sel[0][4]
				ghost = sel[0][3]
				rm = (enabled, mountpoint, autofile, ghost)
				self.readMasterFile(edit=rm, action="remove")
				self.saveMasterFile()
		sel = self["list"].l.getCurrentSelection()
		if sel is None:
			return
		#TODO ... question, if remove autofile too, then delete it too
		self.session.openWithCallback(callback, MessageBox, _("Remove record for %s?") % sel[0][1] , type=MessageBox.TYPE_YESNO, default=False, simple=True)

	def editAutofile(self):
		def callBack():
			pass
		sel = self["list"].l.getCurrentSelection()
		if sel is None:
			return
		name = sel[0][2]
		lines = self.getAutoLines(name)
		if lines == 1:
			self.session.openWithCallback(callBack, ManagerAutofsAutoEdit, name)
		elif lines > 1:
			self.MessageBoxNM(True, _("File %s with %d lines. Not supported yet") % (name, lines), 5)
			#TODO: nejak vyresit jak na viceradkovy soubor
			#self.session.openWithCallback(callBack, ManagerAutofsAutoEdit, name) # dodelat
		elif lines == -1:
			self.MessageBoxNM(True, _("File %s is missing!") % name, 5)
			#TODO: create
		else:
			self.MessageBoxNM(True, _("File %s is empty!") % name, 5)
			#TODO: add line

	def getAutoLines(self, name):
		nr = 0
		if not os.path.exists(name):
			return -1
		fi = open(name, "r")
		for mline in fi:
			mline = mline.replace('\n','')
			if mline:
				nr += 1
		fi.close()
		return nr

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
		<screen position="center,center" size="560,320">
			<ePixmap name="red" position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue" position="420,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget  name="key_red" position="0,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="red" font="Regular;20" transparent="1"/>
			<widget  name="key_green" position="140,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="green" font="Regular;20" transparent="1"/>
			<widget  name="key_yellow" position="280,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="yellow" font="Regular;20" transparent="1"/>
			<widget  name="key_blue" position="420,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="blue" font="Regular;20" transparent="1"/>
			<widget name="text" position="5,40" size="550,25" font="Regular;22" halign="left"/>
			<widget name="config" position="5,70" size="550,200" scrollbarMode="showOnDemand"/>
		</screen>"""

	def __init__(self, session, pars):
		Screen.__init__(self, session)
		if pars:
			text = _("ManagerAutofs - edited record: %s") % pars[0][1].split('/')[2]
		else:
			text = _("ManagerAutofs - create new record")

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
			if self.pars[0][4] == "enabled":
				cfg.enabled.value = True
			cfg.mountpoint.value = self.pars[0][1].split('/')[2]
			cfg.autofile.value = self.pars[0][2].split('.')[1]
			if self.pars[0][3] == "--ghost":
				cfg.ghost.value = True
#			if self.pars[0][4] == "--timeout":
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
config.plugins.mautofs.fstype = NoSave(ConfigSelection(default="cifs", choices=[("cifs",_("cifs")),("nfs",_("nfs")) ]))
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
config.plugins.mautofs.sec = NoSave(ConfigSelection(default = "", choices = [("", _("no")),("ntlm", _("ntlm")),("ntlm2", _("ntlm2")) ]))
config.plugins.mautofs.iocharset = NoSave(ConfigSelection(default="utf8", choices=[("", _("no")),("utf8", _("utf8")),("1250", _("1250")) ]))
config.plugins.mautofs.rsize = NoSave(ConfigSelection(default="", choices=[("", _("no")),("4096", _("4096")),("8192", _("8192")),("16384", _("16384")),("32768", _("32768")) ]))
config.plugins.mautofs.wsize = NoSave(ConfigSelection(default="", choices=[("", _("no")),("4096", _("4096")),("8192", _("8192")),("16384", _("16384")),("32768", _("32768")) ]))

#movie -fstype=cifs,rw,noperm,domain=sps.local,user=render,password=render21,iocharset=utf8 ://192.168.1.230/movie
#hdd -fstype=cifs,username=root,password=dreambox,rsize=8192,wsize=32768,noatime,noserverino,iocharset=utf8,sec=ntlm, ://192.168.1.219/hdd

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
			<widget name="text" position="5,40" size="550,25" font="Regular;22" halign="left"/>
			<widget name="config" position="5,70" size="550,400" scrollbarMode="showOnDemand"/>
		</screen>"""

	def __init__(self, session, filename):
		Screen.__init__(self, session)
		self.setTitle(_("ManagerAutofs - edited autofile: %s") % filename)
		self.session = session
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

		self.parseParams()
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

	def changedEntry(self):
		if self["config"].getCurrent()[0] == self.useddomain:
			self.createConfig()
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
		bakName = self.autoName + "_bak"
		os.rename(self.autoName, bakName)

		fo = open(self.autoName, "w")
		fo.write("%s\n" % self["text"].getText())
		fo.close()

	def keyOk(self):
		self.writeFile()
		self.close()

	def keyClose(self):
		self.close()

	def parseParams(self):
		mount = open(self.autoName, "r")
		for mline in mount:
			line = mline.replace('\n','').strip()
			if line:
				self["text"] = Label("%s" % line)
				parts = line.split()
				self.parse(parts)
		mount.close()

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
			print x
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