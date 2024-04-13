import json
import random
import threading
import time
from kivy.core.clipboard import Clipboard
import requests
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
import os
from kivy.core.window import Window
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
from kivymd.uix.button import MDFlatButton, MDRoundFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivy.core.clipboard import Clipboard

Window.size = (480, 800)
node = "https://allen_neon_rpc.serveo.net"

address = "26UfgMo6TEVY3FiGBFjufAiq1ujD47r1A2znBNSyhxfY4"


class Tab(MDFloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''


class Content(MDBoxLayout):
    pass


class Wallet(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.events)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            preview=True
        )
        self.file_manager.ext = [".txt"]
        self.dialog_send = None
        self.dialog_staking = None

    def file_manager_open(self, file):
        self.manager_open = True
        self.file_manager.show(os.path.expanduser("D:/"))

    def show_confirmation_dialog(self):
        self.dialog_send = MDDialog(
            title="Address:",
            type="custom",
            content_cls=Content(),
            buttons=[
                MDFlatButton(
                    text="Отмена",
                    theme_text_color="Custom",
                    text_color=self.theme_cls.primary_color,
                    on_release=lambda x: self.dialog_close(self.dialog_send),
                ),
                MDFlatButton(
                    text="Отправить",
                    theme_text_color="Custom",
                    text_color=self.theme_cls.primary_color,
                    on_release=lambda x: self.send(self.dialog_send),
                ),
            ],
        )
        self.dialog_send.open()

    def select_path(self, path):
        '''It will be called when you click on the file name
        or the catalog selection button.

        :type path: str;
        :param path: path to the selected directory or file;
        '''

        self.exit_manager()
        self.root.ids.download_pem.text = f"{path}"

        toast(path)

    def exit_manager(self, *args):
        '''Called when the user reaches the root of the directory tree.'''

        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        '''Called when buttons are pressed on the mobile device.'''

        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.material_style = "M3"
        return Builder.load_file("kivy.kv")

    def on_start(self):
        self.screen("main_screen")
        self.refresh_balance()

    def screen(self, id_):
        self.root.current = id_

    def dialog_close(self, target):
        target.dismiss()

    def refresh_balance(self):
        account = json.loads(requests.get(f"{node}/account/{address}").text)
        atoms = account["atoms"]
        balance = atoms / 1_000_000
        self.root.ids.user_address.text = address
        self.root.ids.balance_user.text = f"{balance} Neon"

wallet = Wallet()
wallet.run()
