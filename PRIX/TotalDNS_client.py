import sys
import subprocess
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QListWidget, QLineEdit, QCheckBox, QListWidgetItem
from PyQt5.QtCore import Qt

class DNSApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DNS Alkalmazás")
        self.setGeometry(100, 100, 600, 400)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.dns_list_label = QLabel("Elérhető DNS-ek:")
        self.layout.addWidget(self.dns_list_label)

        self.dns_list = QListWidget()
        self.layout.addWidget(self.dns_list)

        self.add_dns_layout = QHBoxLayout()
        self.dns_input = QLineEdit()
        self.dns_input.setPlaceholderText("Add meg a DNS címet (pl. 8.8.8.8)")
        self.dns_provider_input = QLineEdit()
        self.dns_provider_input.setPlaceholderText("Add meg a szolgáltató nevét (pl. Google)")
        self.add_dns_button = QPushButton("DNS hozzáadása")
        self.add_dns_button.clicked.connect(self.add_dns)
        self.add_dns_layout.addWidget(self.dns_input)
        self.add_dns_layout.addWidget(self.dns_provider_input)
        self.add_dns_layout.addWidget(self.add_dns_button)

        self.layout.addLayout(self.add_dns_layout)

        self.custom_dns_checkbox = QCheckBox("Egyéni DNS használata")
        self.layout.addWidget(self.custom_dns_checkbox)

        self.status_label = QLabel("Nincs csatlakoztatva")
        self.layout.addWidget(self.status_label)

        self.add_connect_buttons()

        self.load_dns()

        self.apply_dark_mode()

    def load_dns(self):
        self.dns_list.clear()
        dns_servers = self.load_dns_from_xml()
        if not dns_servers:
            dns_servers = [
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
            self.save_dns_to_xml(dns_servers)  

        for dns in dns_servers:
            item = QListWidgetItem(f"{dns['provider']} - {dns['dns']}")
            item.setData(Qt.UserRole, dns['dns'])
            self.dns_list.addItem(item)

    def add_dns(self):
        dns = self.dns_input.text()
        provider = self.dns_provider_input.text()
        
        for index in range(self.dns_list.count()):
            item = self.dns_list.item(index)
            if item.data(Qt.UserRole) == dns:
                self.status_label.setText("A megadott DNS már szerepel a listában.")
                self.status_label.setStyleSheet("color: red;")
                return
        
        if dns and provider:
            item = QListWidgetItem(f"{provider} - {dns}")
            item.setData(Qt.UserRole, dns)
            self.dns_list.addItem(item)
            self.dns_input.clear()
            self.dns_provider_input.clear()
            self.save_dns_to_xml(self.get_dns_list())  # Mentjük az új DNS beállításokat

    def save_dns_to_xml(self, dns_servers):
        root = ET.Element("dns_servers")
        for dns in dns_servers:
            dns_element = ET.SubElement(root, "dns")
            ET.SubElement(dns_element, "provider").text = dns['provider']
            ET.SubElement(dns_element, "address").text = dns['dns']
        tree = ET.ElementTree(root)
        tree.write("dns_servers.xml")

    def load_dns_from_xml(self):
        try:
            tree = ET.parse("dns_servers.xml")
            root = tree.getroot()
            dns_servers = []
            for dns_element in root.findall("dns"):
                provider = dns_element.find("provider").text
                address = dns_element.find("address").text
                dns_servers.append({"dns": address, "provider": provider})
            return dns_servers
        except FileNotFoundError:
            return None

    def apply_dark_mode(self):
        dark_stylesheet = """
        QMainWindow {
            background-color: #2E2E2E;
        }
        QLabel, QPushButton, QLineEdit, QListWidget, QCheckBox {
            color: #FFFFFF;
            background-color: #2E2E2E;
        }
        QPushButton {
            background-color: #444444;
            border: 1px solid #555555;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #555555;
        }
        QLineEdit, QListWidget, QCheckBox {
            border: 1px solid #555555;
        }
        """
        self.setStyleSheet(dark_stylesheet)

    def get_active_interface(self):
        try:
            output = subprocess.check_output("netsh interface show interface", shell=True, text=True)
            lines = output.splitlines()
            for line in lines:
                if "Connected" in line:
                    return line.split()[-1]
            return None
        except subprocess.CalledProcessError as e:
            print(f"Nem sikerült lekérdezni az aktív interfészt: {e}")
            return None

    def set_dns(self, dns):
        try:
            interface = self.get_active_interface()
            if not interface:
                self.status_label.setText("Nem található aktív interfész")
                self.status_label.setStyleSheet("color: red;")
                return
            subprocess.check_call(f"powershell -Command \"Start-Process cmd -ArgumentList '/c netsh interface ip set dns name=\"{interface}\" source=\"static\" address=\"{dns}\"' -Verb runAs\"", shell=True)
            subprocess.check_call(f"powershell -Command \"Start-Process cmd -ArgumentList '/c netsh interface ip add dns name=\"{interface}\" addr=\"{dns}\" index=2' -Verb runAs\"", shell=True)
            self.status_label.setText(f"DNS beállítva: {dns}")
            self.status_label.setStyleSheet("color: green;")
            print(f"DNS beállítva: {dns}")
        except subprocess.CalledProcessError as e:
            self.status_label.setText("DNS beállítás sikertelen")
            self.status_label.setStyleSheet("color: red;")
            print(f"DNS beállítás sikertelen: {e}")

    def reset_dns(self):
        try:
            interface = self.get_active_interface()
            if not interface:
                self.status_label.setText("Nem található aktív interfész")
                self.status_label.setStyleSheet("color: red;")
                return
            subprocess.check_call(f"powershell -Command \"Start-Process cmd -ArgumentList '/c netsh interface ip set dns name=\"{interface}\" source=dhcp' -Verb runAs\"", shell=True)
            self.status_label.setText("DNS visszaállítva automatikusra")
            self.status_label.setStyleSheet("color: green;")
            print("DNS visszaállítva automatikusra")
        except subprocess.CalledProcessError as e:
            self.status_label.setText("DNS visszaállítás sikertelen")
            self.status_label.setStyleSheet("color: red;")
            print(f"DNS visszaállítás sikertelen: {e}")

    def connect_dns(self):
        selected_dns_item = self.dns_list.currentItem()
        if selected_dns_item:
            selected_dns = selected_dns_item.data(Qt.UserRole)
            self.set_dns(selected_dns)
        else:
            self.status_label.setText("Nincs kiválasztott DNS.")
            self.status_label.setStyleSheet("color: red;")
            print("Nincs kiválasztott DNS.")

    def add_connect_buttons(self):
        self.connect_button = QPushButton("Kapcsolódás")
        self.connect_button.clicked.connect(self.connect_dns)
        self.layout.addWidget(self.connect_button)

        self.disconnect_button = QPushButton("Szétkapcsolás")
        self.disconnect_button.clicked.connect(self.reset_dns)
        self.layout.addWidget(self.disconnect_button)

    def get_dns_list(self):
        dns_list = []
        for index in range(self.dns_list.count()):
            item = self.dns_list.item(index)
            dns = item.data(Qt.UserRole)
            provider = item.text().split(' - ')[0]
            dns_list.append({"dns": dns, "provider": provider})
        return dns_list

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DNSApp()
    window.show()
    sys.exit(app.exec_())
