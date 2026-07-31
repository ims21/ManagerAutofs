# -*- coding: utf-8 -*-

from . import _, ngettext

from Components.config import configfile
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import resolveFilename, SCOPE_CONFIG

from shutil import copyfile
import os
import stat
import tempfile


DEFAULT_PATH = "/media/dir/"
SETTINGS_FILE = resolveFilename(SCOPE_CONFIG, "settings")
BACKUP_FILE = SETTINGS_FILE + ".path-editor.bak"


try:
	unicode
except NameError:
	unicode = str


def asBytes(value):
	if isinstance(value, bytes):
		return value
	return value.encode("UTF-8")


def asText(value):
	if isinstance(value, unicode):
		return value
	return value.decode("UTF-8", "replace")


def findEntries(data, oldText):
	oldBytes = asBytes(oldText)
	lines = data.splitlines(True)
	entries = []
	for index, line in enumerate(lines):
		key, separator, value = line.partition(b"=")
		if separator and oldBytes in value:
			entries.append((index, key, value.count(oldBytes)))
	return lines, entries


class SettingsPathEditor:
	def __init__(self, session, bookmarks, callback=None, beforeRestart=None):
		self.session = session
		self.bookmarks = bookmarks
		self.callback = callback
		self.beforeRestart = beforeRestart
		self.selectPath()

	def finish(self, *args):
		if self.callback:
			callback = self.callback
			self.callback = None
			callback()

	def selectPath(self):
		choices = [(_("Enter manually...") + "  " + DEFAULT_PATH, DEFAULT_PATH)]
		seen = {DEFAULT_PATH}
		for path in self.bookmarks:
			if path and path not in seen:
				choices.append((path, path))
				seen.add(path)
		self.session.openWithCallback(
			self.pathSelected,
			ChoiceBox,
			title=_("Select path to replace:"),
			list=choices,
			keys=["dummy"] * len(choices)
		)

	def pathSelected(self, choice):
		if choice:
			self.session.openWithCallback(
				self.searchEntered,
				VirtualKeyBoard,
				title=_("Text to replace in settings:"),
				text=choice[1]
			)
		else:
			self.finish()

	def searchEntered(self, oldText):
		if oldText is None:
			self.finish()
			return
		if not oldText:
			self.session.openWithCallback(
				lambda *_: self.selectPath(),
				MessageBox,
				_("The search text must not be empty."),
				type=MessageBox.TYPE_ERROR,
				timeout=10
			)
			return
		try:
			data = self.readSettings()
			_dummy, entries = findEntries(data, oldText)
		except Exception as error:
			print("[ManagerAutofs] Failed to read settings:", error)
			self.showError(_("Failed to read the settings file."))
			return

		if not entries:
			self.session.openWithCallback(
				self.finish,
				MessageBox,
				_("The search text was not found in any settings value."),
				type=MessageBox.TYPE_INFO,
				timeout=8
			)
			return

		self.session.openWithCallback(
			lambda newText: self.replacementEntered(oldText, newText),
			VirtualKeyBoard,
			title=_("Replace with text:"),
			text=asText(oldText)
		)

	def replacementEntered(self, oldText, newText):
		if newText is None:
			self.finish()
			return
		if oldText == newText:
			self.session.openWithCallback(
				self.finish,
				MessageBox,
				_("The search and replacement texts are identical."),
				type=MessageBox.TYPE_INFO,
				timeout=8
			)
			return
		try:
			data = self.readSettings()
			self.lines, self.entries = findEntries(data, oldText)
		except Exception as error:
			print("[ManagerAutofs] Failed to read settings:", error)
			self.showError(_("Failed to read the settings file."))
			return

		if not self.entries:
			self.session.openWithCallback(
				self.finish,
				MessageBox,
				_("The search text was not found in any settings value."),
				type=MessageBox.TYPE_INFO,
				timeout=8
			)
			return

		self.oldText = oldText
		self.newText = newText
		self.oldBytes = asBytes(oldText)
		self.newBytes = asBytes(newText)
		self.entryIndex = 0
		self.changedEntries = 0
		self.replacements = 0
		self.confirmEntry()

	def confirmEntry(self):
		if self.entryIndex >= len(self.entries):
			self.writeChanges()
			return

		_dummy, key, occurrences = self.entries[self.entryIndex]
		text = _("Replace text in this settings entry?") + "  (%d/%d)" % (self.entryIndex + 1, len(self.entries))
		text += "\n\n" + asText(key)
		text += "\n\n" + ngettext("- %d match found", "- %d matches found", occurrences) % occurrences
		text += "\n\n" + _("Original text:") + "\n" + asText(self.oldText)
		text += "\n\n" + _("New text:") + "\n" + asText(self.newText)
		self.session.openWithCallback(
			self.entryConfirmed,
			MessageBox,
			text,
			type=MessageBox.TYPE_YESNO,
			default=False
		)

	def entryConfirmed(self, answer):
		lineIndex, _key, occurrences = self.entries[self.entryIndex]
		if answer:
			key, separator, value = self.lines[lineIndex].partition(b"=")
			self.lines[lineIndex] = key + separator + value.replace(self.oldBytes, self.newBytes)
			self.changedEntries += 1
			self.replacements += occurrences
		self.entryIndex += 1
		self.confirmEntry()

	def writeChanges(self):
		if not self.changedEntries:
			self.session.openWithCallback(
				self.finish,
				MessageBox,
				_("No settings entries were changed."),
				type=MessageBox.TYPE_INFO,
				timeout=8
			)
			return

		text = ngettext("%d occurrence was updated.", "%d occurrences were updated.", self.replacements) % self.replacements
		text += "\n" + ngettext("%d settings entry was changed.", "%d settings entries were changed.", self.changedEntries) % self.changedEntries
		text += "\n\n" + _("Apply changes and restart the GUI?")
		self.session.openWithCallback(
			self.applyConfirmed,
			MessageBox,
			text,
			type=MessageBox.TYPE_YESNO,
			default=False
		)

	def applyConfirmed(self, answer):
		if not answer:
			self.finish()
			return
		try:
			self.writeSettings(b"".join(self.lines))
		except Exception as error:
			print("[ManagerAutofs] Failed to update settings:", error)
			self.showError(_("Failed to update the settings file."))
			return

		try:
			configfile.load()
		except Exception as error:
			print("[ManagerAutofs] Failed to reload settings:", error)
			try:
				copyfile(BACKUP_FILE, SETTINGS_FILE)
				configfile.load()
			except Exception as restoreError:
				print("[ManagerAutofs] Failed to restore settings:", restoreError)
			self.showError(_("Failed to reload the settings file. The original file was restored."))
			return

		if self.beforeRestart:
			self.beforeRestart()
		self.session.open(TryQuitMainloop, 3)

	def readSettings(self):
		with open(SETTINGS_FILE, "rb") as settings:
			return settings.read()

	def writeSettings(self, data):
		settingsStat = os.stat(SETTINGS_FILE)
		copyfile(SETTINGS_FILE, BACKUP_FILE)
		fileDescriptor, tempFile = tempfile.mkstemp(prefix=".settings.", dir=os.path.dirname(SETTINGS_FILE))
		try:
			with os.fdopen(fileDescriptor, "wb") as settings:
				settings.write(data)
				settings.flush()
				os.fsync(settings.fileno())
			os.chmod(tempFile, stat.S_IMODE(settingsStat.st_mode))
			try:
				os.chown(tempFile, settingsStat.st_uid, settingsStat.st_gid)
			except OSError:
				pass
			os.rename(tempFile, SETTINGS_FILE)
		except Exception:
			try:
				os.unlink(tempFile)
			except OSError:
				pass
			raise

	def showError(self, text):
		self.session.openWithCallback(self.finish, MessageBox, text, type=MessageBox.TYPE_ERROR, timeout=10)
