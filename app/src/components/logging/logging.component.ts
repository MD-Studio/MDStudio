/**
 * Component LoggingComponent
 *
 * Inspect user specific log messages related to the projects the
 * user is running.
 * - Structured log messages are retrieved from the server and 
 *   displayed as DataTable.
 * - The DataTable has all the usual filtering and sorting features
 *   required to analyze the logs.
 */

// Angular imports
import {Component,
        ViewEncapsulation,
        NgModule,
        NgZone,
        OnInit}             from '@angular/core';
        
// Third-party imports
import {InputText,
        DataTable,
        Button,
        Dialog,
        Column,
        Header,
        Footer}             from 'primeng/primeng';

// App imports
import {UserService}        from '../../shared/services/src/user.service';
import {WampService}        from '../../shared/services/src/wamp.service';

@Component({
  selector:      'logging',
  moduleId:      module.id,
  templateUrl:   'logging.component.html',
  styleUrls :    ['logging.component.css'],
  encapsulation: ViewEncapsulation.None
})

@NgModule({
  declarations: [InputText, DataTable, Button, Dialog, Column, Header, Footer]
})
export class LoggingComponent implements OnInit {
    
    // General log statistics
    public  total_log_message_count: number = 0;
    public  warn_log_message_count: number = 0;
    public  error_log_message_count: number = 0;
     
    // DataTable row selection
    public  selectedLogs: any[];
    public  logs: any[];
    
    // Log custom filter
    public  log_custom_filter_unfold: boolean = false;   // Fold/unfold log custom filter input fields 
    
    constructor(public user: UserService, public wamp: WampService, public zone: NgZone) {
    }
    
    /**
     * Init component
     * - Retrieve log messages for the user from the server
     */
    public ngOnInit() {
        this.retrieveLogMessagesFromServer();
    }
    
    /**
     * Retrieve structured log messages from server
     * - Convert all Unix timestamps (log message time) to JavaScript Date objects
     */ 
    public retrieveLogMessagesFromServer() {
        
        // Set up 'onopen' handler
        var that = this;
        var connection = this.wamp.connect();
        connection.onopen = function (session) {

          // Need to call zone.run to update statusmessage immediately
          session.call('liestudio.logger.get', [that.user.username]).then(
              function(result) {
                  that.zone.run(() => {
                  if (result) {
                      that.logs = result;
                      
                      // Convert Unix timestamp to Date objects
                      // Calculate statistics
                      that.total_log_message_count = that.logs.length;
                      for (var i in that.logs) {
                          that.logs[i]['log_time'] = new Date(that.logs[i]['log_time'] * 1000);
                          
                          if (that.logs[i]['log_level'] == 'warn') {
                              that.warn_log_message_count += 1;
                          }
                          else if (that.logs[i]['log_level'] == 'err') {
                              that.error_log_message_count += 1;
                          }
                      }
                    }
                });
              },
              function(error) {
                  console.log("Unable to retrieve logs:", error);
              }
          );
        };

        connection.open();
    }
}