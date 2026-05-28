/**
 * InsightsHelpTooltip.jsx
 *
 * Reused everywhere across /admin/insights — same visual / interaction language
 * as the legacy Dashboard tooltips: dark `#18181B` rounded panel, hover delay,
 * inline `HelpCircle` trigger next to section / KPI / tab titles.
 *
 *   <InsightsHelpTooltip text={t('ins_tip_revenue_mtd')} />        // inline icon
 *   <InsightsHelpTooltip text={...}>                                // wrap children
 *     <span>Revenue MTD</span>
 *   </InsightsHelpTooltip>
 *
 * Built on the existing shadcn/Radix `Tooltip` so it inherits keyboard /
 * accessibility behaviour and does not introduce a new dependency.
 */
import React from 'react';
import { Question } from '@phosphor-icons/react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../../ui/tooltip';

/** Shared tooltip-panel className — same look across all Insights surfaces. */
const PANEL_CLASS =
  'max-w-xs sm:max-w-sm bg-[#18181B] text-white text-[12px] leading-relaxed px-3 py-2 rounded-lg shadow-lg';

const InsightsHelpTooltip = ({
  text,
  side = 'top',
  align = 'start',
  delay = 150,
  iconSize = 12,
  className = '',
  children,
}) => {
  if (!text) return children || null;
  return (
    <TooltipProvider delayDuration={delay}>
      <Tooltip>
        <TooltipTrigger asChild>
          {children ? (
            <span className={`inline-flex cursor-help items-center gap-1 ${className}`}>
              {children}
              <Question
                size={iconSize}
                weight="duotone"
                className="shrink-0 text-zinc-400 transition-colors hover:text-zinc-600"
              />
            </span>
          ) : (
            <button
              type="button"
              aria-label="info"
              className={`inline-flex shrink-0 cursor-help items-center justify-center text-zinc-400 transition-colors hover:text-zinc-600 ${className}`}
            >
              <Question size={iconSize} weight="duotone" />
            </button>
          )}
        </TooltipTrigger>
        <TooltipContent side={side} align={align} className={PANEL_CLASS}>
          {text}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default InsightsHelpTooltip;
