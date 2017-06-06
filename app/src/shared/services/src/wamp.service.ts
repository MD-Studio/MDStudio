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
  
  // this callback is fired during Ticket-based authentication
  //
  onchallenge (session, method, extra) {

     console.log("onchallenge", method, extra);

     if (method === "ticket") {
        return 'liepw@#';

     } else {
        throw "don't know how to authenticate using '" + method + "'";
     }
  }

  connect() {
    
    this.active = true;
    
    return new autobahn.Connection({
      transports: [
        { 'type': 'websocket', 'url': 'wss://localhost:8080/ws' },
        { 'type': 'longpoll', 'url': 'https://localhost:8080/lp' }
      ],
      realm: 'liestudio',
      authid: 'lieadmin',
      onchallenge: this.onchallenge
    });
  }

}