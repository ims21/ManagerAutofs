from . import _

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
		self["HelpText"].setText(self.prolog() + self.mode1txt() + self.mode2txt() + self.mode3txt())

	def prolog(self):
		text = _("Install autofs with:  opkg install autofs") + "\n\n"
		text += _("- then edit:") + "\n\n"
		text += 4*" " + _("/etc/auto.master file (for this plugin use lines with parameters only!)") + "\n"
		text += 4*" " + _("/etc/auto.xxxx - as 'xxxx' use any name") + "\n\n"
		return text

	def mode1txt(self):
		text = _("%sMode I:%s  (auto.master + one auto.xxxx only)") % (ui.yC,ui.fC) + "\n\n"
		text += _("/etc/auto.master - one record only, mountpoint must be '/mnt/net':") + "\n"
		text += 4*" " + ("%s/mnt/net /etc/auto.test --ghost%s") % (ui.greyC,ui.fC) + "\n\n"
		text += _("/etc/auto.test - 'test' used as example:") + "\n"
		text += 4*" " + ("%svideo -fstype=cifs,user=root,...,sec=ntlm ://192.168.1.10/hdd%s") % (ui.greyC,ui.fC) + "\n"
		text +=	4*" " + ("%shdd -fstype=cifs,...,iocharset=utf8,sec=ntlm ://192.168.1.20/hdd%s") % (ui.greyC,ui.fC) + "\n"
		text +=	4*" " + ("%shdd2 -fstype=cifs,...,sec=ntlm ://192.168.1.17/hdd%s") % (ui.greyC,ui.fC) + "\n\n"
		text += _("All remote directories from all devices will be mounted under '/media/net':") + "\n"
		text += 4*" " + ("%s/media/net/video%s") % (ui.greyC,ui.fC) + "\n"
		text += 4*" " + ("%s/media/net/hdd%s") % (ui.greyC,ui.fC) + "\n"
		text += 4*" " + ("%s/media/net/hdd2%s") % (ui.greyC,ui.fC) + "\n\n"
		text += _("+ only 2 files for whole work") + "\n"
		text += _("- mount/umount all together") + "\n"
		text += _("- it is not very clear what is what") + "\n"
		text += _("(It has not sense using this mode with this plugin)") + "\n\n"
		return text

	def mode2txt(self):
		text = _("%sMode II:%s  (auto.master + more auto.xxxx files)") % (ui.yC,ui.fC) + "\n\n"
		text += _("auto.master with more records (no mountpoint as '/mnt/net'):") + "\n"
		text += 4*" " + ("%s/mnt/f1 /etc/auto.formuler --ghost%s") % (ui.greyC,ui.fC) + "\n"
		text += 4*" " + ("%s/mnt/render /etc/auto.render --ghost%s") % (ui.greyC,ui.fC) + "\n"
		text += 4*" " + ("%s/mnt/wd /etc/auto.wd --ghost%s") % (ui.greyC,ui.fC) + "\n\n"
		text += _("more auto.xxxx files - each file for one shared directory:") + "\n"
		text += ("auto.formuler:") + "\n"
		text += 4*" " + ("%shdd -fstype=cifs,...,sec=ntlm ://192.168.1.20/hdd%s") % (ui.greyC,ui.fC) + "\n\n"
		text += ("auto.render:") + "\n"
		text += 4*" " + ("%svideo -fstype=cifs,...,sec=ntlm, ://192.168.1.219/hdd%s") % (ui.greyC,ui.fC) + "\n\n"
		text += ("auto.wd:") + "\n"
		text += 4*" " + ("%shdd -fstype=cifs,...,sec=ntlm ://192.168.1.17/hdd%s") % (ui.greyC,ui.fC) + "\n\n"
		text += _("Each shared directory has own mounpoint under /media:") + "\n"
		text += 4*" " + ("%s/media/f1/hdd%s") % (ui.greyC,ui.fC) + "\n"
		text += 4*" " + ("%s/media/render/video%s") % (ui.greyC,ui.fC) + "\n"
		text += 4*" " + ("%s/media/wd/hdd%s") % (ui.greyC,ui.fC) + "\n\n"
		text += _("- more auto.xxxx files") + "\n"
		text += _("+ very clear what is what") + "\n"
		text += _("+ can be mounted/umounted independently with uncomment/comment line(s) in auto.master") + "\n\n"
		return text

	def mode3txt(self):
		text = _("%sMode III:%s  (similar as II)") % (ui.yC,ui.fC) + "\n\n"
		text += _("-in auto.xxxx files can be used more lines") + "\n"
		text += _("-useful, if one device sharing more directories") + "\n"
		text += _("-everything else is the same as for II") + "\n\n"
		text += _("example of auto.synology:") + "\n"
		text += 4*" " + ("%svideo -fstype=cifs,...,iocharset=utf8 ://192.168.1.99/video%s") % (ui.greyC,ui.fC) + "\n"
		text += 4*" " + ("%saudio -fstype=cifs,...,iocharset=utf8 ://192.168.1.99/music%s") % (ui.greyC,ui.fC) + "\n\n"
		text += _("then will be mounted as:") + "\n"
		text += 4*" " + ("...") + "\n"
		text += 4*" " + ("%s/media/synology/video%s") % (ui.greyC,ui.fC) + "\n"
		text += 4*" " + ("%s/media/synology/audio%s") % (ui.greyC,ui.fC) + "\n"
		text += 4*" " + ("...") + "\n"
		return text