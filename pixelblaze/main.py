"""Control your Pixelblaze device from TiLDA"""

___name___         = "Pixelblaze"
___license___      = "MIT"
___dependencies___ = ["wifi", "websockets", "ugfx_helper", "sleep", "app"]
___categories___   = ["LEDs"]

import ugfx_helper, ugfx
import dialogs
import wifi
import websockets

print("PixelBlaze init")

class PixelBlaze:
    _patterns = None
    _ws = None

    def __init__(self, url):
        super().__init__()
        self._ws = websockets.connect(url)
        print("Connected to {}".format(url))

    def __del__(self):
        try:
            self._ws.close()
        except:
            print("Couldn't close websocket cleanly")
        super().__del__()

    @property
    def patterns(self):
        if self._patterns:
            return self._patterns

        print("fetching patterns...")
        # ws.settimeout(3)
        # print("set sockettimeout to 3 seconds")
        self._ws.send('{"listPrograms": true}')
        print("sent listPrograms frame")

        self._patterns = []
        while True:
            frame = self._ws.recv()
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
        self._ws.send("""{{"activeProgramId": "{}", "save": true}}""".format(pid))
        print("set pattern to {}".format(pid))

    @property
    def brightness(self):
        return 0.1

    @brightness.setter
    def brightness(self, brightness):
        self._ws.send("""{{"brightness": {} }}""".format(brightness))
        print("set brightness to {}".format(brightness))




wifi.connect()
print("wifi connected")
ugfx_helper.init()
print("ugfx init")


pixelblaze = None
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
