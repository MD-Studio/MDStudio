###LIEStudio

This is the read me for the LIEStudio Angular based web application

####Installation
1) Install NodeJs (use NodeJS installer: https://nodejs.org/en/download/)
2) Install the Node Package Manager (npm)
3) Run 'npm install' to install all required packages listed in package.json
4) Run the application in interactive mode using 'gulp serve'

####Fonts
The LIEStudio app uses the Roboto font loaded from the server with fallback to Trebuchet MS, 
Helvetica or Arial respectivly.
Scalable vector icons are from the fontawesome project (http://fontawesome.io).

####UI-elements
The LIEStudio app mostly uses the reusable application UI widgets of the PrimeUI project packed as
Angular 2 directives in the PrimeNG package (https://github.com/primefaces/primeng).
Application specific styles are implemented in the '/shared/styles/_theme_ui_elements.scss'
stylesheet on top of the primeui-ng-all.css.

####Modifications made to third-party packages
- PrimeNG: added support for default active (unfolded) menu panel (PanelMenu component)
  Changed MenuItem interface in 'primeng/components/common.d.ts: added defaultActive?: boolean;
  
  export interface MenuItem {
      label?: string;
      icon?: string;
      command?: (event?: any) => void;
      url?: string;
      routerLink?: any;
      eventEmitter?: EventEmitter<any>;
      items?: MenuItem[];
      defaultActive?: boolean;
  }
  
  Changed PanelMenu.prototype.headerClick function in 'primeng/components/panelmenu/panelmenu.js':
  
  PanelMenu.prototype.headerClick = function (event, item) {
      var index = this.activeItems.indexOf(item);
      if (index == -1)
          this.activeItems.push(item);
      else
          this.activeItems.splice(index, 1);
      if (item.defaultActive) {
        for (var _i = 0, _a = this.model; _i < _a.length; _i++) {
          if (this.model[_i] === item) {
            this.model[_i].defaultActive = false;
          }
        }
      }
      event.preventDefault();
  };
  
  Changed PanelMenu.prototype.isActive function in 'primeng/components/panelmenu/panelmenu.js':
  
  PanelMenu.prototype.isActive = function (item) {
      var index = this.activeItems.indexOf(item);
      if (item.defaultActive && index == -1) {
        this.activeItems.push(item);
        return true;
      }
      return index != -1;
  };

- PrimeNG: Changed menu bar positioning in 'primeng/components/menubar/menubar.js':
 
  line 28 change: sublist.style.left = '0px'; 
          to:     sublist.style.left = '-' + this.domHandler.getOuterWidth(item.children[0]) / 2 + 'px';
  
- PrimeNG: Added class to p-menubarsub class of PrimeNG menubar component in 'primeng/components/menubar/menubar.js':
  
  template: "\n        <ul [ngClass]=\"{'ui-helper-reset':root, 'ui-widget-content ui-corner-all 
  ui-helper-clearfix ui-menu-child ui-shadow':!root}\" class=\"ui-menu-list\"\n            
  (click)=\"listClick($event)\">\n            <template ngFor let-child [ngForOf]=\"(root ? item : item.items)\">\n
  <li #item [ngClass]=\"{'ui-menuitem ui-widget ui-corner-all':true,'ui-menu-parent':child.items,
  'ui-menuitem-active':item==activeItem, 'ui-menuitem-notext':!child.label}\"\n
  (mouseenter)=\"onItemMouseEnter($event, item)\" (mouseleave)=\"onItemMouseLeave($event, item)\">\n
  <a #link [href]=\"child.url||'#'\" class=\"ui-menuitem-link ui-corner-all\" 
  [ngClass]=\"{'ui-state-hover':link==activeLink}\" (click)=\"itemClick($event, child)\">\n
  <span class=\"ui-submenu-icon fa fa-fw\" *ngIf=\"child.items\" [ngClass]=\"{'fa-caret-down':root,
  'fa-caret-right':!root}\"></span>\n <span class=\"ui-menuitem-icon fa fa-fw\" *ngIf=\"child.icon\" 
  [ngClass]=\"child.icon\"></span>\n <span class=\"ui-menuitem-text\">{{child.label}}</span>\n 
   </a>\n <p-menubarSub class=\"ui-submenu\" [item]=\"child\" *ngIf=\"child.items\"></p-menubarSub>\n
  </li>\n            </template>\n        </ul>\n    ",

- PrimeNG: Changed InputSwitch ui px width calculation to match rounded corner switcher in 'primeng/components/inputswitch/inputswitch.js':
  
  Line 81 from: this.onContainer.style.width = this.offset + 'px';
  Line 81 to: this.onContainer.style.width = this.offset + 4 + 'px';
  Line 84 from: this.handle.style.left = this.offset + 'px';
  Line 84 to: this.handle.style.left = this.offset - 4 + 'px';
  
####TODO
- Upon app init, check browser compatibility with respect to enabled javascript, flexbox support.