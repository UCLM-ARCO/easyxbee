
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

#ifndef EASYXBEE_H
#define EASYXBEE_H

#include <XBee.h>


class EasyXBee {
public:
    EasyXBee();
    void begin(uint16_t rate);
    void wait_until_ready();

    bool receive(uint8_t** data, uint8_t* size);
    bool send(XBeeAddress64& addr64, uint16_t addr16, uint8_t* data, uint8_t size);

    bool lookup(uint8_t* name, uint8_t size, XBeeAddress64* addr64, uint16_t* addr16);
    bool set_pan_id(uint8_t* pan_id, uint8_t size);
    bool set_name(uint8_t* name, uint8_t size);
    bool write_config();

private:
    bool send_and_check_at_command(AtCommandRequest& request);
    uint8_t get_next_frame_id();
    void handle_rx_response(XBeeResponse& response);

    bool rx_pending_valid;
    uint8_t rx_pending_size;
    uint8_t rx_pending_data[MAX_FRAME_DATA_SIZE];

    XBee xbee;
    uint8_t frame_id;
};

#endif // EASYXBEE_H
