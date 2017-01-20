/**
 * Router service
 *
 * Define basic application routing and export as router provider at 
 * application bootstrap stage.
 */

import {Routes}                 from '@angular/router';

import {AppRoutes}              from '../../../components/app/app.routes';
import {LoginRoutes}            from '../../../components/login/login.routes';
import {AUTH_PROVIDERS}         from './auth.service';

export const routes: Routes = [
  ...AppRoutes,
  ...LoginRoutes
];
