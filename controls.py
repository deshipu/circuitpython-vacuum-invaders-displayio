import board
import digitalio
import analogio
import audioio
import audiocore
import gamepadshift


B_X = 0x01
B_O = 0x02
B_START = 0x04
B_SELECT = 0x08
B_DOWN = 0x10
B_LEFT = 0x20
B_RIGHT = 0x40
B_UP = 0x80


class Buttons:
    def __init__(self):
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
            pressed |= B_LEFT
        elif x > dead:
            pressed |= B_RIGHT
        y = self.joy_y.value - 32767
        if y < -dead:
            pressed |= B_UP
        elif y > dead:
            pressed |= B_DOWN
        return pressed


class Audio:
    last_audio = None

    def __init__(self, speaker_pin, mute_pin=None):
        self.muted = True
        self.buffer = bytearray(128)
        if mute_pin:
            self.mute_pin = digitalio.DigitalInOut(mute_pin)
            self.mute_pin.switch_to_output(value=not self.muted)
        else:
            self.mute_pin = None
        self.audio = audioio.AudioOut(speaker_pin)

    def play(self, audio_file, loop=False):
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


buttons = Buttons()
audio = Audio(board.SPEAKER, board.SPEAKER_ENABLE)
display = board.DISPLAY
