// -*- mode: c++; coding: utf-8 -*-

// FIXME: including XBee.h here is a hack to fix a problem on Arduino
// IDE. The problem is that a library could not use other libraries,
// because the library path is dinamically generated from the main
// sketch's includes. For more information, see http://goo.gl/EpFSw
#include <XBee.h>

#include <EasyXBee.h>

#define LED 13
EasyXBee xbee;

void
flash_led(int times, int wait) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED, HIGH);
    delay(wait);
    digitalWrite(LED, LOW);

    if (i + 1 < times) {
      delay(wait);
    }
  }
}

void setup() {
    pinMode(LED, OUTPUT);

    xbee.begin(9600);
    xbee.wait_until_ready();

    flash_led(3, 50);
}

void loop() {
    uint8_t name[] = "receiver";
    uint8_t data[] = "Hello World!\n";
    XBeeAddress64 addr64;
    uint16_t addr16;

    // try to resolve the name of the other peer...
    if (not xbee.lookup(name, 7, &addr64, &addr16)) {

	// not resolved; fire LED and stops
      	digitalWrite(LED, HIGH);
 	while(true);
    }

    // try to send data...
    if (not xbee.send(addr64, addr16, data, 14)) {

	// could not send; fire LED and stops
	digitalWrite(LED, HIGH);
	while(true);
    }

    delay(1000);
}
