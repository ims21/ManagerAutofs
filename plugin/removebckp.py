#
#  Manager Autofs
#
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
from Components.ActionMap import ActionMap
from Tools.Directories import SCOPE_PLUGINS, resolveFilename, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
import skin
import os

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, getDesktop
from Components.MenuList import MenuList
from plugin import plugin_path

from Components.Pixmap import Pixmap

select_png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/lock_on.png"))

# change select icons in list operation
def setIcon(delete=False):
	global select_png
	resolution = ""
	if getDesktop(0).size().width() <= 1280:
		resolution = "_sd"
	select_png = None
	if delete:
		select_png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, plugin_path + "/png/select_del%s.png" % resolution))
	else:
		select_png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, plugin_path + "/png/select_on%s.png" % resolution))
	if select_png is None:
		select_png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/lock_on.png"))

def MySelectionEntryComponent(description, value, index, selected):
	dx, dy, dw, dh = skin.parameters.get("SelectionListDescr",(35, 2, 650, 30))
	res = [
		(description, value, index, selected),
		(eListboxPythonMultiContent.TYPE_TEXT, dx, dy, dw, dh, 0, RT_HALIGN_LEFT, description)
	]
	if selected:
		ix, iy, iw, ih = skin.parameters.get("SelectionListLock",(0, 0, 24, 24))
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, ix, iy, iw, ih, select_png))
	return res

class MySelectionList(MenuList):
	def __init__(self, list = None, enableWrapAround = False):
		MenuList.__init__(self, list or [], enableWrapAround, content = eListboxPythonMultiContent)
		font = skin.fonts.get("SelectionList", ("Regular", 20, 30))
		self.l.setFont(0, gFont(font[0], font[1]))
		self.l.setItemHeight(font[2])

	def addSelection(self, description, value, index, selected = True):
		self.list.append(MySelectionEntryComponent(description, value, index, selected))
		self.setList(self.list)

	def removeSelection(self, line):
		for item in self.list:
			if item[0][2] == line[2]:
				self.list.pop(self.list.index(item))
		self.setList(self.list)

	def toggleSelection(self):
		idx = self.getSelectedIndex()
		item = self.list[idx][0]
		self.list[idx] = MySelectionEntryComponent(item[0], item[1], item[2], not item[3])
		self.setList(self.list)

	def getSelectionsList(self):
		return [ (item[0][0], item[0][1], item[0][2]) for item in self.list if item[0][3] ]

	def toggleAllSelection(self):
		for idx,item in enumerate(self.list):
			item = self.list[idx][0]
			self.list[idx] = MySelectionEntryComponent(item[0], item[1], item[2], not item[3])
		self.setList(self.list)

	def sort(self, sortType=False, flag=False):
		# sorting by sortType: # 0 - description, 1 - value, 2 - index, 3 - selected
		self.list.sort(key=lambda x: x[0][sortType],reverse=flag)
		self.setList(self.list)

	def len(self):
		return len(self.list)

class ManagerAutofsRemoveBackupFiles(Screen):
	skin = """
		<screen name="ManagerAutofsRemoveBackupFiles" position="center,center" size="560,410" title="RefreshBouquet - results">
		<ePixmap name="red"    position="0,0"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap name="green"  position="140,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap name="yellow" position="280,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap name="blue"   position="420,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" /> 
		<widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" /> 
		<widget name="key_yellow" position="280,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
		<widget name="key_blue" position="420,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
		<widget name="files" position="5,50" zPosition="2" size="550,300" itemHeight="30" font="Regular;20" foregroundColor="white" scrollbarMode="showOnDemand" />
		<ePixmap pixmap="skin_default/div-h.png" position="5,355" zPosition="2" size="545,2" />
		<widget name="text" position="5,360" zPosition="2" size="550,50" valign="center" halign="left" font="Regular;20" foregroundColor="white" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.setTitle(_("Remove backup files"))

		setIcon(True) # selection will be as red cross

		data = MySelectionList([])
		nr = 0
		for x in os.listdir("/etc"):
			if x.startswith("auto.") and (x.endswith(".bak") or x.endswith(".del") or x.endswith(".$$$")):
				data.addSelection(x, "/etc/%s" % x, nr, False)
				nr += 1

		self.list = data
		self.list.sort()

		self["files"] = self.list
		self["text"] = Label()

		self["actions"] = ActionMap(["OkCancelActions", "RefreshBouquetActions"],
			{
				"cancel": self.exit,
				"ok": self.list.toggleSelection,
				"red": self.exit,
				"green": self.removeCurrentEntries,
				"blue": self.list.toggleAllSelection,
			})

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Remove"))
#		self["key_yellow"] = Button()
		self["key_blue"] = Button(_("Inversion"))

		self["text"].setText(_("Press 'Remove' on file or mark files with OK and then use 'Remove'"))

	def removeCurrentEntries(self):
		marked = len(self.list.getSelectionsList())
		if marked:
			text = _("Are you sure to remove selected files?")
		else:
			text = _("Are you sure to remove file '%s'?") % self["files"].getCurrent()[0][1]
		self.session.openWithCallback(self.removeFromSource, MessageBox, text, MessageBox.TYPE_YESNO, default=False )

	def removeFromSource(self, answer):
		if answer == True:
			data = self.list.getSelectionsList()
			if data:
				for i in data:
					os.unlink(i[1])
					self.list.removeSelection(i)
			else:
				os.unlink(i[1])
				self.list.removeSelection(self["files"].getCurrent()[0])
		if not self.list.len():
			self.exit()

	def exit(self):
		self.close()
