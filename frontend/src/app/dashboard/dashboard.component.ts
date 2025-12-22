import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, Product, Rule } from '../services/api.service';
import { Observable } from 'rxjs';
import { AuroraBackgroundComponent } from '../components/ui/aurora-background.component';
import { SpotlightCardComponent } from '../components/ui/spotlight-card.component';
import { trigger, transition, style, animate, stagger, query } from '@angular/animations';

@Component({
    selector: 'app-dashboard',
    standalone: true,
    imports: [CommonModule, AuroraBackgroundComponent, SpotlightCardComponent],
    templateUrl: './dashboard.component.html',
    animations: [
        trigger('staggerFade', [
            transition('* => *', [
                query(':enter', [
                    style({ opacity: 0, transform: 'translateY(10px)' }),
                    stagger(100, [
                        animate('0.3s ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
                    ])
                ], { optional: true })
            ])
        ])
    ]
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
        this.api.calculatePrice(product.id).subscribe(() => {
            this.refreshData();
        });
    }
}
