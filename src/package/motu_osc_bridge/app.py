import rumps
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

class MyListener(ServiceListener):
    def __init__(self, onAdded, onUpdated, onRemoved):
        self.onAdded= onAdded
        self.onRemoved = onRemoved
        self.onUpdated = onUpdated 
        super().__init__()

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        self.onUpdated(name, info)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self.onRemoved(name)

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        self.onAdded(name, info)

class MotuOscBridgeApp(rumps.App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.services = {}

        # self.config = {
        #     "app_name": "Motu OSC Bridge",
        #     "connect": "Connect",
        #     "disconnect": "Disconnect"
        # }
        # self.app = rumps.App(self.config["app_name"])
        # self.app.title = "M->OSC"
        # self.connect_button = rumps.MenuItem(title=self.config["connect"], callback=self.on_connect)
        # self.disconnect_button = rumps.MenuItem(title=self.config["disconnect"], callback=self.on_disconnect)
        # self.app.menu = [self.connect_button, self.disconnect_button]
        
    @rumps.clicked("Connect")
    def on_connect(self, *args, **kwargs):
        self.start_browsing()
        # rumps.notification(title="MOTU OSC Bridge", subtitle="Connect", message='connecting')

    # @rumps.clicked("Disconnect")
    # def on_disconnect(self, *args, **kwargs):
    #     rumps.notification("MOTU OSC Bridge", subtitle="Disconnect", message='disconnecting')

    def onAdded(self, name, info):
        print("added")
        self.services[name] = info
        self.build_menu()

    def onUpdated(self, name, info):
        self.services[name] = info
        self.build_menu()

    def onRemoved(self, name):
        if name in self.services:
            del self.services[name]
            self.build_menu()

    def start_browsing(self):
        zeroconf = Zeroconf()
        listener = MyListener(self.onAdded, self.onUpdated, self.onRemoved)
        service_types = ["_motu-csr._udp.local.", "_http._tcp.local.", "_osc._udp.local."]
        ServiceBrowser(zeroconf, service_types, listener)

    def build_menu(self):
        self.menu["Servers"] = list(self.services.keys())

    def start():
        app = MotuOscBridgeApp("M->OSC")
        app.menu = [
        'Servers',
        None,  # None functions as a separator in your menu
        {'Arbitrary':
            {"Depth": ["Menus", "It's pretty easy"],
             "And doesn't": ["Even look like Objective C", rumps.MenuItem("One bit")]}},
        None
    ]
        app.run()
        return app