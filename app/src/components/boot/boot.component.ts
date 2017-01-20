/**
 * The application bootstrap component
 */

// Angular imports
import {Component,
        OnInit}                 from '@angular/core';
import {Router,
        RouterModule}      from '@angular/router';
import {NgModule}      from '@angular/core';

// App imports
import {UserService}            from '../../shared/services/src/user.service';
import {WampService}            from '../../shared/services/src/wamp.service';

@Component({
  selector:      'app',
  moduleId:      module.id,
  templateUrl:   'boot.component.html',
  styleUrls:     ['boot.component.css'],
})

@NgModule({
  imports: [RouterModule],
  declarations: [BootComponent]
})
export class BootComponent implements OnInit {

  public system_message: String;
  public message_level: String = 'info';

  constructor
    (private router: Router,
     private wamp: WampService,
     private user: UserService
    ) {
    this.system_message = null;
  }

  ngOnInit() {

    //TODO: Check WAMP connection status
    //TODO: Check server status .. (out of service etc.)
    this.router.navigate(['/']);
  }

}