/**
 * Command center sidebar: logo, one link per tab (with a live badge such as the
 * Critical count or "Draft"), then the phone simulator, About and Reset demo.
 * Below the lg breakpoint it collapses to an icon rail; labels stay for screen readers.
 *
 * Implements: PLAN.md §9.1 (navigation between the command center views). Owner: P1 (Frontend and UX).
 */
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import Icon, { type IconName } from './Icon';

export interface SidebarTab {
  id: string;
  label: string;
  icon: IconName;
  href: string;
  /** Short text beside the label ("3", "Draft"); `label` is what screen readers hear. */
  badge?: { text: string; label: string; className: string };
}

interface Props {
  tabs: SidebarTab[];
  active: string;
  resetDisabled: boolean;
  onAbout: () => void;
  onReset: () => void;
}

const ITEM =
  'relative flex h-11 w-full items-center gap-3 rounded-lg px-3 text-sm font-medium transition-colors duration-150';
const IDLE = 'text-stone-600 hover:bg-stone-200/60 hover:text-stone-900';

export default function Sidebar({ tabs, active, resetDisabled, onAbout, onReset }: Props) {
  return (
    <aside className="flex w-16 shrink-0 flex-col border-r border-stone-200 bg-panel lg:w-60">
      <div className="flex h-16 items-center gap-3 px-3 lg:px-4">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-stone-900 text-white">
          <Icon name="radio" className="h-5 w-5" />
        </span>
        <span className="hidden lg:block">
          <span className="block font-semibold leading-tight">StillHere</span>
          <span className="block text-xs text-stone-500">Medical-needs check-ins</span>
        </span>
      </div>

      <nav aria-label="Command center" className="flex-1 px-2 py-2 lg:px-3">
        <ul className="space-y-1">
          {tabs.map((t) => {
            const current = t.id === active;
            return (
              <li key={t.id}>
                <Link
                  to={t.href}
                  aria-current={current ? 'page' : undefined}
                  title={t.label}
                  className={`${ITEM} ${current ? 'bg-white text-stone-900 shadow-sm ring-1 ring-stone-200' : IDLE}`}
                >
                  {current && <span className="absolute inset-y-2 left-0 w-1 rounded-r bg-indigo-600" />}
                  <Icon name={t.icon} className={`h-5 w-5 ${current ? 'text-indigo-600' : ''}`} />
                  <span className="sr-only lg:not-sr-only">{t.label}</span>
                  {t.badge && (
                    <span
                      title={t.badge.label}
                      className={`absolute right-0.5 top-0.5 rounded-full px-1.5 text-[11px] font-semibold leading-4 lg:static lg:ml-auto ${t.badge.className}`}
                    >
                      <span aria-hidden="true">{t.badge.text}</span>
                      <span className="sr-only">, {t.badge.label}</span>
                    </span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="space-y-1 border-t border-stone-200 px-2 py-3 lg:px-3">
        <a href="/phone" target="_blank" rel="noreferrer" title="Phone simulator" className={`${ITEM} ${IDLE}`}>
          <Icon name="phone" className="h-5 w-5" />
          <Label>Phone simulator</Label>
          <Icon name="external" className="ml-auto hidden h-3.5 w-3.5 text-stone-400 lg:block" />
        </a>
        <button onClick={onAbout} title="About StillHere" className={`${ITEM} ${IDLE}`}>
          <Icon name="info" className="h-5 w-5" />
          <Label>About</Label>
        </button>
        <button onClick={onReset} disabled={resetDisabled} title="Reset demo" className={`${ITEM} ${IDLE} disabled:opacity-50`}>
          <Icon name="reset" className="h-5 w-5" />
          <Label>Reset demo</Label>
        </button>
      </div>
    </aside>
  );
}

function Label({ children }: { children: ReactNode }) {
  return <span className="sr-only lg:not-sr-only">{children}</span>;
}
