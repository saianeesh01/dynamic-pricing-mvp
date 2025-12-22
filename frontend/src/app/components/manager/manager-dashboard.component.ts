import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, Product, PricingLog } from '../../services/api.service';
import { GridModule } from '@progress/kendo-angular-grid';
import { Observable } from 'rxjs';

@Component({
    selector: 'app-manager-dashboard',
    standalone: true,
    imports: [CommonModule, GridModule],
    template: `
    <div class="p-8 bg-zinc-900 min-h-screen text-slate-100 font-sans">
      <header class="mb-8 flex justify-between items-center">
        <div>
           <h1 class="text-3xl font-black tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-orange-400 to-amber-500">
             MANAGER INTELLIGENCE
           </h1>
           <p class="text-zinc-500 text-sm mt-1 uppercase tracking-widest font-bold">AI Pricing & Inventory Control</p>
        </div>
        <button (click)="refresh()" class="px-6 py-2 rounded-lg bg-zinc-800 border border-zinc-700 hover:bg-zinc-700 transition-all font-bold text-sm text-zinc-300">
           REFRESH ENGINE
        </button>
      </header>

      <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <!-- Left: Inventory Grid -->
        <div class="xl:col-span-2 space-y-6">
          <div class="flex items-center gap-2 mb-2">
            <span class="w-1.5 h-6 bg-orange-500 rounded-full"></span>
            <h2 class="text-lg font-bold text-zinc-200">LIVE STOCK</h2>
          </div>
          
          <kendo-grid 
              [data]="(products$ | async) || []" 
              [height]="450"
              class="shadow-2xl rounded-2xl overflow-hidden border-none"
          >
              <kendo-grid-column field="name" title="Bottle Name" [width]="200"></kendo-grid-column>
              
              <kendo-grid-column field="inventory_count" title="Stock" [width]="100">
                  <ng-template kendoGridCellTemplate let-dataItem>
                      <div class="flex items-center gap-2">
                        <div class="w-2 h-2 rounded-full" [ngClass]="dataItem.inventory_count < 10 ? 'bg-red-500 animate-pulse' : 'bg-emerald-500'"></div>
                        <span class="font-mono text-xs uppercase">{{ dataItem.inventory_count }} PCS</span>
                      </div>
                  </ng-template>
              </kendo-grid-column>

              <kendo-grid-column field="current_price" title="Live Price" [width]="120">
                   <ng-template kendoGridCellTemplate let-dataItem>
                      <span class="font-bold text-white">{{ dataItem.current_price | currency }}</span>
                  </ng-template>
              </kendo-grid-column>

              <kendo-grid-column title="Actions" [width]="150">
                  <ng-template kendoGridCellTemplate let-dataItem>
                      <button (click)="simulateSale(dataItem)" class="text-[10px] bg-orange-600 hover:bg-orange-500 px-3 py-1.5 rounded-md font-black text-white transition-all shadow-lg shadow-orange-900/40 uppercase tracking-tighter">
                          SURGE DEMAND
                      </button>
                  </ng-template>
              </kendo-grid-column>
          </kendo-grid>
        </div>

        <!-- Right: Activity Log -->
        <div class="space-y-6">
          <div class="flex items-center gap-2 mb-2">
            <span class="w-1.5 h-6 bg-cyan-500 rounded-full"></span>
            <h2 class="text-lg font-bold text-zinc-200">PRICING LOGS</h2>
          </div>

          <div class="bg-zinc-800/30 rounded-2xl border border-zinc-800 p-4 space-y-4 max-h-[450px] overflow-y-auto backdrop-blur-md">
            <div *ngFor="let log of (logs$ | async)" class="p-4 bg-zinc-900/60 rounded-xl border border-zinc-800 hover:border-cyan-500/30 transition-all text-xs group">
              <div class="flex justify-between items-start mb-2 opacity-50 font-bold tracking-widest text-[10px] uppercase">
                <span>Product #{{ log.product_id }}</span>
                <span>{{ log.timestamp | date:'shortTime' }}</span>
              </div>
              <p class="text-cyan-100 font-bold mb-3 tracking-tight">{{ log.reason }}</p>
              <div class="flex items-center gap-3">
                <span class="text-zinc-500 line-through">{{ log.old_price | currency }}</span>
                <span class="text-emerald-400 font-black text-sm">→ {{ log.new_price | currency }}</span>
                <span class="ml-auto bg-cyan-500/10 text-cyan-400 px-2 py-1 rounded-md text-[10px] font-black border border-cyan-500/20">x{{ log.multiplier }}</span>
              </div>
            </div>
            <div *ngIf="!(logs$ | async)?.length" class="text-center py-20 text-zinc-700 text-sm font-bold uppercase tracking-widest">
              Awaiting initialization...
            </div>
          </div>
        </div>
      </div>

      <footer class="mt-8 pt-8 border-t border-zinc-800 flex justify-between items-center text-[10px] text-zinc-600 uppercase tracking-widest font-black">
        <div class="flex items-center gap-4">
            <span class="flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> ENGINE: ML ACTIVE</span>
            <span class="flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-cyan-500"></span> MODE: OPTIMIZED</span>
        </div>
        <div>Ethical Guardrails: Enforced (+20% / -15%)</div>
      </footer>
    </div>
  `,
    styles: [`
    :host ::ng-deep .k-grid {
        background-color: transparent;
        color: #e4e4e7;
        font-family: inherit;
        border: none;
    }
    :host ::ng-deep .k-grid-header {
        background-color: transparent;
        border-bottom: 1px solid #27272a;
    }
    :host ::ng-deep .k-grid-header .k-header {
        color: #52525b;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        font-size: 10px;
        padding: 1.5rem 1rem;
        background: transparent;
        border: none;
    }
    :host ::ng-deep .k-grid td {
        padding: 1.25rem 1rem;
        border-bottom: 1px solid #27272a;
        background: transparent;
    }
    :host ::ng-deep .k-grid-content {
        background-color: #09090b80;
    }
    :host ::ng-deep .k-grid tr.k-alt {
        background-color: transparent;
    }
    :host ::ng-deep .k-grid tr:hover {
        background-color: #18181b80 !important;
    }
  `]
})
export class ManagerDashboardComponent implements OnInit {
    private api = inject(ApiService);
    products$!: Observable<Product[]>;
    logs$!: Observable<PricingLog[]>;

    ngOnInit() {
        this.refresh();
    }

    refresh() {
        this.products$ = this.api.getProducts();
        this.logs$ = this.api.getPricingLogs();
    }

    simulateSale(product: Product) {
        this.api.calculatePrice(product.id).subscribe(() => this.refresh());
    }
}
