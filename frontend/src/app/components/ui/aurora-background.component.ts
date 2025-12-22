import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-aurora-background',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div class="relative flex flex-col h-[100vh] items-center justify-center bg-zinc-950 text-slate-950 transition-bg overflow-hidden">
      <div class="absolute inset-0 overflow-hidden">
        <div 
            class="pointer-events-none absolute -inset-[10px] opacity-50 will-change-transform"
            [ngClass]="{
                '[--white-gradient:repeating-linear-gradient(100deg,var(--white)_0%,var(--white)_7%,var(--transparent)_10%,var(--transparent)_12%,var(--white)_16%)]': true,
                '[--dark-gradient:repeating-linear-gradient(100deg,var(--black)_0%,var(--black)_7%,var(--transparent)_10%,var(--transparent)_12%,var(--black)_16%)]': true,
                '[--aurora:repeating-linear-gradient(100deg,#3b82f6_10%,#a855f7_15%,#0ea5e9_20%,#e879f9_25%,#3b82f6_30%)]': true
            }"
        >
            <div class="absolute inset-0 [background-image:var(--dark-gradient),var(--aurora)] [background-size:300%,_200%] [background-position:50%_50%,50%_50%] filter blur-[10px] invert-0 after:content-[''] after:absolute after:inset-0 after:[background-image:var(--dark-gradient),var(--aurora)] after:[background-size:200%,_100%] after:animate-aurora after:[background-attachment:fixed] after:mix-blend-difference"></div>
        </div>
      </div>
      <div class="relative z-10 w-full h-full overflow-y-auto">
        <ng-content></ng-content>
      </div>
    </div>
  `,
    styles: [`
    @keyframes aurora {
      from {
        background-position: 50% 50%, 50% 50%;
      }
      to {
        background-position: 350% 50%, 350% 50%;
      }
    }
    .animate-aurora {
      animation: aurora 60s linear infinite;
    }
  `]
})
export class AuroraBackgroundComponent {
    // Adapted from popular simplified Aurora implementations
}
