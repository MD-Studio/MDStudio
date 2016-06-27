import {RouterConfig}            from '@angular/router';

import {AppComponent}            from './app.component';
import {DashboardComponent}      from '../../components/dashboard/dashboard.component';
import {AnalysisComponent}       from '../../components/analysis/analysis.component';
import {LoggingComponent}        from '../../components/logging/logging.component';
import {MDComponent}             from '../../components/md/md.component';
import {Authorize}               from '../../shared/services/src/auth.service';

// Setup main application component router.
// - TODO: Lazy load the log component, not needed by default.
// - TODO: rerouting undefined routes not working
export const AppRoutes: RouterConfig = [
  {
    path: '/dashboard',
    component: DashboardComponent,
    canActivate: [Authorize],
  },
  {
    path: '/md',
    component: MDComponent,
    canActivate: [Authorize]
  },
  {
    path: '/analysis',
    component: AnalysisComponent,
    canActivate: [Authorize]
  },
  {
    path: '/log',
    component: LoggingComponent,
    canActivate: [Authorize]
  },
  {
    path: '/',
    component: DashboardComponent,
    canActivate: [Authorize],
    index: true
  },
  {
    path: '/*',
    component: DashboardComponent,
    canActivate: [Authorize],
  }
];