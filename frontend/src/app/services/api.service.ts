import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Product {
    id: number;
    name: string;
    base_price: number;
    current_price: number;
    inventory_count: number;
}

export interface Rule {
    id: number;
    name: string;
    rule_type: string;
    adjustment_factor: number;
    is_active: boolean;
}

@Injectable({
    providedIn: 'root'
})
export class ApiService {
    private http = inject(HttpClient);
    private apiUrl = 'http://127.0.0.1:5000';

    getProducts(): Observable<Product[]> {
        return this.http.get<Product[]>(`${this.apiUrl}/products`);
    }

    getRules(): Observable<Rule[]> {
        return this.http.get<Rule[]>(`${this.apiUrl}/rules`);
    }

    calculatePrice(productId: number): Observable<Product> {
        return this.http.post<Product>(`${this.apiUrl}/calculate-price/${productId}`, {});
    }
}
