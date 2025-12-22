import { Routes } from '@angular/router';
import { DashboardComponent } from './dashboard/dashboard.component';
import { ManagerDashboardComponent } from './components/manager/manager-dashboard.component';

export const routes: Routes = [
    { path: '', component: DashboardComponent },
    { path: 'manager', component: ManagerDashboardComponent },
    { path: '**', redirectTo: '' }
];
