import re
import socket
import sys
import threading
from time import time

import numpy as np
from DAQTasks_2flippers import *  # pylint: disable=W0614
from flippr_3 import *  # pylint: disable=W0614
from PyQt5 import QtCore, QtWidgets
from QPlot import QPlot


class SignalServer(object):
    """Simple implementation of a Qt threaded Python socket server.

    Recieves arbitrary TCP packets and scans for keywords. If a packet is recieved
    containing a command corresponding to one of the Qt signals below, this signal is
    emitted and, where necessary, passed a float argument parsed from the incoming
    packet via regex.

    To be used as follows:

        >>thread = QThread()
        >>server = SignalServer('localhost', 80)
        >>server.moveToThread(thread)

        >>server.toggle.connect(...)

        >>thread.started.connect(server.listen)
        >>thread.start()

    Attributes:
        toggle (pyqtSignal): Signal to toggle flipper on / off
        comp   (pyqtSignal): Signal to alter compensation coil current
        amp    (pyqtSignal): Signal to alter flipping coil maximum current
        const  (pyqtSignal): Signal to alter the time constant of the flipping current
    """

    toggle = QtCore.pyqtSignal(int)
    comp_p = QtCore.pyqtSignal(float)
    comp_a = QtCore.pyqtSignal(float)
    amp_p = QtCore.pyqtSignal(float)
    amp_a = QtCore.pyqtSignal(float)
    const_p = QtCore.pyqtSignal(float)
    const_a = QtCore.pyqtSignal(float)
    fn_p = QtCore.pyqtSignal(str)
    fn_a = QtCore.pyqtSignal(str)
    dt_a = QtCore.pyqtSignal(float)
    dt_p = QtCore.pyqtSignal(float)

    def __init__(self, host, port, parent=None):
        super(SignalServer, self).__init__()
        self.host = host  # : Hostname on which to listen
        self.port = port  # : Port on which to listen
        self.parent = parent  # Need a hook to the main class to retrieve settings

    def listen(self):
        """Listen for incoming connection requests.

        This is an extremely standard implementation, see

            https://docs.python.org/3/howto/sockets.html

        This function is threaded to prevent blocking of the main thread by the while
        loop.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))

        sock.listen(5)
        while True:
            client, addr = sock.accept()
            client.settimeout(60)
            thread = threading.Thread(target=self.listenToClient, args=(client, addr))
            thread.start()

    def listenToClient(self, client, addr):
        """Recieve message from accepted connection, parse, and close.

        This function is called in a thread to prevent collisions between connections.
        This threaded model is compatible with the Qt signals / slots model through the
        use of QThread.
        """
        size = 1024
        while True:
            try:
                data = client.recv(size)
                if data and "*IDN?" in str(data):
                    client.send(("Flipper Control" + ":").encode("utf-8"))
                if data and "comp_p" in str(data):
                    if "?" in str(data):
                        client.send(
                            ("comp_p " + str(self.parent.comp_spin_P.value()) + ":").encode("utf-8")
                        )
                    else:
                        self.comp_p.emit(float(re.findall(r"[-+]?\d*\.\d+|\d+", str(data))[0]))
                        client.send("comp_p:".encode("utf-8"))
                if data and "comp_a" in str(data):
                    if "?" in str(data):
                        client.send(
                            ("comp_a " + str(self.parent.comp_spin_A.value()) + ":").encode("utf-8")
                        )
                    else:
                        self.comp_a.emit(float(re.findall(r"[-+]?\d*\.\d+|\d+", str(data))[0]))
                        client.send("comp_a:".encode("utf-8"))
                if data and "amp_p" in str(data):
                    # print("Amplitude")
                    if "?" in str(data):
                        client.send(
                            ("amp_p " + str(self.parent.amplitude_spin_P.value()) + ":").encode(
                                "utf-8"
                            )
                        )
                        # client.send("amp query received".encode('utf-8'))
                    else:
                        self.amp_p.emit(float(re.findall(r"[-+]?\d*\.\d+|\d+", str(data))[0]))
                        client.send("amp_p:".encode("utf-8"))
                if data and "amp_a" in str(data):
                    # print("Amplitude")
                    if "?" in str(data):
                        client.send(
                            ("amp_a " + str(self.parent.amplitude_spin_A.value()) + ":").encode(
                                "utf-8"
                            )
                        )
                        # client.send("amp query received".encode('utf-8'))
                    else:
                        self.amp_a.emit(float(re.findall(r"[-+]?\d*\.\d+|\d+", str(data))[0]))
                        client.send("amp_a:".encode("utf-8"))
                if data and "const_p" in str(data):
                    if "?" in str(data):
                        client.send(
                            ("const_p " + str(self.parent.decay_spin_P.value()) + ":").encode(
                                "utf-8"
                            )
                        )
                    else:
                        self.const_p.emit(float(re.findall(r"[-+]?\d*\.\d+|\d+", str(data))[0]))
                        client.send("const_p:".encode("utf-8"))
                if data and "const_a" in str(data):
                    if "?" in str(data):
                        client.send(
                            ("const_a " + str(self.parent.decay_spin_A.value()) + ":").encode(
                                "utf-8"
                            )
                        )
                    else:
                        self.const_a.emit(float(re.findall(r"[-+]?\d*\.\d+|\d+", str(data))[0]))
                        client.send("const_a:".encode("utf-8"))
                if data and "dt_p" in str(data):
                    if "?" in str(data):
                        client.send(
                            ("dt_p " + str(self.parent.DeltaT_P.value()) + ":").encode("utf-8")
                        )
                    else:
                        self.dt_p.emit(float(re.findall(r"[-+]?\d*\.\d+|\d+", str(data))[0]))
                        client.send("dt_p:".encode("utf-8"))
                if data and "dt_a" in str(data):
                    if "?" in str(data):
                        client.send(
                            ("dt_a " + str(self.parent.DeltaT_A.value()) + ":").encode("utf-8")
                        )
                    else:
                        self.dt_a.emit(float(re.findall(r"[-+]?\d*\.\d+|\d+", str(data))[0]))
                        client.send("dt_a:".encode("utf-8"))
                if data and "file_p" in str(data):
                    if "?" in str(data):
                        client.send(("file_p " + str(self.parent.filename_P) + ":").encode("utf-8"))
                    else:
                        data = str(data, "utf-8").replace(" ", "")
                        self.fn_p.emit(data.replace("file_p", ""))
                        client.send("file_p:".encode("utf-8"))
                if data and "file_a" in str(data):
                    if "?" in str(data):
                        client.send(("file_a " + str(self.parent.filename_A) + ":").encode("utf-8"))
                    else:
                        data = str(data, "utf-8").replace(" ", "")
                        self.fn_a.emit(data.replace("file_a", ""))
                        client.send("file_a:".encode("utf-8"))
                if data and "toggle" in str(data):
                    if "?" in str(data):
                        client.send(("toggle " + str(self.parent.running) + ":").encode("utf-8"))
                    elif "0" in str(data):
                        self.toggle.emit(0)
                        client.send("toggle0:".encode("utf-8"))
                    elif "1" in str(data):
                        self.toggle.emit(1)
                        client.send("toggle1:".encode("utf-8"))
                    elif "2" in str(data):
                        self.toggle.emit(2)
                        client.send("toggle2:".encode("utf-8"))
                    elif "3" in str(data):
                        self.toggle.emit(3)
                        client.send("toggle3:".encode("utf-8"))
                    else:
                        self.toggle.emit(-1)
                        client.send("toggle:".encode("utf-8"))
                if data and "exit" in str(data):
                    raise Exception("Client disconnected")
                # else:
                #    client.send("?".encode('utf-8'))
                #    return True
                #    raise Exception('Client disconnected')
                # client.shutdown(socket.SHUT_RDWR)
                # client.close()
                # return True
            except BaseException:
                # client.shutdown(socket.SHUT_RDWR)
                import traceback

                traceback.print_exc()
                client.close()
                return False


class Flippr:
    """Main window implementation

    The class functionality can be broadly split into three components: UI, TCPIP server,
    and DAQmx tasks. The UI is bog standard Qt interface stuff, the TCPIP server is
    itself documented above and then run inside a QThread, see

        https://mayaposch.wordpress.com/2011/11/01/how-to-really-truly-use-qthreads-the-full-explanation/,

    and the DAQmx tasks are started / stopped by calling onoff() alongside a simple state
    flag that tracks if the flipper is currently on or off. See DAQTasks.py for detail
    on the functionality of each task.

    When this window is closed, both analog output channels of the DAQ card will be
    zeroed.
    """

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        super(Flippr, self).setupUi(self)

        # Quick botch to implement matplotlib widget, saves me bothering to make an actual
        # Qt widget for this.
        self.pulseOutput_P = QPlot(self, xlabel="Sample", ylabel="Amplitude")
        self.pulseOutput_P.setGeometry(QtCore.QRect(422, 9, 200, 190))
        self.pulseOutput_P.setObjectName("pulseOutput_P")

        self.pulseOutput_A = QPlot(self, xlabel="Sample", ylabel="Amplitude")
        self.pulseOutput_A.setGeometry(QtCore.QRect(422, 200, 200, 200))
        self.pulseOutput_A.setObjectName("pulseOutput_A")

        self.interrupted = 0
        self.running = (
            0  # Important state flag, 0 = both flippers off, 1 = P flipper on, 2 = A flipper on,
        )
        # 3 = Both flippers on. This should ONLY be adjusted by the onoff() function
        self.running_previous = (
            0  # Flag to remember the previous state of running prior to turn off
        )

        # Waveform filename, no file if filename=""
        self.filename_P = ""
        self.filename_A = ""
        self.init_tasks()  # to initialise tasks

        self.P_flipper_button.setChecked(False)
        self.P_flipper_button.clicked[bool].connect(
            lambda pressed: self.toggle_button(pressed, flipper=1)
        )

        self.A_flipper_Button.setChecked(False)
        self.A_flipper_Button.clicked[bool].connect(
            lambda pressed: self.toggle_button(pressed, flipper=2)
        )

        # Set up TCPIP server to recieve OpenGENIE commands
        self.server = SignalServer("", 80, self)
        self.serverThread = QtCore.QThread()
        self.server.moveToThread(self.serverThread)

        self.server.toggle.connect(self.toggle)  # need to double up for two flippers
        self.server.comp_p.connect(lambda amp: self.compensate(amp=amp, flipper="p"))
        self.server.comp_a.connect(lambda amp: self.compensate(amp=amp, flipper="a"))
        self.server.amp_p.connect(lambda amp: self.amplitude(amp=amp, flipper="p"))
        self.server.amp_a.connect(lambda amp: self.amplitude(amp=amp, flipper="a"))
        self.server.const_p.connect(lambda amp: self.const(amp=amp, flipper="p"))
        self.server.const_a.connect(lambda amp: self.const(amp=amp, flipper="a"))
        self.server.dt_p.connect(lambda amp: self.DeltaT(amp=amp, flipper="p"))
        self.server.dt_a.connect(lambda amp: self.DeltaT(amp=amp, flipper="a"))
        self.server.fn_p.connect(lambda amp: self.fn(filename=amp, flipper="p"))
        self.server.fn_a.connect(lambda amp: self.fn(filename=amp, flipper="a"))

        self.serverThread.started.connect(self.server.listen)
        self.serverThread.start()

        # We use ReadbackTask() to monitor if the beam drops. As we write 'amplitude' at the end
        # of our waveforms, we would default to constant, high current when the timing signal cuts.
        #
        # The following timer in addition to the 'EveryNCallback' in ReadbackTask() keeps track of
        # how long since the last timing signal fired. If it's greater than 5 seconds, we interrupt.
        # When this interval again drops below 5 seconds (i.e. as soon as the beam comes back) we start
        # flipping again.

        self.rtask = ReadbackTask()  # Read task for diagnostics
        self.rtask.StartTask()

        self.timeoutClock = QtCore.QTimer(self)
        self.timeoutClock.setInterval(1000)

        def timeout():
            t = time()
            # flipperstate = self.running

            if (self.running == 1 or 2 or 3) and (np.abs(t - self.rtask.time) > 5):
                if self.running_previous == 0:
                    self.running_previous = self.running
                self.off()
                self.interrupted = 1
                print(
                    "Chopper/SMP signal interrupted, check signal cable (AFPI0) or beam status: FLIPPERS OFF"
                )

            if (
                (self.running == 0)
                and (self.interrupted == 1)
                and (np.abs(t - self.rtask.time) < 5)
            ):
                self.on(self.running_previous)
                self.interrupted = 0
                self.running_previous = 0
                print("Chopper/SMP signal state: CONNECTED")

        self.timeoutClock.timeout.connect(timeout)
        self.timeoutClock.start()

    def toggle_button(self, pressed, flipper):
        if pressed:
            if self.running == 0:
                print("button pressed", self.running)
                self.on(flipper)
            elif self.running == 3:
                self.off()
                self.on(flipper)
            else:
                self.off()
                print("toggle button pressed else")
                self.on(3)  # if other flipper is already running then turn both on
        else:
            if self.running == 3:
                self.off()
                if flipper == 1:
                    self.on(2)
                elif flipper == 2:
                    self.on(1)
            else:
                self.off()

    ##########################
    # OpenGENIE signal slots #
    ##########################

    def fn(self, flipper, filename):
        """Sets the filename to read waveform from"""
        turnbackon = "off"  # initialises the parameter to a known state
        if flipper == "p":
            if self.filename_P != filename:
                self.filename_P = filename
                turnbackon = 0

        if flipper == "a":
            if self.filename_A != filename:
                self.filename_A = filename
                turnbackon = 0

        if (self.running == 1 or 2 or 3) and (turnbackon == 0):
            turnbackon = self.running
            self.off()
            print("turnbackon value", turnbackon)
            if flipper == "p":
                self.filename_lineedit_P.setText(filename)
            elif flipper == "a":
                self.filename_lineedit_A.setText(filename)
            if turnbackon != 0:
                print("turning flipper(s) back on")
                self.on(turnbackon)

    def toggle(self, flag):
        """Currently just a wrapper for on() and off(), kept for future"""
        if self.running != 0:
            self.off()
        if flag == 1:  # P flipper on 10
            self.on(1)
        elif flag == 2:  # A flipper on 01
            self.on(2)
        elif flag == 3:  # both flippers on 11
            self.on(3)
        elif flag == 0:
            self.off()
        else:
            self.off()

    def const(self, flipper, amp):
        """Adjusts the decay constant for the flipper current"""
        turnbackon = "off"  # initialises the parameter to a known state
        if flipper == "p":
            if self.decay_spin_P.value() != amp:
                turnbackon = 0

        if flipper == "a":
            if self.decay_spin_A.value() != amp:
                turnbackon = 0

        if (self.running == 1 or 2 or 3) and (turnbackon == 0):
            turnbackon = self.running
            self.off()
            if flipper == "a":
                self.decay_spin_A.setValue(amp)
            elif flipper == "p":
                self.decay_spin_P.setValue(amp)
            if turnbackon != 0:
                self.on(turnbackon)

    def DeltaT(self, flipper, amp):
        """Adjusts the dc time shift for the flipper profile"""
        turnbackon = "off"  # initialises the parameter to a known state
        if flipper == "p":
            if self.DeltaT_P.value() != amp:
                turnbackon = 0

        if flipper == "a":
            if self.DeltaT_A.value() != amp:
                turnbackon = 0

        if (self.running == 1 or 2 or 3) and (turnbackon == 0):
            turnbackon = self.running
            self.off()
            if flipper == "a":
                self.DeltaT_A.setValue(amp)
            elif flipper == "p":
                self.DeltaT_P.setValue(amp)
            if turnbackon != 0:
                self.on(turnbackon)

    def amplitude(self, flipper, amp):
        """Adjusts the maximum allowed amplitude for the flipper current"""
        turnbackon = "off"  # initialises the parameter to a known state
        if flipper == "p":
            if self.amplitude_spin_P.value() != amp:
                turnbackon = 0

        if flipper == "a":
            if self.amplitude_spin_A.value() != amp:
                turnbackon = 0
                print("Sent amp_a ", self.amplitude_spin_A.value())

        if (self.running == 1 or 2 or 3) and (turnbackon == 0):
            turnbackon = self.running
            self.off()
            if flipper == "a":
                self.amplitude_spin_A.setValue(amp)
                print("New amp_a ", self.amplitude_spin_A.value())
            elif flipper == "p":
                self.amplitude_spin_P.setValue(amp)
            if turnbackon != 0:
                self.on(turnbackon)

    def compensate(self, amp, flipper):
        """Adjusts the compensation current"""
        turnbackon = "off"  # initialises the parameter to a known state
        if flipper == "p":
            if self.comp_spin_P.value() != amp:
                turnbackon = 0

        if flipper == "a":
            if self.comp_spin_A.value() != amp:
                turnbackon = 0

        if (self.running == 1 or 2 or 3) and (turnbackon == 0):
            turnbackon = self.running
            self.off()

            if flipper == "a":
                self.comp_spin_A.setValue(amp)
            elif flipper == "p":
                self.comp_spin_P.setValue(amp)
            if turnbackon != 0:
                self.on(turnbackon)

    # filename_P=""
    # filename_A=""
    ##########################
    def init_tasks(self):
        self.cmptask_P = CompensationTask(self.comp_spin_P.value(), "ao0")
        self.cmptask_P.StartTask()
        self.cmptask_P.ClearTask()
        # self.cmptask_A = CompensationTask(self.comp_spin.value(),'ao2')
        self.atask_P = AnalogTask(
            [self.decay_spin_P.value()],
            [self.amplitude_spin_P.value()],
            ["Dev1/ao1"],
            [self.DeltaT_P.value()],
            [self.filename_P],
        )  # Analog signal output
        self.atask_P.StartTask()
        self.atask_P.ClearTask()

        self.atask_A = AnalogTask(
            [self.decay_spin_A.value()],
            [self.amplitude_spin_A.value()],
            ["Dev1/ao3"],
            [self.DeltaT_A.value()],
            [self.filename_A],
        )
        self.atask_A.StartTask()
        self.atask_A.ClearTask()

        # self.running = 2

        ZeroOutput()

    # flipperstate,running
    def on(
        self, flipperstate
    ):  # AJC 5/11/2018 altered all functions to be generic such that only at the global call of the function is the flipper decided
        if self.running != flipperstate:
            print("turn on flippers")
            # ZeroOutput()

            ############################
            # Set up compensation coil #
            ############################

            # self.cmptask_P.StartTask()
            # self.cmptask_P.ClearTask()
            # self.cmptask_A.StartTask()
            # self.cmptask_A.ClearTask()

            ##################################
            # Start triggering flipping coil #
            ##################################

            if flipperstate == 1:
                # self.on_button.toggle()
                self.cmptask_P = CompensationTask(self.comp_spin_P.value(), "ao0")
                self.cmptask_P.StartTask()
                self.cmptask_P.ClearTask()
                self.atask_P = AnalogTask(
                    [self.decay_spin_P.value()],
                    [self.amplitude_spin_P.value()],
                    ["Dev1/ao1"],
                    [self.DeltaT_P.value()],
                    [self.filename_P],
                )  # Analog signal output

                self.atask_P.StartTask()
                # self.atask_P.ClearTask()

                self.running_indicator.setText("RUNNING")
                self.flipper_indicator.setText("Flipper State: 10")

                self.pulseOutput_P.plot_figure(
                    np.arange(len(self.atask_P.write_list[0])), self.atask_P.write_list[0]
                )

                self.running = 1

            elif flipperstate == 2:
                self.cmptask_A = CompensationTask(self.comp_spin_A.value(), "ao2")
                self.cmptask_A.StartTask()
                self.cmptask_A.ClearTask()

                self.atask_A = AnalogTask(
                    [self.decay_spin_A.value()],
                    [self.amplitude_spin_A.value()],
                    ["Dev1/ao3"],
                    [self.DeltaT_A.value()],
                    [self.filename_A],
                )
                self.atask_A.StartTask()

                self.running_indicator.setText("RUNNING")
                self.flipper_indicator.setText("Flipper State: 01")

                self.pulseOutput_A.plot_figure(
                    np.arange(len(self.atask_A.write_list[0])),
                    self.atask_A.write_list[0],
                    format="b-",
                )

                self.running = 2

            elif flipperstate == 3:
                self.cmptask_P = CompensationTask(self.comp_spin_P.value(), "ao0")
                self.cmptask_P.StartTask()
                self.cmptask_P.ClearTask()

                self.cmptask_A = CompensationTask(self.comp_spin_A.value(), "ao2")
                self.cmptask_A.StartTask()
                self.cmptask_A.ClearTask()

                self.atask_AP = AnalogTask(
                    [self.decay_spin_P.value(), self.decay_spin_A.value()],
                    [self.amplitude_spin_P.value(), self.amplitude_spin_A.value()],
                    ["Dev1/ao1", "Dev1/ao3"],
                    [self.DeltaT_P.value(), self.DeltaT_A.value()],
                    [self.filename_P, self.filename_A],
                )
                self.atask_AP.StartTask()
                # self.atask_P.StopTask()

                # self.atask_A = AnalogTask(self.decay_spin_A.value(),
                #               self.amplitude_spin_A.value(),
                #                  'ao3',
                #                 self.filename_A)
                # self.atask_A.StartTask()
                # self.atask_A.ClearTask()
                # Will make a list of const and amp values which will return a list of self.writeP,self.writeA
                self.pulseOutput_P.plot_figure(
                    np.arange(len(self.atask_AP.write_list[0])), self.atask_AP.write_list[0]
                )
                self.pulseOutput_A.plot_figure(
                    np.arange(len(self.atask_AP.write_list[1])),
                    self.atask_AP.write_list[1],
                    format="b-",
                )
                self.running_indicator.setText("RUNNING")
                self.flipper_indicator.setText("Flipper State: 11")

                self.running = 3
            #########################################
            # Hook up some purely cosmetic UI stuff #
            #########################################

        else:
            pass

    def off(self):  # need a clear plot command so it is more obvious which flipper is on.
        print("off() function call, running state: ", self.running)
        # self.on_button.toggle()
        if self.running != 0:
            if self.running == 1:
                self.atask_P.ClearTask()
            elif self.running == 2:
                self.atask_A.ClearTask()
                print("task cleared")
            elif self.running == 3:
                self.atask_AP.ClearTask()

            self.running_indicator.setText("FLIPPERS OFF")
            self.flipper_indicator.setText("Flipper State: 00")

            print("text set")
            ZeroOutput()
            print("output zeroed")
            self.running = 0
            print("running set to 0")
            return
        else:
            pass
            # return

    """def onoff(self):
        if self.running == 0:
            ############################
            # Set up compensation coil #
            ############################

            self.cmptask = CompensationTask(self.comp_spin.value())

            self.cmptask.StartTask()
            self.cmptask.ClearTask()

            ##################################
            # Start triggering flipping coil #
            ##################################

            self.atask = AnalogTask(self.decay_spin.value(),
                                    self.amplitude_spin.value(),
                                    self.filename)    # Analog signal output

            self.pulseOutput.plot_figure(
                np.arange(len(self.atask.write)), self.atask.write)

            self.atask.StartTask()
            
            #########################################
            # Hook up some purely cosmetic UI stuff #
            #########################################

            self.running_indicator.setText("RUNNING")

            self.running = 1
        else:
            self.atask.ClearTask()

            self.running_indicator.setText("NOT RUNNING")

            ZeroOutput()

            self.running = 0"""


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    aw = Flippr()

    aw.show()
    app.aboutToQuit.connect(ZeroOutput)  # Make sure current is always zeroed when we exit
    sys.exit(app.exec_())
