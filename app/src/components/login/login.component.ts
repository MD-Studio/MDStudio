/**
 * Component AppComponent
 */

declare var componentHandler: any

import {Component,
        ViewEncapsulation,
        AfterViewInit,
        NgZone}             from '@angular/core';
import {CORE_DIRECTIVES,
        FORM_DIRECTIVES,
        NgForm,
        Control,
        ControlGroup,
        FormBuilder,
        Validators}         from '@angular/common';
import {Router}             from '@angular/router';

import {UserService}        from '../../shared/services/src/user.service';
import {WampService}        from '../../shared/services/src/wamp.service';

@Component({
  selector:      'app',
  moduleId:      module.id,
  templateUrl:   'login.component.html',
  styleUrls :    ['login.component.css'],
  directives:    [FORM_DIRECTIVES, CORE_DIRECTIVES],
  encapsulation: ViewEncapsulation.None,
})

export class LoginComponent implements AfterViewInit {

  username: Control;
  password: Control;
  email: Control;
  
  form1: ControlGroup;
  form2: ControlGroup;
  form3: ControlGroup;

  statusmessage: String = "Binding affinity prediction for Pro's";
  wampactive: Boolean = false;
  
  constructor(public router: Router,
              public zone: NgZone,
              public user: UserService,
              public wamp: WampService,
              fb: FormBuilder) {

    this.username = new Control('', Validators.required);
    this.password = new Control('', Validators.required);
    this.email = new Control('', Validators.required);
    
    this.form1 = fb.group({
      username: this.username,
      password: this.password
    });
    
    this.form2 = fb.group({
      email: this.email
    });
    
    this.form3 = fb.group({
      email: this.email
    });
  }
  
  ngAfterViewInit() {
    componentHandler.upgradeDom();
  }
  
  onSubmitSignin() {

    this.wampactive = true;

    // Set up 'onopen' handler
    var that = this;
    var connection = this.wamp.connect();
    connection.onopen = function (session) {

      // Need to call zone.run to update statusmessage immediately
      session.call('liestudio.user.login', [that.form1._value.username, that.form1._value.password]).then(
        function(result) {
          that.zone.run(() => {
            if (result) {
              that.user.isLoggedIn = true;
              that.user.update(result);
              that.wampactive = false;
              that.statusmessage = 'Welcome in ' + that.user.username;
              that.router.navigateByUrl('/app');
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
  
  onSubmitSignup() {
    console.log(this.form2);
  }
  
  onSubmitRetrieve() {
    console.log(this.form3);
  }

  clicked(idx) {
    var target = $(".carousel-container > div")[idx];
    $(".carousel-container").css(
      "transform","translateX("+idx * -target.offsetWidth+"px)"
    );
  }
}