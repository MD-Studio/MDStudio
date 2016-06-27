/**
 * Component AnalysisComponent
 */

import {Component}          from '@angular/core';
import {Control,
        CORE_DIRECTIVES}    from '@angular/common';
import {Http, 
        Headers}            from '@angular/http';
import {Router}             from '@angular/router-deprecated';

import {Message}            from 'primeng/primeng';

import {UserService}        from '../../shared/services/src/user.service';
import {WampService}        from '../../shared/services/src/wamp.service';

@Component({
  selector:      'analysis',
  moduleId:      module.id,
  templateUrl:   'analysis.component.html',
  styleUrls :    ['analysis.component.css'],
  directives:    [CORE_DIRECTIVES],
})

export class AnalysisComponent {}