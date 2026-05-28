{
  "file": "design_guidelines.md",
  "product": {
    "route": "/insights",
    "type": "dense BI / observability-style analytics hub inside CRM",
    "audience": [
      "master_admin/admin (company scope)",
      "team_lead (team scope)",
      "manager (personal scope)"
    ],
    "north_star": "One deep Insights area with 5 verticals (tabs), heavy drill-down, minimal nav proliferation."
  },
  "brand_attributes": {
    "keywords": [
      "serious",
      "calm",
      "information-rich",
      "operational",
      "trustworthy",
      "fast-to-scan",
      "actionable"
    ],
    "anti_keywords": [
      "marketing dashboard",
      "giant gradients",
      "card-only shallow",
      "centered hero layouts",
      "transparent surfaces"
    ]
  },
  "information_architecture": {
    "global_layout": {
      "page_header": {
        "pattern": "Keep existing PageHeader pattern: title + scope badge + period selector (Last 7/30/90) + optional filters.",
        "left": [
          "Title: Insights",
          "Scope badge (role-aware): Company / Your team / Personal",
          "Last updated timestamp (subtle)"
        ],
        "right": [
          "Period selector (existing pattern)",
          "Optional: global search (customer / deal / invoice id)",
          "Optional: export menu (CSV/PDF) for tables that support it"
        ],
        "data_testids": {
          "scope_badge": "insights-scope-badge",
          "period_selector": "insights-period-selector",
          "global_search": "insights-global-search-input",
          "export_menu": "insights-export-menu"
        }
      },
      "sticky_overview_kpi_strip": {
        "behavior": "Sticky within main scroll container (below PageHeader). Always visible while scrolling vertical content.",
        "composition": [
          "Revenue MTD",
          "Active Leads",
          "Win Rate",
          "Avg Cycle Time",
          "Composite Risk Score",
          "Critical Alerts"
        ],
        "layout": {
          "desktop": "6-up grid (xl:6 cols), compact KPI cards",
          "tablet": "3x2",
          "mobile": "2 rows wrap (2-3 per row depending width), horizontal scroll is allowed only if absolutely necessary"
        },
        "interaction": {
          "click": "Each KPI opens a Sheet with breakdown + trend + top contributors OR scrolls to the relevant section anchor in current vertical.",
          "hover": "Show delta vs previous period + tooltip definition.",
          "micro_motion": "On hover: border darkens + subtle shadow; on click: press scale 0.99 (no transform transitions globally)."
        },
        "data_testids": {
          "kpi_strip": "insights-kpi-strip",
          "kpi_revenue": "insights-kpi-revenue-mtd",
          "kpi_active_leads": "insights-kpi-active-leads",
          "kpi_win_rate": "insights-kpi-win-rate",
          "kpi_cycle_time": "insights-kpi-avg-cycle-time",
          "kpi_risk": "insights-kpi-composite-risk-score",
          "kpi_critical_alerts": "insights-kpi-critical-alerts"
        }
      },
      "horizontal_vertical_tabs": {
        "pattern": "Radix Tabs (shadcn tabs) as the ONLY navigation inside /insights.",
        "tabs": [
          "Traffic & Engagement",
          "Pipeline (sub-tabs: Leads / Deals)",
          "Revenue",
          "Team & Managers (hidden for manager role)",
          "Risk & Alerts (deepest)"
        ],
        "behavior": {
          "sticky": "Tabs row becomes sticky under KPI strip on scroll (optional but recommended for deep pages).",
          "mobile": "Tabs become horizontally scrollable with scrollbar-hide; keep active tab visible (scrollIntoView)."
        },
        "data_testids": {
          "tabs_root": "insights-vertical-tabs",
          "tab_traffic": "insights-tab-traffic",
          "tab_pipeline": "insights-tab-pipeline",
          "tab_revenue": "insights-tab-revenue",
          "tab_team": "insights-tab-team",
          "tab_risk": "insights-tab-risk",
          "pipeline_subtabs": "insights-pipeline-subtabs",
          "pipeline_tab_leads": "insights-pipeline-tab-leads",
          "pipeline_tab_deals": "insights-pipeline-tab-deals"
        }
      },
      "content_area": {
        "pattern": "Multi-section scrolling page per vertical. Use anchors for major sections; allow cards to scroll-to-section.",
        "grid": {
          "desktop": "12-col grid; primary charts span 7-8 cols, secondary panels 4-5 cols",
          "tablet": "single column with occasional 2-col",
          "mobile": "single column"
        },
        "density_rules": [
          "Prefer 2-column layouts on desktop to reduce scroll length.",
          "Use compact chart heights (220–280px) and small axis fonts.",
          "Tables should be the primary drill surface; charts are for shape/trend + click-to-filter."
        ]
      }
    }
  },
  "visual_system": {
    "palette": {
      "notes": [
        "Must work in light + dark themes.",
        "No transparent backgrounds; always use solid surfaces.",
        "Keep BIBI amber as accent; avoid gradients except tiny decorative accents (and never >20% viewport)."
      ],
      "tokens_css_variables": {
        "instruction": "Define these as CSS custom properties (preferably in index.css under :root and [data-theme='dark'] if present). Use HSL tokens already used by shadcn variables.",
        "light": {
          "--background": "0 0% 98%",
          "--foreground": "240 10% 4%",
          "--card": "0 0% 100%",
          "--card-foreground": "240 10% 4%",
          "--muted": "240 5% 96%",
          "--muted-foreground": "240 4% 46%",
          "--border": "240 6% 90%",
          "--ring": "41 100% 50%",
          "--primary": "240 6% 10%",
          "--primary-foreground": "0 0% 98%",
          "--accent": "41 100% 50%",
          "--accent-foreground": "0 0% 0%",
          "--success": "142 71% 35%",
          "--warning": "41 100% 50%",
          "--danger": "0 84% 60%",
          "--info": "199 89% 48%",
          "--surface-2": "240 5% 98%",
          "--surface-3": "240 5% 96%"
        },
        "dark": {
          "--background": "240 10% 4%",
          "--foreground": "0 0% 98%",
          "--card": "240 6% 10%",
          "--card-foreground": "0 0% 98%",
          "--muted": "240 4% 16%",
          "--muted-foreground": "240 5% 65%",
          "--border": "240 4% 18%",
          "--ring": "41 100% 50%",
          "--primary": "0 0% 98%",
          "--primary-foreground": "240 10% 4%",
          "--accent": "41 100% 50%",
          "--accent-foreground": "0 0% 0%",
          "--success": "142 71% 45%",
          "--warning": "41 100% 50%",
          "--danger": "0 84% 65%",
          "--info": "199 89% 55%",
          "--surface-2": "240 6% 12%",
          "--surface-3": "240 6% 14%"
        }
      },
      "semantic_color_rules": {
        "kpi_deltas": {
          "positive": "text-emerald-600 (dark: text-emerald-300) + subtle bg-emerald-50 (dark: rgba tint)",
          "negative": "text-red-600 (dark: text-red-300) + subtle bg-red-50",
          "neutral": "text-zinc-600 (dark: text-zinc-300)"
        },
        "severity": {
          "critical": "red",
          "high": "amber",
          "medium": "blue",
          "low": "zinc"
        },
        "risk_score": {
          "0-39": "good (emerald)",
          "40-69": "watch (amber)",
          "70-100": "critical (red)"
        }
      }
    },
    "typography": {
      "font_family": "Use existing Mazzard stack (already loaded). Do not introduce new fonts.",
      "scale": {
        "h1": "text-2xl sm:text-3xl lg:text-4xl font-semibold tracking-tight",
        "h2": "text-base md:text-lg font-medium",
        "card_title": "text-sm font-medium",
        "kpi_value": "text-xl sm:text-2xl font-semibold tabular-nums",
        "kpi_label": "text-[11px] font-medium uppercase tracking-wider text-muted-foreground",
        "body": "text-sm text-foreground",
        "meta": "text-xs text-muted-foreground",
        "table_header": "text-[11px] font-medium uppercase tracking-wider",
        "mono_numbers": "Use tabular-nums everywhere for KPIs and tables"
      },
      "density": {
        "rule": "Prefer text-sm for body in dashboards; reserve text-base for empty states and long explanations only."
      }
    },
    "spacing_and_radius": {
      "tokens": {
        "page_padding": "px-4 sm:px-6 lg:px-8",
        "section_gap": "gap-4 lg:gap-6",
        "card_padding": "p-4 sm:p-5",
        "card_radius": "rounded-2xl",
        "control_height": "h-9 (dense), h-10 (default)"
      },
      "rule": "Use 2–3x more whitespace between sections than inside cards."
    },
    "shadows_and_borders": {
      "rule": "Match existing vocabulary: border border-zinc-200 (dark: border-zinc-800) + shadow-sm. Avoid heavy shadows.",
      "hover": "On hover: border-zinc-300 (dark: border-zinc-700) + shadow-md (subtle)."
    }
  },
  "component_vocabulary": {
    "primary_primitives": {
      "tabs": "/app/frontend/src/components/ui/tabs.jsx",
      "card": "/app/frontend/src/components/ui/card.jsx",
      "badge": "/app/frontend/src/components/ui/badge.jsx",
      "table": "/app/frontend/src/components/ui/table.jsx",
      "tooltip": "/app/frontend/src/components/ui/tooltip.jsx",
      "sheet": "/app/frontend/src/components/ui/sheet.jsx",
      "dialog": "/app/frontend/src/components/ui/dialog.jsx",
      "select": "/app/frontend/src/components/ui/select.jsx",
      "popover": "/app/frontend/src/components/ui/popover.jsx",
      "separator": "/app/frontend/src/components/ui/separator.jsx",
      "scroll_area": "/app/frontend/src/components/ui/scroll-area.jsx",
      "skeleton": "/app/frontend/src/components/ui/skeleton.jsx",
      "button": "/app/frontend/src/components/ui/button.jsx",
      "input": "/app/frontend/src/components/ui/input.jsx",
      "calendar": "/app/frontend/src/components/ui/calendar.jsx",
      "sonner": "/app/frontend/src/components/ui/sonner.jsx"
    },
    "existing_admin_helpers": {
      "section_tabs": "/app/frontend/src/components/ui/SectionTabs.jsx",
      "role_badge": "/app/frontend/src/components/ui/RoleZoneBadge.jsx",
      "ui_states": "/app/frontend/src/components/ui/UIStates.js",
      "refresh_button": "/app/frontend/src/components/ui/RefreshButton.jsx",
      "reassign_dialog": "/app/frontend/src/components/ui/ReassignDialog.jsx",
      "white_date_picker": "/app/frontend/src/components/ui/WhiteDatePicker.jsx"
    },
    "composition_patterns": {
      "kpi_tile": "Card + (label + value + delta badge) + optional sparkline (Recharts LineChart) + onClick opens Sheet",
      "chart_card": "CardHeader (title + actions) + CardContent (ResponsiveContainer chart) + CardFooter (legend + last updated)",
      "table_card": "CardHeader (title + filters) + CardContent (ScrollArea + Table) + CardFooter (pagination / summary)",
      "filter_bar": "Select + Input + ToggleGroup + Button (ghost) for reset",
      "drilldown_sheet": "SheetContent right side, width: 520–720px desktop; full-screen on mobile"
    }
  },
  "layout_blueprints": {
    "vertical_1_traffic_engagement": {
      "goal": "Explain acquisition → engagement → intent → hot leads; connect spend/ROI to pipeline outcomes.",
      "section_order": [
        {
          "id": "traffic-funnel",
          "title": "Visits Funnel",
          "layout": "2-col desktop",
          "left": "Funnel chart (Visits → Vehicle views → Favorites → Compare → Lead submit)",
          "right": "Top traffic sources table + conversion rate per source",
          "drilldowns": [
            "Click funnel step → Sheet: step definition + time-series + top pages/vehicles",
            "Click source row → Sheet: campaigns list + ROI + downstream leads"
          ],
          "data_testids": {
            "card": "insights-traffic-funnel-card",
            "chart": "insights-traffic-funnel-chart",
            "sources_table": "insights-traffic-sources-table"
          }
        },
        {
          "id": "campaign-roi",
          "title": "Campaign ROI & Optimizer",
          "layout": "12-col; chart 8 cols + optimizer 4 cols",
          "content": [
            "ROI time-series (spend vs attributed revenue)",
            "Optimizer panel: underperforming campaigns, suggested budget shifts (no mock; show computed deltas)"
          ],
          "drilldowns": [
            "Click campaign → Sheet: daily spend, CPL, lead quality, downstream win rate"
          ],
          "data_testids": {
            "card": "insights-campaign-roi-card",
            "optimizer": "insights-campaign-optimizer-panel"
          }
        },
        {
          "id": "engagement",
          "title": "User Engagement",
          "layout": "3-up small multiples",
          "content": [
            "Favorites trend",
            "Compares trend",
            "Shares trend"
          ],
          "drilldowns": [
            "Click point → filter tables below by date range"
          ],
          "data_testids": {
            "card": "insights-engagement-card"
          }
        },
        {
          "id": "top_entities",
          "title": "Top Users / Vehicles / Hot Leads",
          "layout": "3 cards row on desktop; stack on mobile",
          "content": [
            "Top users table (activity score)",
            "Top vehicles table (views + saves)",
            "Hot leads table with AI intent score + last activity"
          ],
          "drilldowns": [
            "Click user → Sheet: profile + timeline + owned leads",
            "Click vehicle → Sheet: listing performance + lead attribution",
            "Click hot lead → Sheet: customer drill-down + recommended next action"
          ],
          "data_testids": {
            "top_users": "insights-top-users-table",
            "top_vehicles": "insights-top-vehicles-table",
            "hot_leads": "insights-hot-leads-table"
          }
        }
      ]
    },
    "vertical_2_pipeline": {
      "goal": "Make pipeline health obvious: where leads stall, which managers convert, where deals bottleneck.",
      "subtabs": {
        "leads": {
          "section_order": [
            {
              "id": "leads-funnel",
              "title": "Leads Funnel",
              "layout": "chart + breakdown",
              "content": [
                "Funnel: New → Qualified → Contacted → Converted",
                "Side panel: conversion rates + median time-in-stage"
              ],
              "drilldowns": [
                "Click stage → Sheet: list of leads in stage + aging histogram + owners"
              ],
              "data_testids": {
                "card": "insights-leads-funnel-card"
              }
            },
            {
              "id": "stale-leads",
              "title": "Stale Leads (Need Action)",
              "layout": "full-width table",
              "content": [
                "Table columns: Lead, Owner, Source, Age, Last touch, Next step, Risk chip",
                "Inline actions: open, reassign, snooze"
              ],
              "drilldowns": [
                "Row click → Sheet: lead timeline + contact attempts + recommended action"
              ],
              "data_testids": {
                "table": "insights-stale-leads-table",
                "filter_owner": "insights-stale-leads-owner-filter",
                "filter_source": "insights-stale-leads-source-filter"
              }
            },
            {
              "id": "conversion-per-manager",
              "title": "Conversion per Manager",
              "layout": "bar chart + ranking table",
              "drilldowns": [
                "Click manager → Sheet: manager funnel + lead list"
              ],
              "data_testids": {
                "card": "insights-conversion-per-manager-card"
              }
            }
          ]
        },
        "deals": {
          "section_order": [
            {
              "id": "journey-funnel",
              "title": "Deals Journey Funnel",
              "layout": "chart 8 cols + bottlenecks 4 cols",
              "content": [
                "Stage distribution + win/loss",
                "Bottlenecks panel: stages with longest duration"
              ],
              "drilldowns": [
                "Click stage → Sheet: deals list + stage aging + blockers"
              ],
              "data_testids": {
                "card": "insights-deals-journey-funnel-card"
              }
            },
            {
              "id": "cycle-time",
              "title": "Cycle Time per Stage",
              "layout": "line/area chart + table",
              "content": [
                "Time-series of avg cycle time",
                "Table: stage, avg days, p75 days, trend"
              ],
              "drilldowns": [
                "Click stage row → Sheet: distribution chart + example deals"
              ],
              "data_testids": {
                "card": "insights-cycle-time-card"
              }
            },
            {
              "id": "win-loss",
              "title": "Win/Loss Reasons",
              "layout": "stacked bar + reasons table",
              "drilldowns": [
                "Click reason → filter deals table"
              ],
              "data_testids": {
                "card": "insights-win-loss-card"
              }
            }
          ]
        }
      }
    },
    "vertical_3_revenue": {
      "goal": "Revenue truth: trend, ageing risk, contracts/documents operational flow, unpaid drill-down.",
      "section_order": [
        {
          "id": "revenue-trend",
          "title": "Revenue Trend",
          "layout": "chart + breakdown",
          "content": [
            "Line chart: daily/weekly revenue",
            "Breakdown: by payment method / manager / channel"
          ],
          "drilldowns": [
            "Click series → Sheet: ledger slice + export"
          ],
          "data_testids": {
            "card": "insights-revenue-trend-card"
          }
        },
        {
          "id": "ar-ageing",
          "title": "AR Ageing",
          "layout": "bucket cards + table",
          "content": [
            "Buckets: 0–30 / 30–60 / 60–90 / 90+",
            "Table: invoice, customer, amount, age, owner, status"
          ],
          "drilldowns": [
            "Click bucket → filter table",
            "Row click → Sheet: invoice timeline + reminders + actions"
          ],
          "data_testids": {
            "bucket_0_30": "insights-ar-bucket-0-30",
            "bucket_90_plus": "insights-ar-bucket-90-plus",
            "table": "insights-ar-invoices-table"
          }
        },
        {
          "id": "contracts-ledger",
          "title": "Contracts Ledger",
          "layout": "full-width table with filters",
          "content": [
            "Filters: status, manager, date range, amount range",
            "Export button"
          ],
          "drilldowns": [
            "Row click → Sheet: contract details + linked docs + payments"
          ],
          "data_testids": {
            "table": "insights-contracts-ledger-table",
            "export": "insights-contracts-export-button"
          }
        },
        {
          "id": "documents-registry",
          "title": "Documents Registry & Verification Queue",
          "layout": "2-col: registry + queue",
          "content": [
            "Registry table",
            "Verification queue with inline approve/reject"
          ],
          "drilldowns": [
            "Doc click → Dialog: preview + metadata + audit trail"
          ],
          "data_testids": {
            "registry": "insights-documents-registry-table",
            "verification_queue": "insights-documents-verification-queue"
          }
        }
      ]
    },
    "vertical_4_team_managers": {
      "visibility": "Hidden for manager role.",
      "goal": "Operational management: ranking, load, SLA, and audit.",
      "section_order": [
        {
          "id": "manager-scorecards",
          "title": "Manager Scorecards",
          "layout": "ranking table + sparkline column",
          "content": [
            "KPIs: active leads, conversion, revenue, response time, risk",
            "Rank + delta"
          ],
          "drilldowns": [
            "Click manager → Sheet: manager deep view (mini-dashboard)"
          ],
          "data_testids": {
            "table": "insights-manager-scorecards-table"
          }
        },
        {
          "id": "load-board",
          "title": "Manager Load Board",
          "layout": "kanban-like table (not a new lib): use Table with grouped rows",
          "content": [
            "Columns: manager, active leads, active customers, active deals, overdue tasks",
            "Conditional highlight for overload"
          ],
          "drilldowns": [
            "Click overload chip → Sheet: list of items causing overload"
          ],
          "data_testids": {
            "table": "insights-manager-load-board"
          }
        },
        {
          "id": "sla-response",
          "title": "SLA / Response Time",
          "layout": "table + distribution chart",
          "content": [
            "Table: manager, median response, p90 response, breaches",
            "Chart: response time distribution"
          ],
          "drilldowns": [
            "Click breaches → Sheet: breach events list"
          ],
          "data_testids": {
            "card": "insights-sla-response-card"
          }
        },
        {
          "id": "login-audit",
          "title": "Login Activity Audit",
          "layout": "full-width table",
          "content": [
            "Columns: user, role, last login, IP/device, anomalies"
          ],
          "drilldowns": [
            "Click anomaly → Sheet: session history"
          ],
          "data_testids": {
            "table": "insights-login-audit-table"
          }
        }
      ]
    },
    "vertical_5_risk_alerts": {
      "goal": "Triage-first operational console: understand risk drivers, act on alerts, clear stuck items.",
      "section_order": [
        {
          "id": "risk-overview",
          "title": "Risk Overview",
          "layout": "12-col: score viz 7 cols + drivers 5 cols",
          "content": [
            "Composite risk score gauge-like visualization (use Recharts RadialBarChart or Pie with centered label)",
            "Risk score time-series (LineChart) with annotations for spikes",
            "Top risk drivers list (e.g., stale leads, overdue invoices, stalled shipments)"
          ],
          "drilldowns": [
            "Click driver → scroll to Stuck Items section filtered",
            "Click time-series spike → Sheet: what changed (top contributors)"
          ],
          "data_testids": {
            "card": "insights-risk-overview-card",
            "score": "insights-risk-composite-score",
            "timeseries": "insights-risk-timeseries-chart",
            "drivers": "insights-risk-drivers-list"
          }
        },
        {
          "id": "risk-by-entity",
          "title": "Risk by Manager / Team / Deal",
          "layout": "tabs inside card (Manager | Team | Deal) + table",
          "content": [
            "Table columns: entity, risk score, trend sparkline, top driver, critical alerts count",
            "Row heat: subtle background tint based on risk band (never full red fill; use left border accent)"
          ],
          "drilldowns": [
            "Row click → Sheet: entity risk profile (timeline + items list + actions)"
          ],
          "data_testids": {
            "card": "insights-risk-by-entity-card",
            "tab_manager": "insights-risk-entity-tab-manager",
            "tab_team": "insights-risk-entity-tab-team",
            "tab_deal": "insights-risk-entity-tab-deal",
            "table": "insights-risk-entity-table"
          }
        },
        {
          "id": "critical-alerts-feed",
          "title": "Critical Alerts (Live Feed)",
          "layout": "2-col: feed 7 cols + filters/summary 5 cols",
          "content": [
            "Feed cells with severity, title, entity, age, SLA remaining, last event, owner",
            "Filters: severity, type, owner, SLA breached, status (open/ack/resolved)",
            "Show 'Last updated' + auto-refresh toggle (manual refresh button preferred)"
          ],
          "row_anatomy": {
            "left_rail": "Severity bar (4px) + icon",
            "main": "Title (1 line) + meta row (entity • owner • created) + last event snippet",
            "right": "Age chip + SLA chip + actions (Resolve / Reassign / Snooze)"
          },
          "inline_actions": {
            "resolve": "Button variant=secondary, small; confirm via AlertDialog",
            "reassign": "Use existing ReassignDialog",
            "snooze": "Popover with durations (1h, 4h, 1d)"
          },
          "drilldowns": [
            "Click cell → Sheet: full alert timeline + linked objects + audit trail"
          ],
          "data_testids": {
            "card": "insights-critical-alerts-card",
            "filters": "insights-alerts-filters",
            "feed": "insights-alerts-feed",
            "refresh": "insights-alerts-refresh-button",
            "auto_refresh": "insights-alerts-auto-refresh-toggle"
          }
        },
        {
          "id": "escalation-queue",
          "title": "Escalation Queue",
          "layout": "full-width table (dense) with sticky header",
          "content": [
            "Columns: Priority, Item, Owner, Queue, Age, SLA, Risk score, Next action",
            "Row states: new (subtle dot), acknowledged, breached (red outline), snoozed (muted)"
          ],
          "drilldowns": [
            "Row click → Sheet: escalation detail + reassignment history + resolve workflow"
          ],
          "data_testids": {
            "table": "insights-escalation-queue-table",
            "filter_severity": "insights-escalation-filter-severity",
            "filter_queue": "insights-escalation-filter-queue"
          }
        },
        {
          "id": "stuck-items",
          "title": "Unified Stuck Items",
          "layout": "segmented control + table",
          "content": [
            "Segmented: All | Stale leads | Overdue invoices | Stalled shipments",
            "Table columns: Type, Item, Owner, Age, Amount (if any), Last update, Blocker, Action"
          ],
          "drilldowns": [
            "Click type segment → filter table",
            "Row click → Sheet: item timeline + unblock actions"
          ],
          "data_testids": {
            "segmented": "insights-stuck-items-segmented",
            "table": "insights-stuck-items-table"
          }
        }
      ],
      "showcase_details": {
        "composite_score_visual": {
          "recommended": "Radial score with 3 bands + center number + delta vs previous period.",
          "implementation_hint": "Use Recharts RadialBarChart with background track; keep colors muted; add a small legend for bands.",
          "color": "Use emerald/amber/red only as accents; the majority of the chart should be neutral track."
        },
        "alert_cell_micro_interactions": [
          "Hover: reveal secondary actions; keep primary action always visible for critical.",
          "Click: open Sheet; preserve scroll position.",
          "Keyboard: Up/Down to move focus between rows; Enter opens Sheet."
        ],
        "escalation_row_states": {
          "breached": "left border red-500 + subtle bg-red-50 (dark: rgba)",
          "due_soon": "left border amber-500 + subtle bg-amber-50",
          "ok": "left border transparent"
        }
      }
    }
  },
  "kpi_strip_rules": {
    "visual": {
      "style": "Compact KPI cards (existing .kpi-card--compact + .kpi-value--fit).",
      "no_gradients": "Do not use gradients in KPI strip.",
      "icons": "Optional small lucide-react icon in muted tone; never emoji."
    },
    "color_logic": {
      "revenue_mtd": "Show delta vs previous period; green if up, red if down.",
      "active_leads": "Neutral by default; amber if above capacity threshold (team/managers vertical defines capacity).",
      "win_rate": "Green if up; amber if flat; red if down > Xpp.",
      "avg_cycle_time": "Red if increased; green if decreased.",
      "composite_risk_score": "Use risk bands 0–39/40–69/70–100.",
      "critical_alerts": "Red if >0; show count as badge; clicking jumps to Risk & Alerts tab and scrolls to feed."
    }
  },
  "states": {
    "loading": {
      "pattern": "Skeleton inside each card; keep card chrome visible to prevent layout shift.",
      "components": ["/app/frontend/src/components/ui/skeleton.jsx"],
      "data_testids": {
        "card_loading": "insights-card-loading"
      }
    },
    "empty": {
      "pattern": "Use UIStates.js empty state component if available; otherwise: icon + title + 1-line explanation + secondary action (adjust filters).",
      "tone": "Operational, not playful.",
      "examples": [
        "No alerts match current filters.",
        "No revenue data for selected period.",
        "No stale leads — good job."
      ],
      "data_testids": {
        "empty_state": "insights-empty-state"
      }
    },
    "error": {
      "pattern": "Inline Alert component with retry button + error id.",
      "components": ["/app/frontend/src/components/ui/alert.jsx", "/app/frontend/src/components/ui/button.jsx"],
      "data_testids": {
        "error_state": "insights-error-state",
        "retry": "insights-error-retry-button"
      }
    }
  },
  "role_scoping_visual_cues": {
    "badge": {
      "placement": "Next to page title in PageHeader.",
      "style": "Badge variant=secondary; text-xs; icon optional.",
      "copy": {
        "company": "Company",
        "team": "Your team",
        "personal": "Personal"
      }
    },
    "subtle_explainer": {
      "placement": "Under title as meta text.",
      "examples": [
        "Showing company-wide performance.",
        "Showing your team’s performance.",
        "Showing your personal performance."
      ]
    },
    "no_access_pages": "Never show access denied; hide Team & Managers tab for manager role and scope queries silently."
  },
  "charts_recharts_guidance": {
    "defaults": {
      "container": "Always wrap charts in ResponsiveContainer.",
      "font": "Use small tick font: 11px; axis stroke muted.",
      "grid": "Use light CartesianGrid with strokeDasharray='3 3' and low opacity.",
      "tooltip": "Use shadcn Tooltip for definitions; Recharts Tooltip for data hover with custom content component."
    },
    "color_usage": {
      "rule": "Use neutral series by default (zinc/gray). Use amber only for highlight series or selected entity.",
      "avoid": "Avoid rainbow palettes; max 3 series per chart unless small multiples."
    }
  },
  "motion_microinteractions": {
    "principles": [
      "Motion should clarify hierarchy and state, not decorate.",
      "Use framer-motion for: tab content entrance (fade+translateY 6px), sheet open, row highlight on update.",
      "Respect prefers-reduced-motion."
    ],
    "allowed_transitions": {
      "buttons": "transition-colors duration-150",
      "cards": "transition-[box-shadow,border-color] duration-150",
      "rows": "transition-colors duration-100"
    },
    "forbidden": ["transition-all"]
  },
  "mobile_breakpoints": {
    "rules": [
      "KPI strip wraps to 2 rows; keep numbers from overflowing (use existing clamp styles).",
      "Tabs become horizontally scrollable; show subtle edge fade using a pseudo-element (optional).",
      "Sheets become full-screen (width: 100vw) with sticky header inside sheet.",
      "Tables: allow horizontal scroll inside ScrollArea; keep first column sticky only if already supported—otherwise avoid complex sticky columns on mobile."
    ]
  },
  "implementation_notes_js": {
    "file_convention": "Project uses .js/.jsx. Provide components in .jsx and hooks in .js.",
    "data_testid_rule": "Every interactive element and key info element must include data-testid in kebab-case.",
    "suggested_component_structure": [
      "src/pages/InsightsPage.jsx (default export)",
      "src/components/insights/OverviewKpiStrip.jsx",
      "src/components/insights/InsightsVerticalTabs.jsx",
      "src/components/insights/verticals/RiskAlertsVertical.jsx",
      "src/components/insights/verticals/PipelineVertical.jsx",
      "src/components/insights/verticals/TrafficVertical.jsx",
      "src/components/insights/verticals/RevenueVertical.jsx",
      "src/components/insights/verticals/TeamManagersVertical.jsx",
      "src/components/insights/drilldowns/EntitySheet.jsx",
      "src/components/insights/drilldowns/AlertSheet.jsx"
    ]
  },
  "image_urls": {
    "note": "No marketing imagery needed; this is an internal BI console. Use icons + charts. If any illustration is required for empty states, use simple inline SVG (no external images).",
    "categories": []
  },
  "instructions_to_main_agent": [
    "Keep /insights as ONE route with role-aware scoping; do not create separate pages per role.",
    "Use shadcn/ui primitives from /app/frontend/src/components/ui only.",
    "No transparent backgrounds; cards must be solid and theme-safe.",
    "Risk & Alerts must be the deepest vertical: triage feed + escalation queue + stuck items + risk drivers + entity breakdown.",
    "Implement drill-down via Sheet/Dialog; preserve scroll position.",
    "Charts must be dense and readable: small fonts, limited series, neutral palette with amber highlight.",
    "Add data-testid to all interactive and key informational elements.",
    "Do not add new libraries (Recharts, Radix, framer-motion already available)."
  ],
  "general_ui_ux_design_guidelines_appendix": "<General UI UX Design Guidelines>  \n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
