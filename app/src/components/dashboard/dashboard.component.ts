/**
 * Component DashboardComponent
 */

import {Component,
        AfterViewInit,
        NgModule,
        ViewEncapsulation }      from '@angular/core';
import {Http, Headers}      from '@angular/http';

import {Message}            from 'primeng/primeng';

import {UserService}        from '../../shared/services/src/user.service';
import {WampService}        from '../../shared/services/src/wamp.service';

@Component({
  selector:      'dashboard',
  moduleId:      module.id,
  templateUrl:   'dashboard.component.html',
  styleUrls :    ['dashboard.component.css'],
  encapsulation: ViewEncapsulation.None
})

@NgModule({
  declarations: [DashboardComponent]
})
export class DashboardComponent {

}