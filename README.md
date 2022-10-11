SparkFun Artemis Uploader App
========================================

![macOS Artemis Uploader](images/artemis-uploader-banner.png)

The Artemis Uploader App is a simple, easy to use method for updating the firmware and bootloader on SparkFun Artemis based products. Available on all major platforms, as well as a Python package, the Artemis Uploader App simplifies working with SparkFun Artemis. 

## Installation
Installation binaries are available for all major platforms (macOS, Window, and Linux) on the release page of the Artemis Uploader App github repository. 

[Artemis Uploader Release Page](https://github.com/sparkfun/Artemis-Firmware-Upload-GUI/releases)

### Windows
* Download the github release zip file - *ArtemisUploader.win.zip.zip*
* Unzip the release file - *ArtemisUploader.zip*
* This results in the application executable, *ArtemisUploader.exe*
* Double-click *ArtemisUploader.ext to start the application

![macOS Artemis Uploader](images/artemis-windows.png)

### macOS
* Download the release file - *ArtemisUploader.dmg.zip* from product release page
* Double click on the file to unzip the file to *ArtemisUploader.dmg*
* Double click the ArtemisUploader.dmg file to mount the disk image. 
* The following Finder window, with the contents of the file will open

![Artemis Uploader macOS Finder](images/macos-finder.png)

* Install the *ArtemisUploader.app* by dragging it on the *Applications* in the ArtemisUploader Finder Window, or copying the file to a desired location.
* Once complete, unmount the ArtemisUploader disk image by right-clicking on the mounted disk in Finder and ejecting it.

To launch the Artemis Uploader application:
* Double-click ArtemisUploader.app to launch the application
* The ArtemisUploader.app isn't signed, so macOS won't run the application, and will display a warning dialog. Dismiss this dialog.
* To approve app execution bring up the macOS *System Preferences* and navigate to: *Security & Privacy > General*. 
* On this page, select the *Open Anyway* button to launch the ArtemisUploader application.


![macOS Security](images/macos-security.png)

* Once selected, macOS will present one last dialog. Select *Open* to run the application. The ArtemisUploader will now start.

![macOS Artemis Uploader](images/artemis-macos.png)

### Linux
* Download the github release zip file - *ArtemisUploader.linux.gz.zip*
* Unzip the release file - *ArtemisUploader.linux.gz*
* Un-gzip the file, either by double-clicking in on the desktop, or using the `gunzip` command in a terminal window. This results in the file *ArtemisUploader* 
* To run the application, the file must have *execute* permission. This is performed by selecting *Properties* from the file right-click menu, and then selecting permissions. You can also change permissions using the `chmod` command in a terminal window.
* Once the application has execute permission, you can start the application a terminal window. Change directory's to the application location and issue `./ArtemisUploader`

![Linux Artemis Uploader](images/artemis-Linux.png)


### Python Package
The Artemis Uploader App is also provided as an installable Python package. This is advantageous for platforms that lack a pre-compiled application. 

To install the Python package:
* Download the package file - *python-install-package.zip*
* Unzip the github release file. This results in the installable Python package file - *artemis_uploader-3.0.0.tar.gz* (note - the version number might vary)

At a command line - issue the package install command:

* `pip install artemis_uploader-3.0.0.tar.gz`
* Once installed, you can start the Artemis Uploader App by issuing the command `artemis_upload` at the command line. (To see the command, you might need to start a new terminal, or issue a command like `rehash` depending on your platform/shell)

Notes:
* A path might be needed to specify the install file location.
* Depending on your platform, this command might need to be run as admin/root.
* Depending on your system, you might need to use the command `pip3`

The uploader is uninstalled by issuing this pip command: 
* `pip uninstall artemis-uploader`

# Using the Artemis Uploader
  
## Upload Firmware
  
* Click ```Browse``` and select the firmware file you'd like to upload (should end in *.bin*)
* Attach the Artemis target board over USB
* Select the COM port from the dropdown menu
* Adjust the Baud Rate as desired
* Click the  ```Upload Firmware``` Button in the lower left of the app.

The selected firmware is then uploaded to the connected SparkFun Artemis product. Upload information and progress are displayed in the output portion of the interface. 

![Firmware Upload](images/firmware-upload.png)

## Update Bootloader

Clicking the ```Update Bootloader``` button on the lower left of the application will erase all firmware on the Artemis and load the latest bootloader firmware. This is helpful when SparkFun releases updates to the [SVL](https://github.com/sparkfun/SparkFun_Apollo3_AmbiqSuite_BSPs/blob/master/common/examples/artemis_svl/src/main.c).

![Bootloader Upload](images/bootloader-upload.png)


### Example Firmware
I the applications github repo, n example *Blink.bin* firmware file is included in the repo. This firmware will cause these LEDs to blink at 1Hz:
* the D5 LED on the [SparkFun RedBoard Artemis ATP](https://www.sparkfun.com/products/15442)
* the D13 LED on the [SparkFun RedBoard Artemis](https://www.sparkfun.com/products/15444)
* the D18 LED on the [SparkFun Thing Plus - Artemis](https://www.sparkfun.com/products/15574)
* the D19 LED on the [SparkFun RedBoard Artemis Nano](https://www.sparkfun.com/products/15443)
* the Green LED on the [SparkFun Edge Development Board - Apollo3 Blue](https://www.sparkfun.com/products/15170)
* the STAT LED on the [OpenLog Artemis](https://www.sparkfun.com/products/15846)
* the D19 and GNSS LEDs on the [Artemis Global Tracker](https://www.sparkfun.com/products/16469)





