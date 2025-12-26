import { useEffect, useState } from "react";
import { GetAiSuggestions } from "../services/ApiClient";
import { AiSuggestion } from "../models/Models";
import { GetToday } from "../utils/DateUtils";

const WeekStats = [
  { Label: "Calories", Total: 10420, Average: 1488, Accent: "#f26b5b" },
  { Label: "Protein", Total: 512, Average: 73, Accent: "#3ccf91" },
  { Label: "Steps", Total: 52000, Average: 7429, Accent: "#5cc0c7" },
  { Label: "Net calories", Total: 9200, Average: 1314, Accent: "#ffc857" }
];

const Bars = [
  { Day: "Mon", Value: 1300 },
  { Day: "Tue", Value: 1420 },
  { Day: "Wed", Value: 1550 },
  { Day: "Thu", Value: 1490 },
  { Day: "Fri", Value: 1630 },
  { Day: "Sat", Value: 1200 },
  { Day: "Sun", Value: 1300 }
];

export const InsightsPage = () => {
  const [AiSuggestions, SetAiSuggestions] = useState<AiSuggestion[]>([]);
  const [AiStatus, SetAiStatus] = useState<"idle" | "loading" | "error">("idle");
  const [AiError, SetAiError] = useState<string | null>(null);
  const MaxValue = Math.max(...Bars.map((Bar) => Bar.Value));

  useEffect(() => {
    const LoadSuggestions = async () => {
      SetAiStatus("loading");
      SetAiError(null);
      const Today = GetToday();
      try {
        const Response = await GetAiSuggestions(Today);
        SetAiSuggestions(Response.Suggestions);
        SetAiStatus("idle");
      } catch (ErrorValue) {
        SetAiStatus("error");
        SetAiError("AI suggestions are unavailable right now.");
      }
    };

    void LoadSuggestions();
  }, []);

  return (
    <section className="space-y-6">
      <div className="Card space-y-3">
        <h2 className="Headline text-2xl">Weekly insights</h2>
        <p className="text-sm text-Ink/70">
          Your Monday to Sunday rhythm with totals and averages.
        </p>
      </div>

      <div className="grid gap-4">
        {WeekStats.map((Stat) => (
          <div key={Stat.Label} className="Card space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">{Stat.Label}</h3>
              <span className="Chip">Avg {Stat.Average}</span>
            </div>
            <div className="text-2xl font-semibold">{Stat.Total}</div>
            <div className="h-2 rounded-full bg-white/70">
              <div
                className="h-2 rounded-full"
                style={{ width: "72%", backgroundColor: Stat.Accent }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="Card space-y-4">
        <h3 className="Headline text-xl">Calories flow</h3>
        <div className="grid grid-cols-7 gap-2">
          {Bars.map((Bar) => (
            <div key={Bar.Day} className="flex flex-col items-center gap-2 text-xs">
              <div className="flex h-32 w-6 items-end rounded-full bg-white/70">
                <div
                  className="w-full rounded-full bg-Coral"
                  style={{ height: `${Math.round((Bar.Value / MaxValue) * 100)}%` }}
                />
              </div>
              <span className="text-Ink/70">{Bar.Day}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="Card space-y-4">
        <h3 className="Headline text-xl">AI suggestions</h3>
        {AiStatus === "loading" && (
          <p className="text-sm text-Ink/70">Loading suggestions...</p>
        )}
        {AiStatus === "error" && (
          <p className="text-sm text-Ink/70">{AiError}</p>
        )}
        {AiStatus === "idle" && AiSuggestions.length === 0 && (
          <p className="text-sm text-Ink/70">No suggestions yet.</p>
        )}
        {AiSuggestions.length > 0 && (
          <div className="grid gap-3 text-sm">
            {AiSuggestions.map((Suggestion, Index) => (
              <div key={`${Suggestion.Title}-${Index}`} className="rounded-2xl bg-white/80 p-4">
                <p className="font-semibold">{Suggestion.Title}</p>
                <p className="text-Ink/70">{Suggestion.Detail}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
};
