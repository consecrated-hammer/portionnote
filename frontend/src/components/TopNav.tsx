import { useEffect, useRef, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";

const NavItems = [
  { Label: "Foods", To: "/foods" },
  { Label: "History", To: "/history" },
  { Label: "About", To: "/about" },
  { Label: "Settings", To: "/settings" }
];

export const TopNav = () => {
  const [IsTodayMenuOpen, SetIsTodayMenuOpen] = useState(false);
  const TodayMenuRef = useRef<HTMLDivElement>(null);
  const CloseTimeoutRef = useRef<number | null>(null);
  const Navigate = useNavigate();
  const Location = useLocation();
  const IsTodayActive = Location.pathname === "/today";

  useEffect(() => {
    const HandleClickOutside = (Event: MouseEvent) => {
      if (IsTodayMenuOpen && TodayMenuRef.current && !TodayMenuRef.current.contains(Event.target as Node)) {
        SetIsTodayMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", HandleClickOutside);
    return () => {
      document.removeEventListener("mousedown", HandleClickOutside);
      if (CloseTimeoutRef.current) {
        window.clearTimeout(CloseTimeoutRef.current);
        CloseTimeoutRef.current = null;
      }
    };
  }, [IsTodayMenuOpen]);

  const HandleTodayToggle = () => {
    if (!IsTodayActive) {
      Navigate("/today");
    }
    SetIsTodayMenuOpen((Value) => !Value);
  };
  const HandleTodayHoverOpen = () => {
    if (CloseTimeoutRef.current) {
      window.clearTimeout(CloseTimeoutRef.current);
      CloseTimeoutRef.current = null;
    }
    SetIsTodayMenuOpen(true);
  };
  const HandleTodayHoverClose = () => {
    if (CloseTimeoutRef.current) {
      window.clearTimeout(CloseTimeoutRef.current);
    }
    CloseTimeoutRef.current = window.setTimeout(() => {
      SetIsTodayMenuOpen(false);
      CloseTimeoutRef.current = null;
    }, 150);
  };

  const HandleQuickLog = (Mode: "meal" | "steps" | "weight") => {
    SetIsTodayMenuOpen(false);
    if (Mode === "meal") {
      Navigate("/log?mode=meal");
      return;
    }
    Navigate(`/today?mode=${Mode}`);
  };

  return (
    <nav className="fixed top-4 left-1/2 z-20 w-[min(100%-2rem,520px)] -translate-x-1/2 rounded-full border border-white/70 bg-white/80 px-4 py-3 shadow-Soft backdrop-blur">
      <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wide">
        <div className="relative flex flex-1" ref={TodayMenuRef}>
          <button
            type="button"
            onClick={HandleTodayToggle}
            onMouseEnter={HandleTodayHoverOpen}
            onMouseLeave={HandleTodayHoverClose}
            className={`flex flex-1 items-center justify-center rounded-full px-3 py-2 transition ${
              IsTodayMenuOpen || IsTodayActive ? "bg-Ink text-white" : "text-Ink/70"
            }`}
            aria-haspopup="menu"
            aria-expanded={IsTodayMenuOpen}
          >
            TODAY
          </button>
          {IsTodayMenuOpen && (
            <div
              role="menu"
              className="absolute left-0 top-full mt-1 w-48 rounded-2xl border border-Ink/10 bg-white p-2 text-sm shadow-Soft"
              onMouseEnter={HandleTodayHoverOpen}
              onMouseLeave={HandleTodayHoverClose}
            >
              <button
                type="button"
                role="menuitem"
                onClick={() => HandleQuickLog("meal")}
                className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left font-medium text-Ink hover:bg-Ink/5"
                style={{ minHeight: "44px" }}
              >
                <span className="text-lg">🍽️</span>
                <span>Log a meal</span>
              </button>
              <button
                type="button"
                role="menuitem"
                onClick={() => HandleQuickLog("steps")}
                className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left font-medium text-Ink hover:bg-Ink/5"
                style={{ minHeight: "44px" }}
              >
                <span className="text-lg">👟</span>
                <span>Update steps</span>
              </button>
              <button
                type="button"
                role="menuitem"
                onClick={() => HandleQuickLog("weight")}
                className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left font-medium text-Ink hover:bg-Ink/5"
                style={{ minHeight: "44px" }}
              >
                <img src="/images/scale.png" alt="" className="h-5 w-5" />
                <span>Update weight</span>
              </button>
            </div>
          )}
        </div>
        {NavItems.map((Item) => (
          <NavLink
            key={Item.Label}
            to={Item.To}
            onClick={() => SetIsTodayMenuOpen(false)}
            className={({ isActive }) =>
              `flex flex-1 items-center justify-center rounded-full px-3 py-2 transition ${
                isActive ? "bg-Ink text-white" : "text-Ink/70"
              }`
            }
          >
            {Item.Label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
};
