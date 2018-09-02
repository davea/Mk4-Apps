"""Control your Pixelblaze device from TiLDA"""

___name___         = "Pixelblaze"
___license___      = "MIT"
___dependencies___ = ["wifi", "websockets", "ugfx_helper", "sleep", "app"]
___categories___   = ["LEDs"]

import ugfx_helper, ugfx
import dialogs
import wifi
import websockets

wifi.connect()
print("wifi connected")
ugfx_helper.init()
print("ugfx init")

websockets.enable_debug()

pixelblaze = None

class PixelBlaze:
    _patterns = None
    _ws = None
    _url = None

    def __init__(self, url):
        super().__init__()
        self._url = url

    def __del__(self):
        try:
            self._ws.close()
        except:
            print("Couldn't close websocket cleanly")
        super().__del__()

    @property
    def ws(self):
        try:
            if self._ws.open:
                return self._ws
            else:
                raise Exception("Not connected yet")
        except:
            self._ws = websockets.connect(self._url)
            self._ws.settimeout(5)
            print("Connected to {}".format(self._url))
        return self._ws


    @property
    def patterns(self):
        if self._patterns:
            return self._patterns

        print("fetching patterns...")
        self.ws.send('{"listPrograms": true}')
        print("sent listPrograms frame")

        self._patterns = []
        while True:
            frame = self.ws.recv()
            print("Received frame")
            print("frame length {}".format(len(frame)))
            if isinstance(frame, bytes):
                print("bytes frame")
                if frame[0] != 0x07:
                    print("not a pattern frame")
                    continue
                patterns = frame[2:].decode("utf-8").split("\n")
                for pattern in patterns:
                    if "\t" not in pattern:
                        print("empty line")
                        continue # empty line
                    pid, name = pattern.split("\t")
                    print("found pattern {} {}".format(pid, name))
                    self._patterns.append((pid, name))
                if frame[1] & 0x04:
                    print("last frame!")
                    break # last frame
        self._patterns.sort(key=lambda i: i[1])
        return self._patterns

    def set_pattern(self, pid):
        self.ws.send("""{{"activeProgramId": "{}", "save": true}}""".format(pid))
        print("set pattern to {}".format(pid))

    @property
    def brightness(self):
        return 0.1

    @brightness.setter
    def brightness(self, brightness):
        self.ws.send("""{{"brightness": {} }}""".format(brightness))
        print("set brightness to {}".format(brightness))


def connect_pixelblaze():
    global pixelblaze
    ugfx.clear(ugfx.html_color(0x7c1143))
    with dialogs.WaitingMessage(text="Please wait...", title="Connecting Pixelblaze") as message:
        pixelblaze = PixelBlaze("ws://pixelblaze.davea.me:81/")


def choose_pattern():
    ugfx.clear(ugfx.html_color(0x7c1143))

    with dialogs.WaitingMessage(text="Please wait...", title="Downloading patterns") as message:
        menu_items = []
        for pid, name in pixelblaze.patterns:
            menu_items.append({'title': name, 'pid': pid})
            message.text = "Loaded {} patterns so far...".format(len(menu_items))

    option = dialogs.prompt_option(menu_items, none_text="Back", text="Available patterns", title="Select pattern")

    if option:
        with dialogs.WaitingMessage(text="Activating pattern {}".format(option['pid']), title="Setting pattern...") as message:
            pixelblaze.set_pattern(option['pid'])
        dialogs.notice("""{} activated""".format(option['title']), title="Pattern selected", close_text="OK")

def choose_brightness():
    ugfx.clear(ugfx.html_color(0x7c1143))
    with dialogs.WaitingMessage(text="Getting brightness...", title="Communicating") as message:
        brightness = pixelblaze.brightness
    new_brightness = dialogs.prompt_text("Brightness:", init_text=str(brightness))
    if new_brightness is not None:
        with dialogs.WaitingMessage(text="Setting brightness...", title="Communicating") as message:
            pixelblaze.brightness = new_brightness


def choose_function():
    patterns = dialogs.prompt_boolean("Choose function", title="Pixelblaze", true_text="Patterns", false_text="Brightness")
    if patterns:
        choose_pattern()
    else:
        choose_brightness()


while True:
    if pixelblaze is None:
        connect_pixelblaze()

    choose_function()
