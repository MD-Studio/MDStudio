/**
 * Component HomeComponent
 */

// Angular imports
import {Component,
        AfterViewInit,
        ViewEncapsulation,
        OnInit}                 from '@angular/core';
import {CORE_DIRECTIVES}        from '@angular/common';
import {Http, 
        Headers}                from '@angular/http';
import {Router,
        ROUTER_DIRECTIVES}      from '@angular/router';

// PrimeNG imports
import {Button,
        PanelMenu,
        Menubar,
        MenuItem}               from 'primeng/primeng';

// App imports
import {UserService}            from '../../shared/services/src/user.service';
import {WampService}            from '../../shared/services/src/wamp.service';

declare var componentHandler: any;

// Component configuration decorator
// - Disable view encapsulation to override ui element styles
@Component({
  selector:      'app',
  moduleId:      module.id,
  templateUrl:   'app.component.html',
  styleUrls :    ['app.component.css'],
  encapsulation: ViewEncapsulation.None,
  directives:    [CORE_DIRECTIVES, ROUTER_DIRECTIVES, Button, PanelMenu, Menubar],
  host:          {'class' : 'ng-animate AppComponent'}, 
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
        defaultActive: true,
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
        defaultActive: true,
        items: [
          {label: 'Account', icon: 'fa-user'},
          {label: 'Cloud', icon: 'fa-cloud-download'}
        ]
      },
      {
        label: 'Settings',
        icon: 'fa-gear',
        defaultActive: true,
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
            {label: 'Logout', icon: 'fa-power-off', command: (event) => {this.onSubmitLogout()}},
            {label: 'Profile'},
            {label: 'Contact'}
          ]
        },
        { label: '', icon: 'fa-user' }
    ];
  }

  ngAfterViewInit() {
    //componentHandler.upgradeDom();
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