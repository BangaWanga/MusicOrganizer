import enum
import rtmidi
from rtmidi.midiutil import open_midiinput
import time
from multiprocessing import Process, Pipe

midiout = rtmidi.MidiOut()
midiin_test = False

class MIDI_Signal:
    def __init__(self):
        pass

if midiin_test:
    port = 1

    import sys
    try:
        midiin, port_name = open_midiinput(port)
    except (EOFError, KeyboardInterrupt):
        sys.exit()
    try:
        while True:
            msg = midiin.get_message()
            if msg:
                print(msg)
            # timer += deltatime
            # print("[%s] @%0.6f %r" % (port_name, timer, message))
            # time.sleep(0.001)
    except (KeyboardInterrupt, EOFError):
        print("Stopping polling")


class MIDI_Type(enum.Enum):
    Note_Off = lambda channel, note, velocity: [0x80 + channel, note, velocity]
    Note_On = lambda channel, note, velocity: [0x90 + channel, note, velocity]
    Polyphonic_Aftertouch = lambda channel, note, velocity: [0xA0 + channel, note, velocity]
    Control_Change = lambda channel, cc, value: [0xA0 + channel, cc, value]

    def __call__(self, *args, **kwargs):
        return self.value(*args, **kwargs)

    @staticmethod
    def request_program_edit_buffer_dump_sequence():
        sequence = [
            int("11110000", 2),  # System Exclusive (SysEx)',
            int("00000001", 2),  # DSI ID',
            int("00101111", 2),  # Rev2 ID',
            int("00000110", 2),  # Request Program Edit Buffer Transmit',
            int("11110111", 2),  # End of Exclusive (EOX)']
        ]
        return [[s, 0, 0] for s in sequence]
def writer(p_input):
    channel = 0
    velocity = 100
    wait_time = 0.2
    for note in range(128):

        note_on = MIDI_Type.Note_On(channel, note, velocity)
        note_off = MIDI_Type.Note_On(channel, note, velocity)
        p_input.send((note_on, wait_time,))  # Write 'count' numbers into the input pipe
        p_input.send((note_off, wait_time,))  # Write 'count' numbers into the input pipe
    p_input.send((0, 'DONE',))


def decode_msg(msg):
    return msg, 0.5


def get_midi_outs() -> list[str]:
    print("midiout.get_ports() ", midiout.get_ports())
    return midiout.get_ports()


def reader_proc(pipe, port):
    # Read from the pipe; this will be spawned as a separate Process
    p_output, p_input = pipe
    p_input.close()  # We are only reading
    global midiout
    midiout.open_port(port)
    with midiout:
        while True:
            midi_msg = p_output.recv()
            if midi_msg == 'DONE':
                del midiout
                break
            print("sending midi message ", midi_msg)
            midiout.send_message(midi_msg)


class Midi_Port:
    def __init__(self, port: int):
        print("INIT MIDI PORT")
        p_output, p_input = Pipe()  # writer() writes to p_input from _this_ process
        self.reader_p = Process(target=reader_proc, args=((p_output, p_input), port))
        self.reader_p.daemon = True
        self.reader_p.start()  # Launch the reader process
        _start = time.time()
        self.p_input = p_input
        p_output.close()
        # writer(p_input)  # Send a lot of stuff to reader_proc()

    def request_program_edit_buffer_dump(self):
        for _msg in MIDI_Type.request_program_edit_buffer_dump_sequence():
            self.send(msg)

    def close(self):
        self.p_input.send((0, 'DONE',))
        self.p_input.close()

        self.reader_p.join()

    def send(self, message, wait_time: float = .0):
        self.p_input.send(message) # , wait_time))


if __name__ == "__main__":
    # Pipes are unidirectional with two endpoints:  p_input ------> p_output
    p_output, p_input = Pipe()  # writer() writes to p_input from _this_ process
    port = port_input()
    reader_p = Process(target=reader_proc, args=((p_output, p_input), port))
    reader_p.daemon = True
    reader_p.start()  # Launch the reader process

    p_output.close()  # We no longer need this part of the Pipe()
    _start = time.time()
    writer(p_input)  # Send a lot of stuff to reader_proc()
    p_input.close()
    reader_p.join()