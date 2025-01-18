from Screens.Screen import Screen
from Components.Label import Label
from enigma import eTimer

class NonModalMessageBoxDialog(Screen):
	skin = """
		<screen name="NonModalMessageBoxDialog" position="center,center" size="470,120" backgroundColor="#00808080" zPosition="2" flags="wfNoBorder">
			<widget name="message" position="center,center" size="460,110" font="Regular;20" valign="center" halign="center"/>
		</screen>
	"""

	def __init__(self, session, text="", delay=1):
		Screen.__init__(self, session)
		self.text = text
		self.delay = delay
		self["message"] = Label(text=text)

		self.timer = eTimer()
		self.timer.callback.append(self.timerLoop)

		self.onLayoutFinish.append(self.timerStart)

	def timerStart(self):
		self["message"].setText(self.text)
		self.timer.start(True)

	def timerLoop(self):
		if self.delay > 0:
			self.delay -= 1
			self.timer.start(1000, True)
		else:
			self.session.deleteDialog(self)

	def show(self):
		self["message"].setText(self.text)
		Screen.show(self)

def MessageBoxNM(session, text="", delay=1):
	msgNM = getattr(session, 'msgNM', None)

	if msgNM:
		session.deleteDialog(msgNM)
		del session.msgNM
	elif text and session:
		session.msgNM = session.instantiateDialog(NonModalMessageBoxDialog, text=text, delay=delay)
		session.msgNM.show()
