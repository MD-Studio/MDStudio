/**
 * Main app instantiation
 *
 * - Provides the UserService and WampService at the main app level
 *   so it is accessible as singleton to every method in the application.
 * - Initialize the main App components to bootstrap the UI.
 */


// Angular imports
import {platformBrowserDynamic } from '@angular/platform-browser-dynamic';
import {enableProdMode}          from '@angular/core';

// App imports
import {AppComponent}         from './components/app/app.component';
import {UserService}          from './shared/services/src/user.service';
import {WampService}          from './shared/services/src/wamp.service';

import 'rxjs/Rx';

enableProdMode();
platformBrowserDynamic().bootstrapModule(
  AppComponent,
  [
    UserService,
    WampService
  ]
).catch(err => console.error(err));