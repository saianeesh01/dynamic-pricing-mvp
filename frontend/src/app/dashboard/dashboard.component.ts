import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, Product, Rule } from '../services/api.service';
import { Observable } from 'rxjs';

@Component({
    selector: 'app-dashboard',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
    private api = inject(ApiService);

    products$!: Observable<Product[]>;
    rules$!: Observable<Rule[]>;

    ngOnInit() {
        this.refreshData();
    }

    refreshData() {
        this.products$ = this.api.getProducts();
        this.rules$ = this.api.getRules();
    }

    simulateDemand(product: Product) {
        // Optimistic UI or just reload
        this.api.calculatePrice(product.id).subscribe(() => {
            this.refreshData();
        });
    }
}
