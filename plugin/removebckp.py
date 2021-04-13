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
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
from myselectionlist import MySelectionList
import skin
import os


class ManagerAutofsRemoveBackupFiles(Screen):
	skin = """
		<screen name="ManagerAutofsRemoveBackupFiles" position="center,center" size="560,410" title="ManagerAutofs - remove backup files">
		<ePixmap name="red"    position="0,0"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap name="green"  position="140,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap name="yellow" position="280,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap name="blue"   position="420,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" /> 
		<widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" /> 
		<widget name="key_yellow" position="280,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
		<widget name="key_blue" position="420,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />
		<widget name="config" position="5,50" zPosition="2" size="550,300" itemHeight="30" font="Regular;20" foregroundColor="white" scrollbarMode="showOnDemand" />
		<ePixmap pixmap="skin_default/div-h.png" position="5,355" zPosition="2" size="545,2" />
		<widget name="text" position="5,360" zPosition="2" size="550,50" valign="center" halign="left" font="Regular;20" foregroundColor="white" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.setTitle(_("Remove backup files"))

		data = MySelectionList([])
		nr = 0
		for x in os.listdir("/etc"):
			if x.startswith("auto.") and (x.endswith(".bak") or x.endswith(".del") or x.endswith(".$$$") or x.endswith("_bak")):
				data.addSelection(x, "/etc/%s" % x, nr, False)
				nr += 1

		self.list = data
		self.list.sort()

		self["config"] = self.list
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
		self["key_blue"] = Button(_("Inversion"))

		self["text"].setText(_("Press 'Remove' on file or mark files with OK and then use 'Remove'"))

	def removeCurrentEntries(self):
		marked = len(self.list.getSelectionsList())
		if marked:
			text = _("Are you sure to remove selected files?")
		else:
			text = _("Are you sure to remove file '%s'?") % self["config"].getCurrent()[0][1]
		self.session.openWithCallback(self.removeFromSource, MessageBox, text, MessageBox.TYPE_YESNO, default=False)

	def removeFromSource(self, answer):
		if answer == True:
			data = self.list.getSelectionsList()
			if data:
				for i in data:
					os.unlink(i[1])
					self.list.removeSelection(i)
			else:
				os.unlink(self["config"].getCurrent()[0][1])
				self.list.removeSelection(self["config"].getCurrent()[0])
		if not len(self.list.list):
			self.exit()

	def exit(self):
		self.close()
