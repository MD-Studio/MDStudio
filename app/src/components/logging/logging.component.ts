/**
 * Component LoggingComponent
 */

// Angular imports
import {Component,
        AfterViewInit}      from '@angular/core';
import {Control,
        CORE_DIRECTIVES}    from '@angular/common';
import {Http, Headers,
        HTTP_PROVIDERS,
        Response}           from '@angular/http';
import {Router}             from '@angular/router';

// Third-party imports
import {InputText,
        DataTable,
        Button,
        Dialog,
        Column,
        Header,
        Footer}             from 'primeng/primeng';

// App imports
import {UserService}        from '../../shared/services/src/user.service';
import {WampService}        from '../../shared/services/src/wamp.service';

@Component({
  selector:      'logging',
  moduleId:      module.id,
  templateUrl:   'logging.component.html',
  styleUrls :    ['logging.component.css'],
  directives:    [InputText, DataTable, Button, Dialog, Column, Header, Footer],
  providers:     [HTTP_PROVIDERS]
})

export class LoggingComponent {}