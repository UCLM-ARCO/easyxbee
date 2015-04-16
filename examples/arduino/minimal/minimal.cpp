// -*- mode: c++; coding: utf-8 -*-

#include <Arduino.h>
#include <SoftwareSerial.h>
#include "EasyXBee.h"

#define OK   do { _(" OK\n"); } while(0);
#define FAIL do { _(" FAILED\n"); while(1); } while(0);

EasyXBee xb;
SoftwareSerial logger(2, 3); // Rx, Tx

void
_(const char* message) {
    logger.write(message);
    logger.flush();
}

void
setup() {
    logger.begin(9600);
    xb.begin(9600);
    _("--------------------\n");

    const char* panid = "pan";

    _(" - setting panid...");
    if (not xb.set_pan_id((uint8_t*)panid, strlen(panid)))
	FAIL; OK;

    _(" - waiting until ready...");
    xb.wait_until_ready(); OK;
}


void
loop() {
    logger.write("loop:\n");
    while(1);
}
