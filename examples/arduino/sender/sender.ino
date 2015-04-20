// -*- mode: c++; coding: utf-8 -*-

// FIXME: including XBee.h here is a hack to fix a problem on Arduino
// IDE. The problem is that a library could not use other libraries,
// because the library path is dinamically generated from the main
// sketch's includes. For more information, see http://goo.gl/EpFSw
#include <XBee.h>

#include <SoftwareSerial.h>
#include <EasyXBee.h>

#define LED 13
EasyXBee exbee;
SoftwareSerial logger(2, 3); // Rx, Tx

XBeeAddress64 addr64;
uint16_t addr16;

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
    logger.begin(9600);
    exbee.begin(9600);

    char* panid = "pan";
    char* name = "server";

    // join a pan
    logger.write("\n\nchanging pan id... ");
    logger.flush();
    if (not exbee.set_pan_id((uint8_t*)panid, strlen(panid))) {
    	logger.write("\n -- exbee.set_pan_id() FAILED\n");
    	digitalWrite(LED, HIGH);
    	while(true);
    }
    logger.write("OK\n");

    // wait until ready
    logger.write("wait for joining network... ");
    logger.flush();
    exbee.wait_until_ready();
    flash_led(3, 50);
    logger.write("OK\n");

    // resolve the name of the other peer...
    logger.write("resolve destination... ");
    logger.flush();
    if (not exbee.lookup((uint8_t*)name, strlen(name), &addr64, &addr16)) {
    	logger.write("\n -- exbee.lookup() FAILED\n");
      	digitalWrite(LED, HIGH);
 	while(true);
    }

    // print 64-bit address of resolved node
    {
	logger.write("\n -- addr64: ");
	uint32_t msb = addr64.getMsb();
	uint32_t lsb = addr64.getLsb();
	uint8_t aux;
	for (int i=0; i<4; i++) {
	    aux = *(((uint8_t*)&msb) + i);
	    logger.print((int)aux, HEX);
	    logger.write(" ");
	}
	for (int i=0; i<4; i++) {
	    aux = *(((uint8_t*)&lsb) + i);
	    logger.print((int)aux, HEX);
	    logger.write(" ");
	}
    }

    // print 16-bit address of resolved node
    {
	logger.write(", -- addr16: ");
	uint8_t aux;
	for (int i=0; i<2; i++) {
	    aux = *(((uint8_t*)&addr16) + i);
	    logger.print((int)aux, HEX);
	    logger.write(" ");
	}
    }

    logger.write(" -> OK\n");
    logger.write("setup() done\n\n");
}

void
loop() {
    uint8_t data[]  = "Hello World!\n";

    logger.write("sending data... ");
    logger.flush();

    if (not exbee.send(addr64, 0, data, 14)) {
    	logger.write("\n -- exbee.send() FAILED\n");
    	digitalWrite(LED, HIGH);
    	while(true);
    }
    logger.write("OK\n");

    flash_led(1, 50);
    delay(1000);
}
