import React, {
  useState,
  useEffect,
  useRef,
  useMemo,
  useCallback,
} from "react";
import { createRoot } from "react-dom/client";
import { createPortal } from "react-dom";
import {
  motion,
  AnimatePresence,
  useReducedMotion,
  MotionConfig,
} from "motion/react";
import {
  Search,
  Bell,
  Sun,
  Moon,
  Menu,
  X,
  ArrowUpRight,
  ArrowRight,
  ArrowDownLeft,
  LayoutDashboard,
  Layers,
  Plus,
  Archive,
  ChartNoAxesCombined,
  Laptop,
  Box,
  ArrowLeftRight,
  Undo2,
  ShieldAlert,
  History,
  FileChartColumn,
  CheckCheck,
  Building2,
  Users,
  Settings,
  LogOut,
  ChevronsUpDown,
  RefreshCw,
  AlertTriangle,
  Pin,
  CircleCheck,
  Circle,
  Sparkles,
  SlidersHorizontal,
  Clock3,
  Eye,
  LockKeyhole,
  Grid2X2,
  List,
  Keyboard,
  CornerDownLeft,
  ChevronLeft,
  ChevronRight,
  ArrowDownUp,
  Monitor,
  Smartphone,
  Tablet,
  Headphones,
  Package,
  MapPin,
  CalendarDays,
  ChevronDown,
  Check,
  Printer,
  Inbox,
} from "lucide-react";
import "./fonts.css";

document.querySelectorAll("[data-count]").forEach((element) => {
  element.textContent = "";
});
const config = document.getElementById("experience-root").dataset;
const base = config.base || "";
const path = (value) => base + value;
const icons = {
  external: ArrowUpRight,
  arrow: ArrowRight,
  dashboard: LayoutDashboard,
  layers: Layers,
  plus: Plus,
  archive: Archive,
  bell: Bell,
  chart: ChartNoAxesCombined,
  laptop: Laptop,
  box: Box,
  arrows: ArrowLeftRight,
  return: Undo2,
  shield: ShieldAlert,
  history: History,
  report: FileChartColumn,
  check: CheckCheck,
  building: Building2,
  users: Users,
  settings: Settings,
  logout: LogOut,
  chevrons: ChevronsUpDown,
  refresh: RefreshCw,
  alert: AlertTriangle,
  pin: Pin,
  circle: Circle,
  sparkles: Sparkles,
  sliders: SlidersHorizontal,
  clock: Clock3,
  eye: Eye,
  lock: LockKeyhole,
};
const deviceIcon = (category) =>
  category?.includes("Phone")
    ? Smartphone
    : category?.includes("Tablet")
      ? Tablet
      : category?.includes("Monitor") || category?.includes("Desktop")
        ? Monitor
        : category?.includes("Headset")
          ? Headphones
          : category?.includes("Laptop")
            ? Laptop
            : Package;
const dateLabel = (value) =>
  value
    ? value.slice(0, 16).replace("T", " ") + (value.includes("T") ? " UTC" : "")
    : "Not recorded";
const statusClass = (status) =>
  ({
    Assigned: "assigned",
    Missing: "missing",
    "Under Repair": "repair",
    Retired: "retired",
  })[status] || "available";
function Status({ value }) {
  return (
    <span className={`status-badge status-${statusClass(value)}`}>{value}</span>
  );
}

async function api(url, options = {}) {
  const response = await fetch(path(url), {
    ...options,
    headers: { Accept: "application/json", ...options.headers },
  });
  if (
    !response.ok ||
    !response.headers.get("content-type")?.includes("application/json")
  )
    throw new Error("Your session may have expired. Please sign in again.");
  return response.json();
}
function Dialog({ open, onClose, className, label, children }) {
  const ref = useRef(null),
    opener = useRef(null);
  useEffect(() => {
    const dialog = ref.current;
    if (open && !dialog.open) {
      opener.current = document.activeElement;
      dialog.showModal();
    }
    if (!open && dialog.open) {
      dialog.close();
      opener.current?.focus();
    }
  }, [open]);
  return (
    <dialog
      ref={ref}
      className={className}
      aria-label={label}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      onClick={(e) => {
        if (e.target === ref.current) {
          const r = ref.current.getBoundingClientRect();
          if (
            e.clientX < r.left ||
            e.clientX > r.right ||
            e.clientY < r.top ||
            e.clientY > r.bottom
          )
            onClose();
        }
      }}
    >
      {children}
    </dialog>
  );
}
function useTheme() {
  const [theme, setTheme] = useState(
    document.documentElement.dataset.theme || "light",
  );
  const toggle = () => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("cirrus-theme", next);
    } catch {}
  };
  return [theme, toggle];
}
function Toolbar({ onSearch, onNotifications, unread }) {
  const [theme, toggleTheme] = useTheme();
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="toolbar">
      <button
        className="icon-button mobile-menu"
        aria-label="Open navigation"
        onClick={() => {
          const open = !document.body.classList.contains("nav-open");
          document.body.classList.toggle("nav-open", open);
          const sidebar = document.querySelector(".sidebar");
          if (sidebar)
            sidebar.inert = !open && matchMedia("(max-width: 760px)").matches;
        }}
      >
        <Menu />
      </button>
      <span className="toolbar-clock">
        {time.toLocaleDateString(undefined, { month: "short", day: "2-digit" })}{" "}
        <span> / </span>{" "}
        {time.toLocaleTimeString(undefined, {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        })}
      </span>
      <button
        className="toolbar-search"
        onClick={onSearch}
        aria-label="Search workspace"
      >
        <Search />
        <span>Search anything...</span>
        <kbd>Ctrl K</kbd>
      </button>
      <span className="toolbar-divider" />
      <button
        className="icon-button"
        onClick={toggleTheme}
        aria-label={
          theme === "light" ? "Switch to dark theme" : "Switch to light theme"
        }
        title="Change appearance"
      >
        {theme === "light" ? <Moon /> : <Sun />}
      </button>
      <button
        className="icon-button"
        aria-label={`Open notifications${unread ? `, ${unread} unread` : ""}`}
        onClick={onNotifications}
      >
        <Bell />
        {unread > 0 && <i className="notification-dot" />}
      </button>
      <div className="toolbar-avatar" title={config.user}>
        {config.user?.[0]?.toUpperCase()}
      </div>
    </div>
  );
}
function CommandPalette({ open, onClose }) {
  const [query, setQuery] = useState(""),
    [results, setResults] = useState([]),
    [loading, setLoading] = useState(false),
    [error, setError] = useState("");
  const input = useRef(null);
  const nav = useMemo(
    () =>
      Array.from(document.querySelectorAll("nav a")).map((a) => ({
        title: a.textContent.trim(),
        url: a.getAttribute("href"),
        icon: a.querySelector("[data-ui-icon]")?.dataset.uiIcon,
      })),
    [],
  );
  useEffect(() => {
    if (open) {
      setTimeout(() => input.current?.focus(), 30);
    } else setQuery("");
  }, [open]);
  useEffect(() => {
    setError("");
    setResults([]);
    if (query.trim().length < 2) {
      setLoading(false);
      return;
    }
    setLoading(true);
    const controller = new AbortController();
    const t = setTimeout(
      () =>
        api("/api/experience/search?q=" + encodeURIComponent(query), {
          signal: controller.signal,
        })
          .then((v) => {
            setResults(v.results);
            setLoading(false);
          })
          .catch((e) => {
            if (e.name !== "AbortError") {
              setError(e.message);
              setLoading(false);
            }
          }),
      220,
    );
    return () => {
      clearTimeout(t);
      controller.abort();
    };
  }, [query]);
  const pages = nav.filter((n) =>
    n.title.toLowerCase().includes(query.toLowerCase()),
  );
  const keyDown = (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const links = [
        ...e.currentTarget
          .closest("dialog")
          .querySelectorAll(".command-result"),
      ];
      const i = links.indexOf(document.activeElement),
        next = e.key === "ArrowDown" ? i + 1 : i - 1;
      links[(next + links.length) % links.length]?.focus();
    }
    if (e.key === "Enter" && document.activeElement === input.current) {
      const first = document.querySelector(".command-dialog .command-result");
      if (first) location.assign(first.href);
    }
  };
  return (
    <Dialog
      open={open}
      onClose={onClose}
      className="command-dialog"
      label="Search workspace"
    >
      <div onKeyDown={keyDown}>
        <div className="command-input">
          <Search />
          <input
            ref={input}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Where would you like to go?"
            aria-label="Search pages and records"
          />
          <button
            className="dialog-close"
            aria-label="Close search"
            onClick={onClose}
          >
            <X />
          </button>
        </div>
        <div className="command-results">
          {pages.length > 0 && (
            <>
              <div className="command-section">PAGES & WORKSPACES</div>
              {pages.map((p) => {
                const Icon = icons[p.icon] || LayoutDashboard;
                return (
                  <a key={p.url} className="command-result" href={p.url}>
                    <span className="result-icon">
                      <Icon size={16} />
                    </span>
                    <div>
                      <b>{p.title}</b>
                      <small>Jump to workspace</small>
                    </div>
                    <CornerDownLeft className="result-enter" />
                  </a>
                );
              })}
            </>
          )}
          {query.trim().length >= 2 && (
            <>
              <div className="command-section">PERMITTED RECORDS</div>
              {loading ? (
                <div className="command-loading">
                  Finding your company signal…
                </div>
              ) : error ? (
                <div className="command-loading" role="alert">
                  {error}
                </div>
              ) : results.length ? (
                results.map((r) => (
                  <a className="command-result" key={r.url} href={path(r.url)}>
                    <span className="result-icon">
                      {r.type === "asset" ? (
                        <Laptop size={16} />
                      ) : (
                        <Layers size={16} />
                      )}
                    </span>
                    <div>
                      <b>{r.title}</b>
                      <small>{r.subtitle}</small>
                    </div>
                    <ArrowUpRight className="result-enter" />
                  </a>
                ))
              ) : (
                <div className="command-loading">
                  No matching records in your permitted scope.
                </div>
              )}
            </>
          )}
        </div>
        <div className="command-footer">
          <span>
            <Keyboard size={12} /> Navigate with ↑ ↓ · Enter to open
          </span>
          <span>
            <kbd>Esc</kbd> to close
          </span>
        </div>
      </div>
    </Dialog>
  );
}
function Notifications({ open, onClose, items, unread, error, onRead }) {
  const [busy, setBusy] = useState(false);
  const mark = async () => {
    setBusy(true);
    try {
      await onRead();
    } finally {
      setBusy(false);
    }
  };
  return (
    <Dialog
      open={open}
      onClose={onClose}
      className="drawer-dialog"
      label="Your notifications"
    >
      <div className="drawer-heading">
        <div>
          <div className="eyebrow">YOUR COMPANY SIGNAL</div>
          <h2>
            Notifications<span className="accent">.</span>
          </h2>
        </div>
        <button
          className="dialog-close"
          aria-label="Close notifications"
          onClick={onClose}
        >
          <X />
        </button>
      </div>
      <div className="drawer-toolbar">
        <span>
          {unread} unread {unread === 1 ? "update" : "updates"}
        </span>
        <button
          className="text-button"
          disabled={busy || !unread}
          onClick={mark}
        >
          {busy ? "Updating…" : "Mark all as read"} <CheckCheck size={12} />
        </button>
      </div>
      {error ? (
        <div className="drawer-empty" role="alert">
          <ShieldAlert />
          <h3>Let’s reconnect.</h3>
          <p>{error}</p>
          <a className="button" href={path("/login")}>
            Sign in again
          </a>
        </div>
      ) : items.length ? (
        <div className="drawer-content">
          {items.map((n) => (
            <a key={n.id} href={path(n.url)} className="drawer-item">
              <span className="drawer-event-icon">
                <Bell />
              </span>
              <span>
                <b>{n.message}</b>
                <small>{dateLabel(n.created_at)}</small>
              </span>
              {!n.seen && <span className="unread-indicator" />}
            </a>
          ))}
        </div>
      ) : (
        <div className="drawer-empty">
          <Inbox />
          <h3>A little breathing room.</h3>
          <p>You’re all caught up. New updates will appear here.</p>
        </div>
      )}
      <div className="drawer-footer">
        <a href={path("/notifications")}>
          Open notification history <ArrowUpRight size={12} />
        </a>
      </div>
    </Dialog>
  );
}
function BoardControls() {
  const [active, setActive] = useState("All updates"),
    [view, setView] = useState("grid"),
    [visible, setVisible] = useState(0);
  const cards = useMemo(
    () => [...document.querySelectorAll("#notice-feed article.notice-card")],
    [],
  );
  const tabs = ["All updates", "Critical", "Pinned", "Needs acknowledgement"];
  const accepts = (card, tab) =>
    tab === "All updates" ||
    (tab === "Critical" && card.dataset.severity === "Critical") ||
    (tab === "Pinned" && card.dataset.pinned === "1") ||
    (tab === "Needs acknowledgement" && card.dataset.pending === "1");
  useEffect(() => {
    let count = 0;
    cards.forEach((c) => {
      c.hidden = !accepts(c, active);
      if (!c.hidden) count++;
    });
    setVisible(count);
    const feed = document.getElementById("notice-feed");
    if (feed) feed.dataset.view = view;
  }, [active, view, cards]);
  return (
    <>
      <div className="board-controls">
        <div className="board-tabs" role="tablist" aria-label="Notice views">
          {tabs.map((t) => (
            <button
              key={t}
              className={`tab ${active === t ? "active" : ""}`}
              role="tab"
              aria-selected={active === t}
              onClick={() => setActive(t)}
            >
              {t === "All updates" && <Layers />}
              {t === "Critical" && <AlertTriangle />}
              {t === "Pinned" && <Pin />}
              {t === "Needs acknowledgement" && <CircleCheck />}
              {t}
              <span>{cards.filter((c) => accepts(c, t)).length}</span>
            </button>
          ))}
        </div>
        <div className="view-switch" aria-label="Board layout">
          {[
            ["grid", Grid2X2],
            ["list", List],
          ].map(([v, Icon]) => (
            <button
              key={v}
              className={`view-option ${view === v ? "active" : ""}`}
              aria-label={`${v} board view`}
              aria-pressed={view === v}
              onClick={() => setView(v)}
            >
              <Icon />
            </button>
          ))}
        </div>
      </div>
      {active !== "All updates" && visible === 0 && (
        <div className="empty filter-empty">
          <CircleCheck size={25} />
          <h3>Nothing needs your attention here.</h3>
          <p>Try another view to see more of your company signal.</p>
        </div>
      )}
    </>
  );
}
function Priorities({ element }) {
  const total = Number(element.dataset.total),
    critical = Number(element.dataset.critical),
    warning = Number(element.dataset.warning),
    important = Number(element.dataset.important);
  const bars = Array.from({ length: 20 }, (_, i) => {
    const proportion = total ? (i / 20) * total : Infinity;
    return proportion < critical
      ? "critical"
      : proportion < critical + warning
        ? "warning"
        : total
          ? "normal"
          : "empty";
  });
  return (
    <div className="priority-content">
      <span className="priority-icon">
        <ChartNoAxesCombined />
      </span>
      <div className="priority-copy">
        <b>Your priority mix</b>
        <p>
          {critical} critical · {warning} warnings · {important} important
        </p>
      </div>
      <div
        className="priority-meter"
        role="img"
        aria-label={`${total} notices: ${critical} critical, ${warning} warnings, ${important} important`}
      >
        {bars.map((b, i) => (
          <motion.span
            key={i}
            className={"bar-" + b}
            style={{ "--bar": `${9 + ((i * 7) % 17)}px` }}
            initial={{ scaleY: 0 }}
            animate={{ scaleY: 1 }}
            transition={{ delay: i * 0.02, duration: 0.5 }}
          />
        ))}
      </div>
    </div>
  );
}
function AssetAnalytics({ element }) {
  const data = JSON.parse(element.dataset.metrics),
    total = data["Total assets"];
  const slices = [
    ["Available", "#a9bf8a"],
    ["Assigned", "#607f72"],
    ["Under Repair", "#e0bd86"],
    ["Missing", "#f39b70"],
    ["Retired", "#d5dace"],
  ];
  let offset = 0;
  const circumference = 2 * Math.PI * 48;
  return (
    <>
      <div className="analytics-header">
        <h3>Equipment distribution</h3>
        <span>
          IN YOUR SCOPE <ChevronDown size={10} />
        </span>
      </div>
      <div className="analytics-body">
        <div
          className="donut-chart"
          role="img"
          aria-label={`${total} assets. ${slices.map(([s]) => `${data[s]} ${s}`).join(", ")}`}
        >
          <svg viewBox="0 0 120 120">
            <circle
              cx="60"
              cy="60"
              r="48"
              stroke="var(--line)"
              strokeWidth="11"
              fill="none"
            />
            {slices.map(([name, color]) => {
              const length = total ? (data[name] / total) * circumference : 0,
                start = offset;
              offset += length;
              return (
                <motion.circle
                  key={name}
                  cx="60"
                  cy="60"
                  r="48"
                  fill="none"
                  stroke={color}
                  strokeWidth="11"
                  strokeLinecap="round"
                  strokeDasharray={`${Math.max(0, length - 5)} ${circumference}`}
                  strokeDashoffset={-start}
                  initial={{
                    opacity: 0,
                    strokeDasharray: `0 ${circumference}`,
                  }}
                  animate={{
                    opacity: length ? 1 : 0,
                    strokeDasharray: `${Math.max(0, length - 5)} ${circumference}`,
                  }}
                  transition={{ duration: 0.9, delay: 0.15 }}
                />
              );
            })}
          </svg>
          <div className="donut-center">
            <b>{total}</b>
            <span>TOTAL ASSETS</span>
          </div>
        </div>
        <div className="chart-legend">
          {slices.map(([label, color]) => (
            <div className="legend-row" key={label}>
              <i style={{ background: color }} />
              <span>{label}</span>
              <b>{data[label]}</b>
            </div>
          ))}
        </div>
      </div>
      <div className="analytics-foot">
        <ShieldAlert /> Counts reflect your currently permitted equipment.
      </div>
    </>
  );
}
function Count({ value }) {
  const [n, setN] = useState(value),
    reduce = useReducedMotion();
  useEffect(() => {
    if (reduce || value === 0) return;
    let id,
      start = performance.now();
    const step = (t) => {
      let progress = Math.min((t - start) / 650, 1);
      setN(Math.round(value * (1 - Math.pow(1 - progress, 3))));
      if (progress < 1) id = requestAnimationFrame(step);
    };
    id = requestAnimationFrame(step);
    return () => cancelAnimationFrame(id);
  }, [value, reduce]);
  return (
    <span aria-label={String(value)} aria-live="off">
      {n}
    </span>
  );
}
function Inventory({ element }) {
  const all = useMemo(
    () =>
      Array.from(element.querySelectorAll("[data-equipment-item]")).map(
        (r) => ({ ...r.dataset, id: Number(r.dataset.id) }),
      ),
    [element],
  );
  const [query, setQuery] = useState(""),
    [view, setView] = useState(() => {
      try {
        return localStorage.getItem("cirrus-equipment-view") || "table";
      } catch {
        return "table";
      }
    }),
    [sort, setSort] = useState("tag"),
    [direction, setDirection] = useState(1),
    [selected, setSelected] = useState(new Set()),
    [page, setPage] = useState(1),
    [quick, setQuick] = useState(null);
  const perPage = 12;
  useEffect(() => {
    element.querySelector(".equipment-fallback").hidden = true;
    return () => {
      element.querySelector(".equipment-fallback").hidden = false;
    };
  }, [element]);
  useEffect(() => {
    setPage(1);
  }, [query, sort, direction]);
  const results = useMemo(
    () =>
      all
        .filter((a) =>
          (
            a.tag +
            " " +
            a.model +
            " " +
            a.manufacturer +
            " " +
            a.category +
            " " +
            a.status +
            " " +
            a.location
          )
            .toLowerCase()
            .includes(query.toLowerCase()),
        )
        .sort(
          (a, b) =>
            String(a[sort]).localeCompare(String(b[sort]), undefined, {
              numeric: true,
            }) * direction,
        ),
    [all, query, sort, direction],
  );
  const pages = Math.max(1, Math.ceil(results.length / perPage)),
    shown = results.slice((page - 1) * perPage, page * perPage);
  const changeView = (value) => {
    setView(value);
    try {
      localStorage.setItem("cirrus-equipment-view", value);
    } catch {}
  };
  const toggle = (id) =>
    setSelected((previous) => {
      const next = new Set(previous);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  const sortBy = (key) => {
    if (sort === key) setDirection(-direction);
    else {
      setSort(key);
      setDirection(1);
    }
  };
  const QuickIcon = deviceIcon(quick?.category);
  const warrantyState = (value) => {
    if (!value) return "";
    const left = (new Date(value + "T23:59:59Z") - Date.now()) / 86400000;
    return left < 0 ? "Expired" : left <= 30 ? "Expiring soon" : "";
  };
  const checkbox = (a) => (
    <input
      type="checkbox"
      checked={selected.has(a.id)}
      onChange={() => toggle(a.id)}
      aria-label={`Select ${a.tag}`}
    />
  );
  return (
    <>
      <div className="equipment-toolbar">
        <div className="inline-search">
          <Search />
          <input
            placeholder="Find in this inventory…"
            aria-label="Find in inventory results"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <span>
          {results.length} {results.length === 1 ? "asset" : "assets"} in view
        </span>
        <div className="view-switch" aria-label="Equipment layout">
          <button
            className={`view-option ${view === "table" ? "active" : ""}`}
            aria-label="Table equipment view"
            aria-pressed={view === "table"}
            onClick={() => changeView("table")}
          >
            <List />
          </button>
          <button
            className={`view-option ${view === "cards" ? "active" : ""}`}
            aria-label="Cards equipment view"
            aria-pressed={view === "cards"}
            onClick={() => changeView("cards")}
          >
            <Grid2X2 />
          </button>
        </div>
      </div>
      {selected.size > 0 && (
        <motion.div
          className="selection-bar"
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Check size={14} />
          <b>{selected.size} selected</b>
          <button
            className="text-button"
            onClick={() => setSelected(new Set())}
          >
            Clear selection
          </button>
          {config.manager === "1" && selected.size <= 50 && (
            <a
              className="text-link"
              href={path("/assetpass/labels?ids=" + [...selected].join(","))}
            >
              <Printer size={13} /> Print labels
            </a>
          )}
        </motion.div>
      )}
      {results.length === 0 ? (
        <div className="empty">
          <Package size={28} />
          <h2>A little room for possibility.</h2>
          <p>
            {all.length
              ? "No equipment matches your search."
              : "No equipment in your current scope yet."}
          </p>
          {query && <button onClick={() => setQuery("")}>Clear search</button>}
        </div>
      ) : view === "table" ? (
        <div className="table-wrap panel equipment-table">
          <table>
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    aria-label="Select visible equipment"
                    checked={
                      shown.length > 0 && shown.every((a) => selected.has(a.id))
                    }
                    onChange={() =>
                      setSelected((prev) => {
                        const next = new Set(prev),
                          clear = shown.every((a) => next.has(a.id));
                        shown.forEach((a) =>
                          clear ? next.delete(a.id) : next.add(a.id),
                        );
                        return next;
                      })
                    }
                  />
                </th>
                {[
                  ["tag", "Asset / Equipment", ""],
                  ["category", "Category", "equipment-category"],
                  ["status", "Status", "equipment-status"],
                  ["warranty", "Warranty", "equipment-warranty"],
                  ["location", "Location", "equipment-location"],
                ].map(([key, label, css]) => (
                  <th key={key} className={css}>
                    <button className="sort-button" onClick={() => sortBy(key)}>
                      {label}
                      <ArrowDownUp />
                    </button>
                  </th>
                ))}
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((a) => {
                const Icon = deviceIcon(a.category);
                return (
                  <tr key={a.id}>
                    <td>{checkbox(a)}</td>
                    <td>
                      <a
                        className="equipment-identity"
                        href={path("/assetpass/assets/" + a.id)}
                      >
                        <span className="equipment-icon">
                          <Icon />
                        </span>
                        <span>
                          <b>{a.tag}</b>
                          <small>
                            {a.manufacturer} {a.model}
                          </small>
                        </span>
                      </a>
                    </td>
                    <td className="equipment-category">{a.category}</td>
                    <td className="equipment-status">
                      <Status value={a.status} />
                    </td>
                    <td className="equipment-warranty">
                      {a.warranty || "—"}
                      {warrantyState(a.warranty) && (
                        <small>{warrantyState(a.warranty)}</small>
                      )}
                    </td>
                    <td className="equipment-location">{a.location || "—"}</td>
                    <td>
                      <button
                        className="quick-view"
                        aria-label={`Quick view ${a.tag}`}
                        onClick={() => setQuick(a)}
                      >
                        <Eye />
                        Quick view
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="equipment-cards">
          {shown.map((a, i) => {
            const Icon = deviceIcon(a.category);
            return (
              <motion.article
                className="equipment-card"
                key={a.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.035, duration: 0.3 }}
              >
                <div className="equipment-card-visual">
                  <Status value={a.status} />
                  {checkbox(a)}
                  <span className="device-icon">
                    <Icon />
                  </span>
                </div>
                <div className="equipment-card-body">
                  <h3>{a.tag}</h3>
                  <p>
                    {a.manufacturer} {a.model || a.category}
                  </p>
                  <div className="equipment-card-meta">
                    <span>{a.category}</span>
                    <span>{a.condition}</span>
                  </div>
                  <div className="equipment-card-actions">
                    <a href={path("/assetpass/assets/" + a.id)}>
                      Open record <ArrowUpRight size={12} />
                    </a>
                    <button
                      className="quick-view"
                      aria-label={`Quick view ${a.tag}`}
                      onClick={() => setQuick(a)}
                    >
                      <Eye />
                      Quick view
                    </button>
                  </div>
                </div>
              </motion.article>
            );
          })}
        </div>
      )}
      <div className="equipment-pagination">
        <span>
          {results.length
            ? `${(page - 1) * perPage + 1}–${Math.min(page * perPage, results.length)} of ${results.length}`
            : "0 assets"}{" "}
          <span> · </span> Your permitted inventory
        </span>
        <div className="pagination-controls">
          <button
            className="page-number"
            aria-label="Previous equipment page"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            <ChevronLeft size={13} />
          </button>
          <span className="page-number active">{page}</span>
          <button
            className="page-number"
            aria-label="Next equipment page"
            disabled={page >= pages}
            onClick={() => setPage(page + 1)}
          >
            <ChevronRight size={13} />
          </button>
        </div>
      </div>
      <Dialog
        open={!!quick}
        onClose={() => setQuick(null)}
        className="quick-dialog"
        label={
          quick ? `Equipment quick view: ${quick.tag}` : "Equipment quick view"
        }
      >
        {quick && (
          <>
            <div className="quick-visual">
              <QuickIcon />
              <button
                className="dialog-close"
                aria-label="Close equipment quick view"
                onClick={() => setQuick(null)}
              >
                <X />
              </button>
            </div>
            <div className="quick-content">
              <div className="eyebrow">ASSETPASS / QUICK LOOK</div>
              <h2>{quick.tag}</h2>
              <p>
                {quick.manufacturer} {quick.model}
              </p>
              <Status value={quick.status} />
              <dl className="quick-specs">
                {[
                  ["Category", quick.category],
                  ["Condition", quick.condition],
                  ["Location", quick.location || "Not recorded"],
                  ["Warranty", quick.warranty || "Not recorded"],
                ].map(([label, value]) => (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
              </dl>
              <a
                className="button"
                href={path("/assetpass/assets/" + quick.id)}
              >
                Open full equipment record <ArrowUpRight size={14} />
              </a>
            </div>
          </>
        )}
      </Dialog>
    </>
  );
}
function Experience() {
  const [search, setSearch] = useState(false),
    [drawer, setDrawer] = useState(false),
    [notifications, setNotifications] = useState({ items: [], unread: 0 }),
    [error, setError] = useState(""),
    [toast, setToast] = useState(null);
  const authenticated = config.authenticated === "1";
  const refresh = useCallback(async () => {
    try {
      const data = await api("/api/experience/notifications");
      setNotifications(data);
      setError("");
    } catch (e) {
      setError(e.message);
    }
  }, []);
  useEffect(() => {
    if (!authenticated) return;
    refresh();
    const t = setInterval(refresh, 60000);
    return () => clearInterval(t);
  }, [refresh, authenticated]);
  useEffect(() => {
    const handle = (e) => {
      if (
        (e.ctrlKey || e.metaKey) &&
        e.key.toLowerCase() === "k" &&
        authenticated
      ) {
        e.preventDefault();
        setSearch((p) => !p);
      }
    };
    const open = () => setSearch(true);
    document.addEventListener("keydown", handle);
    document
      .querySelectorAll("[data-open-command]")
      .forEach((e) => e.addEventListener("click", open));
    return () => {
      document.removeEventListener("keydown", handle);
      document
        .querySelectorAll("[data-open-command]")
        .forEach((e) => e.removeEventListener("click", open));
    };
  }, [authenticated]);
  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(null), 4000);
      return () => clearTimeout(t);
    }
  }, [toast]);
  const markRead = async () => {
    try {
      await api("/api/experience/notifications/read", {
        method: "POST",
        body: new URLSearchParams({ csrf: config.csrf }),
      });
      await refresh();
      setToast({ message: "A little clarity. Your inbox is up to date." });
    } catch (e) {
      setToast({ message: e.message, error: true });
    }
  };
  const slots = [];
  document.querySelectorAll("[data-ui-icon]").forEach((element, i) => {
    const Icon = icons[element.dataset.uiIcon];
    if (Icon)
      slots.push(
        createPortal(<Icon aria-hidden="true" />, element, "icon-" + i),
      );
  });
  document
    .querySelectorAll("[data-count]")
    .forEach((element, i) =>
      slots.push(
        createPortal(
          <Count value={Number(element.dataset.count)} />,
          element,
          "count-" + i,
        ),
      ),
    );
  const board = document.getElementById("board-controls");
  if (board) slots.push(createPortal(<BoardControls />, board, "board"));
  const priority = document.getElementById("pulse-priorities");
  if (priority)
    slots.push(
      createPortal(<Priorities element={priority} />, priority, "priority"),
    );
  const analytics = document.getElementById("asset-analytics");
  if (analytics)
    slots.push(
      createPortal(
        <AssetAnalytics element={analytics} />,
        analytics,
        "analytics",
      ),
    );
  document
    .querySelectorAll("[data-equipment-root]")
    .forEach((element, i) =>
      slots.push(
        createPortal(
          <Inventory element={element} />,
          element.querySelector(".equipment-react-root"),
          "inventory-" + i,
        ),
      ),
    );
  const toolbar = document.getElementById("workspace-toolbar");
  if (toolbar)
    slots.push(
      createPortal(
        <Toolbar
          onSearch={() => setSearch(true)}
          onNotifications={() => {
            setDrawer(true);
            refresh();
          }}
          unread={notifications.unread}
        />,
        toolbar,
        "toolbar",
      ),
    );
  const badge = document.getElementById("nav-notification-count");
  if (badge && notifications.unread)
    slots.push(
      createPortal(
        <span className="notification-count">
          {notifications.unread > 99 ? "99+" : notifications.unread}
        </span>,
        badge,
        "badge",
      ),
    );
  return (
    <MotionConfig reducedMotion="user">
      {slots}
      {authenticated && (
        <>
          <CommandPalette open={search} onClose={() => setSearch(false)} />
          <Notifications
            open={drawer}
            onClose={() => setDrawer(false)}
            {...notifications}
            error={error}
            onRead={markRead}
          />
        </>
      )}
      <div className="toast-region" aria-live="polite">
        <AnimatePresence>
          {toast && (
            <motion.div
              className={"toast " + (toast.error ? "error" : "")}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              key={toast.message}
            >
              {toast.error ? <AlertTriangle /> : <CircleCheck />}
              {toast.message}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </MotionConfig>
  );
}
createRoot(document.getElementById("experience-root")).render(<Experience />);
