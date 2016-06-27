/**
 * Service UserService
 *
 * Singleton user object representing all data for the logged in user.
 */

import {Injectable}         from '@angular/core';

@Injectable()
export class UserService {
  
  public uid: number;
  public username: String;
  public email: String;
  public session_id: any;
  public isLoggedIn: Boolean = true;
  public initTime: Number = Date.now() / 1000 | 0;
  
  constructor() {
    this.initDefaults();
  }
  
  private initDefaults() {
    this.uid = null;
    this.username = 'anonymous';
    this.email = null;
    this.session_id = null;
  }
  
  update(login_array) {
    
    // Update user object attributes from other object.
    for (var key in login_array) {
      if (this.hasOwnProperty(key)) {
        this[key] = login_array[key];
      }
    }
  }
  
  clear() {
    
    // Reinitiate the class for instance on logout.
    for (var attribute of Object.getOwnPropertyNames(this)) {
      delete this[attribute];
    }
    this.initDefaults();
  }
}