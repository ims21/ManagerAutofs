#from . import _

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from Components.Button import Button
from Components.Pixmap import Pixmap

import ui

class ManagerAutofsHelp(Screen):
	skin = """
	<screen position="center,center" size="660,520" title="ManagerAutofs Help" backgroundColor="#00000000">
		<ePixmap name="red"    position="0,0"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
		<ePixmap name="green"  position="140,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on"/>
		<ePixmap name="yellow" position="280,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on"/> 
		<ePixmap name="blue"   position="420,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on"/>
		<widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;22" transparent="1" shadowColor="background" shadowOffset="-2,-2"/> 
		<widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;22" transparent="1" shadowColor="background" shadowOffset="-2,-2"/> 
		<widget name="key_yellow" position="280,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;22" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_blue" position="420,0" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;22" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="HelpText" position="5,50" size="650,441" font="Regular;18" backgroundColor="#00000000" scrollbarMode="showOnDemand"/>

		<ePixmap pixmap="skin_default/div-h.png" position="0,496" zPosition="1" size="660,2"/>
		<ePixmap alphatest="on" pixmap="skin_default/icons/clock.png" position="580,503" size="14,14" zPosition="3"/>
		<widget font="Regular;18" halign="left" position="605,500" render="Label" size="55,20" source="global.CurrentTime" transparent="1" valign="center" zPosition="3">
			<convert type="ClockToText">Default</convert>
		</widget>
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self["key_red"] = Button(_("Close"))
		self["key_green"] = Button(_("All"))
		self["key_yellow"] = Button(_("Mode II"))
		self["key_blue"] = Button(_("Mode III"))

		self["HelpText"] = ScrollLabel()

		self["Actions"] = ActionMap(["WizardActions","ColorActions"],
			{
				"back": self.close,
				"red": self.close,
				"green": self.all,
				"yellow": self.mode2,
				"blue": self.mode3,
				"ok": self.close,
				"up": self["HelpText"].pageUp,
				"down": self["HelpText"].pageDown,
			}, -1)

		self.setTitle(_("Help"))
		self.all()

	def mode2(self):
		self["HelpText"].setText(self.mode2txt())

	def mode3(self):
		self["HelpText"].setText(self.mode3txt())

	def all(self):
		self["HelpText"].setText(self.mode1txt() + self.mode2txt() + self.mode3txt())

	def mode1txt(self):
		text = ("Install autofs as: opkg install autofs\n")
		text += "\n"
		text += "\n"
		text += ("Then edit:\n")
		text += ("    /etc/auto.master file (for this plugin use lines with parameters only!)\n")
		text += ("    /etc/auto.xxxx - as 'xxxx' use any name\n")
		text += "\n"
		text += ("%sMode I:%s  (auto.master + one auto.xxxx only)\n") % (ui.yC,ui.fC)
		text += "\n"
		text += ("/etc/auto.master -one record only, mountpoint must be '/mnt/net':\n")
		text += ("/mnt/net /etc/auto.test --ghost\n")
		text += "\n"
		text += ("/etc/auto.test - 'test' used as example:\n")
		text += "\n"
		text += ("video -fstype=cifs,user=root,...,sec=ntlm ://10.0.0.10/hdd\n")
		text +=	("hdd -fstype=cifs,...,iocharset=utf8,sec=ntlm ://10.0.0.20/hdd\n")
		text +=	("hdd2 -fstype=cifs,...,sec=ntlm ://10.0.0.17/hdd\n")
		text += "\n"
		text += ("All remote directories from all devices will be mounted under '/media/net':\n")
		text += ("  /media/net/video\n")
		text += ("  /media/net/hdd\n")
		text += ("  /media/net/hdd2\n")
		text += "\n"
		text += ("+ only 2 files for whole work\n")
		text += ("- mount/umount all together\n")
		text += ("- it is not very clear what is what\n")
		text += ("(It has not sense using this mode with this plugin)\n")
		text += "\n"
		return text

	def mode2txt(self):
		text = ("%sMode II:%s  (auto.master + more auto.xxxx files)\n") % (ui.yC,ui.fC)
		text += "\n"
		text += ("auto.master with more records (no mountpoint as '/mnt/net'):\n")
		text += ("/mnt/f1 /etc/auto.formuler --ghost\n")
		text += ("/mnt/render /etc/auto.render --ghost\n")
		text += ("/mnt/wd /etc/auto.wd --ghost\n")
		text += "\n"
		text += ("more auto.xxxx files - each file for one shared directory:\n")
		text += ("auto.formuler:\n")
		text += ("hdd -fstype=cifs,...,sec=ntlm ://192.168.0.20/hdd\n")
		text += "\n"
		text += ("auto.render:\n")
		text += ("video -fstype=cifs,...,sec=ntlm, ://192.168.0.219/hdd\n")
		text += "\n"
		text += ("auto.wd:\n")
		text += ("hdd -fstype=cifs,...,sec=ntlm ://192.168.0.17/hdd\n")
		text += "\n"
		text += ("Each shared directory has own mounpoint under /media:\n")
		text += ("/media/f1/hdd\n")
		text += ("/media/render/video\n")
		text += ("/media/wd/hdd\n")
		text += "\n"
		text += ("- more auto.xxxx files\n")
		text += ("+ can be mounted/umounted independently with uncomment/comment line(s) in auto.master\n")
		text += ("+ very clear what is what\n")
		text += "\n"
		return text

	def mode3txt(self):
		text = ("%sMode III:%s  (similar as II)\n") % (ui.yC,ui.fC)
		text += "\n"
		text += ("-in auto.xxxx files can be used more lines\n")
		text += ("-useful, if one device sharing more directories\n")
		text += "\n"
		text += ("example of auto.synology:\n")
		text += ("video -fstype=cifs,...,iocharset=utf8 ://10.0.0.99/video\n")
		text += ("audio -fstype=cifs,...,iocharset=utf8 ://10.0.0.99/music\n")
		text += ("then will be mounted as:\n")
		text += ("...\n")
		text += ("/media/synology/video\n")
		text += ("/media/synology/audio\n")
		text += ("...\n")
		text += "\n"
		return text