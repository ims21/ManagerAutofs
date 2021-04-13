#
#  Manager Autofs
#
#  $Id$
#
#  Coded by ims (c) 2017-2019
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
from Components.config import config, ConfigSubsection, ConfigYesNo, ConfigText

plugin_path = None

config.plugins.mautofs = ConfigSubsection()
config.plugins.mautofs.extended_menu = ConfigYesNo(default=False)
config.plugins.mautofs.hddreplace = ConfigText(default="/media/hdd", visible_width=30, fixed_size=False)

def mountedLocalHDD():
	from os import system
	cmd = "mount | grep '/dev' | grep '/media/hdd'"
	if system(cmd):
		return False
	return True

def main(session, **kwargs):
	import ui
	session.open(ui.ManagerAutofsMasterSelection)

def sessionstart(reason, **kwargs):
	if reason == 0:
		import ui
		if not mountedLocalHDD():
			if config.plugins.mautofs.hddreplace.value != "/media/hdd":
				ui.makeMountAsHDD.createSymlink()

def Plugins(path,**kwargs):
	global plugin_path
	plugin_path = path
	name = _("Manager Autofs")
	descr = _("Manage autofs files and conection")
	list = [PluginDescriptor(name=name, description=descr, where=PluginDescriptor.WHERE_PLUGINMENU, icon='plugin.png', fnc=main)]
	list.append(PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart))
	if config.plugins.mautofs.extended_menu.value:
		list.append(PluginDescriptor(name=name, description=descr, where=PluginDescriptor.WHERE_EXTENSIONSMENU, icon='plugin.png', fnc=main))
	return list
