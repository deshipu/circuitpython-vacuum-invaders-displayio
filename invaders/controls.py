import board
import digitalio
import time


class _PyGamerButtons:
    O = 0x01
    X = 0x02
    Z = 0x04
    SELECT = 0x08
    RIGHT = 0x10
    DOWN = 0x20
    UP = 0x40
    LEFT = 0x80

    def __init__(self):
        import gamepadshift
        import analogio

        self.buttons = gamepadshift.GamePadShift(
            digitalio.DigitalInOut(board.BUTTON_CLOCK),
            digitalio.DigitalInOut(board.BUTTON_OUT),
            digitalio.DigitalInOut(board.BUTTON_LATCH),
        )
        self.joy_x = analogio.AnalogIn(board.JOYSTICK_X)
        self.joy_y = analogio.AnalogIn(board.JOYSTICK_Y)

    def get_pressed(self):
        pressed = self.buttons.get_pressed()
        dead = 15000
        x = self.joy_x.value - 32767
        if x < -dead:
            pressed |= self.LEFT
        elif x > dead:
            pressed |= self.RIGHT
        y = self.joy_y.value - 32767
        if y < -dead:
            pressed |= sefl.UP
        elif y > dead:
            pressed |= self.DOWN
        return pressed


class _PyBadgeButtons:
    O = 0x01 # A
    X = 0x02 # B
    Z = 0x04 # Start
    SELECT = 0x08
    RIGHT = 0x10
    DOWN = 0x20
    UP = 0x40
    LEFT = 0x80

    def __init__(self):
        import gamepadshift

        self.buttons = gamepadshift.GamePadShift(
            digitalio.DigitalInOut(board.BUTTON_CLOCK),
            digitalio.DigitalInOut(board.BUTTON_OUT),
            digitalio.DigitalInOut(board.BUTTON_LATCH),
        )

    def get_pressed(self):
        return self.buttons.get_pressed()


class _PewPewM4Buttons:
    O = 0x01
    X = 0x02
    Z = 0x04
    SELECT = 0x08
    RIGHT = 0x10
    DOWN = 0x20
    UP = 0x40
    LEFT = 0x80

    def __init__(self):
        import gamepad

        self.buttons = gamepad.GamePad(
            digitalio.DigitalInOut(board.BUTTON_O),
            digitalio.DigitalInOut(board.BUTTON_X),
            digitalio.DigitalInOut(board.BUTTON_Z),
            digitalio.DigitalInOut(board.BUTTON_Z),
            digitalio.DigitalInOut(board.BUTTON_RIGHT),
            digitalio.DigitalInOut(board.BUTTON_DOWN),
            digitalio.DigitalInOut(board.BUTTON_UP),
            digitalio.DigitalInOut(board.BUTTON_LEFT),
        )
        self.last_z_press = None

    def get_pressed(self):
        return self.buttons.get_pressed()


class _MeowBitButtons:
    O = 0x01
    X = 0x02
    Z = 0x04
    SELECT = 0x08
    RIGHT = 0x10
    DOWN = 0x20
    UP = 0x40
    LEFT = 0x80

    def __init__(self):
        import gamepad

        self.buttons = gamepad.GamePad(
            digitalio.DigitalInOut(board.BTNA),
            digitalio.DigitalInOut(board.BTNB),
            digitalio.DigitalInOut(board.MENU),
            digitalio.DigitalInOut(board.MENU),
            digitalio.DigitalInOut(board.RIGHT),
            digitalio.DigitalInOut(board.DOWN),
            digitalio.DigitalInOut(board.UP),
            digitalio.DigitalInOut(board.LEFT),
        )

    def get_pressed(self):
        return self.buttons.get_pressed()


class _AudioioAudio:
    last_audio = None

    def __init__(self, speaker_pin, mute_pin=None):
        import audioio
        import audiocore

        self.muted = True
        self.buffer = bytearray(128)
        if mute_pin:
            self.mute_pin = digitalio.DigitalInOut(mute_pin)
            self.mute_pin.switch_to_output(value=not self.muted)
        else:
            self.mute_pin = None
        self.audio = audioio.AudioOut(speaker_pin)

    def play(self, audio_file, loop=False):
        import audiocore
        if self.muted:
            return
        self.stop()
        wave = audiocore.WaveFile(audio_file, self.buffer)
        self.audio.play(wave, loop=loop)

    def stop(self):
        self.audio.stop()

    def mute(self, value=True):
        self.muted = value
        if self.mute_pin:
            self.mute_pin.value = not value


class _DummyAudio:
    def play(self, f, loop=False):
        pass

    def stop(self):
        pass

    def mute(self, mute):
        pass


if hasattr(board, 'JOYSTICK_X'):
    buttons = _PyGamerButtons()
    audio = _AudioioAudio(board.SPEAKER, board.SPEAKER_ENABLE)
    display = board.DISPLAY
elif hasattr(board, 'BUTTON_X'):
    buttons = _PewPewM4Buttons()
    audio = _AudioioAudio(board.P5)
    display = board.DISPLAY
elif hasattr(board, 'BUTTON_CLOCK'):
    buttons = _PyBadgeButtons()
    audio = _AudioioAudio(board.SPEAKER, board.SPEAKER_ENABLE)
    display = board.DISPLAY
elif hasattr(board, 'BTNA'):
    buttons = _MeowBitButtons()
    audio = _DummyAudio()
    display = board.DISPLAY
