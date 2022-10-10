SparkFun Artemis Firmware Uploader GUI
========================================

![Artemis Firmware Uploader GUI](https://cdn.sparkfun.com/assets/home_page_posts/3/1/2/3/Artemis-GUI-v2.jpg)

The Artemis Firmware Uploader (AFU) is a simple to use GUI for updating firmware and the bootloader on Artemis based products.

## Installation
To use the compiled binaries for the supported platforms, use the binaries that are part of the latest release. 

### Windows
* Download the release zip file - ArtemisUploader.win.zip
* Unzip the application file - ArtemisUploader.exe
* Double click ArtemisUploader.exe to start the application

### macOS
* Download the release dmg file - ArtemisUploader.dmg
* Double click ArtemisUpaloder.dmg to mount the disk image. A Finder window with the image contents is shown
* Copy the ArtemisUploader.app application file to the desired locatoin (Often /Applications)
* Unmount the Artemis Uploader disk image
* Double click ArtemisUploader.app to launch the app
* Since this application isn't signed, exeuction must be approved in "System Preferences" > "Security & Privacy". In the "General" section, the application should be listed. Select the "Run Anyway" option to launch ArtemisUploader.app. 

### Linux
* Download the release  file - ArtemisUploader.linux.gz
* At a command line, uncompress the file.  $ gunzip ./ArtemisUploader.linux.gz
* Give the binary execute permissions:  $ chmod 755 ./ArtemisUploader
* Run the application: $ ./ArtemisUploader.


### TODO
* RPi
* Python Package

## Using the Artemis Uploader
  
  
* Click ```Browse``` and select the firmware file you'd like to upload (should end in *.bin*)
* Attach the Artemis target board over USB
* Select the COM port (click ```Refresh``` to refresh the list of USB devices)
* For the [SparkFun Edge](https://www.sparkfun.com/products/15170): click the ```Board Type``` menu and select ```Apollo3```
* Click ```Upload Firmware```

The GUI does take a few seconds to load and run. _**Don't Panic**_ if the GUI does not start right away.

Be sure you are loading firmware for your board or product. While it's unlikely to damage Artemis by loading incorrect firmware it will erase the pre-existing firmware and may lead to the peripherals being controlled incorrectly.

An example *Blink.bin* firmware file is included in the repo. This firmware will cause these LEDs to blink at 1Hz:
* the D5 LED on the [SparkFun RedBoard Artemis ATP](https://www.sparkfun.com/products/15442)
* the D13 LED on the [SparkFun RedBoard Artemis](https://www.sparkfun.com/products/15444)
* the D18 LED on the [SparkFun Thing Plus - Artemis](https://www.sparkfun.com/products/15574)
* the D19 LED on the [SparkFun RedBoard Artemis Nano](https://www.sparkfun.com/products/15443)
* the Green LED on the [SparkFun Edge Development Board - Apollo3 Blue](https://www.sparkfun.com/products/15170)
* the STAT LED on the [OpenLog Artemis](https://www.sparkfun.com/products/15846)
* the D19 and GNSS LEDs on the [Artemis Global Tracker](https://www.sparkfun.com/products/16469)

Clicking ```Update Bootloader``` will erase all firmware on the Artemis and load the latest bootloader firmware. This is handy when SparkFun releases updates to the [SVL](https://github.com/sparkfun/SparkFun_Apollo3_AmbiqSuite_BSPs/blob/master/common/examples/artemis_svl/src/main.c).

SparkFun labored with love to create this code. Feel like supporting open source hardware?
Buy a [breakout board](https://www.sparkfun.com/products/15444) from SparkFun!

Repository Contents
-------------------

* **/tools** contains the python source files and SVL binary
* **/Raspberry_Pi__Debian** contains an executable for Raspberry Pi 4 (Debian Buster)
* **LICENSE.md** contains the licence information

