# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from os import environ as os_environ
import gettext


def localeInit():
	gettext.bindtextdomain("ManagerAutofs", resolveFilename(SCOPE_PLUGINS, "Extensions/ManagerAutofs/locale"))


def _(txt):
	t = gettext.dgettext("ManagerAutofs", txt)
	if t == txt:
#		print("[ManagerAutofs] fallback to default translation for", txt)
		t = gettext.gettext(txt)
	return t


def ngettext(singular, plural, n):
	t = gettext.dngettext('ManagerAutofs', singular, plural, n)
	if t in (singular, plural):
		t = gettext.ngettext(singular, plural, n)
	return t


localeInit()
language.addCallback(localeInit)
