/**
 * Component HomeComponent
 */

// Angular imports
import {Component,
        AfterViewInit,
        ViewEncapsulation,
        OnInit,
        NgModule}                 from '@angular/core';
import {FormsModule}              from '@angular/forms';
import {Http, 
        HttpModule,
        Headers}                from '@angular/http';
import {BrowserModule} from '@angular/platform-browser';
import {Router,
        RouterModule}  from '@angular/router';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';

import {DashboardComponent} from '../dashboard/dashboard.component'
import {BootComponent} from '../boot/boot.component'
import {DockingComponent} from '../docking/docking.component'
import {MDComponent} from '../md/md.component'
import {LoggingComponent} from '../logging/logging.component'
import {LoginComponent} from '../login/login.component'
import {AppRouting} from './app.routes';
import {nvD3} from './utils/ng2-nvd3'

// PrimeNG imports
import {Button,
        PanelMenu,
        Menubar,
        MenuItem,
        PanelMenuSub,
        MenubarSub,
        MultiSelectModule,
        DataTableModule,
        ContextMenuModule,
        SliderModule,
        DialogModule,
        InputSwitchModule}               from 'primeng/primeng';

// App imports
import {UserService}            from '../../shared/services/src/user.service';
import {WampService}            from '../../shared/services/src/wamp.service';
import {Authorize}            from '../../shared/services/src/auth.service';

declare var componentHandler: any;
declare var jQuery: any;

// Component configuration decorator
// - Disable view encapsulation to override ui element styles
@Component({
  selector:      'app',
  moduleId:      module.id,
  templateUrl:   'app.component.html',
  styleUrls :    ['app.component.css'],
  encapsulation: ViewEncapsulation.None,
  host:          {'class' : 'ng-animate AppComponent'}, 
})

@NgModule({
  imports: [BrowserModule, AppRouting, HttpModule, MultiSelectModule, FormsModule, DataTableModule, ContextMenuModule, SliderModule, DialogModule, InputSwitchModule, BrowserAnimationsModule],
  declarations: [AppComponent, DashboardComponent, BootComponent, DockingComponent, MDComponent, LoggingComponent, LoginComponent, Button, PanelMenu, Menubar, PanelMenuSub, MenubarSub, nvD3],
  bootstrap: [ AppComponent ],
  providers: [UserService, WampService, Authorize] 
})

export class AppComponent implements AfterViewInit, OnInit {

  private main_menu_items: MenuItem[];
  private top_menu_items: MenuItem[];
  public  aside_left_unfold: Boolean = false;
  
  constructor(public router: Router, public http: Http, public user: UserService, public wamp: WampService) {
  }
  
  ngOnInit() {
    
    // Aside-left main application menu items
    this.main_menu_items = [
      {
        label: 'Main',
        icon: 'fa-home',
        expanded: true,
        items: [
          {label: 'Dashboard', icon: 'fa-dashboard', routerLink: ['/dashboard']},
          {label: 'Logs', icon: 'fa-tasks', routerLink: ['/log']},
          {label: 'Docking', icon: 'fa-flask', routerLink: ['/docking']},
          {label: 'MD', icon: 'fa-th-list', routerLink: ['/md']},
        ]
      },
      {
        label: 'Account',
        icon: 'fa-edit',
        items: [
          {label: 'Account', icon: 'fa-user'},
          {label: 'Cloud', icon: 'fa-cloud-download'}
        ]
      },
      {
        label: 'Settings',
        icon: 'fa-gear',
        items: [
          {label: 'Preferences', icon: 'fa-gear'},
          {label: 'Help', icon: 'fa-info-circle'}
        ]
      }
    ];
    
    // Top menu bar
    this.top_menu_items = [
        {
          label: this.user.username,
          items: [
            {label: 'Logout', 
             icon: 'fa-power-off', 
             command: (event) => {this.onSubmitLogout()}},
            {label: 'Profile'},
            {label: 'Contact'}
          ]
        },
        { label: '', icon: 'fa-user' }
    ];
  }
  
  ngAfterViewInit() {
    //componentHandler.upgradeDom();

    jQuery( document ).ready( ($) => 
    {
      $( '.ui-menu-parent > .ui-menuitem-link' ).each( ( i, item ) => 
      {
        if( $(item).attr("href") == "#" )
        {
          var after = $('<span class="after-link" />');
          $( item ).append( after );

          after.click( (event) => 
          {
            event.preventDefault();
            
            return false;
          } ); // click
        }
      } ); // each
    } ); // ready
  }
  
  onSubmitLogout() {

    var that = this;
    var connection = this.wamp.connect();
    connection.onopen = function (session) {

      session.call('liestudio.user.logout', [that.user.session_id]).then(
        function(result) {
           if (result) {
             console.log(result);
             that.user.clear();
             that.router.navigateByUrl('/');
           }
           else {
             console.log('unable to logout');
           }
        },
        function(error) {
          console.log("Logout failed:", error);
        }
     );

    };

    connection.open();
  }
}