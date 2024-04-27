import ecdsa.util
from kivy.core.clipboard import Clipboard
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.core.window import Window
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
from kivymd.uix.button import MDFlatButton, MDRoundFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivy.core.clipboard import Clipboard
from pathlib import Path

import requests
import json
import random
import os
import ecdsa
import base58
import random
import hashlib
import time
import threading

Window.size = (480, 800)
node = "http://allen_neon_rpc.serveo.net"

home_path = Path.joinpath(Path.home(), "neon_keypair.pem")

class Tab(MDFloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''


class Content(MDBoxLayout):
    pass


class Wallet(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.events)
        self.address = ""
        self.sk = None
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
                    on_release=lambda x: self.send(),
                )
            ],
        )
        self.dialog_send.open()

    def show_pem_dialog(self):
        self.dialog_pem = MDDialog(
            title="Private Key PEM",
            type="custom",
            content_cls=MDTextField (
                    text = self.sk.to_pem().decode(),
                    multiline=True
                ),
            buttons=[
                MDFlatButton(
                    text="Ок",
                    theme_text_color="Custom",
                    text_color=self.theme_cls.primary_color,
                    on_release=lambda x: self.dialog_close(self.dialog_pem),
                )
            ],
        )
        self.dialog_pem.open()

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
        self.screen("login")

        if os.path.isfile(home_path):
            f = open(home_path, "r")
            data = f.read()
            f.close()
            self.root.ids.sk_text.text = data
            self.login_by_sk()

    def screen(self, id_):
        self.root.current = id_

    def dialog_close(self, target):
        target.dismiss()

    def refresh_balance(self):
        balance = 0
        account = json.loads(requests.get(f"{node}/account/{self.address}").text)

        if account:
            atoms = account["atoms"]
            balance = atoms / 1_000_000
        
        self.root.ids.balance_user.text = f"{balance} Neon"

    def create_account(self):
        global address

        self.root.ids.sk_text.text = ecdsa.SigningKey.generate(curve=ecdsa.curves.SECP256k1).to_pem()

        self.login_by_sk()
    def send_logic(self, amount: int, to: str) -> tuple[dict, str]:
        message = {
            "nonce": str(random.randint(0, 10**100)),
            "instruction": {
                "program_id": "System",
                "accounts": [
                    # sender
                    {
                        "pubkey": self.address,
                        "is_signer": True,
                        "is_writable": True
                    },
                    # receiver
                    {
                        "pubkey": to,
                        "is_signer": False,
                        "is_writable": True
                    }
                ],
                "data": json.dumps (
                    {
                        "Send": {
                            "amount": int(amount * 1_000_000)
                        }
                    }
                ).replace(" ", "")
            }
        }
        a = json.dumps(message).replace(" ", "")
        print(f"Siging: {a}")

        sig = list(self.sk.sign_deterministic(a.encode(), sigencode=ecdsa.util.sigencode_der_canonize, hashfunc=hashlib.sha256))

        tx = {
            "signatures": [
                sig
            ],
            "message": message
        }

        print(f"Tx: {json.dumps(tx)}")

        ser_sig = base58.b58encode(bytes(sig)).decode()

        return (tx, ser_sig)
    
    def create_system_account_logic(self, pubkey: str) -> tuple[dict, str]:
        message = {
            "nonce": str(random.randint(0, 10**100)),
            "instruction": {
                "program_id": "System",
                "accounts": [
                    # Just a fee payer
                    {
                        "pubkey": self.address,
                        "is_signer": True,
                        "is_writable": True
                    }
                ],
                "data": json.dumps (
                    {
                        "CreateSystemAccount": {
                            "pubkey": pubkey
                        }
                    }
                ).replace(" ", "")
            }
        }
        a = json.dumps(message).replace(" ", "")

        sig = list(self.sk.sign_deterministic(a.encode(), sigencode=ecdsa.util.sigencode_der_canonize, hashfunc=hashlib.sha256))

        tx = {
            "signatures": [
                sig
            ],
            "message": message
        }


        ser_sig = base58.b58encode(bytes(sig)).decode()

        return (tx, ser_sig)

    def login_by_sk(self):
        sk_pem = self.root.ids.sk_text.text

        f = open(home_path, "w")
        f.write(sk_pem)
        f.close()
        
        self.sk = ecdsa.SigningKey.from_pem(sk_pem, hashfunc=hashlib.sha256)
        self.address = base58.b58encode(self.sk.verifying_key.to_string("compressed")).decode()
        self.screen("main_screen")
        self.refresh_balance()

    def logout(self):
        os.remove(home_path)
        self.address = None
        self.sk = None
        self.root.ids.sk_text.text = ""
        self.screen("login")

    def send(self):
        self.dialog_close(self.dialog_send)
        to = self.dialog_send.content_cls.ids.to.text
        amount = float(self.dialog_send.content_cls.ids.amount.text)

        self.create_receiver_account()

        tx, sig = self.send_logic(amount, to)
        res = requests.post(f"{node}/add_tx", json=tx)

        if res.status_code != 200:
            toast("RPC отклонил транзакцию")

    def create_receiver_account(self):
        print("Create receiver account")
        pubkey = self.dialog_send.content_cls.ids.to.text

        if json.loads(requests.get(f"{node}/account/{pubkey}").text): print("Account already exists!") ; return

        tx, sig = self.create_system_account_logic(pubkey)

        res = requests.post(f"{node}/add_tx", json=tx)

        if res.status_code != 200:
            toast("RPC отклонил транзакцию")

        print("End create receiver account")


    def wait_for(self, sig):
        while True:
            res = requests.get(f"{node}/is_spent/{sig}").text

            print(f"Got response: {res}")

            if json.loads(res):
                break
            else:
                time.sleep(500)
                continue
        
        toast("Готово!")
        self.refresh_balance()



# def der_thing():
#     for i in range(5):
#         sk = ecdsa.SigningKey.generate()
#         vk: ecdsa.VerifyingKey = sk.verifying_key
#         der = base58.b58encode(vk.to_string("compressed")).decode()
#         pem = base58.b58encode(vk.from_pem("compressed")).decode()


#         print(der)

# der_thing()


Wallet().run()

