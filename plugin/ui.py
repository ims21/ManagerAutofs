#
#  Manager Autofs
#
VERSION = "1.81"
#
#  Coded by ims (c) 2018
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
from Components.ActionMap import ActionMap, HelpableActionMap
from Screens.HelpMenu import HelpableScreen
from Components.SelectionList import SelectionList
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigIP, ConfigInteger, ConfigText, getConfigListEntry, ConfigYesNo, NoSave, ConfigSelection, ConfigPassword
from Tools.BoundFunction import boundFunction
from Screens.ChoiceBox import ChoiceBox
from Components.Sources.List import List
from Components.PluginComponent import plugins
from Tools.Directories import SCOPE_PLUGINS, resolveFilename, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
from Components.Sources.Boolean import Boolean
from Components.Sources.StaticText import StaticText

from shutil import copyfile
import enigma
import skin
import os

from Components.Pixmap import Pixmap
from helptexts import ManagerAutofsHelp
from plugin import mountedLocalHDD

# parameters for auto.master file
config.plugins.mautofs.enabled = NoSave(ConfigYesNo(default = False))
config.plugins.mautofs.mountpoint = NoSave(ConfigText(default = "/mnt/remote", visible_width = 30, fixed_size = False))
config.plugins.mautofs.autofile = NoSave(ConfigText(default = "remote", visible_width = 30, fixed_size = False ))
config.plugins.mautofs.ghost = NoSave(ConfigYesNo(default = True))
config.plugins.mautofs.timeout = NoSave(ConfigYesNo(default = False))
config.plugins.mautofs.timeouttime = NoSave(ConfigInteger(default = 60, limits = (1, 300)))

# parameters for prefilled user/pass
config.plugins.mautofs.pre_user = ConfigText(default="", fixed_size=False)
config.plugins.mautofs.pre_passwd = ConfigPassword(default="", fixed_size=False)
config.plugins.mautofs.pre_save = ConfigYesNo(default = False)

cfg = config.plugins.mautofs

AUTOMASTER="/etc/auto.master"
BACKUPCFG="/etc/backup.cfg"
AUTOFS="/etc/init.d/autofs"
DEFAULT_HDD = '/media/hdd'

def hex2strColor(argb):
	out = ""
	for i in range(28,-1,-4):
		out += "%s" % chr(0x30 + (argb>>i & 0xf))
	return out

try:
	yC = "\c%s" % hex2strColor(int(skin.parseColor("selectedFG").argb()))
except:
	yC = "\c%s" % hex2strColor(0x00fcc000)
try:
	fC = "\c%s" % hex2strColor(int(skin.parseColor("foreground").argb()))
except:
	fC = "\c%s" % hex2strColor(0x00f0f0f0)

greyC = "\c%s" % hex2strColor(0x00a0a0a0)
rC = "\c%s" % hex2strColor(0x00ff4000)
gC = "\c%s" % hex2strColor(0x0000ff80)
bC = "\c%s" % hex2strColor(0x000080ff)

_X_ = "%sx%s" % (gC,fC)

MOUNTED = "%s~%s" % (gC,fC)
CHANGED = "%s~%s" % (yC,fC)
FAILED = "%s~%s" % (rC,fC)
MISSING_FILE = "%s!%s" % (rC,fC)
MISSING_LINE = "%s?%s" % (yC,fC)

class ManagerAutofsMasterSelection(Screen, HelpableScreen):
	skin = """
		<screen name="ManagerAutofsMasterSelection" position="center,center" size="660,485">
			<widget name="red" pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on"/>
			<widget name="green" pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on"/>
			<widget name="yellow" pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on"/>
			<widget name="blue" pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on"/>
			<widget  name="key_red" position="0,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="red" font="Regular;20" transparent="1"/>
			<widget  name="key_green" position="140,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="green" font="Regular;20" transparent="1"/>
			<widget  name="key_yellow" position="280,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="yellow" font="Regular;20" transparent="1"/>
			<widget  name="key_blue" position="420,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="blue" font="Regular;20" transparent="1"/>
			<widget source="list" render="Listbox" position="5,60" size="650,375" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
				{"templates":
					{"default": (25,[
							MultiContentEntryText(pos = (5, 6), size = (10, 25), font=1, flags = RT_HALIGN_LEFT, text = 0), # index 0 is e/d status
							MultiContentEntryText(pos = (50, 3), size = (250, 25), font=0, flags = RT_HALIGN_LEFT, text = 1), # index 1 is the name
							MultiContentEntryText(pos = (300, 3), size = (250, 25), font=0, flags = RT_HALIGN_LEFT, text = 2), # index 2 is the autofile
							MultiContentEntryText(pos = (15, 6), size = (20, 25), font=0, flags = RT_HALIGN_LEFT, text = 4), # mount status
						])
					},
					"fonts": [gFont("Regular", 18),gFont("Regular", 12)],
					"itemHeight": 25
				}
				</convert>
			</widget>
			<widget name="mntpoint" position="55,40" size="250,20" font="Regular;14" halign="left" valign="center" zPosition="1"/>
			<widget name="autofile" position="305,40" size="250,20" font="Regular;14" halign="left" valign="center" zPosition="1"/>
			<widget name="text" position="55,435" zPosition="10" size="560,25" font="Regular;22" halign="left" valign="center"/>
			<widget name="status" position="55,460" zPosition="10" size="300,20" font="Regular;18" halign="left" valign="center"/>
			<widget name="statusbar" position="355,460" zPosition="10" size="300,20" font="Regular;18" halign="left" valign="center"/>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.session = session

		self.data = ''
		self.container = enigma.eConsoleAppContainer()
		self.container.appClosed.append(self.appClosed)
		self.container.dataAvail.append(self.dataAvail)
		self["status"] = Label()
		self["statusbar"] = Label()

		self["mntpoint"] = Label(_("Mountpoint"))
		self["autofile"] = Label(_("auto.file"))
		self["text"] = Label()

		self["ManagerAutofsActions"] = HelpableActionMap(self, ["SetupActions","ColorActions","MenuActions"],
			{
			"ok":		(self.editMasterRecord,	_("Edit mountpoint")),
			"cancel":	(self.keyClose, _("Close")),
			"red":		(self.keyClose, _("Close")),
			"green":	(self.addMasterRecord, _("Add mountpoint")),
			"blue":		(self.changeMasterRecordStatus, _("Enable/disable mountpoint")),
			"yellow":	(self.editAutofile, _("Edit auto file")),
			"menu":		(self.menu, _("Menu")),
			}, -1)
		self["ManagerAutofsEditActions"] = HelpableActionMap(self, ["DirectionActions","NumberActions"],
			{
			"moveUp":	(self.moveUp, _("Move item up")),
			"moveDown":	(self.moveDown, _("Move item down")),
			"0": 		(self.startMoving, _("Enable/disable moving item")),
			}, -1)
		self.edit = 0
		self.idx = 0
		self.changes = False
		self["h_prev"] = Pixmap()
		self["h_next"] = Pixmap()
		self.showPrevNext()

		self.list = []
		self["list"] = List(self.list)
		if not self.selectionChanged in self["list"].onSelectionChanged:
			self["list"].onSelectionChanged.append(self.selectionChanged)

		self["key_red"] = Button(_("Close"))
		self["key_green"] = Button(_("Add mountpoint"))
		self["key_yellow"] = Button(_("Edit auto file"))
		self["key_blue"] = Button()
		self["red"] = Pixmap()
		self["green"] = Pixmap()
		self["yellow"] = Pixmap()
		self["blue"] = Pixmap()

		self.msgNM=None
		self.selectionUtilitySubmenu = 0
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
		# mandatory: 0 - status 1 - mountpoint 2 - autofile  Optional pars: 3 , 4 - mount status
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
			mounted = self.getMountedStatus(m[0], m[1], m[2])
			self.list.append((_X_ if m[0] == "x" else '', m[1], m[2], self.parseOptional(m), mounted))
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
			self["text"].setText(self.formatString(sel))
		self.hddRealPath()

	def getMountedStatus(self, selected, device, autofile):
		if not os.path.exists(autofile):
			return MISSING_FILE
		if self.getAutoLines(autofile) < 1:
			return MISSING_LINE
		# TODO: solve test for multiline files
		point = open(autofile,"r").readline().split(' ')[0]
		if os.path.exists("%s/%s/." % (device, point)):
			if selected == "x":
				return ""
			return MOUNTED
		if selected == "x":
			return FAILED
		return ""

	def clearTexts(self):
		self.MessageBoxNM()
		self["statusbar"].setText("")
		self["status"].setText("")
		self["text"].setText("")

	def keyClose(self):
		self.saveMasterFile()
		self.updateAutofs()
		self.resetCfg()
		self.close()

	def resetCfg(self):
		if not cfg.pre_save.value:
			config.plugins.mautofs.pre_user.value = ""
			config.plugins.mautofs.pre_passwd.value = ""
		config.plugins.mautofs.pre_user.save()
		config.plugins.mautofs.pre_passwd.save()

	def startMoving(self):
		self.edit = not self.edit
		self.idx = self["list"].getIndex()
		self.showPrevNext()
	def showPrevNext(self):
		if self.edit:
			self["h_prev"].show()
			self["h_next"].show()
		else:
			self["h_prev"].hide()
			self["h_next"].hide()
	def moveUp(self):
		if self.edit and self.idx -1 >= 0:
			self.moveDirection(-1)
	def moveDown(self):
		if self.edit and self.idx +1 < self["list"].count():
			self.moveDirection(1)
	def moveDirection(self, direction):
			self["list"].setIndex(self.idx)
			tmp = self["list"].getCurrent()
			self["list"].setIndex(self.idx+direction)
			tmp2 = self["list"].getCurrent()
			self["list"].modifyEntry(self.idx, tmp2)
			self["list"].modifyEntry(self.idx+direction, tmp)
			self.idx+=direction
			self.changes = True

	def help(self):
		self.session.open(ManagerAutofsHelp)

	def menu(self):
		menu = []
		buttons = []

		sel = self["list"].getCurrent()
		if sel:
			recordname = "%s" % (sel[1].split('/')[2])
			device = "%s%s%s" % (gC,recordname,fC)
			autoname = "%s" % sel[2].split('/')[2]
			mountpoint = "%s%s%s" % (bC,autoname,fC)
			menu.append(((_("Edit record:") + "  " + device), 0, _("Edit record for '%s' remote device in 'auto.master' file.") % device))
			buttons = [""]
		menu.append((_("New record"), 1, _("Add new record to 'auto.master' file.")))
		menu.append((_("Remove record:") + "  " + device, 2, _("Remove record with '%s' remote device from 'auto.master' file.") % device))
		menu.append((_("Create new record from:") + "  " + device, 5, _("Clone record with '%s' remote device in 'auto.master' file and create file with mountpoint parameters withal.") % device))
		buttons += ["","",""]
		if sel:
			menu.append((_("Edit -") + " " + mountpoint, 10, _("Edit file '%s' with mountpoint parameters for existing '%s' remote device.") % (mountpoint, device)))
			menu.append((_("Add line to -") + " " + mountpoint, 11, _("Add next mountpoint parameters line to '%s' for existing '%s' remote device.") % (mountpoint, device)))
			menu.append((_("Remove -") + " " + mountpoint, 12, _("Remove file '%s' with mountpoint parameters for '%s' remote device.") % (mountpoint, device)))
			buttons += ["", "", ""]
		menu.append((_("Help")+"...", 30, _("Brief help on how to use autofs.")))
		buttons += [""]
		if cfg.extended_menu.value:
			txt = _("Remove from extended menu")
			descr = _("Remove plugin's run from Extended menu.")
		else:
			txt = _("Add into extended menu")
			descr = _("Add plugin's run to Extended menu.")
		menu.append((txt,40,descr))
		buttons += ["blue"]
		menu.append((_("Utility")+"...", 50, _("Next utilities.")))
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
			elif choice[1] == 5:
				self.duplicateMountPoint()
			elif choice[1] == 10:
				self.editAutofile()
			elif choice[1] == 11:
				self.addAutofileLine()
			elif choice[1] == 12:
				self.removeAutofile()
			elif choice[1] == 30:
				self.help()
			elif choice[1] == 40:
				cfg.extended_menu.value = not cfg.extended_menu.value
				cfg.extended_menu.save()
				self.refreshPlugins()
			elif choice[1] == 50:
				self.selectionUtilitySubmenu = 0
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
				self.createMountpointWithAutofile(add)
		self.session.openWithCallback(boundFunction(callbackAdd), ManagerAutofsMasterEdit, None, self.list)

	def duplicateMountPoint(self):
		def callbackAdd(original_autofile, change=False):
			if change:
				mountpoint = "/mnt/%s" % cfg.mountpoint.value
				autofile = "/etc/auto.%s" % cfg.autofile.value
				enabled =  cfg.enabled.value and _X_ or ""
				ghost = cfg.ghost.value and "--ghost" or ""
				optional = ghost + (" --timeout=%s" % cfg.timeouttime.value if cfg.timeout.value else '')
				add = (enabled, mountpoint, autofile, optional )
				self.addItem(add)
				# autofile is created
				if os.path.exists(original_autofile):
					copyfile(original_autofile, autofile)
				else:
					self.MessageBoxNM(True, _("'%s' not exists, %s will be with default values") % (original_autofile, autofile), 5)

		sel = self["list"].getCurrent()
		if sel:
			suffix = "_new"
			mountpoint = "%s" % sel[1] + suffix
			original_autofile = sel[2]
			autofile = "%s" % original_autofile + suffix
			enabled =  ""
			ghost = sel[3]
			sel = [enabled, mountpoint, autofile, ghost]
			self.session.openWithCallback(boundFunction(callbackAdd, original_autofile), ManagerAutofsMasterEdit, sel, self.list)

	def editMasterRecord(self):
		def callbackEdit( index, old_autofile, mnt_status, change = False):
			if change:
				mountpoint = "/mnt/%s" % cfg.mountpoint.value
				autofile = "/etc/auto.%s" % cfg.autofile.value
				enabled =  cfg.enabled.value and _X_ or ""
				ghost = cfg.ghost.value and "--ghost" or ""
				optional = ghost + (" --timeout=%s" % cfg.timeouttime.value if cfg.timeout.value else '')
				edit = (enabled, mountpoint, autofile, optional if len(optional) else '', mnt_status)
				self.changeItem(index, edit)
				if old_autofile != autofile:
					if os.path.exists(old_autofile):
						if os.path.exists(autofile):
							def callBackRemove(old_autofile, change=False):
								if change:
									os.rename(old_autofile, old_autofile + '.del')
									self.MessageBoxNM(True, _("'%s' was removed" % old_autofile), 2)
							self.session.openWithCallback(boundFunction(callBackRemove, old_autofile), MessageBox, _("Auto.name '%s' was attached to this record.\nRemove original '%s'?") % (autofile, old_autofile), type=MessageBox.TYPE_YESNO, default=False)
						else:
							def callBackRename(old_autofile, autofile, change=False):
								if change:
									copyfile(old_autofile, old_autofile + '.$$$')
									os.rename(old_autofile, autofile)
									self.MessageBoxNM(True, _("'%s' was renamed to '%s'") % (old_autofile, autofile), 2)
							self.session.openWithCallback(boundFunction(callBackRename, old_autofile, autofile) , MessageBox, _("Auto.name in record was changed.\nDo You want rename original '%s' to '%s' too?") % (old_autofile, autofile), type=MessageBox.TYPE_YESNO, default=True)
		sel = self["list"].getCurrent()
		if sel:
			index = self["list"].getIndex()
			old_autofile = sel[2]
			mnt_status = sel[4]
			self.session.openWithCallback(boundFunction(callbackEdit, index, old_autofile, mnt_status), ManagerAutofsMasterEdit, sel, self.list)

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
			removing = [(_("Nothing"), False), (_("Record '%s' only") % record, 1), (_("Record '%s' and its file '%s'") % (record, autofile), 2)]
			self.session.openWithCallback(boundFunction(callbackRemove, index, autofile), MessageBox, _("What all do You want to remove?"), type=MessageBox.TYPE_YESNO, default=False, list=removing)

	def changeItemStatus(self, index, data):
		if data[0] == _X_:
			status = ""
		else:
			status = _X_
		self["list"].modifyEntry(index, (status ,data[1], data[2], data[3] if len(data) > 3 else '', CHANGED))

	def changeItem(self, index, new):
		self["list"].modifyEntry(index,(new[0], new[1], new[2], new[3], new[4]))
		self.refreshText()

	def addItem(self, new):
		self.list.append((new[0], new[1], new[2], new[3] if len(new) > 3 else '', ''))
		self.refreshText()

	def removeItem(self, index):
		self.list.pop(index)
		self["list"].updateList(self.list)
		self.refreshText()

	def addAutofileLine(self):
		def callBackCreate(name,text=""):
			if text:
				self.backupFile(name,"bak")
				self.saveFile(name, text)
		sel = self["list"].getCurrent()
		if sel:
			name = sel[2]
			lines = self.getAutoLines(name)
			if lines == -1 or lines == 0: # file not exist or is empty
				data = ""
				self.session.openWithCallback(boundFunction(callBackCreate, name), ManagerAutofsAutoEdit, name, data, True)
			else:
				self.session.open(ManagerAutofsMultiAutoEdit, name)

	def createMountpointWithAutofile(self, add):
		name = add[2]
		def callBackSingle(name, text=""):
			if text:
				self.saveFile(name, text)
				self.addItem(add)
		data = ""
		self.session.openWithCallback(boundFunction(callBackSingle, name), ManagerAutofsAutoEdit, name, data, True)

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
			menu.append((_("Update autofs files in AutoBackup"), 0, _("Automaticaly add valid autofs files to /etc/backup.cfg file used by AutoBackup plugin.")))
			menu.append((_("Remove unused autofs files in AutoBackup"), 2, _("Remove unused autofs files from /etc/backup.cfg file.")))
			buttons += ["",""]
		if self.isBackupFile():
			menu.append((_("Remove backup files"), 3, _("Remove selected backup files created when editing autofs files.")))
			buttons += [""]
		if not os.path.exists(AUTOFS):
			menu.append((_("Install autofs"), 12, _("Install required autofs package if missing.")))
			buttons += [""]
		menu.append(("%s" % bC + _("Next items are not needed standardly:") + "%s" % fC, 1000))
		buttons += [""]
		space = 4 * " "
		if not mountedLocalHDD():
			sel = self["list"].getCurrent()
			if sel:
				currentpoint = sel[1][sel[1].rfind('/')+1:]
				if sel[0] == _X_ and currentpoint not in cfg.hddreplace.value: # mounted and not used
					menu.append((space + _("Use '%s' as HDD replacement") % currentpoint, 20, _("You can use current mountpoint '%s' as HDD replacement.") % currentpoint))
					buttons += ["green"]
				if cfg.hddreplace.value != DEFAULT_HDD:
					mountpoint = cfg.hddreplace.value.split('/')[2]
					menu.append((space + _("Cancel '%s' as HDD replacement") % mountpoint, 21, _("Cancel using '%s' as HDD replacement.") % currentpoint))
					buttons += ["red"]
		if os.path.exists(AUTOFS):
			menu.append((space + _("Reload autofs"), 10, _("Reload autofs mount maps. It is made standardly on each plugin close.")))
			menu.append((space + _("Restart autofs with GUI restart"),11,_("Sometimes it is needed restart autofs deamon and GUI. Use this option and then wait for finishing and for restart GUI.")))
			buttons += ["","green"]
		menu.append((space +_("Open AutoBackup plugin"), 1, _("Runs AutoBackup plugin")))
		buttons += ["3"]
		menu.append((space + _("Reload Bookmarks"), 100, _("Check bookmarks with current mountpoints. It is made standardly on each plugin close.")))
		buttons += [""]
		menu.append((space + _("Clear bookmarks..."), 110 ,_("Removing selected bookmarks.")))
		buttons += [""]
		txt = _("You can set user and password before creating more autofiles. Values are used too, when item 'used user/pass' is turned off and on again and values in auto.file were empty before it. Presettings can be on plugin exit cleared.")
		menu.append((space + _("User and password presetting..."), 200, txt))
		buttons += [""]
		text = _("Select operation:")
		self.session.openWithCallback(boundFunction(self.utilityCallback, menu), ChoiceBox, title=text, list=menu, keys=buttons, selection = self.selectionUtilitySubmenu)

	def utilityCallback(self, menu, choice):
		if choice is None:
			return
		self.selectionUtilitySubmenu = menu.index(choice)
		if choice[1] == 0:
			self.updateAutoBackup()
		elif choice[1] == 1:
			def autobackupCallback(tmp1, tmp2):
				self.utilitySubmenu()
			self.saveMasterFile()
			self.updateAutofs()
			from Plugins.Extensions.AutoBackup.ui import Config
			self.session.openWithCallback(autobackupCallback, Config)
		elif choice[1] == 2:
			self.refreshAutoBackup()
		elif choice[1] == 3:
			self.removeBackupFiles()
		elif choice[1] == 10:
			self.updateAutofs()
		elif choice[1] == 11:
			def callback(value=False):
				if value:
					self.updateAutofs(option="restart", restartGui=True)
			self.session.openWithCallback(callback, MessageBox, _("Really reload autofs and restart GUI?"), type=MessageBox.TYPE_YESNO, default=False)
		elif choice[1] == 12:
			self.installAutofs()
		elif choice[1] == 20:
			self.hddReplacement()
		elif choice[1] == 21:
			self.hddReplacementReset()
		elif choice[1] == 100:
			config.movielist.videodirs.load()
		elif choice[1] == 110:
			self.session.open(ManagerAutofsClearBookmarks)
		elif choice[1] == 200:
			self.session.open(ManagerAutofsPreset)
		elif choice[1] == 1000:
			self.selectionUtilitySubmenu += 1 # jump to next item
			self.utilitySubmenu()
		else:
			return

	def hddReplacement(self):
		sel = self["list"].getCurrent()
		if sel:
			name = sel[2]
			if sel[0] != _X_:
				self.MessageBoxNM(True, _("Point '%s' is not mounted!") % name.split('.')[1], 3)
				return
			lines = self.getAutoLines(name)
			if lines == 1:	# single record file
				line = open(name, "r").readline()
				data = line.replace('\n','').strip()
				if data:
					local_dir = data.split()[0].strip()
					path = '/media/%s/%s' % (name.split('.')[1],local_dir)
					self.callCreateSymlink(path)
				else:
					return
			elif lines > 1: # multi record file
				def callbackGetName(answer):
					if answer:
						path = '/media/%s/%s' % (name.split('.')[1],answer)
						self.callCreateSymlink(path)
				list = []
				text = _("Select '%s' directory:") % name.split('.')[1]
				for x in open(name, "r"):
					line = x.replace('\n','').strip()
					if line:
						local_dir = line.split()[0].strip()
						if local_dir:
							list.append((local_dir, local_dir))
						self.session.openWithCallback(callbackGetName, MessageBox, text, MessageBox.TYPE_INFO, list=list )
			else:
				self.MessageBoxNM(True, _("'%s.auto' has wrong format or is empty!") % name.split('.')[1], 5)
				return

	def hddReplacementReset(self):
		makeMountAsHDD.setDefault()
		makeMountAsHDD.createSymlink()
		self.hddRealPath()

	def callCreateSymlink(self, path):
		cfg.hddreplace.value = path
		cfg.hddreplace.save()
		makeMountAsHDD.createSymlink()
		self.hddRealPath()

	def hddRealPath(self):
		if os.path.realpath('/hdd') != DEFAULT_HDD:
			self["statusbar"].setText(_("%s as /hdd") % os.path.realpath('/hdd'))
		else:
			self["statusbar"].setText("")

	def isBackupFile(self):
		files = [x for x in os.listdir("/etc") if x.startswith("auto.") and (x.endswith(".bak") or x.endswith(".del") or x.endswith(".$$$"))]
		return len(files)

	def removeBackupFiles(self):
		from removebckp import ManagerAutofsRemoveBackupFiles
		self.session.open( ManagerAutofsRemoveBackupFiles)

	def updateAutoBackup(self):	# add missing /etc/auto. lines into /etc/backup.cfg
		def callbackBackup(value=False):
			def readBackup():
				if os.path.exists(BACKUPCFG):
					file = open(BACKUPCFG, "r")
					content = file.read()
					file.close()
					return content
				self.MessageBoxNM(True, _("File '%s' was created!") % BACKUPCFG, 3)
				return ""
			if value:
				backup = readBackup()
				update = open(BACKUPCFG, "a")
				if AUTOMASTER not in backup:
					update.write(AUTOMASTER + '\n')
				for rec in self.list:
					if rec[2] not in backup:
						update.write(rec[2] + '\n')
				update.close()
				self.MessageBoxNM(True, _("Done"), 1)
			self.utilitySubmenu()
		self.session.openWithCallback(callbackBackup, MessageBox, _("Update AutoBackup's '%s'?") % BACKUPCFG, type=MessageBox.TYPE_YESNO, default=False)

	def refreshAutoBackup(self):	# remove unused /etc/auto.files lines from /etc/backup.cfg
		def callbackBackup(value=False):
			if value:
				if os.path.exists(BACKUPCFG):
					copyfile(BACKUPCFG, BACKUPCFG + '.bak')

					backupcfg = open(BACKUPCFG + '.bak',"r")
					new = open(BACKUPCFG, "w")

					autofslines = []	# auto.xxxx lines
					lines = []		# other lines
					for line in backupcfg:
						line = line.replace('\n','')
						if not line:
							continue
						if line.startswith('/etc/auto.'):
							for rec in self.list:
								if rec[2] == line:
									autofslines.append(line + '\n')
						else:
							lines.append(line + '\n')
					autofslines.sort()
					new.write(AUTOMASTER + '\n')
					for auto in autofslines:
						new.write(auto)
					for f in lines:
						new.write(f)
					new.close()
					backupcfg.close()
					self.MessageBoxNM(True, _("Done"), 1)
				else:
					self.MessageBoxNM(True, _("Missing '/etc/backup.cfg'"), 3)
			self.utilitySubmenu()
		self.session.openWithCallback(callbackBackup, MessageBox, _("Remove unused lines from '%s'?") % BACKUPCFG, type=MessageBox.TYPE_YESNO, default=False)

	def installAutofs(self):
		cmd = 'opkg install autofs'
		if self.container.execute(cmd):
			print "[ManagerAutofs] failed to execute"
			self.showOutput()

	def updateAutofs(self, option="reload", restartGui=False):
		if os.path.exists(AUTOFS):
			cmd = '%s %s' % (AUTOFS, option)
			if restartGui:
				cmd += '; killall enigma2'
			if self.container.execute(cmd):
				print "[ManagerAutofs] failed to execute"
				self.showOutput()
		else:
			self.MessageBoxNM(True, _("Autofs is not installed!"), 3)

	def refreshPlugins(self):
		plugins.clearPluginList()
		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))

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
			<widget name="red" position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<widget name="green" position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<widget name="yellow" position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<widget objectTypes="key_blue,StaticText" source="key_blue" render="Pixmap" position="420,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on">
				<convert type="ConditionalShowHide"/>
			</widget>
			<widget  name="key_red" position="0,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="red" font="Regular;20" transparent="1"/>
			<widget  name="key_green" position="140,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="green" font="Regular;20" transparent="1"/>
			<widget  name="key_yellow" position="280,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="yellow" font="Regular;20" transparent="1"/>
			<widget source="key_blue" render="Label" position="420,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="blue" font="Regular;20" transparent="1"/>
			<widget name="text" position="5,40" size="550,20" font="Regular;16" halign="left" valign="center"/>
			<widget name="config" position="5,65" size="550,125" scrollbarMode="showOnDemand"/>
			<widget source="VKeyIcon" render="Pixmap" pixmap="skin_default/buttons/key_text.png" position="10,200" zPosition="10" size="35,25" transparent="1" alphatest="on">
				<convert type="ConditionalShowHide"/>
			</widget>
			<!--widget name="HelpWindow" position="160,400" size="0,0"/-->
		</screen>"""

	def __init__(self, session, pars, master):
		Screen.__init__(self, session)
		self.inputMountPoint = None
		self.inputAutoFile = None
		if pars:
			record = "%s%s%s" % (gC, pars[1].split('/')[2], fC)
			text = _("Manager Autofs - edited record: %s") % record
			self.inputMountPoint = pars[1]
			self.inputAutoFile = pars[2]
		else:
			text = _("Manager Autofs - create new record")
		self.setTitle(text)

		self.master = master # master file records
		self.pars = pars

		self["text"] = Label()

		self["key_red"] = Button(_("Close"))
		self["key_green"] = Button(_("Ok"))
		self["key_blue"] = StaticText()

		self["red"] = Pixmap()
		self["green"] = Pixmap()
		self["blue"] = Pixmap()
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["VKeyIcon"] = Boolean(False)

		self.list = [ ]
		self.onChangedEntry = [ ]
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)		

		self["actions"] = ActionMap(["SetupActions","OkCancelActions","ColorActions"],
			{
			"ok":		self.keyOk,
			"cancel":	self.keyClose,
			"green":	self.keyOk,
			"red":		self.keyClose,
			"blue":		self.keyBlue,
			}, -1)

		self.msgNM=None

		self["config"].onSelectionChanged.append(self.moveOverItem)

		self.setDefault()
		self.parsePars()
		self.createConfig()

	def createConfig(self):
		dx = 4*' '
		self.list = [ ]
		self.list.append(getConfigListEntry(_("enabled"), cfg.enabled))
		self.mountpoint = _("mountpoint name")
		self.list.append(getConfigListEntry(self.mountpoint, cfg.mountpoint))
		self.autofile = _("auto.name")
		self.list.append(getConfigListEntry(self.autofile, cfg.autofile))
		self.list.append(getConfigListEntry(_("ghost"), cfg.ghost))
		self.timeout = _("timeout")
		self.list.append(getConfigListEntry(self.timeout, cfg.timeout))
		if cfg.timeout.value:
			self.list.append(getConfigListEntry(dx + _("time"), cfg.timeouttime))
		self["config"].list = self.list
		self["config"].setList(self.list)
		self.actualizeString()

	def parsePars(self):
		if self.pars:
			self.prepareOff()
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

	def prepareOff(self): # set (all what has sence, f.eg. if default is as True) as off or empty before parsing existing line
		cfg.ghost.value = False
		cfg.timeout.value = False

	def changedEntry(self):
		if self["config"].getCurrent()[0] == self.timeout:
			self.createConfig()
		elif self["config"].getCurrent()[0] == self.mountpoint:
			self.blueText(_("Put autoname"))
		elif self["config"].getCurrent()[0] == self.autofile:
			self.blueText(_("Put mountpoint name"))
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

	def moveOverItem(self):
		self.blueText("")
		if cfg.mountpoint.value != cfg.autofile.value:
			if self["config"].getCurrent()[0] == self.mountpoint:
				self.blueText(_("Put autoname"))
			elif self["config"].getCurrent()[0] == self.autofile:
				self.blueText(_("Put mountpoint name"))

	def keyBlue(self): # use same text as in mounpoint or autofile
		if self["config"].getCurrent()[0] == self.mountpoint:
			cfg.mountpoint.value = cfg.autofile.value
			self.createConfig()
		elif self["config"].getCurrent()[0] == self.autofile:
			cfg.autofile.value = cfg.mountpoint.value
			self.createConfig()

	def blueText(self, text):
		self["key_blue"].setText(text)

	def existMountPoint(self, mountpoint):
		for rec in self.master:
			if rec[1] == mountpoint:
				return True
		return False

	def existAutoFile(self, autofile):
		for rec in self.master:
			if rec[2] == autofile:
				return True
		return False

	def keyOk(self):
		if cfg.autofile.value == "master":
			self.MessageBoxNM(True, _("You cannot use 'master' in auto.file name"), 3)
			return
		af = "/etc/auto.%s" % cfg.autofile.value
		if af != self.inputAutoFile:
			if os.path.exists(af):
				def callBackUse(old_autofile, change=False):
					if not change: # set back original auto.name
						cfg.autofile.value = self.inputAutoFile.split('.')[1]
						return
					self.mountPointTest()
				self.session.openWithCallback(boundFunction(callBackUse, af), MessageBox, _("Do You want use existing '%s' file?\nIf not then change auto.name.") % (af), type=MessageBox.TYPE_YESNO, default=False)
			else:
				self.mountPointTest()
		else:
			self.mountPointTest()

	def mountPointTest(self):
		mnt = "/mnt/%s" % cfg.mountpoint.value
		if mnt != self.inputMountPoint: # mountpoint name was changed, test if not exist record with same mountpoint
			if not self.existMountPoint(mnt):
				self.close(True)
			else:
				self.MessageBoxNM(True, _("Mountpoint name '%s' is used!" % mnt), 3)
		else:	# mountpoint record was edited, but mountpoint name was not changed
			self.close(True)

	def keyClose(self):
		self.close()

	def MessageBoxNM(self, display=False, text="", delay=0):
		if self.msgNM:
			self.session.deleteDialog(self.msgNM)
			self.msgNM = None
		else:
			if display and self.session is not None:
				self.msgNM = self.session.instantiateDialog(NonModalMessageBoxDialog, text=text, delay=delay)
				self.msgNM.show()

# parameters for selected auto. file
config.plugins.mautofs.localdir = NoSave(ConfigText(default = "dirname", visible_width = 30, fixed_size = False))
config.plugins.mautofs.fstype = NoSave(ConfigSelection(default="cifs", choices=[("",_("no")),("cifs","cifs"),("nfs","nfs"),("auto","auto"),("udf","udf"),("iso9660","iso9660")]))
config.plugins.mautofs.soft = NoSave(ConfigYesNo(default=False))
config.plugins.mautofs.intr = NoSave(ConfigYesNo(default=False))
config.plugins.mautofs.rw = NoSave(ConfigSelection(default = "", choices = [("", _("no")),("rw", "rw"),("ro", "ro")]))

config.plugins.mautofs.useduserpass = NoSave(ConfigYesNo(default=True))
config.plugins.mautofs.user = NoSave(ConfigText(default="", fixed_size=False))
config.plugins.mautofs.passwd = NoSave(ConfigPassword(default="", fixed_size=False))

config.plugins.mautofs.useddomain = NoSave(ConfigYesNo(default=False))
config.plugins.mautofs.domain = NoSave(ConfigText(default="domain.local", fixed_size=False))
config.plugins.mautofs.noperm = NoSave(ConfigYesNo(default=False))

config.plugins.mautofs.noatime = NoSave(ConfigYesNo(default=True))
config.plugins.mautofs.noserverino = NoSave(ConfigYesNo(default=True))
config.plugins.mautofs.nosuid = NoSave(ConfigYesNo(default=False))
config.plugins.mautofs.nodev = NoSave(ConfigYesNo(default=False))
config.plugins.mautofs.rsize = NoSave(ConfigSelection(default="", choices=[("", _("no")),("4096", "4096"),("8192", "8192"),("16384", "16384"),("32768", "32768")]))
config.plugins.mautofs.wsize = NoSave(ConfigSelection(default="", choices=[("", _("no")),("4096", "4096"),("8192", "8192"),("16384", "16384"),("32768", "32768")]))
config.plugins.mautofs.iocharset = NoSave(ConfigSelection(default="utf8", choices=[("", _("no")),("utf8", "utf8")]))
config.plugins.mautofs.sec = NoSave(ConfigSelection(default = "", choices = [("", _("no")),("ntlm", "ntlm"),("ntlmv2", "ntlmv2"),("ntlmssp", "ntlmssp")]))

config.plugins.mautofs.use_ip_or_name = NoSave(ConfigYesNo(default=True))
config.plugins.mautofs.usedip = NoSave(ConfigYesNo(default=True))
config.plugins.mautofs.ip = NoSave(ConfigIP(default=[192,168,1,100]))
config.plugins.mautofs.name = NoSave(ConfigText(default = "servername", visible_width = 30, fixed_size = False))
config.plugins.mautofs.dev = NoSave(ConfigSelection(default="dev", choices=[("",_("no")),("dev","dev")]))

config.plugins.mautofs.remotedir = NoSave(ConfigText(default = "dirname", visible_width = 30, fixed_size = False))
config.plugins.mautofs.smb = NoSave(ConfigSelection(default="", choices=[("",_("no")),("1.0","1.0"),("2.1","2.1"),("3.0","3.0")]))
#user defined string
config.plugins.mautofs.rest = NoSave(ConfigText(default = "", visible_width = 40, fixed_size = False))

class ManagerAutofsAutoEdit(Screen, ConfigListScreen):
	skin = """
		<screen position="center,center" size="560,495">
			<widget name="red" position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<widget name="green" position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="red" font="Regular;20" transparent="1"/>
			<widget name="key_green" position="140,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="green" font="Regular;20" transparent="1"/>
			<widget name="text" position="5,42" size="550,56" font="Regular;14" halign="left" valign="center"/>
			<widget name="config" position="5,100" size="550,375" scrollbarMode="showOnDemand"/>
			<widget source="VKeyIcon" render="Pixmap" pixmap="skin_default/buttons/key_text.png" position="10,475" zPosition="10" size="35,25" transparent="1" alphatest="on">
				<convert type="ConditionalShowHide"/>
			</widget>
			<!--widget name="HelpWindow" position="160,300" size="0,0"/-->
		</screen>"""

	def __init__(self, session, filename, line, new=False):
		Screen.__init__(self, session)
		name = "%s%s%s" % (bC, filename, fC)
		self.setTitle(_("Manager Autofs - edited autofile/record: %s") % name)
		self.session = session
		self.new = new
		self["text"] = Label("")
		self.autoName = filename
		
		self["key_red"] = Button(_("Close"))
		self["key_green"] = Button(_("Ok"))
		self["red"] = Pixmap()
		self["green"] = Pixmap()
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["VKeyIcon"] = Boolean(False)
		
		self.list = [ ]
		self.onChangedEntry = [ ]
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)		

		self["actions"] = ActionMap(["SetupActions","OkCancelActions","ColorActions"],
			{
#			"ok":		self.keyOk,
			"cancel":	self.keyClose,
			"green":	self.keyOk,
			"red":		self.keyClose,
			 }, -1)

		self.msgNM=None

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
		self.fstype = _("fstype")
		self.list.append(getConfigListEntry(self.fstype, cfg.fstype))
		if cfg.fstype.value == "nfs":
			self.list.append(getConfigListEntry(dx + _("soft"), cfg.soft))
			self.list.append(getConfigListEntry(dx + _("intr"), cfg.intr))
		self.list.append(getConfigListEntry(_("rw/ro"), cfg.rw))
		self.useduserpass = _("use user/pass")
		self.list.append(getConfigListEntry(self.useduserpass, cfg.useduserpass))
		if cfg.useduserpass.value:
			if cfg.user.value == "":
				cfg.user.value = cfg.pre_user.value
			if not cfg.passwd.value:
				cfg.passwd.value = cfg.pre_passwd.value
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
		self.use_ip_or_name = _("use ip/name or dev")
		self.list.append(getConfigListEntry(self.use_ip_or_name, cfg.use_ip_or_name))
		if cfg.use_ip_or_name.value:
			self.usedip = dx + _("ip or name")
			self.list.append(getConfigListEntry(self.usedip, cfg.usedip))
			if cfg.usedip.value:
				self.list.append(getConfigListEntry(2*dx + _("ip"), cfg.ip))
			else:
				self.list.append(getConfigListEntry(2*dx + _("name"), cfg.name))
		else:
			self.list.append(getConfigListEntry(dx + _("dev"), cfg.dev))
		self.list.append(getConfigListEntry(_("shared remote directory"), cfg.remotedir))
		if cfg.fstype.value == "cifs":
			self.list.append(getConfigListEntry(_("smb version"), cfg.smb))
		self.list.append(getConfigListEntry(_("user string"), cfg.rest))

		self["config"].list = self.list
		self["config"].setList(self.list)

		self.fillString()

	def changedEntry(self):
		if self["config"].getCurrent()[0] in (self.useddomain, self.useduserpass, self.use_ip_or_name, self.usedip, self.fstype):
			self.createConfig()
		self.fillString()

	def fillString(self):
		self["text"].setText(self.actualizeString())

	def actualizeString(self):
		string = cfg.localdir.value
		string += " "
		string += "-"
		string += ("fstype=%s," % cfg.fstype.value) if cfg.fstype.value != "" else ""
		string += ("%s," % cfg.rw.value) if cfg.rw.value else ""
		string += "soft," if cfg.soft.value else ""
		string += "intr," if cfg.intr.value else ""
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
		string += ("vers=%s," % cfg.smb.value) if cfg.smb.value != "" and cfg.fstype.value == "cifs" else ""
		string += ("%s,") % cfg.rest.value if cfg.rest.value else ""
		string = string.rstrip(',')
		string += " "
		if cfg.use_ip_or_name.value:
			server = "%s.%s.%s.%s" % (tuple(cfg.ip.value)) if cfg.usedip.value else cfg.name.value
			if cfg.fstype.value == "nfs":
				string += ("%s:/%s" % (server, cfg.remotedir.value))
			else:
				string += ("://%s/%s" % (server, cfg.remotedir.value))
		else:
			string += (":/%s/%s" % (cfg.dev.value, cfg.remotedir.value))
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
		cfg.soft.value = cfg.soft.default
		cfg.intr.value = cfg.intr.default
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
		cfg.use_ip_or_name.value = cfg.use_ip_or_name.default
		cfg.ip.value = cfg.ip.default
		cfg.name.value = cfg.name.default
		cfg.dev.value = cfg.dev.default
		cfg.remotedir.value = cfg.remotedir.default
		cfg.smb.value = cfg.smb.default
		cfg.rest.value = cfg.rest.default

	def prepareOff(self):
		# set (all what has sence, f.eg. if default is as True) as off or empty before parsing existing line
		cfg.rw.value = ""
		cfg.soft.value = False
		cfg.intr.value = False
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
				if "fstype" in x:
					cfg.fstype.value=x.split('=')[1]
				elif "vers" in x:
					cfg.smb.value=x.split('=')[1]
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
				elif x == "soft":
					cfg.nodev.value=True
				elif x == "intr":
					cfg.nodev.value=True
				else:
					rest +=x

			# dir name
			cfg.localdir.value = parts[0].strip()

			# ip/name and shared remote dir or dev and remote dir
			cfg.usedip.value = False
			if parts[2].startswith('://'): 		# cifs	://10.0.0.10/video
				cfg.use_ip_or_name.value = True
				remote = parts[2].split('/')
				if self.testIfIP(remote[2]):
					cfg.usedip.value = True
					cfg.ip.value = self.convertIP(remote[2])
				else:
					cfg.name.value = remote[2]
				cfg.remotedir.value = remote[3]
			elif parts[2].find(':/'):		# nfs	10.0.0.10:/video
				cfg.use_ip_or_name.value = True
				remote = parts[2].split(':/')
				if self.testIfIP(remote[0]):
					cfg.usedip.value = True
					cfg.ip.value = self.convertIP(remote[0])
				else:
					cfg.name.value = remote[0]
				cfg.remotedir.value = remote[1]
			else:					# DVD,CD	:/dev/sr0
				cfg.use_ip_or_name.value = False
				remote = parts[2].split('/')
				cfg.dev.value = remote[1]
				cfg.remotedir.value = remote[2]
			cfg.rest.value = rest
		except:
			self.MessageBoxNM(True, _("Wrong file format!"), 5)

	def testIfIP(self, string):
		if len(string.split('.'))==4:
			return True
		return False

	def convertIP(self, ip):
		strIP = ip.split('.')
		ip = []
		for x in strIP:
			ip.append(int(x))
		return ip

	def MessageBoxNM(self, display=False, text="", delay=0):
		if self.msgNM:
			self.session.deleteDialog(self.msgNM)
			self.msgNM = None
		else:
			if display and self.session is not None:
				self.msgNM = self.session.instantiateDialog(NonModalMessageBoxDialog, text=text, delay=delay)
				self.msgNM.show()

class ManagerAutofsMultiAutoEdit(Screen):
	skin = """
		<screen name="ManagerAutofsMultiAutoEdit" position="center,center" size="680,400">
			<widget name="red" position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<widget name="green" position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<widget name="yellow" position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<widget name="blue" position="420,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="red" font="Regular;20" transparent="1"/>
			<widget name="key_green" position="140,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="green" font="Regular;20" transparent="1"/>
			<widget name="key_yellow" position="280,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="yellow" font="Regular;20" transparent="1"/>
			<widget name="key_blue" position="420,0" size="140,40" zPosition="1" valign="center" halign="center" backgroundColor="blue" font="Regular;20" transparent="1"/>
			<widget source="list" render="Listbox" position="5,40" size="670,320" scrollbarMode="showOnDemand">
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
			<widget name="text" position="5,380" zPosition="10" size="660,15" font="Regular;11" halign="left" valign="center"/>
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
		self["red"] = Pixmap()
		self["green"] = Pixmap()
		self["yellow"] = Pixmap()
		self["blue"] = Pixmap()

		self["text"] = Label("")

		self.msgNM=None

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
					self.list.append((line.split()[0], line))
			self['list'].setList(self.list)

	def selectionChanged(self):
		self.refreshText()

	def refreshText(self):
		current = self["list"].getCurrent()
		if current:
			self["text"].setText("%s" % current[1])

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

	def MessageBoxNM(self, display=False, text="", delay=0):
		if self.msgNM:
			self.session.deleteDialog(self.msgNM)
			self.msgNM = None
		else:
			if display and self.session is not None:
				self.msgNM = self.session.instantiateDialog(NonModalMessageBoxDialog, text=text, delay=delay)
				self.msgNM.show()

class ManagerAutofsPreset(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "Setup"
		self["config"] = List()

		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("OK"))

		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["VKeyIcon"] = Boolean(False)

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.save,
			"ok": self.save,
			"red": self.exit,
			"cancel": self.exit
		}, -2)

		list = []
		list.append(getConfigListEntry(_("user"), cfg.pre_user))
		list.append(getConfigListEntry(_("password"), cfg.pre_passwd))
		list.append(getConfigListEntry(_("save preset values"), cfg.pre_save, _("Preset values will be or will not be saved on plugin exit.")))
		ConfigListScreen.__init__(self, list, session)
		self.onShown.append(self.setWindowTitle)

	def setWindowTitle(self):
		self.setTitle(_("User and password preseting"))
	def save(self):
		self.keySave()
	def exit(self):
		self.keyCancel()

class ManagerAutofsClearBookmarks(Screen, HelpableScreen):
	skin="""
	<screen name="ManagerAutofs" position="center,center" size="600,390" title="List of bookmarks">
		<ePixmap name="red"    position="0,0"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
		<ePixmap name="green"  position="140,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on"/>
		<ePixmap name="yellow" position="280,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on"/>
		<ePixmap name="blue"   position="420,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on"/>
		<widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_yellow" position="280,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_blue" position="420,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="config" position="5,50" zPosition="2" size="590,300" foregroundColor="white" scrollbarMode="showOnDemand"/>
		<ePixmap pixmap="skin_default/div-h.png" position="5,355" zPosition="2" size="590,2"/>
		<widget name="text" position="5,360" zPosition="2" size="590,25" valign="center" halign="left" font="Regular;22" foregroundColor="white"/>
	</screen>
	"""
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.skinName = ["ManagerAutofsRemoveBackupFiles", "Setup"]
		self.session = session

		self.setTitle(_("List of bookmarks"))
		self.original_selectionpng = None
		self.changePng()

		self.list = SelectionList([])
		if self.loadAllMovielistVideodirs():
			index = 0
			for bookmark in eval(config.movielist.videodirs.saved_value):
				self.list.addSelection(bookmark, bookmark, index, False)
				index += 1
		self["config"] = self.list

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
			"cancel": (self.exit, _("Close")),
			"ok": (self.list.toggleSelection, _("Add or remove item of selection")),
			})
		self["ManagerAutofsActions"] = HelpableActionMap(self, "ColorActions",
			{
			"red": (self.exit, _("Close")),
			"green": (self.deleteSelected, _("Delete selected")),
			"yellow": (self.sortList, _("Sort list")),
			"blue": (self.list.toggleAllSelection, _("Invert selection")),
			}, -2)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Delete"))
		self["key_yellow"] = Button(_("Sort"))
		self["key_blue"] = Button(_("Inversion"))

		self.sort = 0
		self["text"] = Label(_("Select with 'OK' and then remove with 'Delete'."))
		self["config"].onSelectionChanged.append(self.bookmark)

	def loadAllMovielistVideodirs(self):
		if config.movielist.videodirs.saved_value:
			sv = config.movielist.videodirs.saved_value
			tmp = eval(sv)
			locations = [[x, None, False, False] for x in tmp]
			for x in locations:
				x[1] = x[0]
				x[2] = True
			config.movielist.videodirs.locations = locations
			return True
		return False

	def bookmark(self):
		item = self["config"].getCurrent()
		if item:
			text = "%s" % item[0][0]
			self["text"].setText(text)

	def sortList(self):
		if self.sort == 0:	# z-a
			self.list.sort(sortType=0, flag=True)
			self.sort += 1
		elif self.sort == 1 and len(self.list.getSelectionsList()):	# selected top
			self.list.sort(sortType=3, flag=True)
			self.sort += 1
		else:			# a-z
			self.list.sort(sortType=0)
			self.sort = 0

	def deleteSelected(self):
		if self["config"].getCurrent():
			selected = len(self.list.getSelectionsList())
			if not selected:
				selected = 1
			self.session.openWithCallback(self.delete, MessageBox, _("Are You sure to delete %s selected bookmark(s)?") % selected, type=MessageBox.TYPE_YESNO, default=False)

	def delete(self, choice):
		if choice:
			bookmarks = config.movielist.videodirs.value
			data = self.list.getSelectionsList()
			selected = len(data)
			if not selected:
				data = [self["config"].getCurrent()[0]]
				selected = 1
			for item in data:
				# item ... (name, name, index, status)
				self.list.removeSelection(item)
				bookmarks.remove(item[0])
			config.movielist.videodirs.value = bookmarks
			config.movielist.videodirs.save()

	def changePng(self):
		path = resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/mark_select.png")
		if os.path.exists(path):
			import Components.SelectionList
			self.original_selectionpng = Components.SelectionList.selectionpng
			Components.SelectionList.selectionpng = LoadPixmap(cached=True, path=path)

	def exit(self):
		if self.original_selectionpng:
			import Components.SelectionList
			Components.SelectionList.selectionpng = self.original_selectionpng
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

class useMountAsHDD():
	def __init__(self):
		pass

	def createSymlink(self):
		path = cfg.hddreplace.value
		hdd_dir = DEFAULT_HDD
		print "[ManagerAutofs] symlink %s %s" % (path, hdd_dir)
		if os.path.islink(hdd_dir):
			if os.readlink(hdd_dir) != path:
				os.remove(hdd_dir)
				os.symlink(path, hdd_dir)
		elif os.path.ismount(hdd_dir) is False:
			if os.path.isdir(hdd_dir):
				rm_rf(hdd_dir)
		try:
			os.symlink(path, hdd_dir)
		except OSError, ex:
			print "[ManagerAutofs] add symlink fails!", ex
		movie = os.path.join(hdd_dir, 'movie')
		if not os.path.exists(movie):
			try:
				os.mkdir(movie)
			except Exception, ex:
				print "[ManagerAutofs] Failed to create ", movie, "Error:", ex
	def setDefault(self):
		cfg.hddreplace.value = DEFAULT_HDD
		cfg.hddreplace.save()

makeMountAsHDD = useMountAsHDD()