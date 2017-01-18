import {Routes}            from '@angular/router';

import {AppComponent}            from './app.component';
import {DashboardComponent}      from '../../components/dashboard/dashboard.component';
import {DockingComponent}       from '../../components/docking/docking.component';
import {LoggingComponent}        from '../../components/logging/logging.component';
import {MDComponent}             from '../../components/md/md.component';
import {Authorize}               from '../../shared/services/src/auth.service';

// Setup main application component router.
// - TODO: Lazy load the log component, not needed by default.
// - TODO: rerouting undefined routes not working
export const AppRoutes: Routes = [
  {
    path: 'dashboard',
    component: DashboardComponent,
    canActivate: [Authorize],
  },
  {
    path: 'md',
    component: MDComponent,
    canActivate: [Authorize]
  },
  {
    path: 'docking',
    component: DockingComponent,
    canActivate: [Authorize]
  },
  {
    path: 'log',
    component: LoggingComponent,
    canActivate: [Authorize]
  },
  {
    path: '',
    component: DashboardComponent,
    canActivate: [Authorize],
  },
  {
    path: '*',
    component: DashboardComponent,
    canActivate: [Authorize],
  }
];