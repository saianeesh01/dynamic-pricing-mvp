import { Component, ElementRef, HostListener, Input, ViewChild, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-spotlight-card',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div 
      class="relative group rounded-3xl border border-slate-800 bg-slate-900/50 overflow-hidden"
      (mousemove)="handleMouseMove($event)"
      (mouseleave)="handleMouseLeave()"
    >
      <div 
        class="pointer-events-none absolute -inset-px rounded-3xl opacity-0 transition duration-300 group-hover:opacity-100"
        [style.background]="'radial-gradient(600px circle at ' + position().x + 'px ' + position().y + 'px, rgba(56, 189, 248, 0.15), transparent 40%)'"
      ></div>
      <div class="relative h-full">
        <ng-content></ng-content>
      </div>
    </div>
  `
})
export class SpotlightCardComponent {
    position = signal({ x: 0, y: 0 });

    @HostListener('mousemove', ['$event'])
    handleMouseMove(event: MouseEvent) {
        const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
        this.position.set({
            x: event.clientX - rect.left,
            y: event.clientY - rect.top
        });
    }

    handleMouseLeave() {
        // Optional: Reset or fade out handled by CSS
    }
}
