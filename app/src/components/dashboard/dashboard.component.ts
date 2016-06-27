/**
 * Component DashboardComponent
 */

import {Component,
        AfterViewInit}      from '@angular/core';
import {Control,
        CORE_DIRECTIVES}    from '@angular/common';
import {Http, Headers}      from '@angular/http';
import {Router}             from '@angular/router-deprecated';

import {Message}            from 'primeng/primeng';

import {UserService}        from '../../shared/services/src/user.service';
import {WampService}        from '../../shared/services/src/wamp.service';

@Component({
  selector:      'dashboard',
  moduleId:      module.id,
  templateUrl:   'dashboard.component.html',
  styleUrls :    ['dashboard.component.css'],
  directives:    [CORE_DIRECTIVES],
})

export class DashboardComponent {

}