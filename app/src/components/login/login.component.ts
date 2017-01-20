/**
 * Component LoginComponent
 * - Handles user authentication and authorization
 * - Can remember user login using cookies
 */

// Angular imports
import {Component,
        ViewEncapsulation,
        NgZone,
        NgModule}           from '@angular/core';
import {Router}             from '@angular/router';

// Third-party imports
import {Dialog,
        Button,
        InputSwitch,
        InputText}          from 'primeng/primeng';
import {CookieService}      from 'angular2-cookie/core';

// App imports
import {UserService}        from '../../shared/services/src/user.service';
import {WampService}        from '../../shared/services/src/wamp.service';

@Component({
  selector:      'app',
  moduleId:      module.id,
  templateUrl:   'login.component.html',
  styleUrls :    ['login.component.css'],
  encapsulation: ViewEncapsulation.None,
  providers:     [CookieService],
  host:          {'class' : 'ng-animate LoginComponent'}, 
})

@NgModule({
  declarations: [Dialog, Button, InputText, InputSwitch]
})
export class LoginComponent {
  
  // Activate buttons
  public signin_inactive: boolean = true;
  public signup_inactive: boolean = true;
  public retrieve_inactive: boolean = true;
  
  // Validation status
  public email_is_valid: string = '';
  
  // Remember login
  public remember_login: boolean = false;
  
  public email: string = '';
  public username: string = '';
  public password: string = '';
  public statusmessage: string = "Binding affinity prediction for Pro's";
  
  public wampactive: boolean = false;
  
  constructor(public router: Router, public user: UserService, 
              public wamp: WampService, public zone: NgZone,
              private _cookieService: CookieService) {
    
    // Check cookie for automatic login
    this.getCookie();
  }
  
  /**
   * If there is a liestudio cookie, get its auth_stamp and verify it 
   * with the server. 
   * - If valid, prefill username and password
   */
  private getCookie() {
    
    var lie_sso_cookie = this._cookieService.get('liestudio');
    if (lie_sso_cookie) {
      
      this.wampactive = true;
    
      // Set up 'onopen' handler
      var that = this;
      var connection = this.wamp.connect();
      connection.onopen = function (session) {

        // Need to call zone.run to update statusmessage immediately
        session.call('liestudio.user.sso', [lie_sso_cookie]).then(
          function(result) {
            that.zone.run(() => {
              if (result) {
                that.username = result.username;
                that.password = result.password;
                that.remember_login = true;
                that.signin_inactive = false;
                that.wampactive = false;
              }
              else {
                that.statusmessage = 'Cookie no longer valid';
                that.wampactive = false;
                that.remember_login = false;
              }
            });
          },
          function(error) {
            console.log("Login failed:", error);
            that.zone.run(() => {
              that.statusmessage = 'Unable to authenticate';
              that.wampactive = false;
            });
          }
       );

      };

      connection.open();
    }
  }
  
  /**
   * If remember login, store authentication stamp cookie for one month
   * if not remember log, remove cookie
   */
  private storeCookie(auth_stamp) {
    
    if (this.remember_login) {
      
      // Set cookie expiration data to 1 month
      var now = new Date(),
      exp = new Date(now.getFullYear(), now.getMonth()+1, now.getDate());
    
      this._cookieService.put('liestudio', auth_stamp, {expires: exp});
    } else {
      this._cookieService.remove('liestudio');
    }
  }
  
  /**
   * Validate content of email input field and set email_is_valid property
   */
  private validateEmail() {
    
    // If the input field is empty clear email_is_valid
    if (!this.email.length) {
      this.email_is_valid = '';
      return false;
    }
    
    var EMAIL_REGEXP = /^[a-z0-9!#$%&'*+\/=?^_`{|}~.-]+@[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$/i;
    if (!EMAIL_REGEXP.test(this.email)) {
      this.email_is_valid = 'invalid';
      return false;
    }
    else {
      this.email_is_valid = 'valid';
      return true;
    }
  }
  
  /**
   * Input field callback
   * Check validity of the email, username and password field and set
   * the retrieval, signup or signin buttons.
   */
  public validateInput(event) {
    
    // Password retrieval service
    if (this.validateEmail() && !this.username.length) {
      this.retrieve_inactive = false;
      this.signin_inactive = true;
      this.signup_inactive = true;
      return;
    }
    
    // Signup
    if (this.validateEmail() && this.username.length) {
      this.retrieve_inactive = true;
      this.signin_inactive = true;
      this.signup_inactive = false;
      return;
    }
    
    // Signin
    if (this.password.length && this.username.length) {
      this.retrieve_inactive = true;
      this.signin_inactive = false;
      this.signup_inactive = true;
      return;
    }
    
    this.retrieve_inactive = true;
    this.signin_inactive = true;
    this.signup_inactive = true;
  }
  
  /**
   * Submit signin button callback
   * - Contact server to validate username and password
   */
  public onSubmitSignin() {
    
    this.wampactive = true;
    
    // Set up 'onopen' handler
    var that = this;
    var connection = this.wamp.connect();
    connection.onopen = function (session) {

      // Need to call zone.run to update statusmessage immediately
      session.call('liestudio.user.login', ['liestudio', that.username, {'ticket': that.password, 'authmethod': 'ticket'}]).then(
        function(result) {
          that.zone.run(() => {
            if (result) {
              console.log(result);
              that.user.isLoggedIn = true;
              that.user.update(result);
              that.wampactive = false;
              that.statusmessage = 'Welcome in ' + that.user.username;
              that.storeCookie(that.user.session_id);
              that.router.navigateByUrl('/dashboard');
            }
            else {
              that.statusmessage = 'Oh... wrong username or password';
              that.wampactive = false;
            }
          });
        },
        function(error) {
          console.log("Login failed:", error);
          that.zone.run(() => {
            that.statusmessage = 'Unable to authenticate';
            that.wampactive = false;
          });
        }
     );

    };

    connection.open();
  }
  
  /**
   * Submit signup button callback
   * - Contact server to process sign-up request
   */
  public onSubmitSignup() {
    this.statusmessage = 'LIEStudio sign up request send';
  }
  
  /**
   * Submit retrieve button callback
   * - Contact server to process login credential retrieve request
   */
  public onSubmitRetrieve() {
    
    this.wampactive = true;
  
    // Set up 'onopen' handler
    var that = this;
    var connection = this.wamp.connect();
    connection.onopen = function (session) {

      // Need to call zone.run to update statusmessage immediately
      session.call('liestudio.user.retrieve', [that.email]).then(
        function(result) {
          that.zone.run(() => {
            if (result) {
              that.statusmessage = result;
              that.wampactive = false;
            }
            else {
              that.statusmessage = 'Unknown email';
              that.wampactive = false;
            }
          });
        },
        function(error) {
          that.zone.run(() => {
            that.statusmessage = 'Unable to authenticate';
            that.wampactive = false;
          });
        }
     );

    };

    connection.open();
  }
}