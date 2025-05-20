import sys
import subprocess
import xml.etree.ElementTree as ET
import requests
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QListWidget, QLineEdit,
    QCheckBox, QListWidgetItem, QSpacerItem, QSizePolicy, QSpinBox, QDialog, QMessageBox, QFileDialog, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon

APP_VERSION = "2.0"
XML_PATH = "dns_servers.xml"

GLASS_STYLE = """
QMainWindow, QWidget {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #232946, stop:1 #191724);
    font-family: 'Segoe UI', 'Arial', sans-serif;
    color: #fff;
}
QFrame#GlassFrame {
    background: rgba(44, 62, 80, 0.5);
    border-radius: 25px;
    border: 1.2px solid rgba(255,255,255,0.18);
    box-shadow: 0 8px 32px 0 rgba(31,38,135,0.19);
}
QLabel, QCheckBox {
    color: #fff;
    font-size: 16px;
}
QLineEdit, QSpinBox {
    background: rgba(60, 68, 89, 0.33);
    color: #fff;
    border-radius: 12px;
    padding: 8px;
    border: 1.2px solid #424257;
    font-size: 15px;
}
QPushButton {
    background-color: #3A86FF;
    color: #fff;
    border-radius: 12px;
    font-size: 15px;
    padding: 8px 20px;
    border: none;
    margin: 4px;
    font-weight: 500;
    transition: 0.2s;
}
QPushButton:hover {
    background-color: #5271FF;
}
QListWidget {
    background: rgba(60, 68, 89, 0.38);
    border-radius: 14px;
    color: #fff;
    font-size: 15px;
    border: none;
    padding: 6px;
}
QStatusBar {
    background: rgba(44, 62, 80, 0.5);
    color: #e6e6e6;
    font-size: 14px;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}
"""

class AddEditDNSDialog(QDialog):
    def __init__(self, parent=None, edit_item=None):
        super().__init__(parent)
        self.setWindowTitle("DNS szerver hozzáadása/szerkesztése")
        self.setFixedSize(370, 160)
        self.layout = QVBoxLayout(self)

        self.input_dns = QLineEdit(self)
        self.input_dns.setPlaceholderText("DNS cím (pl. 8.8.8.8)")
        self.input_provider = QLineEdit(self)
        self.input_provider.setPlaceholderText("Szolgáltató (pl. Google)")

        if edit_item:
            self.input_provider.setText(edit_item.text().split(' - ')[0])
            self.input_dns.setText(edit_item.data(Qt.UserRole))

        self.btn_ok = QPushButton("Mentés", self)
        self.btn_cancel = QPushButton("Mégsem", self)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self.accept)

        row = QHBoxLayout()
        row.addWidget(self.btn_ok)
        row.addWidget(self.btn_cancel)

        self.layout.addWidget(QLabel("DNS szerver adatai:"))
        self.layout.addWidget(self.input_provider)
        self.layout.addWidget(self.input_dns)
        self.layout.addLayout(row)

    def get_data(self):
        return self.input_provider.text().strip(), self.input_dns.text().strip()

class DNSApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TotalDNS - Modern Glass DNS Client")
        self.setGeometry(100, 100, 1050, 600)
        self.setWindowIcon(QIcon(":/icons/glass_icon.png"))

        central = QWidget()
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(18)
        main_layout.setContentsMargins(26, 16, 26, 16)
        self.setCentralWidget(central)

        self.left_frame = QFrame()
        self.left_frame.setObjectName("GlassFrame")
        self.left_layout = QVBoxLayout(self.left_frame)
        self.left_layout.setContentsMargins(26, 22, 26, 22)
        self.left_layout.setSpacing(14)

        self.label_dnslist = QLabel("DNS szerverek")
        self.label_dnslist.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.left_layout.addWidget(self.label_dnslist)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Keresés DNS vagy szolgáltató...")
        self.search_input.textChanged.connect(self.filter_dns_list)
        self.left_layout.addWidget(self.search_input)

        self.dns_list = QListWidget()
        self.dns_list.setSelectionMode(QListWidget.SingleSelection)
        self.left_layout.addWidget(self.dns_list)

        # Akciók
        row = QHBoxLayout()
        btn_add = QPushButton("Hozzáadás")
        btn_add.clicked.connect(self.add_dns_dialog)
        btn_edit = QPushButton("Szerkesztés")
        btn_edit.clicked.connect(self.edit_dns_dialog)
        btn_del = QPushButton("Törlés")
        btn_del.clicked.connect(self.remove_dns)
        row.addWidget(btn_add)
        row.addWidget(btn_edit)
        row.addWidget(btn_del)
        self.left_layout.addLayout(row)

        # Export/Import
        exp_row = QHBoxLayout()
        btn_export = QPushButton("Exportálás")
        btn_export.clicked.connect(self.export_dns)
        btn_import = QPushButton("Importálás")
        btn_import.clicked.connect(self.import_dns)
        exp_row.addWidget(btn_export)
        exp_row.addWidget(btn_import)
        self.left_layout.addLayout(exp_row)

        main_layout.addWidget(self.left_frame, 1)

        # JOBB: Glass funkció panel
        self.right_frame = QFrame()
        self.right_frame.setObjectName("GlassFrame")
        self.right_layout = QVBoxLayout(self.right_frame)
        self.right_layout.setContentsMargins(34, 24, 34, 24)
        self.right_layout.setSpacing(17)

        # Status & aktuális DNS
        self.status_label = QLabel("Üdvözöl a TotalDNS 2.0!")
        self.status_label.setFont(QFont("Segoe UI", 12))
        self.right_layout.addWidget(self.status_label)

        # Egyéni DNS
        custom_dns_row = QHBoxLayout()
        self.custom_dns_checkbox = QCheckBox("Egyéni DNS")
        self.custom_dns_checkbox.stateChanged.connect(self.toggle_custom_dns_input)
        self.custom_dns_input = QLineEdit()
        self.custom_dns_input.setPlaceholderText("pl. 9.9.9.9")
        self.custom_dns_input.setEnabled(False)
        custom_dns_row.addWidget(self.custom_dns_checkbox)
        custom_dns_row.addWidget(self.custom_dns_input)
        self.right_layout.addLayout(custom_dns_row)

        # Gyors akciók kártyán
        action_row = QHBoxLayout()
        btn_connect = QPushButton("Kapcsolódás")
        btn_connect.clicked.connect(self.connect_dns)
        btn_disconnect = QPushButton("DHCP visszaállítás")
        btn_disconnect.clicked.connect(self.reset_dns)
        btn_ping = QPushButton("Ping teszt")
        btn_ping.clicked.connect(self.ping_dns)
        btn_geo = QPushButton("GeoIP")
        btn_geo.clicked.connect(self.geoip_lookup)
        action_row.addWidget(btn_connect)
        action_row.addWidget(btn_disconnect)
        action_row.addWidget(btn_ping)
        action_row.addWidget(btn_geo)
        self.right_layout.addLayout(action_row)

        # Speciális tesztek
        spec_row = QHBoxLayout()
        btn_flush = QPushButton("Flush DNS")
        btn_flush.clicked.connect(self.flush_dns)
        btn_curr = QPushButton("DNS státusz")
        btn_curr.clicked.connect(self.show_current_dns)
        btn_ns = QPushButton("NSLookup")
        btn_ns.clicked.connect(self.nslookup_test)
        spec_row.addWidget(btn_flush)
        spec_row.addWidget(btn_curr)
        spec_row.addWidget(btn_ns)
        self.right_layout.addLayout(spec_row)

        # DNS váltás időzítő
        sched_row = QHBoxLayout()
        sched_row.addWidget(QLabel("DNS váltás időzítve (mp):"))
        self.sched_spin = QSpinBox()
        self.sched_spin.setRange(1, 3600)
        self.sched_spin.setValue(10)
        sched_row.addWidget(self.sched_spin)
        btn_sched = QPushButton("Időzített váltás")
        btn_sched.clicked.connect(self.schedule_dns_change)
        sched_row.addWidget(btn_sched)
        self.right_layout.addLayout(sched_row)

        # Alapértelmezett DNS gomb
        btn_default = QPushButton("Gyári DNS lista visszaállítása")
        btn_default.clicked.connect(self.reset_to_default_dns)
        self.right_layout.addWidget(btn_default)

        # App info
        info_row = QHBoxLayout()
        info_label = QLabel(f"<b>TotalDNS</b> Glass UI &nbsp;|&nbsp; <small>verzió: {APP_VERSION}</small>")
        info_row.addWidget(info_label)
        info_row.addStretch()
        btn_dark = QPushButton("Sötét/Világos")
        btn_dark.clicked.connect(self.toggle_theme)
        info_row.addWidget(btn_dark)
        self.right_layout.addLayout(info_row)

        main_layout.addWidget(self.right_frame, 2)

        # Statusbar (üzenetekhez)
        self.statusBar().showMessage("Készen áll.")

        # Sötét mód (alap)
        self.theme = "dark"
        self.setStyleSheet(GLASS_STYLE)

        # DNS lista betöltése
        self.load_dns()


    def load_dns(self):
        self.dns_list.clear()
        dns_servers = self.load_dns_from_xml()
        if not dns_servers:
            dns_servers = self.default_dns_list()
            self.save_dns_to_xml(dns_servers)
        for dns in dns_servers:
            item = QListWidgetItem(f"{dns['provider']} - {dns['dns']}")
            item.setData(Qt.UserRole, dns['dns'])
            self.dns_list.addItem(item)

    def load_dns_from_xml(self):
        try:
            tree = ET.parse(XML_PATH)
            root = tree.getroot()
            return [{"provider": d.find("provider").text, "dns": d.find("address").text} for d in root.findall("dns")]
        except Exception:
            return None

    def save_dns_to_xml(self, dns_servers):
        root = ET.Element("dns_servers")
        for dns in dns_servers:
            d = ET.SubElement(root, "dns")
            ET.SubElement(d, "provider").text = dns["provider"]
            ET.SubElement(d, "address").text = dns["dns"]
        tree = ET.ElementTree(root)
        tree.write(XML_PATH)

    def get_dns_list(self):
        return [{"provider": self.dns_list.item(i).text().split(" - ")[0], "dns": self.dns_list.item(i).data(Qt.UserRole)} for i in range(self.dns_list.count())]

    def default_dns_list(self):
        return [
            {"dns": "1.1.1.1", "provider": "Cloudflare"},
            {"dns": "1.0.0.1", "provider": "Cloudflare (Secondary)"},
            {"dns": "8.8.8.8", "provider": "Google"},
            {"dns": "8.8.4.4", "provider": "Google (Secondary)"},
            {"dns": "94.140.14.14", "provider": "AdGuard DNS"},
            {"dns": "94.140.15.15", "provider": "AdGuard DNS (Secondary)"},
            {"dns": "185.228.168.9", "provider": "CleanBrowsing"},
            {"dns": "185.228.169.9", "provider": "CleanBrowsing (Secondary)"},
            {"dns": "76.76.19.19", "provider": "Alternate DNS"},
            {"dns": "76.223.122.150", "provider": "Alternate DNS (Secondary)"},
            {"dns": "9.9.9.9", "provider": "Quad9"},
            {"dns": "149.112.112.112", "provider": "Quad9 (Secondary)"},
            {"dns": "208.76.50.50", "provider": "SmartViper"},
            {"dns": "208.76.51.51", "provider": "SmartViper (Secondary)"},
            {"dns": "104.197.28.121", "provider": "SafeSurfer"},
            {"dns": "104.155.237.225", "provider": "SafeSurfer (Secondary)"},
            {"dns": "198.54.117.10", "provider": "SafeServe"},
            {"dns": "198.54.117.11", "provider": "SafeServe (Secondary)"},
            {"dns": "91.239.100.100", "provider": "UncensoredDNS"},
            {"dns": "89.233.43.71", "provider": "UncensoredDNS (Secondary)"},
            {"dns": "77.88.8.88", "provider": "Yandex DNS"},
            {"dns": "77.88.8.2", "provider": "Yandex DNS (Secondary)"},
        ]


    def add_dns_dialog(self):
        dlg = AddEditDNSDialog(self)
        if dlg.exec_():
            provider, dns = dlg.get_data()
            if not dns or not provider:
                self.set_status("DNS cím vagy szolgáltató hiányzik!", "error")
                return
            if any(dns == item.data(Qt.UserRole) for item in [self.dns_list.item(i) for i in range(self.dns_list.count())]):
                self.set_status("Ez a DNS már létezik a listában!", "error")
                return
            item = QListWidgetItem(f"{provider} - {dns}")
            item.setData(Qt.UserRole, dns)
            self.dns_list.addItem(item)
            self.save_dns_to_xml(self.get_dns_list())
            self.set_status("DNS sikeresen hozzáadva.", "success")

    def edit_dns_dialog(self):
        current = self.dns_list.currentItem()
        if not current:
            self.set_status("Előbb válassz ki egy DNS-t a szerkesztéshez.", "warn")
            return
        dlg = AddEditDNSDialog(self, edit_item=current)
        if dlg.exec_():
            provider, dns = dlg.get_data()
            if not dns or not provider:
                self.set_status("DNS cím vagy szolgáltató hiányzik!", "error")
                return
            current.setText(f"{provider} - {dns}")
            current.setData(Qt.UserRole, dns)
            self.save_dns_to_xml(self.get_dns_list())
            self.set_status("DNS szerver frissítve.", "success")

    def remove_dns(self):
        current = self.dns_list.currentItem()
        if not current:
            self.set_status("Előbb válassz ki egy DNS-t a törléshez.", "warn")
            return
        self.dns_list.takeItem(self.dns_list.currentRow())
        self.save_dns_to_xml(self.get_dns_list())
        self.set_status("DNS törölve.", "success")

    def export_dns(self):
        path, _ = QFileDialog.getSaveFileName(self, "DNS exportálása", "dns_export.xml", "XML Files (*.xml)")
        if not path:
            return
        dns = self.get_dns_list()
        root = ET.Element("dns_servers")
        for d in dns:
            e = ET.SubElement(root, "dns")
            ET.SubElement(e, "provider").text = d["provider"]
            ET.SubElement(e, "address").text = d["dns"]
        tree = ET.ElementTree(root)
        tree.write(path)
        self.set_status(f"DNS lista exportálva: {path}", "success")

    def import_dns(self):
        path, _ = QFileDialog.getOpenFileName(self, "DNS importálása", "", "XML Files (*.xml)")
        if not path:
            return
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            dns_list = [{"provider": d.find("provider").text, "dns": d.find("address").text} for d in root.findall("dns")]
            self.save_dns_to_xml(dns_list)
            self.load_dns()
            self.set_status(f"Sikeres import: {path}", "success")
        except Exception:
            self.set_status("Nem sikerült importálni az XML-t!", "error")

    def reset_to_default_dns(self):
        self.save_dns_to_xml(self.default_dns_list())
        self.load_dns()
        self.set_status("DNS lista visszaállítva alapértelmezettre.", "info")


    def set_status(self, msg, typ="info"):
        color = {"success": "#9cffbe", "error": "#ff7b7b", "warn": "#ffe066", "info": "#e3e3e3"}.get(typ, "#e3e3e3")
        self.status_label.setText(f"<span style='color:{color};'>{msg}</span>")
        self.statusBar().showMessage(msg)


    def filter_dns_list(self, text):
        text = text.lower()
        for i in range(self.dns_list.count()):
            item = self.dns_list.item(i)
            item.setHidden(text not in item.text().lower())


    def toggle_custom_dns_input(self, state):
        self.custom_dns_input.setEnabled(state == Qt.Checked)


    def get_active_interface(self):
        try:
            output = subprocess.check_output("netsh interface show interface", shell=True, text=True)
            lines = output.splitlines()
            for line in lines:
                if "Connected" in line or "Csatlakoztatva" in line:
                    parts = line.split()
                    return parts[-1]
            return None
        except subprocess.CalledProcessError:
            return None

    def set_dns(self, dns):
        try:
            interface = self.get_active_interface()
            if not interface:
                self.set_status("Nem található aktív interfész.", "error")
                return
            set_cmd = f'netsh interface ip set dns name="{interface}" source=static address={dns}'
            add_cmd = f'netsh interface ip add dns name="{interface}" addr={dns} index=2'
            subprocess.check_call(
                f'powershell -Command "Start-Process cmd -ArgumentList \'/c {set_cmd}\' -Verb runAs"', shell=True
            )
            subprocess.check_call(
                f'powershell -Command "Start-Process cmd -ArgumentList \'/c {add_cmd}\' -Verb runAs"', shell=True
            )
            self.set_status(f"DNS beállítva: {dns}", "success")
        except subprocess.CalledProcessError as e:
            self.set_status(f"DNS beállítás sikertelen! ({e})", "error")

    def reset_dns(self):
        try:
            interface = self.get_active_interface()
            if not interface:
                self.set_status("Nem található aktív interfész.", "error")
                return
            reset_cmd = f'netsh interface ip set dns name="{interface}" source=dhcp'
            subprocess.check_call(
                f'powershell -Command "Start-Process cmd -ArgumentList \'/c {reset_cmd}\' -Verb runAs"', shell=True
            )
            self.set_status("DNS visszaállítva automatikusra (DHCP).", "success")
        except subprocess.CalledProcessError as e:
            self.set_status("DNS visszaállítás sikertelen.", "error")

    def connect_dns(self):
        if self.custom_dns_checkbox.isChecked():
            custom_dns = self.custom_dns_input.text().strip()
            if custom_dns:
                self.set_dns(custom_dns)
            else:
                self.set_status("Nincs megadva egyéni DNS.", "error")
        else:
            selected = self.dns_list.currentItem()
            if selected:
                self.set_dns(selected.data(Qt.UserRole))
            else:
                self.set_status("Nincs kiválasztott DNS.", "error")

    def ping_dns(self):
        dns = self.custom_dns_input.text().strip() if self.custom_dns_checkbox.isChecked() else (
            self.dns_list.currentItem().data(Qt.UserRole) if self.dns_list.currentItem() else None)
        if not dns:
            self.set_status("Nincs DNS a pingeléshez.", "error")
            return
        try:
            output = subprocess.check_output(f'ping {dns}', shell=True, text=True)
            if "Reply from" in output or "Válasz" in output:
                self.set_status(f"Sikeres ping: {dns}", "success")
            else:
                self.set_status(f"Sikertelen ping: {dns}", "error")
        except subprocess.CalledProcessError:
            self.set_status(f"Sikertelen ping: {dns}", "error")

    def flush_dns(self):
        try:
            subprocess.check_output('ipconfig /flushdns', shell=True, text=True)
            self.set_status("DNS gyorsítótár törölve.", "success")
        except subprocess.CalledProcessError:
            self.set_status("Flush DNS sikertelen.", "error")

    def show_current_dns(self):
        try:
            interface = self.get_active_interface()
            if not interface:
                self.set_status("Nincs aktív interfész.", "error")
                return
            cmd = f'netsh interface ip show config name="{interface}"'
            output = subprocess.check_output(cmd, shell=True, text=True)
            dns_info = []
            for line in output.splitlines():
                if "." in line and "Subnet" not in line and ":" not in line:
                    dns_info.append(line.strip())
            if dns_info:
                self.set_status(f"Jelenlegi DNS: {', '.join(dns_info)}", "success")
            else:
                self.set_status("Nem találtam DNS-t vagy automatikus a DNS.", "warn")
        except subprocess.CalledProcessError:
            self.set_status("Nem sikerült lekérdezni az aktuális DNS-t.", "error")

    def nslookup_test(self):
        domain = "google.com"
        try:
            output = subprocess.check_output(f'nslookup {domain}', shell=True, text=True)
            if "Name:" in output or "Name" in output:
                self.set_status(f"NSLookup sikeres: {domain}", "success")
            else:
                self.set_status(f"NSLookup sikertelen: {domain}", "error")
        except subprocess.CalledProcessError:
            self.set_status(f"NSLookup sikertelen: {domain}", "error")

    def geoip_lookup(self):
        dns = self.custom_dns_input.text().strip() if self.custom_dns_checkbox.isChecked() else (
            self.dns_list.currentItem().data(Qt.UserRole) if self.dns_list.currentItem() else None)
        if not dns:
            self.set_status("Nincs DNS a GeoIP lekérdezéshez.", "error")
            return
        try:
            url = f"http://ip-api.com/json/{dns}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if data["status"] == "success":
                country = data.get("country", "N/A")
                city = data.get("city", "N/A")
                isp = data.get("isp", "N/A")
                self.set_status(f"GeoIP: {dns} → {country}, {city}, ISP: {isp}", "success")
            else:
                self.set_status(f"GeoIP sikertelen: {data.get('message', 'ismeretlen hiba')}", "error")
        except Exception as e:
            self.set_status(f"GeoIP hiba: {e}", "error")

    def schedule_dns_change(self):
        delay = self.sched_spin.value()
        QTimer.singleShot(delay * 1000, self._do_scheduled_dns)
        self.set_status(f"DNS váltás beütemezve {delay} mp múlva.", "warn")

    def _do_scheduled_dns(self):
        if self.custom_dns_checkbox.isChecked():
            custom_dns = self.custom_dns_input.text().strip()
            if custom_dns:
                self.set_dns(custom_dns)
            else:
                self.set_status("Ütemezett váltás: nincs egyéni DNS!", "error")
        else:
            selected = self.dns_list.currentItem()
            if selected:
                self.set_dns(selected.data(Qt.UserRole))
            else:
                self.set_status("Ütemezett váltás: nincs kiválasztott DNS!", "error")

    # ---- Light/dark mód kapcsoló ----

    def toggle_theme(self):
        if self.theme == "dark":
            light_style = GLASS_STYLE.replace("#232946", "#e8eaef").replace("#191724", "#f5f7fb").replace("color: #fff;", "color: #222;")
            self.setStyleSheet(light_style)
            self.theme = "light"
        else:
            self.setStyleSheet(GLASS_STYLE)
            self.theme = "dark"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DNSApp()
    window.show()
    sys.exit(app.exec_())
