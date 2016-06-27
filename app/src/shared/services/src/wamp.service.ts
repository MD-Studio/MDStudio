/**
 * Service WampService
 *
 * Singleton WAMP object representing a WAMP connection with the server.
 */

import {Injectable} from '@angular/core';

declare var autobahn: any;
@Injectable()
export class WampService {

  constructor() {
  }

  connect() {
    return new autobahn.Connection({
      transports: [
        { 'type': 'websocket', 'url': 'ws://localhost:8080/ws' },
        { 'type': 'longpoll', 'url': 'http://localhost:8080/lp' }
      ],
      realm: 'liestudio'
    });
  }

}