/**
 * Service WampService
 *
 * Singleton WAMP object representing a WAMP connection with the server.
 */

import {Injectable} from '@angular/core';

declare var autobahn: any;

@Injectable()
export class WampService {
  
  public active: Boolean = false;
  
  constructor() {
  }

  connect() {
    
    this.active = true;
    
    return new autobahn.Connection({
      transports: [
        { 'type': 'websocket', 'url': 'wss://localhost:8083/ws' },
        { 'type': 'longpoll', 'url': 'https://localhost:8083/lp' }
      ],
      realm: 'liestudio'
    });
  }

}