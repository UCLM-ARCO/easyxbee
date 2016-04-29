To use Python version of EasyXBee, you will need to install the xbee
module for Python. From now, it is only available using pip (altough it 
will be installed along the easyxbee Debian package):

    $ sudo pip install xbee

You may add a link to the library on your 'libraries' path:
  
    $ ln -s /usr/share/arduino/libraries/EasyXBee/ $HOME/Arduino/libraries

Important Notes
---------------

* If using _xbee-arduino_ (or _EasyXBee_ on Arduino), your firmware
  must be in **API mode**, and level of API (ATAP parameter) **must be
  2**.

* If using _python-xbee_ (or _EasyXBee_ on Python), your firmware must
  be in **API mode**, and level of API (ATAP parameter) **must be 1**
  (note the difference!!).

* Initialize your XBee on Arduino like this (otherwise, it may not work):

    Serial.begin(9600);
    xbee.setSerial(Serial);