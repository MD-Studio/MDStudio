/**
 * Component DockingComponent
 *
 * Inspect Molecular Dynamics runs part of the current project.
 * - Visualize trajectory information as a time series plot with time 
 *   range selection support (visuals using D3.js)
 * - Inspect key MD parameters in a data table
 * - Modify parameters for single or multiple MD selections
 */

// Angular imports
import {Component,
        ViewChild,
        NgModule,
        ViewEncapsulation }             from '@angular/core';
import {Http,
        HttpModule,
        Response}             from '@angular/http';

// Third-party imports
import {InputText,
        DataTable,
        MenuItem,
        ContextMenu,
        Button,
        Dialog,
        Column,
        Slider,
        SelectItem,
        MultiSelect}          from 'primeng/primeng';
import {nvD3}                 from '../app/utils/ng2-nvd3';

// App imports
import {UserService}          from '../../shared/services/src/user.service';
import {WampService}          from '../../shared/services/src/wamp.service';

// Global variable declaration
declare let d3: any;

// MD data object interface defenition
export interface MD {
    id?: number;
    compound?: string;
    pose?: number;
    range?: number;
    start?: number;
    end?: number;
}

// MD details object used by MD details side panel
class MDDetails implements MD {
  
  public traj_start_frame: number = 0;
  public traj_end_frame: number = 2000;
  
  // TODO: these are now parsed as string by the .toFixed(2) function in
  // the calculateStats function. This is used bacause Angular 2 Pipes are
  // broken in Safari.
  public ave_elec: string;
  public std_elec: string;
  public ave_vdw: string;
  public std_vdw: string;
  
  public rangeSlider: number[];
   
  constructor(public traj_data?: any[], public id?, public compound?, public pose?, 
              public range?, public start?, public end?) {
    
    //Determine last trajectory frame number from trajectory data
    if (this.traj_data) {
      var elec_values = this.traj_data[0].values;
      this.traj_end_frame = elec_values[elec_values.length - 1].x;
    
      //Calculate average and standard deviation of trajectory data keys
      this.calculateStats();
    }
  }
  
  /**
   * Calculate standard deviation of a values in array
   */
  private standardDeviation(values) {
    var avg = this.average(values);
  
    var squareDiffs = values.map(function(value){
      var diff = value - avg;
      var sqrDiff = diff * diff;
      return sqrDiff;
    });
  
    var avgSquareDiff = this.average(squareDiffs);

    var stdDev = Math.sqrt(avgSquareDiff);
    return stdDev;
  }
  
  /**
   * Calculate average of a values in array
   */
  private average(data) {
    var sum = data.reduce(function(sum, value){
      return sum + value;
    }, 0);

    var avg = sum / data.length;
    return avg;
  }
  
  /**
   * Range slider 'slider stopped being adjusted' callback
   * - Calculate trajectory data average and standard deviation for 
   *   selected frame range (by default the electrostatic and Van der Waals)
   * - Only calculate when the slider is no longer being adjusted to keep
   *   the slider responsive.
   */
  public calculateStats() {
    
    for (var k of ['Elec','Vdw']) {
      
      for (var i in this.traj_data) {
        if (this.traj_data[i].key == k) {
          
          var data = this.traj_data[i].values;
          var col = [];
          for (var d in data) {
            if (data[d].x >= this.start && data[d].x <= this.end) {
              col.push(data[d].y);
            }
          }
          
          if (k == 'Elec') {
            this.std_elec = this.standardDeviation(col).toFixed(2);
            this.ave_elec = this.average(col).toFixed(2);
          }
          
          if (k == 'Vdw') {
            this.std_vdw = this.standardDeviation(col).toFixed(2);
            this.ave_vdw = this.average(col).toFixed(2);
          }
          
        }
      }
    }
  }
  
  /**
   * Range slider 'slider is being adjusted' callback
   * - Adjust start and end frame number and calculate frame range
   * - Values are activly updated while the user is adjusting the slider
   */ 
  public rangeSliderAdjust() {
    this.start = this.rangeSlider[0]; 
    this.end = this.rangeSlider[1]; 
    this.range = this.rangeSlider[1] - this.rangeSlider[0];
  }
}

@Component({
  selector:      'docking',
  moduleId:      module.id,
  templateUrl:   'docking.component.html',
  styleUrls:     ['docking.component.css'],
  encapsulation: ViewEncapsulation.None
})

@NgModule({
  imports: [HttpModule],
  declarations: [InputText, DataTable, ContextMenu, Button, Dialog, Column, nvD3, Slider, MultiSelect]
})
export class DockingComponent {
    
    // DataTable column selection
    public  availableColumns: SelectItem[];
    public  selectedColumns: string[] = ['id','compound','pose','range']; // Default columns
    
    // DataTable row selection
    public  selectedMD: MD[];
    public  mds: MD[];
    
    // MD details panel
  	public  data_has_changed: boolean = false;
    public  md_detail_unfold: boolean = false;   // Fold/unfold MD details panel 
    public  md: MD = new MDDetails();
    public  items: MenuItem[];
    
    // Trajectory chart
    // TODO: Define callback in nvD3 chart to get active brush extend after graph update
    //       and set active_brush_extend
    public  chart_options: any;
    public  chart_data: any;
    public  displayedTrajID: Number;
    public  active_brush_extend: Number[];
    
    @ViewChild(nvD3)
    nvD3: nvD3;
    
    constructor(private http: Http) {
      this.initColumnMultiselect(this.selectedColumns);
    }
    
    /**
     * Init component
     * - Retrieve information for the Molecular Dynamics runs for the current
     *   project from the server.
     * - Add first MD data table row to selectedMD array and init MD details panel
     * - Load the Elec/VdW energy trajectory for the first MD run and display
     *   as a chart.
     * - Update the column multiselect with data table columns names
     */
    public ngOnInit() {
      
        // Fetch MD information and load first trajectory
        this.loadProjectMDinfo()
          .then(mds => this.mds = mds)
          .then(mds => {
            this.selectedMD = [mds[0]],
            this.loadMDenergyTrajectory(mds[0]),
            this.md = this.cloneMD(mds[0]),
            this.initColumnMultiselect(Object.keys(mds[0]));
          });
        
        // Initiate contextual menu for the DataTable
        this.items = [
            {label: 'View', icon: 'fa-search', command: (event) => this.delete(this.selectedMD)},
            {label: 'Delete', icon: 'fa-close', command: (event) => this.delete(this.selectedMD)}
        ];
    }
    
    /**
     * User is leaving the component view
     * - If unsaved data, send data back to server
     */
    public ngOnDestroy() {
      
      if (this.data_has_changed) {
        console.log('TODO: implement data save on md.component exit');
      }
    }
    
    /**
     * Fetch MD energy trajectory data for MD run with id (id) and convert to
     * json format suitable for display with D3 chart.
     */
    private loadMDenergyTrajectory(md) {
      
      // Retrieve the new data. This will automatically update the chart.  
      this.http.get('assets/data/md-traj-' + md.id + '.json')
        .map((res: Response) => res.json())
        .map(res => res.map(function(series) {
          series.values = series.values.map(function(d) { 
            return {x: d[0], y: d[1] } });
          return series;
        }))
        .subscribe(
          res => {this.chart_data = res, this.updateChartInfo(md, res)},
          error => console.log('unable to update chart')
        );
    }
    
    /**
     * Update the D3.js style chart information object to display the
     * new/updated trajectory chart.
     */
    private updateChartInfo(md: MD, res?) {
      
      // Set the brush range. Full x range if md.end not defined.
      var brushrange = [md.start, md.end];
      if (!md.end) {
        var elec_values = res[0].values;
        brushrange = [0, elec_values[elec_values.length - 1].x];
      }
      
      var default_chart = { 
        chart: {
          type: 'lineWithFocusChart',
          useInteractiveGuideline: true,
          brushExtent: brushrange,
          margin: { top: 10, right: 75, bottom: 50, left: 75 },
          xAxis: {
            axisLabel: 'Frames',
          },
          x2Axis: {
            showMaxMin: false
          },
          yAxis: {
            axisLabel: 'Energy (kJ/mol)',
            tickFormat: function(d){
              return d3.format(',f')(d);
            },
          },
          y2Axis: {
            axisLabel: 'Energy (kJ/mol)',
            tickFormat: function(d) {
              return d3.format(',f')(d);
            }
          },
        }
      }
      
      this.chart_options = default_chart;
      
      // Set MD ID for charted trajectory
      this.displayedTrajID = md.id;
    }
    
    /**
     * Fetch information for the Molecular Dynamics runs for the current
     * project from the server.
     * - first convert data to JSON.
     * - then convert each untyped object to type MD.
     */
    private loadProjectMDinfo() {
        return this.http.get('assets/data/md-data.json')
                    .toPromise()
                    .then(res => <MD[]> res.json().data)
                    .then(data => {return data;});
    }
    
    /**
     * Update the multiselect dropdown with column names.
     */
    private initColumnMultiselect(columns: string[]) {
      
      this.availableColumns = [];
      for (var i of columns) {
        this.availableColumns.push({label:i, value:i});
      }
    }
    
    /**
     * Return the index of the selected MD row in the 
     * mds data array.
     */
    private findSelectedMDIndex(md) {
      return this.mds.indexOf(md);
    }
    
    /**
     * Clone the currently selected MD run and set the
     * MD range slider
     */
    private cloneMD(c: MD): MD {
      
      let md = new MDDetails(this.chart_data);
      for(let prop in c) {
        md[prop] = c[prop];
      }
      
      // Set MD frame range for range slider.
      md.rangeSlider = [md.start, md.end];
      
      // Update statistics
      md.calculateStats();
      
      return md;
    }
    
    /**
     * MultiSelect callback
     * - sort selected headers alphabetically.
     * - move 'id' to position 0.
     */
    public sortSelectedColumns() {
      
        this.selectedColumns.sort();
        var idx = this.selectedColumns.indexOf('id');
        if (idx > 0) {
          this.selectedColumns.splice(idx, 1);
          this.selectedColumns.unshift('id');
        }
    } 
    
    /**
     * Delete rows from the MD data table
     * - If first_selected == true, only delete the first entry in the 
     *   selectedMD array and load details of the next in line in case of
     *   multiple selection. This option is used when deleting from the
     *   MD details panel.
     * - If first_selected == false, remove all selected rows in the 
     *   selectedMD array.
     * - If selection empty, fold MD details panel and disable details button.
     */
    public delete(first_selected: boolean = false) {
      
      // Nothing selected nothing to delete
      if (this.selectedMD.length == 0) {
        return;
      }
      
      // Confirmation dialog
      var del_count = first_selected ? 1 : this.selectedMD.length;
      if (!confirm('Delete ' + del_count + ' trajectories?')) {
        return;
      }
      
      // Only delete first selected row, load MD details for first on stack.
      if (first_selected) {
          this.mds.splice(this.findSelectedMDIndex(this.selectedMD[0]), 1);
          this.selectedMD.shift();
          this.md = this.cloneMD(this.selectedMD[0]);
      }
      
      // Delete all selected rows
      else {
        for (var i = 0; i < this.selectedMD.length; i++) {
            this.mds.splice(this.findSelectedMDIndex(this.selectedMD[i]), 1);
        }
        this.selectedMD = [];
        this.md_detail_unfold = false;
        this.md = null;
      }
    }
    
    /**
     * Save changes made to MD details and update chart
     */
    public save() {
      
      // Update MD data table
      this.mds[this.findSelectedMDIndex(this.selectedMD[0])] = this.md;
      
      // Update chart
      this.updateChartInfo(this.md);
      this.nvD3.chart.update();
      
      // Tag the state of the data as changed
      this.data_has_changed = true;
    }
    
    /**
     * Reload table data only if data changed
     */
    public reload() {
      
      if (this.data_has_changed) {
        if (confirm('Reload MD data? any changes will be lost.')) {
          this.ngOnInit();
          this.data_has_changed = false;
        }
      }
    }
    
    /**
     * Reset data table sorting and filter settings
     */ 
    public update(dt: DataTable) {
      dt.reset();
    }
    
    /**
     * (Multi) row selection callback.
     * - displays the trajectory graph for the first item in the selection.
     * - Enable MD details panel unfold button. 
     */
    public onRowSelect(event) {
      
      if (this.selectedMD.length > 0) {
        
        // Don't reload the same data twice
        if (this.selectedMD[0].id != this.displayedTrajID) {
            this.loadMDenergyTrajectory(this.selectedMD[0]);
            this.md = this.cloneMD(this.selectedMD[0]);
        }
      } 
    }
}
