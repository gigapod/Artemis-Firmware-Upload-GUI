"""
This is a simple firmware upload GUI designed for the Artemis platform.
Very handy for updating devices in the field without the need for compiling
and uploading through Arduino.

This is the "integrated" version which includes code from both ambiq_bin2board.py and artemis_svl.py

If you are building with a new version of artemis_svl.bin, remember to update BOOTLOADER_VERSION below.

Based on gist by Stefan Lehmann: https://gist.github.com/stlehmann/bea49796ad47b1e7f658ddde9620dff1

MIT license

Pyinstaller:
Windows:
pyinstaller --onefile --noconsole --distpath=. --icon=artemis_firmware_uploader_gui.ico --add-data="artemis_svl.bin;." --add-data="Artemis-Logo-Rounded.png;." artemis_firmware_uploader_gui.py
Linux:
pyinstaller --onefile --noconsole --distpath=. --icon=artemis_firmware_uploader_gui.ico --add-data="artemis_svl.bin:." --add-data="Artemis-Logo-Rounded.png:." artemis_firmware_uploader_gui.py

Pyinstaller needs:
artemis_firmware_uploader_gui.py (this file!)
artemis_firmware_uploader_gui.ico (icon file for the .exe)
Artemis-Logo-Rounded.png (icon for the GUI widget)
artemis_svl.bin (the bootloader binary)

"""

# Immediately upon reset the Artemis module will search for the timing character
#   to auto-detect the baud rate. If a valid baud rate is found the Artemis will
#   respond with the bootloader version packet
# If the computer receives a well-formatted version number packet at the desired
#   baud rate it will send a command to begin bootloading. The Artemis shall then
#   respond with the a command asking for the next frame.
# The host will then send a frame packet. If the CRC is OK the Artemis will write
#   that to memory and request the next frame. If the CRC fails the Artemis will
#   discard that data and send a request to re-send the previous frame.
# This cycle repeats until the Artemis receives a done command in place of the
#   requested frame data command.
# The initial baud rate determination must occur within some small timeout. Once
#   baud rate detection has completed all additional communication will have a
#   universal timeout value. Once the Artemis has begun requesting data it may no
#   no longer exit the bootloader. If the host detects a timeout at any point it
#   will stop bootloading.

# Notes about PySerial timeout:
# The timeout operates on whole functions - that is to say that a call to
#   ser.read(10) will return after ser.timeout, just as will ser.read(1) (assuming
#   that the necessary bytes were not found)
# If there are no incoming bytes (on the line or in the buffer) then two calls to
#   ser.read(n) will time out after 2*ser.timeout
# Incoming UART data is buffered behind the scenes, probably by the OS.

# Information about the firmware updater (taken from ambiq_bin2board.py):
#   This script performs the three main tasks:
#       1. Convert 'application.bin' to an OTA update blob
#       2. Convert the OTA blob into a wired update blob
#       3. Push the wired update blob into the Artemis module

from typing import Iterator, Tuple
from PyQt5.QtCore import QSettings, QProcess, QTimer, pyqtSignal, pyqtSlot, QObject, Qt
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QGridLayout, \
    QPushButton, QApplication, QLineEdit, QFileDialog, QPlainTextEdit, \
    QAction, QActionGroup, QMenu, QMenuBar, QMainWindow
from PyQt5.QtGui import QCloseEvent, QTextCursor, QIcon, QFont, QPixmap
from PyQt5.QtSerialPort import QSerialPortInfo
import sys
import time
import math
import os
import serial
from Crypto.Cipher import AES # pip install pycryptodome
import array
import hashlib
import hmac
import binascii
import os.path


# What version is this app (need something)
_APP_VERSION = "v2.1.0"
_APP_NAME = "Artemis Firmware Uploader"

#---------------------------------------------------------------------------------------
# resource_path()
#
# Get the runtime path of app resources. This changes depending on how the app is
# run -> locally, or via pyInstaller
#
#https://stackoverflow.com/a/50914550

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """

    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

#--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------
# AUxIOWedge
#
# Used to redirect/capture output chars from the print() function and redirect to our
# console. Allows the use of command line routines in this GUI app


from io import TextIOWrapper, BytesIO
from contextlib import redirect_stdout, redirect_stderr

class AUxIOWedge(TextIOWrapper):
    def __init__(self, output_funct, supress=False, newline="\n"):
        super(AUxIOWedge, self).__init__(BytesIO(),
                                        encoding="utf-8",
                                        errors="surrogatepass",
                                        newline=newline)

        self._output_func = output_funct
        self._supress = supress

    def write(self, buffer):

        # Just send buffer to our output console
        if not self._supress:
            self._output_func(buffer)

        return len(buffer)

#--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------
# Worker/threads
#
import artemis_svl
import queue

# Import the asb

import asb 
# determine the current GUI style (TODO: Is there another way to do this?)
import darkdetect
import platform
import tempfile

# Note: Not using QThread, but just standard python threading. QThread caused
# memory corruption issues on some platforms.
from threading import Thread

import ax_actions

#--------------------------------------------------------------------------------------
# Move upload to a thread, jobs passed in via a queue

# define a worker class/thread

class AUxUploadWorker(QObject):

    # define signals to communicate with the GUI

    sig_message     = pyqtSignal(str)
    sig_finished    = pyqtSignal(int)

    def __init__(self, theQueue):

        QObject.__init__(self)

        self._queue = theQueue

        self._shutdown = False;

    def __del__(self):

        self._shutdown = True

    def shutdown(self):

        self._shutdown = True

    #------------------------------------------------------
    # call back function for output from the bootloader - called from our IO wedge class.
    #
    def message_callback(self, message):

        # relay/post message to the GUI's console - sent via a signal,
        # which is thread safe.
        self.sig_message.emit(message)

    #------------------------------------------------------
    # Job dispatcher. Job is a dict.
    def dispatch_job(self, job):

        # make sure we have a job
        if type(job) != ax_actions.AxJob:
            self.message_callback("ERROR - invalid job dispatched\n")
            return 1

        # Check job type, run desired command
        if job.action_id == 'firmware':

            # Use an IO class to redirect the output of Print() to our
            # console  during this call

            with redirect_stdout(AUxIOWedge(self.message_callback)):
                with redirect_stderr(AUxIOWedge(self.message_callback, supress=True)):
                    artemis_svl.upload_firmware(job.file, job.port, job.baud)

            return 0

        elif job.action_id == 'bootloader':
            # >> TODO - 
            # AND -> Move this and firmware job action to seperate "action classes"
            #      that make this generic
            #
            # fake command line args - since the apollo3 bootloader command will use
            # argparse 
            sys.argv = [resource_path('./asb/asb.py'), \
                    "--bin", job.file, \
                    "-port", job.port, \
                    "-b", str(job.baud), \
                    "-o", tempfile.gettempdir(), \
                    "--load-address-blob", "0x20000", \
                    "--magic-num", "0xCB", \
                    "--version", "0x0", \
                    "--load-address-wired", "0xC000", \
                    "-i", "6", \
                    "-clean", "1" ]

            status = 1 
            # Use an IO class to redirect the output of Print() to our
            # console  during this call
            with redirect_stdout(AUxIOWedge(self.message_callback)):
                with redirect_stderr(AUxIOWedge(self.message_callback, supress=True)):
                    # catch any call to exit() in the apollo3 bootloader command
                    try:
                        # Call the ambiq command
                        asb.main()
                        status = 0 
                    except SystemExit as  error:
                        print("Error executing bootloader upload command.")

                        status = 1 

               
            return status
        else:
            self.message_callback("Unknown job type. Aborting\n")
            return 1

        return 0

    #------------------------------------------------------
    # The thread processing loop
    def process_loop(self):

        # Wait on jobs .. forever

        self._shutdown = False

        # run
        while not self._shutdown:

            if self._queue.empty():
                time.sleep(1)
            else:
                job = self._queue.get()

                status = self.dispatch_job(job)

                self.sig_finished.emit(status)

    #------------------------------------------------------
    # Called to start job processing
    def start(self):

        # throw the work/job into a thread
        self._th_process = Thread(target = self.process_loop)
        self._th_process.start()

#----------------------------------------------------------------
# hack to know when a combobox menu is being shown. Helpful if contents
# of list are dynamic -- like serial ports.
class AUxComboBox(QComboBox):

    popupAboutToBeShown = pyqtSignal()

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super().showPopup()

#----------------------------------------------------------------
# ux_is_darkmode()
#
# Helpful function used during setup to determine if the Ux is in 
# dark mode
_is_darkmode = None
def ux_is_darkmode() -> bool:
    global _is_darkmode

    if _is_darkmode != None:
        return _is_darkmode

    osName = platform.system()

    if osName == "Darwin":
        _is_darkmode = darkdetect.isDark()

    elif osName == "Windows":
        # it appears that the Qt interface on Windows doesn't apply DarkMode
        # So, just keep it light
        _is_darkmode = False
    elif osName == "Linux":
        # Need to check this on Linux at some pont
        _is_darkmod = False

    else: 
        _is_darkmode = False 

    return _is_darkmode

#--------------------------------------------------------------------------------------

BOOTLOADER_VERSION = 5 # << Change this to match the version of artemis_svl.bin

# Setting constants
SETTING_PORT_NAME = 'port_name'
SETTING_FILE_LOCATION = 'message'
SETTING_BAUD_RATE = '115200' # Default to 115200 for upload
SETTING_ARTEMIS = 'True' # Default to Artemis-based boards

def gen_serial_ports() -> Iterator[Tuple[str, str, str]]:
    """Return all available serial ports."""
    ports = QSerialPortInfo.availablePorts()
    return ((p.description(), p.portName(), p.systemLocation()) for p in ports)



# noinspection PyArgumentList

#---------------------------------------------------------------------------------------
class MainWindow(QMainWindow):
    """Main Window"""

    def __init__(self, parent: QMainWindow = None) -> None:
        super().__init__(parent)

        self.installed_bootloader = -1 # Use this to record the bootloader version

        # ///// START of code taken from ambiq_bin2board.py

        # Global Variables
        self.loadTries = 0 #If we fail, try again. Tracks the number of tries we've attempted
        self.loadSuccess = False
        self.blob2wiredfile = ''
        self.uploadbinfile = ''

        #
        self.appFile = 'artemis_svl.bin'    # --bin Bootloader binary file
        
        self.load_address_blob = 0xC000     # --load-address-wired  dest=loadaddress_blob   default=0x60000
        self.load_address_image = 0x20000   # --load-address-blob   dest=loadaddress_image  default=AM_SECBOOT_DEFAULT_NONSECURE_MAIN=0xC000
        self.magic_num = 0xCB       # --magic-num   Magic Num (AM_IMAGE_MAGIC_NONSECURE)
        

        # File location line edit
        msg_label = QLabel(self.tr('Firmware File:'))
        self.fileLocation_lineedit = QLineEdit()
        msg_label.setBuddy(self.fileLocation_lineedit)
        self.fileLocation_lineedit.setEnabled(False)
        self.fileLocation_lineedit.returnPressed.connect(
            self.on_browse_btn_pressed)

        # Browse for new file button
        browse_btn = QPushButton(self.tr('Browse'))
        browse_btn.setEnabled(True)
        browse_btn.pressed.connect(self.on_browse_btn_pressed)

        # Port Combobox
        port_label = QLabel(self.tr('COM Port:'))
        self.port_combobox = AUxComboBox()
        port_label.setBuddy(self.port_combobox)
        self.update_com_ports()
        self.port_combobox.popupAboutToBeShown.connect(self.on_port_combobox)


        # Baudrate Combobox
        baud_label = QLabel(self.tr('Baud Rate:'))
        self.baud_combobox = QComboBox()
        baud_label.setBuddy(self.baud_combobox)
        self.update_baud_rates()

        # Upload Button
        myFont=QFont()
        myFont.setBold(True)
        self.upload_btn = QPushButton(self.tr('  Upload Firmware  '))
        self.upload_btn.setFont(myFont)
        self.upload_btn.pressed.connect(self.on_upload_btn_pressed)

        # Upload Button
        self.updateBootloader_btn = QPushButton(self.tr(' Update Bootloader '))
        self.updateBootloader_btn.pressed.connect(self.on_update_bootloader_btn_pressed)

        # Messages Bar
        messages_label = QLabel(self.tr('Status / Warnings:'))

        # Messages/Console Window
        self.messages = QPlainTextEdit()
        color =  "C0C0C0" if ux_is_darkmode() else "424242"
        self.messages.setStyleSheet("QPlainTextEdit { color: #" + color + ";}")

        # Attempting to reduce window size
        #self.messages.setMinimumSize(1, 2)
        #self.messages.resize(1, 2)

        # Menu Bar
        menubar = self.menuBar()
        boardMenu = menubar.addMenu('Board Type')
        
        boardGroup = QActionGroup(self)

        self.artemis = QAction('Artemis', self, checkable=True)
        self.artemis.setStatusTip('Artemis-based boards including the OLA and AGT')
        self.artemis.setChecked(True) # Default to artemis
        a = boardGroup.addAction(self.artemis)
        boardMenu.addAction(a)
        
        self.apollo3 = QAction('Apollo3', self, checkable=True)
        self.apollo3.setStatusTip('Apollo3 Blue development boards including the SparkFun Edge')
        a = boardGroup.addAction(self.apollo3)
        boardMenu.addAction(a)

        # Add an artemis logo to the user interface
        logo = QLabel(self)
        icon = "artemis-icon.png" if ux_is_darkmode() else "artemis-icon-blk.png"
        pixmap = QPixmap(resource_path(icon))
        logo.setPixmap(pixmap)

        # Arrange Layout
        layout = QGridLayout()
        
        layout.addWidget(msg_label, 1, 0)
        layout.addWidget(self.fileLocation_lineedit, 1, 1)
        layout.addWidget(browse_btn, 1, 2)

        layout.addWidget(port_label, 2, 0)
        layout.addWidget(self.port_combobox, 2, 1)

        layout.addWidget(logo, 2,2, 2,3, alignment=Qt.AlignCenter)

        layout.addWidget(baud_label, 3, 0)
        layout.addWidget(self.baud_combobox, 3, 1)

        layout.addWidget(messages_label, 4, 0)
        layout.addWidget(self.messages, 5, 0, 5, 3)

        layout.addWidget(self.upload_btn, 15, 2)
        layout.addWidget(self.updateBootloader_btn, 15, 0)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)


        #self._clean_settings() # This will delete all existing settings! Use with caution!
        
        self._load_settings()

        # Make the text edit window read-only
        self.messages.setReadOnly(True)
        self.messages.clear()  # Clear the message window

        self.setWindowTitle( _APP_NAME + " - " + _APP_VERSION)

        # Initial Status Bar
        self.statusBar().showMessage(_APP_NAME + " - " + _APP_VERSION, 10000)



        #---------------------------------------------------
        # KDB testing -

        self._queue = queue.Queue()

        self._thread = AUxUploadWorker(self._queue)

        self._thread.sig_message.connect(self.addMessage)
        self._thread.sig_finished.connect(self.on_finished)

        self._thread.start()

    #--------------------------------------------------------------
    @pyqtSlot(str)
    def addMessage(self, msg: str) -> None:
        """Add msg to the messages window, ensuring that it is visible"""

        self.messages.moveCursor(QTextCursor.End)

        ## Backspace??
        tmp = msg
        while len(tmp) > 2 and tmp.startswith('\b'):
            tmp = tmp[1:]
            self.messages.textCursor().deletePreviousChar()
            self.messages.moveCursor(QTextCursor.End)

        self.messages.insertPlainText(tmp)

        self.messages.moveCursor(QTextCursor.End)
        self.messages.ensureCursorVisible()

        self.repaint() # Update/refresh the message window

    #--------------------------------------------------------------
    @pyqtSlot(int)
    def on_finished(self, status) -> None:

        self.disable_interface(False)
        msg = "successfully" if status == 0 else "with an error"
        self.statusBar().showMessage("The upload process finished " + msg, 2000)        

    #--------------------------------------------------------------
    @pyqtSlot()
    def on_port_combobox(self):
        self.statusBar().showMessage("Updating ports...", 500)
        self.update_com_ports()


    # end KDB
    #----------------------------------------------------------

    def _load_settings(self) -> None:
        """Load settings on startup."""
        settings = QSettings()

        port_name = settings.value(SETTING_PORT_NAME)
        if port_name is not None:
            index = self.port_combobox.findData(port_name)
            if index > -1:
                self.port_combobox.setCurrentIndex(index)

        lastFile = settings.value(SETTING_FILE_LOCATION)
        if lastFile is not None:
            self.fileLocation_lineedit.setText(lastFile)

        baud = settings.value(SETTING_BAUD_RATE)
        if baud is not None:
            index = self.baud_combobox.findData(baud)
            if index > -1:
                self.baud_combobox.setCurrentIndex(index)

        checked = settings.value(SETTING_ARTEMIS)
        if checked is not None:
            if (checked == 'True'):
                self.artemis.setChecked(True)
                self.apollo3.setChecked(False)
            else:
                self.artemis.setChecked(False)
                self.apollo3.setChecked(True)

    def _save_settings(self) -> None:
        """Save settings on shutdown."""
        settings = QSettings()
        settings.setValue(SETTING_PORT_NAME, self.port)
        settings.setValue(SETTING_FILE_LOCATION, self.fileLocation_lineedit.text())
        settings.setValue(SETTING_BAUD_RATE, self.baudRate)
        if (self.artemis.isChecked()): # Convert isChecked to str
            checkedStr = 'True'
        else:
            checkedStr = 'False'
        settings.setValue(SETTING_ARTEMIS, checkedStr)

    def _clean_settings(self) -> None:
        """Clean (remove) all existing settings."""
        settings = QSettings()
        settings.clear()

    def show_error_message(self, msg: str) -> None:
        """Show a Message Box with the error message."""
        QMessageBox.critical(self, QApplication.applicationName(), str(msg))

    def update_com_ports(self) -> None:
        """Update COM Port list in GUI."""
        previousPort = self.port # Record the previous port before we clear the combobox
        
        self.port_combobox.clear()

        index = 0
        indexOfCH340 = -1
        indexOfPrevious = -1
        for desc, name, sys in gen_serial_ports():

            longname = desc + " (" + name + ")"
            self.port_combobox.addItem(longname, sys)
            if("CH340" in longname):
                # Select the first available CH340
                # This is likely to only work on Windows. Linux port names are different.
                if (indexOfCH340 == -1):
                    indexOfCH340 = index
                    # it could be too early to call
                    #self.addMessage("CH340 found at index " + str(indexOfCH340))
                    # as the GUI might not exist yet
            if(sys == previousPort): # Previous port still exists so record it
                indexOfPrevious = index
            index = index + 1

        if indexOfPrevious > -1: # Restore the previous port if it still exists
            self.port_combobox.setCurrentIndex(indexOfPrevious)
        if indexOfCH340 > -1: # If we found a CH340, let that take priority
            self.port_combobox.setCurrentIndex(indexOfCH340)

    def update_baud_rates(self) -> None:
        """Update baud rate list in GUI."""
        # Lowest speed first so code defaults to that
        # if settings.value(SETTING_BAUD_RATE) is None
        self.baud_combobox.clear()
        self.baud_combobox.addItem("115200", 115200)
        self.baud_combobox.addItem("460800", 460800)
        self.baud_combobox.addItem("921600", 921600)

    @property
    def port(self) -> str:
        """Return the current serial port."""
        return self.port_combobox.currentData()

    @property
    def baudRate(self) -> str:
        """Return the current baud rate."""
        return self.baud_combobox.currentData()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle Close event of the Widget."""
        self._save_settings()

        self._thread.shutdown()

        event.accept()

    def disable_interface(self, bDisable=False):

        self.upload_btn.setDisabled(bDisable)
        self.updateBootloader_btn.setDisabled(bDisable)

    def on_upload_btn_pressed(self) -> None:
        """Check if port is available"""
        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.port):
                portAvailable = True
        if (portAvailable == False):
            self.addMessage("Port No Longer Available")
            return

        """Check if file exists"""
        fileExists = False
        try:
            f = open(self.fileLocation_lineedit.text())
            fileExists = True
        except IOError:
            fileExists = False
        finally:
            if (fileExists == False):
                self.addMessage("File Not Found")
                return
            f.close()

        # send a line break across the console - start of a new activity
        self.addMessage('_'*70)

        # Make up a job and add it to the job queue. The worker thread will pick this up and
        # process the job
        theJob = ax_actions.AxJob("firmware")
        theJob.port = self.port
        theJob.baud = self.baudRate
        theJob.file = self.fileLocation_lineedit.text()
        self._queue.put(theJob)

        self.disable_interface(True)

    def on_update_bootloader_btn_pressed(self) -> None:
        """Check if port is available"""
        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.port):
                portAvailable = True
        if (portAvailable == False):
            self.addMessage("Port No Longer Available")
            return

        """Check if file exists"""
        fileExists = False
        try:
            f = open(resource_path(self.appFile))
            fileExists = True
        except IOError:
            fileExists = False
        finally:
            if (fileExists == False):
                self.addMessage("Bootloader file Not Found")
                return
            f.close()

        self.addMessage("\nUpdating bootloader\n")

        # send a line break across the console - start of a new activity
        self.addMessage(('_'*70)+'\n')

        # Make up a job and add it to the job queue. The worker thread will pick this up and
        # process the job
        theJob = ax_actions.AxJob("bootloader")
        theJob.port = self.port
        theJob.baud = self.baudRate
        theJob.file = self.appFile
        self._queue.put(theJob)

        self.disable_interface(True)
        #self.update_main() # Call ambiq_bin2board.py (previously this spawned a QProcess)

    def on_browse_btn_pressed(self) -> None:
        """Open dialog to select bin file."""

        self.statusBar().showMessage("Select firmware file for upload...", 4000)
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            None,
            "Select Firmware to Upload",
            "",
            "Firmware Files (*.bin);;All Files (*)",
            options=options)
        if fileName:
            self.fileLocation_lineedit.setText(fileName)


   

if __name__ == '__main__':
    import sys
    app = QApplication([])
    app.setOrganizationName('SparkFun Electronics')
    app.setApplicationName(_APP_NAME + ' - ' + _APP_VERSION)
    app.setWindowIcon(QIcon(resource_path("Artemis-Logo-Rounded.png")))
    app.setApplicationVersion(_APP_VERSION)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
