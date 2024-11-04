from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import StringProperty
import xml.etree.ElementTree as ET
import subprocess

class DNSItem(RecycleDataViewBehavior, BoxLayout):
    text = StringProperty()

class DNSRecycleView(RecycleView):
    pass

class DNSAppLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10

        # DNS list label
        self.dns_list_label = Label(text="Elérhető DNS-ek:", font_size='18sp', color=(1, 1, 1, 1), size_hint_y=None, height=30)
        self.add_widget(self.dns_list_label)

        # DNS list RecycleView
        self.dns_list = DNSRecycleView()
        self.add_widget(self.dns_list)

        # New DNS addition layout
        self.add_dns_layout = BoxLayout(size_hint_y=None, height='50dp', spacing=10)
        self.dns_input = TextInput(hint_text="DNS cím (pl. 8.8.8.8)", multiline=False, size_hint_x=0.4)
        self.dns_provider_input = TextInput(hint_text="Szolgáltató neve", multiline=False, size_hint_x=0.4)
        self.add_dns_button = Button(text="Hozzáadás", size_hint_x=0.2)
        self.add_dns_button.bind(on_release=self.add_dns)
        self.add_dns_layout.add_widget(self.dns_input)
        self.add_dns_layout.add_widget(self.dns_provider_input)
        self.add_dns_layout.add_widget(self.add_dns_button)
        self.add_widget(self.add_dns_layout)

        # Custom DNS checkbox
        self.custom_dns_checkbox = CheckBox()
        self.add_widget(Label(text="Egyéni DNS használata", font_size='16sp', color=(1, 1, 1, 1)))
        self.add_widget(self.custom_dns_checkbox)

        # Status label
        self.status_label = Label(text="Nincs csatlakoztatva", font_size='16sp', color=(1, 1, 1, 1))
        self.add_widget(self.status_label)

        # Connect and Disconnect buttons layout
        self.button_layout = BoxLayout(size_hint_y=None, height='50dp', spacing=10)
        self.disconnect_button = Button(text="Szétkapcsolás")
        self.disconnect_button.bind(on_release=self.reset_dns)
        self.button_layout.add_widget(self.disconnect_button)
        
        self.delete_button = Button(text="Kijelölt DNS törlése")
        self.delete_button.bind(on_release=self.delete_selected_dns)
        self.button_layout.add_widget(self.delete_button)

        self.add_widget(self.button_layout)

        self.load_dns()

    def load_dns(self):
        self.dns_list.data = []
        dns_servers = self.load_dns_from_xml()
        if not dns_servers:
            dns_servers = [
                {"dns": "8.8.8.8", "provider": "Google"},
                {"dns": "8.8.4.4", "provider": "Google (Secondary)"}
            ]
            self.save_dns_to_xml(dns_servers)

        for dns in dns_servers:
            item_text = f"{dns['provider']} - {dns['dns']}"
            self.dns_list.data.append({"text": item_text})

    def add_dns(self, instance):
        dns = self.dns_input.text
        provider = self.dns_provider_input.text
        item_text = f"{provider} - {dns}"
        if dns and provider:
            self.dns_list.data.append({"text": item_text})
            self.dns_input.text = ""
            self.dns_provider_input.text = ""
            self.save_dns_to_xml(self.get_dns_list())
            self.status_label.text = "DNS hozzáadva"

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

    def get_dns_list(self):
        dns_list = []
        for item in self.dns_list.data:
            provider, dns = item["text"].split(" - ")
            dns_list.append({"dns": dns, "provider": provider})
        return dns_list

    def get_active_interface(self):
        try:
            output = subprocess.check_output("netsh interface show interface", shell=True, text=True)
            lines = output.splitlines()
            for line in lines:
                if "Connected" in line:
                    return line.split()[-1]
            return None
        except subprocess.CalledProcessError:
            return None

    def set_dns(self, dns):
        try:
            interface = self.get_active_interface()
            if not interface:
                self.status_label.text = "Nem található aktív interfész"
                return
            subprocess.check_call(f"netsh interface ip set dns name={interface} source=static address={dns}", shell=True)
            self.status_label.text = f"DNS beállítva: {dns}"
        except subprocess.CalledProcessError:
            self.status_label.text = "DNS beállítás sikertelen"

    def reset_dns(self, instance):
        try:
            interface = self.get_active_interface()
            if not interface:
                self.status_label.text = "Nem található aktív interfész"
                return
            subprocess.check_call(f"netsh interface ip set dns name={interface} source=dhcp", shell=True)
            self.status_label.text = "DNS visszaállítva automatikusra"
        except subprocess.CalledProcessError:
            self.status_label.text = "DNS visszaállítás sikertelen"

    def connect_to_dns(self, dns):
        self.set_dns(dns)

    def delete_selected_dns(self, instance):
        if self.dns_list.data:
            self.dns_list.data.pop(0)
            self.save_dns_to_xml(self.get_dns_list())
            self.status_label.text = "DNS törölve"

class DNSApp(App):
    def build(self):
        Builder.load_file('dns_app.kv')
        return DNSAppLayout()

if __name__ == "__main__":
    DNSApp().run()
