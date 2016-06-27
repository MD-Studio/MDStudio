import {Injectable}             from '@angular/core';
import {CanActivate,
        Router,
        ActivatedRouteSnapshot,
        RouterStateSnapshot}    from '@angular/router';
import {UserService}            from './user.service';

/**
 * Authorize
 *
 * Function to use in Angular's CanActivate decorator class.
 * Used to resolve user privilages for accessing app components by:
 * - Checking if a user is logged in. If not redirect to login page
 * - TODO: this is the place to do a privilage check for accessing a component
 *   by role or otherwise
 */
@Injectable()
export class Authorize implements CanActivate {
  
  constructor(private userService: UserService, private router: Router) {}
  
  canActivate(next:  ActivatedRouteSnapshot, state: RouterStateSnapshot) {
    
    console.log('check login');
    if (this.userService.isLoggedIn) {
      return true;
    }
    this.router.navigate(['/login']);
    return false;
  }
}

export const AUTH_PROVIDERS = [Authorize];