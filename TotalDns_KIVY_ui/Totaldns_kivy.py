from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.listview import ListItemButton
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
from kivy.uix.textinput import TextInput

class DNSAppLayout(BoxLayout):
    dns_list = ObjectProperty(None)
    dns_input = ObjectProperty(None)
    dns_provider_input = ObjectProperty(None)
    status_label = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_dns()
    
    def load_dns(self):
        default_dns_servers = [
            {"dns": "1.1.1.1", "provider": "Cloudflare"},
            {"dns": "8.8.8.8", "provider": "Google"},
            # Add more default DNS servers here
        ]
        for dns in default_dns_servers:
            self.dns_list.adapter.data.extend([f"{dns['provider']} - {dns['dns']}"])
        self.dns_list._trigger_reset_populate()
    
    def add_dns(self):
        dns = self.dns_input.text
        provider = self.dns_provider_input.text
        if dns and provider:
            self.dns_list.adapter.data.extend([f"{provider} - {dns}"])
            self.dns_list._trigger_reset_populate()
            self.dns_input.text = ""
            self.dns_provider_input.text = ""
            self.status_label.text = "Új DNS hozzáadva!"
        else:
            self.status_label.text = "Adja meg a DNS címet és szolgáltatót."

    def connect_dns(self):
        if self.dns_list.adapter.selection:
            selected_dns = self.dns_list.adapter.selection[0].text.split(" - ")[1]
            self.status_label.text = f"Csatlakozva: {selected_dns}"
        else:
            self.status_label.text = "Nincs kiválasztott DNS."

    def disconnect_dns(self):
        self.status_label.text = "DNS visszaállítva automatikusra."

class DNSApp(App):
    def build(self):
        return DNSAppLayout()

if __name__ == "__main__":
    DNSApp().run()
