# ============================================================
# NEXUS ADMIN - Team App
# Only for Admins: Verify, Ban, Recover, Broadcast
# ============================================================

import os
import json
import requests
from datetime import datetime

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock

Window.clearcolor = (0.06, 0.06, 0.1, 1)


# ============================================================
# CONFIG
# ============================================================
FIREBASE_API_KEY = "AIzaSyAJDEalq7on3_gL7PF6JTIPKI71anS-iqY"
FIREBASE_PROJECT_ID = "nexus-78881"


# ============================================================
# FIREBASE AUTH (Admin)
# ============================================================
class AdminAuth:
    BASE_URL = "https://identitytoolkit.googleapis.com/v1"

    def __init__(self, api_key):
        self.api_key = api_key
        self.session_file = os.path.join(os.getcwd(), "nexus_admin_session.json")
        self.current_user = None

    def login(self, email, password):
        try:
            url = f"{self.BASE_URL}/accounts:signInWithPassword?key={self.api_key}"
            r = requests.post(url, json={
                "email": email, "password": password, "returnSecureToken": True
            }, timeout=15)
            res = r.json()
            if r.status_code == 200:
                user = {
                    "email": res["email"],
                    "localId": res["localId"],
                    "idToken": res["idToken"],
                }
                self.current_user = user
                return True, "Login OK", user
            error = res.get("error", {}).get("message", "Unknown")
            return False, error, None
        except Exception as e:
            return False, f"Error: {e}", None

    def save_session(self, user):
        try:
            with open(self.session_file, "w") as f:
                json.dump(user, f)
            return True
        except:
            return False

    def load_session(self):
        try:
            if not os.path.exists(self.session_file):
                return None
            with open(self.session_file, "r") as f:
                user = json.load(f)
            self.current_user = user
            return user
        except:
            return None

    def clear_session(self):
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            self.current_user = None
        except:
            pass


# ============================================================
# FIRESTORE ADMIN API
# ============================================================
class AdminDB:
    def __init__(self, project_id, id_token=None):
        self.project_id = project_id
        self.base_url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents"
        self.id_token = id_token

    def set_token(self, token):
        self.id_token = token

    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self.id_token:
            h["Authorization"] = f"Bearer {self.id_token}"
        return h

    def _to_fs(self, data):
        r = {}
        for k, v in data.items():
            if isinstance(v, str):
                r[k] = {"stringValue": v}
            elif isinstance(v, bool):
                r[k] = {"booleanValue": v}
            elif isinstance(v, int):
                r[k] = {"integerValue": str(v)}
            else:
                r[k] = {"stringValue": str(v)}
        return {"fields": r}

    def _from_fs(self, doc):
        if "fields" not in doc:
            return {}
        r = {}
        for k, v in doc["fields"].items():
            if "stringValue" in v:
                r[k] = v["stringValue"]
            elif "integerValue" in v:
                r[k] = int(v["integerValue"])
            elif "booleanValue" in v:
                r[k] = v["booleanValue"]
        if "name" in doc:
            r["_id"] = doc["name"].split("/")[-1]
        return r

    # ----- ADMIN CHECK -----
    def is_admin(self, uid):
        try:
            url = f"{self.base_url}/admins/{uid}"
            r = requests.get(url, headers=self._headers(), timeout=10)
            return r.status_code == 200
        except:
            return False

    # ----- USERS -----
    def list_users(self):
        try:
            url = f"{self.base_url}/users"
            r = requests.get(url, headers=self._headers(), timeout=15)
            if r.status_code == 200:
                docs = r.json().get("documents", [])
                return [self._from_fs(d) for d in docs]
            return []
        except:
            return []

    def update_user(self, uid, data):
        try:
            url = f"{self.base_url}/users/{uid}"
            r = requests.patch(url, json=self._to_fs(data),
                             headers=self._headers(), timeout=15)
            return r.status_code in (200, 201)
        except:
            return False

    # ----- BAN -----
    def ban_user(self, uid, reason="Violation"):
        try:
            url = f"{self.base_url}/banned/{uid}"
            data = {
                "uid": uid,
                "reason": reason,
                "banned_at": datetime.now().isoformat(),
            }
            r = requests.patch(url, json=self._to_fs(data),
                             headers=self._headers(), timeout=15)
            return r.status_code in (200, 201)
        except:
            return False

    def unban_user(self, uid):
        try:
            url = f"{self.base_url}/banned/{uid}"
            r = requests.delete(url, headers=self._headers(), timeout=15)
            return r.status_code == 200
        except:
            return False

    def list_banned(self):
        try:
            url = f"{self.base_url}/banned"
            r = requests.get(url, headers=self._headers(), timeout=15)
            if r.status_code == 200:
                docs = r.json().get("documents", [])
                return [self._from_fs(d) for d in docs]
            return []
        except:
            return []

    # ----- REPORTS -----
    def list_reports(self):
        try:
            url = f"{self.base_url}/reports"
            r = requests.get(url, headers=self._headers(), timeout=15)
            if r.status_code == 200:
                docs = r.json().get("documents", [])
                return [self._from_fs(d) for d in docs]
            return []
        except:
            return []

    # ----- BROADCAST -----
    def broadcast(self, title, message):
        try:
            url = f"{self.base_url}/broadcasts"
            data = {
                "title": title,
                "message": message,
                "sent_at": datetime.now().isoformat(),
            }
            r = requests.post(url, json=self._to_fs(data),
                            headers=self._headers(), timeout=15)
            return r.status_code in (200, 201)
        except:
            return False


# ============================================================
# UI
# ============================================================
KV = '''
MDScreenManager:
    id: sm

    MDScreen:
        name: "login"
        md_bg_color: 0.06, 0.06, 0.1, 1
        MDBoxLayout:
            orientation: "vertical"
            padding: "20dp"
            Widget:
            MDLabel:
                text: "NEXUS"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 1, 0.3, 0.4, 1
                font_style: "H2"
                bold: True
                size_hint_y: None
                height: "60dp"
            MDLabel:
                text: "ADMIN PANEL"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.63, 0.63, 0.69, 1
                size_hint_y: None
                height: "25dp"
            Widget:
                size_hint_y: None
                height: "40dp"
            MDTextField:
                id: login_email
                hint_text: "Admin Email"
                mode: "rectangle"
                icon_right: "email"
                size_hint_x: None
                width: "300dp"
                pos_hint: {"center_x": 0.5}
            Widget:
                size_hint_y: None
                height: "10dp"
            MDTextField:
                id: login_password
                hint_text: "Password"
                mode: "rectangle"
                password: True
                icon_right: "eye-off"
                size_hint_x: None
                width: "300dp"
                pos_hint: {"center_x": 0.5}
            Widget:
                size_hint_y: None
                height: "15dp"
            MDLabel:
                id: login_status
                text: ""
                halign: "center"
                theme_text_color: "Custom"
                text_color: 1, 0.4, 0.4, 1
                size_hint_y: None
                height: "40dp"
            MDRaisedButton:
                text: "ADMIN LOGIN"
                size_hint_x: None
                width: "300dp"
                height: "50dp"
                pos_hint: {"center_x": 0.5}
                md_bg_color: 1, 0.3, 0.4, 1
                on_release: app.admin_login()
            Widget:

    MDScreen:
        name: "dashboard"
        md_bg_color: 0.06, 0.06, 0.1, 1
        MDBottomNavigation:
            panel_color: 0.12, 0.12, 0.18, 1
            text_color_active: 1, 0.3, 0.4, 1

            MDBottomNavigationItem:
                name: "tab_users"
                text: "Users"
                icon: "account-multiple"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "Users"
                        md_bg_color: 0.12, 0.12, 0.18, 1
                        specific_text_color: 1, 0.3, 0.4, 1
                        right_action_items: [["refresh", lambda x: app.load_users()], ["logout", lambda x: app.admin_logout()]]
                    ScrollView:
                        MDBoxLayout:
                            id: users_list
                            orientation: "vertical"
                            padding: "10dp"
                            spacing: "8dp"
                            size_hint_y: None
                            height: self.minimum_height

            MDBottomNavigationItem:
                name: "tab_banned"
                text: "Banned"
                icon: "cancel"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "Banned Users"
                        md_bg_color: 0.12, 0.12, 0.18, 1
                        specific_text_color: 1, 0.3, 0.4, 1
                        right_action_items: [["refresh", lambda x: app.load_banned()]]
                    ScrollView:
                        MDBoxLayout:
                            id: banned_list
                            orientation: "vertical"
                            padding: "10dp"
                            spacing: "8dp"
                            size_hint_y: None
                            height: self.minimum_height

            MDBottomNavigationItem:
                name: "tab_reports"
                text: "Reports"
                icon: "alert"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "Reports"
                        md_bg_color: 0.12, 0.12, 0.18, 1
                        specific_text_color: 1, 0.3, 0.4, 1
                        right_action_items: [["refresh", lambda x: app.load_reports()]]
                    ScrollView:
                        MDBoxLayout:
                            id: reports_list
                            orientation: "vertical"
                            padding: "10dp"
                            spacing: "8dp"
                            size_hint_y: None
                            height: self.minimum_height

            MDBottomNavigationItem:
                name: "tab_broadcast"
                text: "Broadcast"
                icon: "bullhorn"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "Broadcast"
                        md_bg_color: 0.12, 0.12, 0.18, 1
                        specific_text_color: 1, 0.3, 0.4, 1
                    MDBoxLayout:
                        orientation: "vertical"
                        padding: "20dp"
                        spacing: "15dp"
                        MDTextField:
                            id: bc_title
                            hint_text: "Title"
                            mode: "rectangle"
                        MDTextField:
                            id: bc_message
                            hint_text: "Message"
                            mode: "rectangle"
                            multiline: True
                            size_hint_y: None
                            height: "120dp"
                        MDRaisedButton:
                            text: "SEND TO ALL"
                            size_hint_x: None
                            width: "300dp"
                            pos_hint: {"center_x": 0.5}
                            md_bg_color: 1, 0.3, 0.4, 1
                            on_release: app.send_broadcast()
                        MDLabel:
                            id: bc_status
                            text: ""
                            halign: "center"
                            theme_text_color: "Custom"
                            text_color: 0.2, 0.9, 0.4, 1
                            size_hint_y: None
                            height: "30dp"
                        Widget:
'''


# ============================================================
# APP
# ============================================================
class NexusAdminApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Red"

        print(f"Admin App - {FIREBASE_PROJECT_ID}")
        self.auth = AdminAuth(FIREBASE_API_KEY)
        self.db = AdminDB(FIREBASE_PROJECT_ID)
        self.current_user = None

        return Builder.load_string(KV)

    def on_start(self):
        Clock.schedule_once(lambda dt: self.check_auto_login(), 0.5)

    # ---------- AUTO LOGIN ----------
    def check_auto_login(self):
        user = self.auth.load_session()
        if user:
            self.db.set_token(user["idToken"])
            if self.db.is_admin(user["localId"]):
                self.current_user = user
                self.root.current = "dashboard"
                print(f"Admin auto-login: {user['email']}")
                Clock.schedule_once(lambda dt: self.load_users(), 0.5)
                Clock.schedule_once(lambda dt: self.load_banned(), 0.7)
                Clock.schedule_once(lambda dt: self.load_reports(), 0.9)
            else:
                self.auth.clear_session()
                self.root.current = "login"
                self.set_status("login_status", "You are not Admin")
        else:
            self.root.current = "login"

    # ---------- LOGIN ----------
    def admin_login(self):
        email = self.root.ids.login_email.text.strip()
        password = self.root.ids.login_password.text

        if not email or not password:
            self.set_status("login_status", "Email & Password din")
            return

        self.set_status("login_status", "Checking...",
                       color=(1, 0.3, 0.4, 1))

        ok, msg, user = self.auth.login(email, password)
        if not ok:
            self.set_status("login_status", msg)
            return

        self.db.set_token(user["idToken"])

        if not self.db.is_admin(user["localId"]):
            self.set_status("login_status", "You are not Admin")
            return

        self.current_user = user
        self.auth.save_session(user)
        self.root.current = "dashboard"
        self.root.ids.login_email.text = ""
        self.root.ids.login_password.text = ""
        self.root.ids.login_status.text = ""

        print(f"Admin logged in: {email}")
        Clock.schedule_once(lambda dt: self.load_users(), 0.3)
        Clock.schedule_once(lambda dt: self.load_banned(), 0.5)
        Clock.schedule_once(lambda dt: self.load_reports(), 0.7)

  # ---------- USERS ----------
    def load_users(self):
        try:
            container = self.root.ids.users_list
            container.clear_widgets()
            users = self.db.list_users()
            print(f"Users: {len(users)}")

            if not users:
                container.add_widget(MDLabel(
                    text="No users",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=(0.63, 0.63, 0.69, 1),
                    size_hint_y=None, height=dp(80),
                ))
                return

            for u in users:
                uid = u.get("_id", "")
                name = u.get("name", "?")
                email = u.get("email", "?")
                verified = u.get("verified", False)

                card = MDCard(
                    size_hint_y=None, height=dp(150),
                    radius=[dp(12)],
                    md_bg_color=(0.12, 0.12, 0.18, 1),
                    padding=dp(12),
                )
                col = MDBoxLayout(orientation="vertical", spacing=dp(4))

                top = MDBoxLayout(size_hint_y=None, height=dp(26), spacing=dp(5))
                top.add_widget(MDLabel(
                    text=name,
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                    bold=True,
                    size_hint_y=None, height=dp(24),
                ))
                if verified:
                    top.add_widget(MDIconButton(
                        icon="check-decagram",
                        theme_text_color="Custom",
                        text_color=(0.3, 0.6, 1, 1),
                        icon_size="18dp",
                        size_hint_x=None, width=dp(30),
                    ))
                col.add_widget(top)

                col.add_widget(MDLabel(
                    text=email,
                    theme_text_color="Custom",
                    text_color=(0.63, 0.63, 0.69, 1),
                    font_style="Caption",
                    size_hint_y=None, height=dp(20),
                ))

                btns = MDBoxLayout(size_hint_y=None, height=dp(45), spacing=dp(4))

                verify_text = "UNVERIFY" if verified else "VERIFY"
                verify_color = (0.63, 0.63, 0.69, 1) if verified else (0.3, 0.8, 0.4, 1)

                btns.add_widget(MDRaisedButton(
                    text=verify_text,
                    size_hint_x=0.33,
                    md_bg_color=verify_color,
                    on_release=lambda x, u=uid, v=not verified: self.toggle_verify(u, v),
                ))
                btns.add_widget(MDRaisedButton(
                    text="BAN",
                    size_hint_x=0.33,
                    md_bg_color=(0.9, 0.3, 0.3, 1),
                    on_release=lambda x, u=uid: self.ban_user(u),
                ))
                btns.add_widget(MDRaisedButton(
                    text="RECOVER",
                    size_hint_x=0.33,
                    md_bg_color=(0.3, 0.6, 0.9, 1),
                    on_release=lambda x, u=uid: self.unban_user(u),
                ))

                col.add_widget(btns)
                card.add_widget(col)
                container.add_widget(card)
        except Exception as e:
            print(f"LOAD USERS ERROR: {e}")

    def toggle_verify(self, uid, value):
        ok = self.db.update_user(uid, {"verified": value})
        if ok:
            print(f"Verified {uid}: {value}")
            self.load_users()

    def ban_user(self, uid):
        ok = self.db.ban_user(uid, "Admin action")
        if ok:
            print(f"Banned: {uid}")
            self.load_banned()
            self.load_users()

    def unban_user(self, uid):
        ok = self.db.unban_user(uid)
        if ok:
            print(f"Unbanned: {uid}")
            self.load_banned()
            self.load_users()
                # ---------- BANNED ----------
    def load_banned(self):
        try:
            container = self.root.ids.banned_list
            container.clear_widgets()
            banned = self.db.list_banned()
            print(f"Banned: {len(banned)}")

            if not banned:
                container.add_widget(MDLabel(
                    text="No banned users",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=(0.63, 0.63, 0.69, 1),
                    size_hint_y=None, height=dp(80),
                ))
                return

            for b in banned:
                uid = b.get("_id", "")
                reason = b.get("reason", "N/A")
                card = MDCard(
                    size_hint_y=None, height=dp(110),
                    radius=[dp(12)],
                    md_bg_color=(0.15, 0.08, 0.08, 1),
                    padding=dp(12),
                )
                col = MDBoxLayout(orientation="vertical", spacing=dp(5))
                col.add_widget(MDLabel(
                    text=f"UID: {uid[:16]}...",
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                    bold=True,
                    size_hint_y=None, height=dp(24),
                ))
                col.add_widget(MDLabel(
                    text=f"Reason: {reason}",
                    theme_text_color="Custom",
                    text_color=(0.9, 0.6, 0.6, 1),
                    font_style="Caption",
                    size_hint_y=None, height=dp(20),
                ))
                col.add_widget(MDRaisedButton(
                    text="RECOVER",
                    size_hint_x=None, width=dp(150),
                    md_bg_color=(0.3, 0.6, 0.9, 1),
                    on_release=lambda x, u=uid: self.unban_user(u),
                ))
                card.add_widget(col)
                container.add_widget(card)
        except Exception as e:
            print(f"LOAD BANNED ERROR: {e}")

    # ---------- REPORTS ----------
    def load_reports(self):
        try:
            container = self.root.ids.reports_list
            container.clear_widgets()
            reports = self.db.list_reports()
            print(f"Reports: {len(reports)}")

            if not reports:
                container.add_widget(MDLabel(
                    text="No reports",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=(0.63, 0.63, 0.69, 1),
                    size_hint_y=None, height=dp(80),
                ))
                return

            for r in reports:
                card = MDCard(
                    size_hint_y=None, height=dp(100),
                    radius=[dp(12)],
                    md_bg_color=(0.15, 0.12, 0.08, 1),
                    padding=dp(12),
                )
                col = MDBoxLayout(orientation="vertical", spacing=dp(5))
                col.add_widget(MDLabel(
                    text=f"Post: {r.get('post_id', '?')[:16]}",
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                    bold=True,
                    size_hint_y=None, height=dp(24),
                ))
                col.add_widget(MDLabel(
                    text=f"Reason: {r.get('reason', 'N/A')}",
                    theme_text_color="Custom",
                    text_color=(1, 0.8, 0.6, 1),
                    font_style="Caption",
                    size_hint_y=None, height=dp(20),
                ))
                card.add_widget(col)
                container.add_widget(card)
        except Exception as e:
            print(f"LOAD REPORTS ERROR: {e}")

    # ---------- BROADCAST ----------
    def send_broadcast(self):
        try:
            title = self.root.ids.bc_title.text.strip()
            msg = self.root.ids.bc_message.text.strip()
            if not title or not msg:
                self.root.ids.bc_status.text = "Title & Message din"
                return
            ok = self.db.broadcast(title, msg)
            if ok:
                self.root.ids.bc_status.text = "Sent to all!"
                self.root.ids.bc_status.text_color = (0.2, 0.9, 0.4, 1)
                self.root.ids.bc_title.text = ""
                self.root.ids.bc_message.text = ""
                print(f"Broadcast: {title}")
            else:
                self.root.ids.bc_status.text = "Failed"
        except Exception as e:
            print(f"BROADCAST ERROR: {e}")

    # ---------- LOGOUT ----------
    def admin_logout(self):
        self.auth.clear_session()
        self.current_user = None
        self.root.current = "login"
        print("Admin logged out")

    # ---------- HELPER ----------
    def set_status(self, label_id, text, color=(1, 0.4, 0.4, 1)):
        try:
            lbl = self.root.ids[label_id]
            lbl.text = text
            lbl.text_color = color
        except:
            pass


if __name__ == "__main__":
    NexusAdminApp().run()