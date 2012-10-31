// -*- mode: c++; coding: utf-8 -*-

//
// Copyright (c) 2012 Oscar Aceña. All rights reserved.
//
// This file is part of EasyXBee.
//
// EasyXBee is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// EasyXBee is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with EasyXBee.  If not, see <http://www.gnu.org/licenses/>.
//


#include "easyxbee.h"

#define RESPONSE_TIMEOUT 1000  // in ms

//
// Wait until node is successfully joined to a network (i.e. AI
// responds with value 0). This will block until ready, and if it
// never happends, will block the execution forever.
//
void
EasyXBee::wait_until_ready() {
    uint8_t cmd[] = {'A', 'I'};
    AtCommandRequest request(cmd);
    AtCommandResponse response;

    request.setFrameId(get_next_frame_id());
    xbee.send(request);

    while (true) {
	if (xbee.readPacket(50)) {
	    xbee.getResponse().getAtCommandResponse(response);

	    if (response.isOk()
		&& response.getApiId() == AT_COMMAND_RESPONSE
		&& response.getFrameId() == request.getFrameId()
		&& response.getValue()[0] == SUCCESS) {

		return;
	    }

	    xbee.send(request);
	}
    }
}

//
// Try to read a Rx frame (non-blocking). If available, returns true
// and points 'data' to its content (no copy of data will be made, so
// if you call readPacket again, pointer data will be changed), and
// 'size' to its size. If no frame available, or frame is not a RX
// Frame, it will return false, whithout modifications to 'data' or
// 'size'.
//
bool
EasyXBee::receive(uint8_t** data, uint8_t* size) {
    ZBRxResponse response;

    xbee.readPacket();

    if (not xbee.getResponse().isAvailable()
	|| xbee.getResponse().getApiId() != ZB_RX_RESPONSE) {

	return false;
    }

    // assume zero-copy from original buffer
    xbee.getResponse().getZBRxResponse(response);
    *size = response.getDataLength();
    *data = response.getData();

    return true;
}

//
// This will try to send 'size' bytes from 'data' to destination
// specified on 'addr16' and 'addr64' (both address could be obtained
// using 'lookup()' method). It waits for a successfull delivery, and
// returns true. If delivery did not happend, or XBee module did not
// responds, it will return false.
//
bool
EasyXBee::send(XBeeAddress64& addr64, uint16_t* addr16, uint8_t* data, uint8_t size) {
    ZBTxRequest request(addr64, data, size);
    ZBTxStatusResponse response;

    request.setAddress16(*addr16);
    request.setFrameId(get_next_frame_id());
    xbee.send(request);

    while (true) {
 	if (xbee.readPacket(RESPONSE_TIMEOUT)) {
	    xbee.getResponse().getZBTxStatusResponse(response);

 	    if (response.isSuccess()
 		&& response.getApiId() == ZB_TX_STATUS_RESPONSE
 		&& response.getFrameId() == request.getFrameId()) {

 		return true;
 	    }
 	}

 	else {
 	    return false;
 	}
    }
}

//
// This performs a lookup over the network, to find the node which
// name is the given 'name' (ATDN command). If found, it will return
// true, and write its address on 'addr16' and 'addr64'). This will
// wait up to 'Node Discovery Timeout' seconds. If this timeout
// expires, and no responses is received, it will return false, and no
// modifications to params will be made.
//
bool
EasyXBee::lookup(uint8_t* name, uint8_t size, XBeeAddress64* addr64, uint16_t* addr16) {
    uint8_t cmd[] = {'D', 'N'};
    AtCommandRequest request(cmd, name, size);
    AtCommandResponse response;

    request.setFrameId(get_next_frame_id());
    xbee.send(request);

    while (true) {
	if (xbee.readPacket(NODE_DISCOVERY_TIMEOUT)) {
	    xbee.getResponse().getAtCommandResponse(response);

	    if (response.isOk()
		&& response.getApiId() == AT_COMMAND_RESPONSE
		&& response.getFrameId() == request.getFrameId()) {

		*addr16 = *((uint16_t*)response.getValue());
		addr64->setMsb(*((uint32_t*)(response.getValue() + 2)));
		addr64->setLsb(*((uint32_t*)(response.getValue() + 6)));

		return true;
	    }
	}

	else {
	    return false;
	}
    }
}

//
// This method will try to set the PAN identifier for this node (ATID
// command). If success, it will return true, and false otherwise. It
// is recommended to call 'wait_until_ready()' method after changing
// the PAN id, to assure that changes are effective.
//
bool
EasyXBee::set_pan_id(uint8_t* pan_id) {
    uint8_t cmd[] = {'I', 'D'};
    AtCommandRequest request(cmd, pan_id, 8);

    return send_and_check_at_command(request);
}

//
// This method will change the name of the node (ATNI command). This
// name is the same used with the 'lookup()' method. It must be of 20
// characters or less. It will return true if success, false
// otherwise.
//
bool
EasyXBee::set_name(uint8_t* name, uint8_t size) {
    uint8_t cmd[] = {'N', 'I'};
    AtCommandRequest request(cmd, name, size);

    return send_and_check_at_command(request);
}

//
// Helper method to send an AT Request command, and wait for
// response. If response is OK, return true. If not response is
// received from within RESPONSE_TIMEOUT, or response is not OK, it
// will return false.
//
bool
EasyXBee::send_and_check_at_command(AtCommandRequest& request) {
    AtCommandResponse response;

    request.setFrameId(get_next_frame_id());
    xbee.send(request);

    while (true) {
	if (xbee.readPacket(RESPONSE_TIMEOUT)) {
	    xbee.getResponse().getAtCommandResponse(response);

	    if (response.isOk()
		&& response.getApiId() == AT_COMMAND_RESPONSE
		&& response.getFrameId() == request.getFrameId()) {

		return true;
	    }
	}

	else {
	    return false;
	}
    }
}

//
// If frame_id is 0, it means no response will be sent. This assures
// it will never be 0.
//
uint8_t
EasyXBee::get_next_frame_id() {
    if (frame_id == 255) {
	frame_id = 1;
    }
    return frame_id++;
}
