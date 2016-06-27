/**
 * Router service
 *
 * Define basic application routing and export as router provider at 
 * application bootstrap stage.
 */

import {provideRouter,
        RouterConfig}           from '@angular/router';

import {AppRoutes}              from '../../../components/app/app.routes';
import {LoginRoutes}            from '../../../components/login/login.routes';
import {AUTH_PROVIDERS}         from './auth.service';

export const routes: RouterConfig = [
  ...AppRoutes,
  ...LoginRoutes
];

export const APP_ROUTER_PROVIDERS = [
  provideRouter(routes),
  AUTH_PROVIDERS
];