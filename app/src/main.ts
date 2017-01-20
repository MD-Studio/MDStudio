/**
 * Main app instantiation
 *
 * - Provides the UserService and WampService at the main app level
 *   so it is accessible as singleton to every method in the application.
 * - Initialize the main App components to bootstrap the UI.
 */


// Angular imports
import {bootstrap}            from '@angular/platform-browser-dynamic';
import {enableProdMode}       from '@angular/core';
import {HTTP_PROVIDERS}       from '@angular/http';

// App imports
import {AppComponent}         from './components/app/app.component';
import {UserService}          from './shared/services/src/user.service';
import {WampService}          from './shared/services/src/wamp.service';
import {APP_ROUTER_PROVIDERS} from './shared/services/src/router.service';

import 'rxjs/Rx';

enableProdMode();
bootstrap(
  AppComponent,
  [
    UserService,
    WampService,
    APP_ROUTER_PROVIDERS,
    HTTP_PROVIDERS
  ]
).catch(err => console.error(err));