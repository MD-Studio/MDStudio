/**
 * Component MDComponent
 *
 * Inspect Molecular Dynamics runs part of the current project.
 * - Visualize trajectory information as a time series plot with time 
 *   range selection support (visuals using D3.js)
 * - Inspect key MD parameters in a data table
 * - Modify parameters for single or multiple MD selections
 */

// Angular imports
import {Component,
        OnInit}               from '@angular/core';
import {CORE_DIRECTIVES}      from '@angular/common';
import {Http,
        HTTP_PROVIDERS,
        Response}             from '@angular/http';

// Third-party imports
import {InputText,
        DataTable,
        MenuItem,
        ContextMenu,
        Button,
        Dialog,
        Column,
        SelectItem,
        MultiSelect}          from 'primeng/primeng';
import {nvD3}                 from 'ng2-nvd3';

// App imports
import {UserService}          from '../../shared/services/src/user.service';
import {WampService}          from '../../shared/services/src/wamp.service';

// Global variable declaration
declare let d3: any;

// MD data object interface defenition
export interface MD {
    id;
    compound;
    range;
    pose;
    start;
    end;
}

class MDDetails implements MD {

    constructor(public id?, public compound?, public pose?, public start?, public end?, public range?) {}
}

@Component({
  selector:      'md',
  moduleId:      module.id,
  templateUrl:   'md.component.html',
  styleUrls:     ['md.component.css'],
  directives:    [InputText, DataTable, ContextMenu, Button, Dialog, Column, nvD3, MultiSelect],
  providers:     [HTTP_PROVIDERS],
})

export class MDComponent implements OnInit {
  
    // DataTable column selection
    public  availableColumns: SelectItem[];
    public  selectedColumns: [] = ['id','compound','pose','range']; // Default columns
    
    // DataTable row selection
    public  selectedMD: [];
    public  mds: MD[];
    
    // MD details panel
  	public  md_detail_unfold: boolean = false;
    public  md: MD = new MDDetails();
    public  items: MenuItem[];
    
    // Trajectory chart
    public  options;
    public  data;
    public  displayedTrajID: Number;

    constructor(private http: Http) {
      this.initColumnMultiselect(this.selectedColumns);
    }
    
    /**
     * Init component
     * - Retrieve information for the Molecular Dynamics runs for the current
     *   project from the server.
     * - Load the Elec/VdW energy trajectory for the first MD run and display
     *   as a chart.
     */
    public ngOnInit() {
      
        // Fetch MD information and load first trajectory
        this.loadProjectMDinfo()
          .then(mds => this.mds = mds)
          .then(mds => {
            this.loadMDenergyTrajectory(mds[0]),
            this.initColumnMultiselect(Object.keys(mds[0]));
          });
        
        // Initiate contextual menu for the DataTable
        this.items = [
          {label: 'View', icon: 'fa-search'},
          {label: 'Delete', icon: 'fa-close'}
        ];
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
          res => {this.data = res, this.updateChartInfo(md, res)},
          error => console.log('unable to update chart')
        );
    }
    
    /**
     * Update the D3.js style chart information object to display the
     * new/updated trajectory chart.
     */
    private updateChartInfo(md, res) {
      
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
          }
        }
      }
      
      this.options = default_chart;
      
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
    private initColumnMultiselect(columns: Array) {
      
      this.availableColumns = [];
      for (var i of columns) {
        this.availableColumns.push({label:i, value:i});
      }
    }
    
    private findSelectedMDIndex(md) {
        return this.mds.indexOf(md);
    }
    
    private cloneMD(c: MD): MD {
        let md = new MDDetails();
        for(let prop in c) {
            md[prop] = c[prop];
        }
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
     *   multiple selection. This option us used when deleting from the
     *   MD details panel.
     * - If first_selected == false, remove all selected rows in the 
     *   selectedMD array.
     */
    public delete(first_selected: boolean = false) {
      
      // Nothing selected nothing to delete
      if (this.selectedMD.length == 0) {
        return;
      }
      
      // Confirmation dialog
      var del_count = first_selected ? 1 : this.selectedMD.length;
      if (!confirm('Delete ${del_count} trajectories?')) {
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
        this.md = null;
      }
    }
    
    save() {
        this.mds[this.findSelectedMDIndex(this.selectedMD[0])] = this.md;
        this.md = null;
    }
    
    update(dt: DataTable) {
        dt.reset();
    }
    
    /**
     * (Multi) row selection callback.
     * - displays the trajectory graph for the first item in the selection
     */
    onRowSelect(event) {
      
      if (this.selectedMD.length > 0) {
        
        // Don't reload the same data twice
        if (this.selectedMD[0].id != this.displayedTrajID) {
            this.loadMDenergyTrajectory(this.selectedMD[0]);
            this.md = this.cloneMD(this.selectedMD[0]);
        }
      } 
    }
}
