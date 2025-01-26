import sys
import subprocess
import xml.etree.ElementTree as ET
import requests  

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QPushButton, QListWidget, QLineEdit, QCheckBox, QListWidgetItem, QSpacerItem,
    QSizePolicy, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer


class DNSApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TotalDNS Alkalmazás")
        self.setGeometry(100, 100, 900, 600)

        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        
        self.top_layout = QHBoxLayout()
        self.dns_list_label = QLabel("Elérhető DNS-ek:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Keresés a listában...")
        self.search_input.textChanged.connect(self.filter_dns_list)

        self.top_layout.addWidget(self.dns_list_label)
        self.top_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.top_layout.addWidget(self.search_input)

        self.main_layout.addLayout(self.top_layout)


        self.dns_list = QListWidget()
        self.main_layout.addWidget(self.dns_list)

      
        self.add_dns_layout = QHBoxLayout()
        self.dns_input = QLineEdit()
        self.dns_input.setPlaceholderText("DNS cím (pl. 8.8.8.8)")
        self.dns_provider_input = QLineEdit()
        self.dns_provider_input.setPlaceholderText("Szolgáltató neve (pl. Google)")

        self.add_dns_button = QPushButton("Hozzáad")
        self.add_dns_button.clicked.connect(self.add_dns)

        self.remove_dns_button = QPushButton("Törlés")
        self.remove_dns_button.clicked.connect(self.remove_dns)

        self.add_dns_layout.addWidget(self.dns_input)
        self.add_dns_layout.addWidget(self.dns_provider_input)
        self.add_dns_layout.addWidget(self.add_dns_button)
        self.add_dns_layout.addWidget(self.remove_dns_button)

        self.main_layout.addLayout(self.add_dns_layout)

        
        self.custom_dns_layout = QHBoxLayout()
        self.custom_dns_checkbox = QCheckBox("Egyéni DNS használata")
        self.custom_dns_input = QLineEdit()
        self.custom_dns_input.setPlaceholderText("Egyéni DNS cím (pl. 9.9.9.9)")
        self.custom_dns_input.setEnabled(False)

        self.custom_dns_checkbox.stateChanged.connect(self.toggle_custom_dns_input)

        self.custom_dns_layout.addWidget(self.custom_dns_checkbox)
        self.custom_dns_layout.addWidget(self.custom_dns_input)
        self.main_layout.addLayout(self.custom_dns_layout)

        
        self.status_label = QLabel("Nincs csatlakoztatva")
        self.main_layout.addWidget(self.status_label)

        
        self.button_layout = QHBoxLayout()

        self.connect_button = QPushButton("Kapcsolódás")
        self.connect_button.clicked.connect(self.connect_dns)

        self.disconnect_button = QPushButton("Szétkapcsolás")
        self.disconnect_button.clicked.connect(self.reset_dns)

        self.ping_button = QPushButton("Ping teszt")
        self.ping_button.clicked.connect(self.ping_dns)

        self.button_layout.addWidget(self.connect_button)
        self.button_layout.addWidget(self.disconnect_button)
        self.button_layout.addWidget(self.ping_button)

        self.main_layout.addLayout(self.button_layout)

        
        self.advanced_layout = QHBoxLayout()
        
        self.flush_button = QPushButton("Flush DNS")
        self.flush_button.clicked.connect(self.flush_dns)

        
        self.current_dns_button = QPushButton("Aktuális DNS megtekintése")
        self.current_dns_button.clicked.connect(self.show_current_dns)

        
        self.nslookup_button = QPushButton("NSLookup teszt")
        self.nslookup_button.clicked.connect(self.nslookup_test)

        
        self.geoip_button = QPushButton("GeoIP lekérdezés")
        self.geoip_button.clicked.connect(self.geoip_lookup)

        self.advanced_layout.addWidget(self.flush_button)
        self.advanced_layout.addWidget(self.current_dns_button)
        self.advanced_layout.addWidget(self.nslookup_button)
        self.advanced_layout.addWidget(self.geoip_button)

        self.main_layout.addLayout(self.advanced_layout)

        
        self.schedule_layout = QHBoxLayout()
        self.schedule_label = QLabel("DNS váltás időzítve (mp):")
        self.schedule_spinbox = QSpinBox()
        self.schedule_spinbox.setRange(1, 3600)
        self.schedule_spinbox.setValue(10)
        self.schedule_button = QPushButton("Időzített váltás")
        self.schedule_button.clicked.connect(self.schedule_dns_change)

        self.schedule_layout.addWidget(self.schedule_label)
        self.schedule_layout.addWidget(self.schedule_spinbox)
        self.schedule_layout.addWidget(self.schedule_button)

        self.main_layout.addLayout(self.schedule_layout)

        
        self.load_dns()

        
        self.apply_custom_style()

    
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

    def save_dns_to_xml(self, dns_servers):
        root = ET.Element("dns_servers")
        for dns in dns_servers:
            dns_element = ET.SubElement(root, "dns")
            ET.SubElement(dns_element, "provider").text = dns['provider']
            ET.SubElement(dns_element, "address").text = dns['dns']
        tree = ET.ElementTree(root)
        tree.write("dns_servers.xml")

    def get_dns_list(self):
        dns_list = []
        for index in range(self.dns_list.count()):
            item = self.dns_list.item(index)
            dns = item.data(Qt.UserRole)
            provider = item.text().split(' - ')[0]
            dns_list.append({"dns": dns, "provider": provider})
        return dns_list

   
    def add_dns(self):
        dns = self.dns_input.text().strip()
        provider = self.dns_provider_input.text().strip()

        if not dns or not provider:
            self.status_label.setText("Hiányzik DNS cím vagy szolgáltató név.")
            self.status_label.setStyleSheet("color: red;")
            return

        
        for index in range(self.dns_list.count()):
            item = self.dns_list.item(index)
            if item.data(Qt.UserRole) == dns:
                self.status_label.setText("A megadott DNS már szerepel a listában.")
                self.status_label.setStyleSheet("color: red;")
                return

       
        item = QListWidgetItem(f"{provider} - {dns}")
        item.setData(Qt.UserRole, dns)
        self.dns_list.addItem(item)
        self.dns_input.clear()
        self.dns_provider_input.clear()

        self.save_dns_to_xml(self.get_dns_list())
        self.status_label.setText("DNS sikeresen hozzáadva.")
        self.status_label.setStyleSheet("color: green;")

    def remove_dns(self):
        selected_item = self.dns_list.currentItem()
        if not selected_item:
            self.status_label.setText("Nincs kiválasztott DNS a törléshez.")
            self.status_label.setStyleSheet("color: red;")
            return

        row = self.dns_list.currentRow()
        self.dns_list.takeItem(row)

        self.save_dns_to_xml(self.get_dns_list())
        self.status_label.setText("Kiválasztott DNS törölve.")
        self.status_label.setStyleSheet("color: green;")

    def filter_dns_list(self, text):
        text = text.lower()
        for i in range(self.dns_list.count()):
            item = self.dns_list.item(i)
            item_text = item.text().lower()
            item.setHidden(text not in item_text)

    
    def toggle_custom_dns_input(self, state):
        if state == Qt.Checked:
            self.custom_dns_input.setEnabled(True)
        else:
            self.custom_dns_input.setEnabled(False)

   
    def get_active_interface(self):
        try:
            output = subprocess.check_output("netsh interface show interface", shell=True, text=True)
            lines = output.splitlines()
            for line in lines:
                
                if "Connected" in line or "Csatlakoztatva" in line:
                    parts = line.split()
                    
                    return parts[-1]
            return None
        except subprocess.CalledProcessError as e:
            print(f"Nem sikerült lekérdezni az aktív interfészt: {e}")
            return None

    def set_dns(self, dns):
        
        try:
            interface = self.get_active_interface()
            if not interface:
                self.status_label.setText("Nem található aktív interfész.")
                self.status_label.setStyleSheet("color: red;")
                return

            set_cmd = f'netsh interface ip set dns name="{interface}" source=static address={dns}'
            add_cmd = f'netsh interface ip add dns name="{interface}" addr={dns} index=2'

            subprocess.check_call(
                f'powershell -Command "Start-Process cmd -ArgumentList \'/c {set_cmd}\' -Verb runAs"',
                shell=True
            )
            subprocess.check_call(
                f'powershell -Command "Start-Process cmd -ArgumentList \'/c {add_cmd}\' -Verb runAs"',
                shell=True
            )

            self.status_label.setText(f"DNS beállítva: {dns}")
            self.status_label.setStyleSheet("color: green;")
            print(f"DNS beállítva: {dns}")
        except subprocess.CalledProcessError as e:
            self.status_label.setText("DNS beállítás sikertelen.")
            self.status_label.setStyleSheet("color: red;")
            print(f"DNS beállítás sikertelen: {e}")

    def reset_dns(self):
        
        try:
            interface = self.get_active_interface()
            if not interface:
                self.status_label.setText("Nem található aktív interfész.")
                self.status_label.setStyleSheet("color: red;")
                return

            reset_cmd = f'netsh interface ip set dns name="{interface}" source=dhcp'
            subprocess.check_call(
                f'powershell -Command "Start-Process cmd -ArgumentList \'/c {reset_cmd}\' -Verb runAs"',
                shell=True
            )

            self.status_label.setText("DNS visszaállítva automatikusra (DHCP).")
            self.status_label.setStyleSheet("color: green;")
            print("DNS visszaállítva automatikusra")
        except subprocess.CalledProcessError as e:
            self.status_label.setText("DNS visszaállítás sikertelen.")
            self.status_label.setStyleSheet("color: red;")
            print(f"DNS visszaállítás sikertelen: {e}")

    def connect_dns(self):
        
        if self.custom_dns_checkbox.isChecked():
            custom_dns = self.custom_dns_input.text().strip()
            if custom_dns:
                self.set_dns(custom_dns)
            else:
                self.status_label.setText("Nincs megadva egyéni DNS cím.")
                self.status_label.setStyleSheet("color: red;")
        else:
            selected_dns_item = self.dns_list.currentItem()
            if selected_dns_item:
                selected_dns = selected_dns_item.data(Qt.UserRole)
                self.set_dns(selected_dns)
            else:
                self.status_label.setText("Nincs kiválasztott DNS.")
                self.status_label.setStyleSheet("color: red;")

   
    def ping_dns(self):
      
        dns_address = None
        if self.custom_dns_checkbox.isChecked():
            dns_address = self.custom_dns_input.text().strip()
        else:
            selected_dns_item = self.dns_list.currentItem()
            if selected_dns_item:
                dns_address = selected_dns_item.data(Qt.UserRole)

        if not dns_address:
            self.status_label.setText("Nincs DNS megadva a pingeléshez.")
            self.status_label.setStyleSheet("color: red;")
            return

        try:
            output = subprocess.check_output(f'ping {dns_address}', shell=True, text=True)
            if "Reply from" in output or "Válasz" in output:
                self.status_label.setText(f"Sikeres ping: {dns_address}")
                self.status_label.setStyleSheet("color: green;")
            else:
                self.status_label.setText(f"Sikertelen ping: {dns_address}")
                self.status_label.setStyleSheet("color: red;")
        except subprocess.CalledProcessError:
            self.status_label.setText(f"Sikertelen ping: {dns_address}")
            self.status_label.setStyleSheet("color: red;")

    
    def flush_dns(self):
        
        try:
            output = subprocess.check_output('ipconfig /flushdns', shell=True, text=True)
            self.status_label.setText("DNS gyorsítótár törölve.")
            self.status_label.setStyleSheet("color: green;")
            print(output)
        except subprocess.CalledProcessError as e:
            self.status_label.setText("Flush DNS sikertelen.")
            self.status_label.setStyleSheet("color: red;")
            print(f"Flush DNS hiba: {e}")

    def show_current_dns(self):
  
        try:
            interface = self.get_active_interface()
            if not interface:
                self.status_label.setText("Nincs aktív interfész a DNS lekérdezéséhez.")
                self.status_label.setStyleSheet("color: red;")
                return

            cmd = f'netsh interface ip show config name="{interface}"'
            output = subprocess.check_output(cmd, shell=True, text=True)
            
            dns_info = []
            for line in output.splitlines():
                if "DNS servers configured" in line or "Statically Configured DNS Servers" in line:
                   
                    continue
                
                if "." in line and "Subnet" not in line and ":" not in line:
                   
                    dns_info.append(line.strip())

            if dns_info:
                self.status_label.setText(f"Aktuálisan beállított DNS(ek): {', '.join(dns_info)}")
                self.status_label.setStyleSheet("color: green;")
            else:
                self.status_label.setText("Nem találtam DNS beállítást vagy automatikus a DNS.")
                self.status_label.setStyleSheet("color: yellow;")

        except subprocess.CalledProcessError as e:
            self.status_label.setText("Nem sikerült lekérdezni az aktuális DNS-t.")
            self.status_label.setStyleSheet("color: red;")
            print(f"DNS lekérdezés hiba: {e}")

    def nslookup_test(self):
        """
        NSLookup teszt a beállított DNS-sel. Itt példaként google.com-ot kérdezünk le.
        """
        domain = "google.com"
        try:
          
            output = subprocess.check_output(f'nslookup {domain}', shell=True, text=True)
            if "Name:" in output or "Name" in output:
                self.status_label.setText(f"NSLookup sikeres: {domain}")
                self.status_label.setStyleSheet("color: green;")
            else:
                self.status_label.setText(f"NSLookup sikertelen: {domain}")
                self.status_label.setStyleSheet("color: red;")
        except subprocess.CalledProcessError:
            self.status_label.setText(f"NSLookup sikertelen: {domain}")
            self.status_label.setStyleSheet("color: red;")

    def geoip_lookup(self):
 
        dns_address = None
        if self.custom_dns_checkbox.isChecked():
            dns_address = self.custom_dns_input.text().strip()
        else:
            selected_dns_item = self.dns_list.currentItem()
            if selected_dns_item:
                dns_address = selected_dns_item.data(Qt.UserRole)

        if not dns_address:
            self.status_label.setText("Nincs DNS megadva a GeoIP lekérdezéshez.")
            self.status_label.setStyleSheet("color: red;")
            return

        try:
            url = f"http://ip-api.com/json/{dns_address}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if data["status"] == "success":
                country = data.get("country", "N/A")
                city = data.get("city", "N/A")
                isp = data.get("isp", "N/A")
                self.status_label.setText(f"GeoIP: {dns_address} → {country}, {city}, ISP: {isp}")
                self.status_label.setStyleSheet("color: green;")
            else:
                
                self.status_label.setText(f"GeoIP sikertelen: {data.get('message', 'ismeretlen hiba')}")
                self.status_label.setStyleSheet("color: red;")
        except Exception as e:
            self.status_label.setText(f"GeoIP hiba: {e}")
            self.status_label.setStyleSheet("color: red;")

    def schedule_dns_change(self):
     
        delay = self.schedule_spinbox.value()
        
        QTimer.singleShot(delay * 1000, self._do_scheduled_dns)

        self.status_label.setText(f"DNS váltás beütemezve {delay} mp múlva.")
        self.status_label.setStyleSheet("color: yellow;")

    def _do_scheduled_dns(self):
       
        if self.custom_dns_checkbox.isChecked():
            custom_dns = self.custom_dns_input.text().strip()
            if custom_dns:
                self.set_dns(custom_dns)
            else:
                self.status_label.setText("Ütemezett váltás: nincs megadva egyéni DNS!")
                self.status_label.setStyleSheet("color: red;")
        else:
            selected_dns_item = self.dns_list.currentItem()
            if selected_dns_item:
                selected_dns = selected_dns_item.data(Qt.UserRole)
                self.set_dns(selected_dns)
            else:
                self.status_label.setText("Ütemezett váltás: nincs kiválasztott DNS!")
                self.status_label.setStyleSheet("color: red;")

    
    def apply_custom_style(self):
        custom_stylesheet = """
        QMainWindow {
            background-color: #1E1E1E;
        }
        QLabel {
            color: #FFFFFF;
            font-size: 14px;
        }
        QPushButton {
            background-color: #007BFF;
            color: white;
            font-size: 14px;
            border-radius: 5px;
            padding: 8px 12px;
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
        QLineEdit {
            background-color: #2E2E2E;
            color: #FFFFFF;
            border: 1px solid #555555;
            padding: 5px;
            border-radius: 5px;
        }
        QListWidget {
            background-color: #2E2E2E;
            color: #FFFFFF;
            border: 1px solid #555555;
            padding: 5px;
            border-radius: 5px;
        }
        QCheckBox {
            color: #FFFFFF;
            font-size: 14px;
        }
        QSpinBox {
            background-color: #2E2E2E;
            color: #FFFFFF;
            border: 1px solid #555555;
            padding: 5px;
            border-radius: 5px;
            width: 60px;
        }
        """
        self.setStyleSheet(custom_stylesheet)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DNSApp()
    window.show()
    sys.exit(app.exec_())
