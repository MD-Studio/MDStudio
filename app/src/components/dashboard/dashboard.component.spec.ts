/**
 * Test Component Dashboard
 */

import {Component} from "@angular/core";
import {NgModule}  from '@angular/core';
import {DashboardComponent} from "./dashboard.component";

@Component({
    selector: 'test-cmp',
    template: '<sd-app></sd-app>'
})
@NgModule({
  declarations: [TestApp],
  bootstrap: [TestApp]
})

class TestApp{}