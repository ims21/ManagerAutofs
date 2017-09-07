#
#  Manager Autofs
#
VERSION = "1.43"
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

from helptexts import ManagerAutofsHelp

config.plugins.mautofs = ConfigSubsection()
# parameters for auto.master file
config.plugins.mautofs.enabled = NoSave(ConfigYesNo(default = False))
config.plugins.mautofs.mountpoint = NoSave(ConfigText(default = "/mnt/remote", visible_width = 30, fixed_size = False))
config.plugins.mautofs.autofile = NoSave(ConfigText(default = "remote", visible_width = 30, fixed_size = False ))
config.plugins.mautofs.ghost = NoSave(ConfigYesNo(default = True))
config.plugins.mautofs.timeout = NoSave(ConfigYesNo(default = False))
config.plugins.mautofs.timeouttime = NoSave(ConfigInteger(default = 60, limits = (1, 300)))

cfg = config.plugins.mautofs

AUTOMASTER="/etc/auto.master"
AUTOBACKUP="/etc/backup.cfg"

def hex2strColor(argb):
	out = ""
	for i in range(28,-1,-4):
		out += "%s" % chr(0x30 + (argb>>i & 0xf))
	return out

yC = "\c%s" % hex2strColor(int(skin.parseColor("selectedFG").argb()))
gC = "\c%s" % hex2strColor(int(skin.parseColor("#0000ff80").argb()))
bC = "\c%s" % hex2strColor(int(skin.parseColor("#000080ff").argb()))
fC = "\c%s" % hex2strColor(int(skin.parseColor("foreground").argb()))

_X_ = "%sx%s" % (gC,fC)

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
			<widget name="mntpoint" position="55,40" size="250,20" font="Regular;14" halign="left" valign="center" zPosition="1"/>
			<widget name="autofile" position="305,40" size="250,20" font="Regular;14" halign="left" valign="center" zPosition="1"/>
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

		self["mntpoint"] = Label(_("Mountpoint"))
		self["autofile"] = Label(_("auto.file"))

		self["shortcuts"] = ActionMap(["SetupActions","OkCancelActions","ColorActions","MenuActions","HelpActions"],
		{
			"ok": self.editMasterRecord,
			"cancel": self.keyClose,
			"red": self.keyClose,
			"green": self.keyOk,
			"blue": self.changeMasterRecordStatus,
			"yellow": self.editAutofile,
			"menu": self.menu,
			"displayHelp": self.help,
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

		if os.path.exists(AUTOMASTER):
			copyfile(AUTOMASTER, AUTOMASTER+".bak")
		else:
			f = open(AUTOMASTER, "w")
			f.write("%s%s /etc/auto.%s %s\n" % ("#", cfg.mountpoint.default, cfg.autofile.default, "--ghost" if cfg.ghost.default else ""))
			f.close()

		self.onLayoutFinish.append(self.readMasterFile)

	def setWindowTitle(self):
		self.setTitle(_("Manager Autofs v.%s - press %sOK%s on record or use %sMenu%s") % (VERSION, yC,fC,yC,fC))

	def readMasterFile(self):
		# mandatory: 0 - status 1 - mountpoint 2 - autofile  Optional pars: 3
		self.list = []

		for line in open(AUTOMASTER, "r"):
			line = line.replace('\n','')
			if '#' in line:
				status = ""
				line = line[1:]
			else:
				status = "x"
			line = status + ' ' + line
			m = line.split(' ')
			if len(m) < 3: # wrong line
				continue

			self.list.append((_X_ if m[0] == "x" else '', m[1], m[2], self.parseOptional(m)))
		self['list'].setList(self.list)

	def parseOptional(self, m):
		optional = ""
		for i in range(3, len(m)):
			optional += m[i]
			optional += " "
		return optional.strip()

	def saveMasterFile(self):
		fo = open(AUTOMASTER, "w")
		for x in self.list:
			fo.write(self.formatString(x) + '\n')
		fo.close()

	def formatString(self, x):
		string = "%s%s %s" % ("" if x[0] == _X_ else "#", x[1], x[2])
		if len(x) > 3:
			string += " " + x[3]
		return string

	def selectionChanged(self):
		self.refreshText()

	def refreshText(self):
		self.clearTexts()
		sel = self["list"].getCurrent()
		if sel:
			if sel[0] == _X_:
				text = _("Disable")
			else:
				text = _("Enable")
			self["key_blue"].setText(text)
			self["status"].setText(self.formatString(sel))

	def clearTexts(self):
		self.MessageBoxNM()
		self["statusbar"].setText("")

	def keyClose(self):
		self.updateAutofs()
		self.close()

	def keyOk(self):
		self.saveMasterFile()
		self.updateAutofs()
		self.close()

	def help(self):
		self.session.open(ManagerAutofsHelp)

	def menu(self):
		menu = []
		buttons = []

		sel = self["list"].getCurrent()
		if sel:
			recordname = "%s" % (sel[1].split('/')[2])
			autoname = "%s" % sel[2].split('/')[2]
			menu.append(((_("Edit record:") + "  %s%s%s" % (gC,recordname,fC)),0))
			buttons = ["4"]
		menu.append((_("New record"),1))
		menu.append(((_("Remove record:") + "  %s%s%s" % (gC,recordname,fC)),2))
		buttons += ["1", "8"]
		if sel:
			menu.append(((_("Edit -") + " %s%s%s" % (bC,autoname,fC)),10))
			menu.append(((_("Add line - ") + " %s%s%s" % (bC,autoname,fC)),11))
			menu.append(((_("Remove -") + " %s%s%s" % (bC,autoname,fC)),12))
			buttons += ["yellow", "", "red"]
		menu.append((_("Help"),14))
		buttons += [""]
		menu.append((_("Utility"),15))
		buttons += ["menu"]

		text = _("Select operation:")
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
			elif choice[1] == 14:
				self.help()
			elif choice[1] == 15:
				self.utilitySubmenu()
			else:
				return

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
				enabled =  cfg.enabled.value and _X_ or ""
				ghost = cfg.ghost.value and "--ghost" or ""
				optional = ghost + (" --timeout=%s" % cfg.timeouttime.value if cfg.timeout.value else '')
				add = (enabled, mountpoint, autofile, optional )
				self.addItem(add)
		self.session.openWithCallback(boundFunction(callbackAdd), ManagerAutofsMasterEdit, None)

	def editMasterRecord(self):
		def callbackEdit( index, change = False):
			if change:
				mountpoint = "/mnt/%s" % cfg.mountpoint.value
				autofile = "/etc/auto.%s" % cfg.autofile.value
				enabled =  cfg.enabled.value and _X_ or ""
				ghost = cfg.ghost.value and "--ghost" or ""
				optional = ghost + (" --timeout=%s" % cfg.timeouttime.value if cfg.timeout.value else '')
				edit = (enabled, mountpoint, autofile, optional )
				self.changeItem(index, edit)
		sel = self["list"].getCurrent()
		if sel:
			index = self["list"].getIndex()
			self.session.openWithCallback(boundFunction(callbackEdit, index), ManagerAutofsMasterEdit, sel)

	def removeMasterRecord(self):
		def callbackRemove(index, autofile, retval=False):
			if retval > 1:	# remove auto file - must be removed before than record due valid "sel" in list!!!
				if os.path.exists(autofile):
					bakName = autofile + ".del"
					os.rename(autofile, bakName)
			if retval:	# remove record
				self.removeItem(index)

		sel = self["list"].getCurrent()
		if sel:
			index = self["list"].getIndex()
			record = sel[1]
			autofile = sel[2]
			removing = [(_("Nothing"), False), (_("Record '%s' only") % record, 1), (_("Record '%s' and its file '%s'") % (record, autofile), 2) ]
			self.session.openWithCallback(boundFunction(callbackRemove, index, autofile), MessageBox, _("What all do You want to remove?"), type=MessageBox.TYPE_YESNO, default=False, list=removing)

	def changeItemStatus(self, index, data):
		if data[0] == _X_:
			status = ""
		else:
			status = _X_
		self.changeItem(index, (status ,data[1], data[2], data[3] if len(data) > 3 else ''))

	def changeItem(self, index, new):
		self["list"].modifyEntry(index,(new[0], new[1], new[2], new[3] if len(new) > 3 else ''))
		self.refreshText()

	def addItem(self, new):
		self.list.append((new[0], new[1], new[2], new[3] if len(new) > 3 else ''))
		self.refreshText()

	def removeItem(self, index):
		self.list.pop(index)
		self["list"].updateList(self.list)
		self.refreshText()

	def addAutofileLine(self):
		sel = self["list"].getCurrent()
		if sel:
			name = sel[2]
			self.session.open(ManagerAutofsMultiAutoEdit, name)

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
				self.session.open(ManagerAutofsMultiAutoEdit, name)
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
					bakName = name + ".del"
					os.rename(name, bakName)
		sel = self["list"].getCurrent()
		if sel:
			name = sel[2]
			self.session.openWithCallback(boundFunction(callBack, name), MessageBox, _("Really remove autofile '%s'?" % name), type=MessageBox.TYPE_YESNO, default=False)

	def utilitySubmenu(self):
		menu = []
		buttons = []

		if os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/AutoBackup/settings-backup.sh'):
			menu.append((_("Update autofs files in AutoBackup"),0))
			menu.append((_("Remove unused autofs files in AutoBackup"),1))
			buttons += ["1","2"]
		menu.append((_("Reload autofs"),4))
		menu.append((_("Restart autofs with GUI restart"),5))
		buttons += ["",""]
		if not os.path.exists('/etc/init.d/autofs'):
			menu.append((_("Install autofs"),6))
			buttons += [""]
		menu.append((_("Reload Bookmarks"),10))
		buttons += [""]

		text = _("Select operation:")
		self.session.openWithCallback(self.utilityCallback, ChoiceBox, title=text, list=menu, keys=buttons)

	def utilityCallback(self, choice):
		if choice is None:
			return
		if choice[1] == 0:
			self.updateAutoBackup()
		elif choice[1] == 1:
			self.refreshAutoBackup()
		elif choice[1] == 4:
			self.updateAutofs()
		elif choice[1] == 5:
			def callback(value=False):
				if value:
					self.updateAutofs(option="restart", restartGui=True)
			self.session.openWithCallback(callback, MessageBox, _("Really reload autofs and restart GUI?"), type=MessageBox.TYPE_YESNO, default=False)
		elif choice[1] == 6:
			self.installAutofs()
		elif choice[1] == 10:
			config.movielist.videodirs.load()
			self.MessageBoxNM(True, _("Done"), 2)
		else:
			return

	def updateAutoBackup(self):	# add missing /etc/auto. lines into /etc/backup.cfg
		def callbackBackup(value=False):
			def readBackup():
				if os.path.exists(AUTOBACKUP):
					return open(AUTOBACKUP, "r").read()
				self.MessageBoxNM(True, _("File '%s' was created!") % AUTOBACKUP, 3)
				return ""
			if value:
				backup = readBackup()
				fo = open(AUTOBACKUP,"a")
				if AUTOMASTER not in backup:
					fo.write(AUTOMASTER+'\n')
				for rec in self.list:
					if rec[2] not in backup:
						fo.write(rec[2]+'\n')
				fo.close()
		self.session.openWithCallback(callbackBackup, MessageBox, _("Update AutoBackup's '%s'?") % AUTOBACKUP, type=MessageBox.TYPE_YESNO, default=False)

	def refreshAutoBackup(self):	# remove unused /etc/auto. lines from /etc/backup.cfg
		def callbackBackup(value=False):
			if value:
				if os.path.exists(AUTOBACKUP):
					copyfile(AUTOBACKUP, AUTOBACKUP + '.bak')

					fi = open(AUTOBACKUP + '.bak',"r")
					fo = open(AUTOBACKUP, "w")

					autofslines = []	# auto.xxxx lines
					lines = []		# other lines
					for l in fi:
						l = l.replace('\n','')
						if not l:
							continue
						if l.startswith('/etc/auto.'):
							for rec in self.list:
								if rec[2] == l:
									autofslines.append(l+'\n')
						else:
							lines.append(l+'\n')
					autofslines.sort()
					fo.write(AUTOMASTER+'\n')
					for auto in autofslines:
						fo.write(auto)
					for f in lines:
						fo.write(f)
					fo.close()
					fi.close()
				else:
					self.MessageBoxNM(True, _("Missing '/etc/backup.cfg'"), 3)
		self.session.openWithCallback(callbackBackup, MessageBox, _("Remove unused lines from '%s'?") % AUTOBACKUP, type=MessageBox.TYPE_YESNO, default=False)

	def installAutofs(self):
		cmd = 'opkg install autofs'
		if self.container.execute(cmd):
			print "[ManagerAutofs] failed to execute"
			self.showOutput()

	def updateAutofs(self, option="reload", restartGui=False):
		if os.path.exists('/etc/init.d/autofs'):
			cmd = '/etc/init.d/autofs %s' % option
			if restartGui:
				cmd += '; killall enigma2'
			if self.container.execute(cmd):
				print "[ManagerAutofs] failed to execute"
				self.showOutput()
		else:
			self.MessageBoxNM(True, _("Autofs is not installed!"), 3)

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

		self.setDefault()
		self.parsePars()
		self.createConfig()
		self.actualizeString()

	def createConfig(self):
		dx = 4*' '
		self.list = [ ]
		self.list.append(getConfigListEntry(_("enabled"), cfg.enabled))
		self.list.append(getConfigListEntry(_("mountpoint name"), cfg.mountpoint))
		self.list.append(getConfigListEntry(_("auto.name"), cfg.autofile))
		self.list.append(getConfigListEntry(_("ghost"), cfg.ghost))
		self.timeout = _("timeout")
		self.list.append(getConfigListEntry(self.timeout, cfg.timeout))
		if cfg.timeout.value:
			self.list.append(getConfigListEntry(dx + _("time"), cfg.timeouttime))
		self["config"].list = self.list
		self["config"].setList(self.list)

	def parsePars(self):
		if self.pars:
			if self.pars[0] == _X_:
				cfg.enabled.value = True
			cfg.mountpoint.value = self.pars[1].split('/')[2]
			cfg.autofile.value = self.pars[2].split('.')[1]
			if len(self.pars) > 3:
				optional = self.pars[3].split()
				for x in optional:
					if "--ghost" in x:
						cfg.ghost.value = True
					if "--timeout" in x:
						cfg.timeout.value = True
						cfg.timeouttime.value = int(x.split('=')[1])
		else:
			cfg.mountpoint.value = cfg.mountpoint.value.split('/')[2]

	def setDefault(self):
		cfg.enabled.value = cfg.enabled.default
		cfg.mountpoint.value = cfg.mountpoint.default
		cfg.autofile.value = cfg.autofile.default
		cfg.ghost.value = cfg.ghost.default
		cfg.timeout.value = cfg.timeout.default
		cfg.timeouttime.value = cfg.timeouttime.default

	def changedEntry(self):
		if self["config"].getCurrent()[0] == self.timeout:
			self.createConfig()
		self.actualizeString()
	
	def actualizeString(self):
		string = "#" if not cfg.enabled.value else ""
		string += "/mnt/%s" % cfg.mountpoint.value
		string += " "
		string += "auto.%s" % cfg.autofile.value
		if cfg.ghost.value:
			string += " "
			string += "--ghost"
		if cfg.timeout.value:
			string += " "
			string += "--timeout"
			string += "=%d" % cfg.timeouttime.value
		self["text"].setText(string)

	def keyOk(self):
		#save file
		self.close(True)

	def keyClose(self):
		self.close()

# parameters for selected auto. file
config.plugins.mautofs.localdir = NoSave(ConfigText(default = "dirname", visible_width = 30, fixed_size = False))
config.plugins.mautofs.fstype = NoSave(ConfigSelection(default="cifs", choices=[("cifs","cifs"),("nfs","nfs"),("auto","auto"),("udf","udf"),("iso9660","iso9660") ]))
config.plugins.mautofs.rw = NoSave(ConfigSelection(default = "", choices = [("", _("no")),("rw", "rw"),("ro", "ro") ]))

config.plugins.mautofs.useduserpass = NoSave(ConfigYesNo(default=True))
config.plugins.mautofs.user = NoSave(ConfigText(default="root", fixed_size=False))
config.plugins.mautofs.passwd = NoSave(ConfigPassword(default="password", fixed_size=False))

config.plugins.mautofs.useddomain = NoSave(ConfigYesNo(default=False))
config.plugins.mautofs.domain = NoSave(ConfigText(default="domain.local", fixed_size=False))
config.plugins.mautofs.noperm = NoSave(ConfigYesNo(default=False))

config.plugins.mautofs.noatime = NoSave(ConfigYesNo(default=True))
config.plugins.mautofs.noserverino = NoSave(ConfigYesNo(default=True))
config.plugins.mautofs.nosuid = NoSave(ConfigYesNo(default=False))
config.plugins.mautofs.nodev = NoSave(ConfigYesNo(default=False))
config.plugins.mautofs.rsize = NoSave(ConfigSelection(default="", choices=[("", _("no")),("4096", "4096"),("8192", "8192"),("16384", "16384"),("32768", "32768") ]))
config.plugins.mautofs.wsize = NoSave(ConfigSelection(default="", choices=[("", _("no")),("4096", "4096"),("8192", "8192"),("16384", "16384"),("32768", "32768") ]))
config.plugins.mautofs.iocharset = NoSave(ConfigSelection(default="utf8", choices=[("", _("no")),("utf8", "utf8"),("1250", "1250") ]))
config.plugins.mautofs.sec = NoSave(ConfigSelection(default = "", choices = [("", _("no")),("ntlm", "ntlm"),("ntlm2", "ntlm2") ]))

config.plugins.mautofs.usedip = NoSave(ConfigYesNo(default=True))
config.plugins.mautofs.ip = NoSave(ConfigIP(default=[192,168,1,100]))
config.plugins.mautofs.dev = NoSave(ConfigSelection(default="dev", choices=[("","no"),("dev","dev") ]))

config.plugins.mautofs.remotedir = NoSave(ConfigText(default = "dirname", visible_width = 30, fixed_size = False))
#user defined string
config.plugins.mautofs.rest = NoSave(ConfigText(default = "", visible_width = 40, fixed_size = False))

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
		self.setTitle(_("Manager Autofs - edited autofile/record: %s") % filename)
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

	def keyOk(self):
#		self.writeFile()
		self.close(self["text"].getText())

	def keyClose(self):
		self.close()

	def writeFile(self):
		if not self.new:
			bakName = self.autoName + ".bak"
			os.rename(self.autoName, bakName)
		fo = open(self.autoName, "w")
		fo.write("%s\n" % self["text"].getText())
		fo.close()

	def createConfig(self):
		self.list = [ ]
		dx = 4*' '
		self.list.append(getConfigListEntry(_("local directory"), cfg.localdir))
		self.list.append(getConfigListEntry(_("fstype"), cfg.fstype))
		self.list.append(getConfigListEntry(_("rw/ro"), cfg.rw))
		self.useduserpass = _("use user/pass")
		self.list.append(getConfigListEntry(self.useduserpass, cfg.useduserpass))
		if cfg.useduserpass.value:
			self.list.append(getConfigListEntry(dx + _("user"), cfg.user))
			self.list.append(getConfigListEntry(dx + _("password"), cfg.passwd))
		self.useddomain = _("domain")
		self.list.append(getConfigListEntry(self.useddomain, cfg.useddomain))
		if cfg.useddomain.value:
			self.list.append(getConfigListEntry(dx + _("domain name"), cfg.domain))
			self.list.append(getConfigListEntry(dx + _("noperm"), cfg.noperm))
		self.list.append(getConfigListEntry(_("noatime"), cfg.noatime))
		self.list.append(getConfigListEntry(_("noserverino"), cfg.noserverino))
		self.list.append(getConfigListEntry(_("nosuid"), cfg.nosuid))
		self.list.append(getConfigListEntry(_("nodev"), cfg.nodev))
		self.list.append(getConfigListEntry(_("rsize"), cfg.rsize))
		self.list.append(getConfigListEntry(_("wsize"), cfg.wsize))
		self.list.append(getConfigListEntry(_("iocharset"), cfg.iocharset))
		self.list.append(getConfigListEntry(_("security"), cfg.sec))
		self.usedip = _("used ip")
		self.list.append(getConfigListEntry(self.usedip, cfg.usedip))
		if cfg.usedip.value:
			self.list.append(getConfigListEntry(dx + _("ip"), cfg.ip))
		else:
			self.list.append(getConfigListEntry(dx + _("dev"), cfg.dev))
		self.list.append(getConfigListEntry(_("remote directory"), cfg.remotedir))
		self.list.append(getConfigListEntry(_("user string"), cfg.rest))

		self["config"].list = self.list
		self["config"].setList(self.list)

		self.fillString()

	def changedEntry(self):
		if self["config"].getCurrent()[0] == self.useddomain:
			self.createConfig()
		elif self["config"].getCurrent()[0] == self.useduserpass:
			self.createConfig()
		elif self["config"].getCurrent()[0] == self.usedip:
			self.createConfig()
		self.fillString()

	def fillString(self):
		self["text"].setText(self.actualizeString())

	def actualizeString(self):
		string = cfg.localdir.value
		string += " "
		string += "-fstype=%s," % cfg.fstype.value
		string += "%s," % cfg.rw.value if cfg.rw.value else ""
		string += ("user=%s," % cfg.user.value) if cfg.useduserpass.value else ""
		string += ("password=%s," % cfg.passwd.value)if cfg.useduserpass.value else ""
		string += ("domain=%s," % cfg.domain.value) if cfg.useddomain.value else ""
		string += "noperm," if cfg.noperm.value else ""
		string += "noatime," if cfg.noatime.value else ""
		string += "noserverino," if cfg.noserverino.value else ""
		string += "nosuid," if cfg.nosuid.value else ""
		string += "nodev," if cfg.nodev.value else ""
		string += ("rsize=%s," % cfg.rsize.value) if cfg.rsize.value else ""
		string += ("wsize=%s," % cfg.wsize.value) if cfg.wsize.value else ""
		string += ("iocharset=%s," % cfg.iocharset.value) if cfg.iocharset.value else ""
		string += ("sec=%s," % cfg.sec.value) if cfg.sec.value else ""
		string += ("%s,") % cfg.rest.value if cfg.rest.value else ""
		string = string.rstrip(',')
		string += " "
		ip = "%s.%s.%s.%s" % (tuple(cfg.ip.value))
		string += ("://%s/%s" % (ip, cfg.remotedir.value)) if cfg.usedip.value else (":/%s/%s" % (cfg.dev.value, cfg.remotedir.value))
		return string

	def parseParams(self, line):
		if line:
			self["text"] = Label("%s" % line)
			parts = line.split()
			self.parse(parts)

	def setDefaultPars(self):
		# set default pars before parsing line
		cfg.localdir.value = cfg.localdir.default
		cfg.fstype.value = cfg.fstype.default
		cfg.rw.value = cfg.rw.default
		cfg.useduserpass.value = cfg.useduserpass.default
		cfg.user.value = cfg.user.default
		cfg.passwd.value = cfg.passwd.default
		cfg.useddomain.value = cfg.useddomain.default
		cfg.domain.value = cfg.domain.default
		cfg.noperm.value = cfg.noperm.default
		cfg.noatime.value = cfg.noatime.default
		cfg.noserverino.value = cfg.noserverino.default
		cfg.nosuid.value = cfg.nosuid.default
		cfg.nodev.value = cfg.nodev.default
		cfg.rsize.value = cfg.rsize.default
		cfg.wsize.value = cfg.wsize.default
		cfg.iocharset.value = cfg.iocharset.default
		cfg.sec.value = cfg.sec.default
		cfg.usedip.value = cfg.usedip.default
		cfg.ip.value = cfg.ip.default
		cfg.dev.value = cfg.dev.default
		cfg.remotedir.value = cfg.remotedir.default
		cfg.rest.value = cfg.rest.default

	def prepareOff(self):
		# set (all what has sence) as off or empty before parsing existing line
		cfg.rw.value = ""
		cfg.useduserpass.value = False
		cfg.useddomain.value = False
		cfg.noatime.value = False
		cfg.noserverino.value = False
		cfg.nosuid.value = False
		cfg.nodev.value = False
		cfg.iocharset.value = ""
		cfg.rest.value = ""

	def parse(self, parts):
		self.setDefaultPars()
		self.prepareOff()
		rest = ""
		try:
			# parse line
			for x in parts[1].split(','):
				if "-fstype" in x:
					cfg.fstype.value=x.split('=')[1]
				elif "user" in x:
					cfg.useduserpass.value = True # rozmyslet!
					cfg.user.value=x.split('=')[1]
				elif "password" in x:
					cfg.useduserpass.value = True
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
				elif x == "rw" or x == "ro":
					cfg.rw.value=x
				elif x == "noperm":
					cfg.noperm.value=True
				elif x == "noatime":
					cfg.noatime.value=True
				elif x == "noserverino":
					cfg.noserverino.value=True
				elif x == "nosuid":
					cfg.nosuid.value=True
				elif x == "nodev":
					cfg.nodev.value=True
				else:
					rest +=x

			# dir name
			cfg.localdir.value = parts[0].strip()

			# ip and shared remote dir or dev and remote dir
			if parts[2].startswith('://'): 		# ://10.0.0.10/video
				cfg.usedip.value = True
				remote = parts[2].split('/')
				cfg.ip.value = self.convertIP(remote[2])
				cfg.remotedir.value = remote[3]
			else:					# DVD, CD  :/dev/sr0
				cfg.usedip.value = False
				remote = parts[2].split('/')
				cfg.dev.value = remote[1]
				cfg.remotedir.value = remote[2]
			cfg.rest.value = rest
		except:
			self.MessageBoxNM(True, _("Wrong file format!"), 5)

	def convertIP(self, ip):
		strIP = ip.split('.')
		ip = []
		for x in strIP:
			ip.append(int(x))
		return ip

class ManagerAutofsMultiAutoEdit(Screen):
	skin = """
		<screen name="ManagerAutofsMultiAutoEdit" position="center,center" size="680,400" backgroundColor="#00000000">
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

		self["shortcuts"] = ActionMap(["SetupActions","OkCancelActions","ColorActions","MenuActions"],
		{
			"ok": self.keyEdit,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keyOk,
			"yellow": self.keyAdd,
			"blue": self.keyErase,
			"menu": self.menu,
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
		self.setTitle(_("Manager Autofs - press %sOK%s for edit or use %sMenu%s") % (yC, fC, yC, fC,))

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
		self.refreshText()

	def refreshText(self):
		current = self["list"].getCurrent()
		if current:
			self["info"].setText("%s" % current[1])

	def menu(self):
		menu = []
		buttons = []

		sel = self["list"].getCurrent()
		if sel:
			menu.append((_("Edit line"),0))
			menu.append((_("Add line"),1))
			menu.append((_("Remove line"),2))
			buttons += ["", "", ""]
		else:
			self.MessageBoxNM(True, _("No valid item"), 5)
			return

		text = _("Select operation:")
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title=text, list=menu, keys=buttons)

	def menuCallback(self, choice):
		if choice is None:
			return
		sel = self["list"].getCurrent()
		if sel:
			if choice[1] == 0:
				self.keyEdit()
			elif choice[1] == 1:
				self.keyAdd()
			elif choice[1] == 2:
				self.keyErase()
			else:
				return

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
		self.refreshText()

	def addItem(self, new):
		self.list.append((new[0], new[1]))
		self.refreshText()

	def removeItem(self, index):
		self.list.pop(index)
		self["list"].updateList(self.list)
		self.refreshText()

	def keyCancel(self):
		self.close()

class NonModalMessageBoxDialog(Screen):
	skin="""
		<screen name="NonModalMessageBoxDialog" position="center,center" size="470,120" backgroundColor="#00808080" zPosition="2" flags="wfNoBorder">
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