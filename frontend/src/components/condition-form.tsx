"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { CloudFog, CloudRain, Info, Loader2, MapPin, RotateCcw, Satellite, Snowflake, Sun, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { getLiveWeather, getStates } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { ConditionInput } from "@/lib/types";

const WEATHER_OPTIONS = [
  "Fair", "Clear", "Partly Cloudy", "Mostly Cloudy", "Cloudy", "Overcast", "Light Drizzle", "Light Rain", "Rain",
  "Heavy Rain", "Thunderstorm", "Light Snow", "Snow", "Heavy Snow", "Freezing Rain", "Fog", "Haze",
];
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

// Fallback if /api/states is unreachable, so the location picker still works.
const FALLBACK_ABBR: Record<string, string> = { California: "CA", Texas: "TX", Florida: "FL", "New York": "NY" };

const PRESETS: { label: string; icon: typeof Sun; patch: ConditionInput }[] = [
  { label: "Clear day", icon: Sun, patch: { weather_condition: "Fair", temperature_f: 72, visibility_mi: 10, wind_speed_mph: 5, precipitation_in: 0, hour: 14, day_of_week: 2 } },
  { label: "Rainy rush hour", icon: CloudRain, patch: { weather_condition: "Heavy Rain", temperature_f: 58, visibility_mi: 2, wind_speed_mph: 18, precipitation_in: 0.3, hour: 17, day_of_week: 4 } },
  { label: "Foggy night", icon: CloudFog, patch: { weather_condition: "Fog", temperature_f: 45, visibility_mi: 0.5, wind_speed_mph: 3, precipitation_in: 0.02, hour: 23, day_of_week: 5 } },
  { label: "Winter storm", icon: Snowflake, patch: { weather_condition: "Snow", temperature_f: 26, visibility_mi: 1.5, wind_speed_mph: 22, precipitation_in: 0.1, hour: 7, day_of_week: 0, month: 1 } },
];

const ROAD_TOGGLES: { key: keyof ConditionInput; label: string }[] = [
  { key: "junction", label: "Junction" },
  { key: "traffic_signal", label: "Traffic signal" },
  { key: "crossing", label: "Crossing" },
  { key: "stop", label: "Stop sign" },
  { key: "give_way", label: "Give way" },
  { key: "railway", label: "Railway" },
  { key: "roundabout", label: "Roundabout" },
  { key: "station", label: "Station" },
  { key: "amenity", label: "Amenity" },
  { key: "bump", label: "Speed bump" },
  { key: "traffic_calming", label: "Traffic calming" },
  { key: "no_exit", label: "No exit" },
];

interface ConditionFormProps {
  value: ConditionInput;
  onChange: (v: ConditionInput) => void;
  onAssess: () => void;
  onReset: () => void;
  loading: boolean;
}

export function ConditionForm({ value, onChange, onAssess, onReset, loading }: ConditionFormProps) {
  const [abbr, setAbbr] = useState<Record<string, string>>(FALLBACK_ABBR);
  const [capitals, setCapitals] = useState<Record<string, string>>({});
  const [fetchingWeather, setFetchingWeather] = useState(false);
  const [weatherError, setWeatherError] = useState<string | null>(null);
  const [liveLabel, setLiveLabel] = useState<string | null>(null);

  useEffect(() => {
    getStates()
      .then((r) => {
        if (r.abbr) setAbbr(r.abbr);
        setCapitals(r.capitals ?? {});
      })
      .catch(() => {});
  }, []);

  const states = useMemo(() => Object.keys(abbr).sort(), [abbr]);
  const nameByCode = useMemo(() => Object.fromEntries(Object.entries(abbr).map(([n, c]) => [c, n])), [abbr]);
  const stateName = value.state ? nameByCode[value.state] : undefined;
  const weatherOptions = value.weather_condition && !WEATHER_OPTIONS.includes(value.weather_condition)
    ? [value.weather_condition, ...WEATHER_OPTIONS]
    : WEATHER_OPTIONS;

  function patch(p: ConditionInput) {
    setLiveLabel(null);
    onChange({ ...value, ...p });
  }

  async function useLiveWeather() {
    if (!stateName) return;
    setFetchingWeather(true);
    setWeatherError(null);
    try {
      // Geocode the state's capital: geocoding a bare state name ("Georgia", "California") can resolve
      // to a town of that name or another country.
      const w = await getLiveWeather(capitals[stateName] ?? stateName);
      const { location_label, fetched_at_local, ...conds } = w;
      void fetched_at_local;
      onChange({ ...value, ...conds, state: conds.state ?? value.state });
      setLiveLabel(location_label);
    } catch (e) {
      setWeatherError(e instanceof Error ? e.message : "Could not fetch live weather.");
    } finally {
      setFetchingWeather(false);
    }
  }

  return (
    <form
      className="space-y-6"
      onSubmit={(e) => {
        e.preventDefault();
        onAssess();
      }}
    >
      {/* Preset scenarios */}
      <Section title="Quick scenarios">
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p) => {
            const Icon = p.icon;
            return (
              <button
                key={p.label}
                type="button"
                onClick={() => patch(p.patch)}
                className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:border-accent hover:bg-accent/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <Icon className="size-3.5 text-accent" aria-hidden />
                {p.label}
              </button>
            );
          })}
        </div>
      </Section>

      {/* Location */}
      <Section title="Location">
        <div className="flex gap-2">
          <Select value={stateName ?? ""} onValueChange={(n) => patch({ state: abbr[n] })}>
            <SelectTrigger className="flex-1" aria-label="US state">
              <SelectValue placeholder="Select a US state" />
            </SelectTrigger>
            <SelectContent>
              {states.map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button type="button" variant="outline" onClick={useLiveWeather} disabled={fetchingWeather || !stateName}>
                {fetchingWeather ? <Loader2 className="animate-spin" /> : <Satellite />}
                <span className="hidden sm:inline">Live weather</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>Fill in current weather and local time for this state (Open-Meteo)</TooltipContent>
          </Tooltip>
        </div>
        {weatherError && <p className="mt-2 text-xs text-risk-high">{weatherError}</p>}
        {liveLabel && (
          <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
            <MapPin className="size-3.5 text-accent" aria-hidden />
            Live conditions loaded for {liveLabel}
          </p>
        )}
      </Section>

      {/* Weather */}
      <Section title="Weather">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="weather">Condition</Label>
            <Select value={value.weather_condition ?? "Fair"} onValueChange={(v) => patch({ weather_condition: v })}>
              <SelectTrigger id="weather" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {weatherOptions.map((w) => (
                  <SelectItem key={w} value={w}>
                    {w}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <SliderField label="Visibility" unit="mi" value={value.visibility_mi ?? 10} min={0} max={20} step={0.5} decimals={1} onChange={(n) => patch({ visibility_mi: n })} />
          <SliderField label="Temperature" unit="°F" value={value.temperature_f ?? 65} min={-20} max={120} step={1} onChange={(n) => patch({ temperature_f: n })} />
          <SliderField label="Wind speed" unit="mph" value={value.wind_speed_mph ?? 5} min={0} max={60} step={1} onChange={(n) => patch({ wind_speed_mph: n })} />
          <SliderField label="Precipitation" unit="in/hr" value={value.precipitation_in ?? 0} min={0} max={1} step={0.01} decimals={2} onChange={(n) => patch({ precipitation_in: n })} />
          <OptionalSliderField label="Humidity" unit="%" value={value.humidity_pct} fallback={65} min={0} max={100} step={1} onChange={(n) => patch({ humidity_pct: n })} onClear={() => patch({ humidity_pct: undefined })} />
          <OptionalSliderField label="Pressure" unit="inHg" value={value.pressure_in} fallback={29.9} min={27} max={31} step={0.1} decimals={1} onChange={(n) => patch({ pressure_in: n })} onClear={() => patch({ pressure_in: undefined })} />
        </div>
      </Section>

      {/* Time */}
      <Section title="Time">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <SliderField
            label="Hour (local)"
            value={value.hour ?? 12}
            min={0}
            max={23}
            step={1}
            format={(n) => `${String(n).padStart(2, "0")}:00`}
            onChange={(n) => patch({ hour: n })}
            className="sm:col-span-2"
          />
          <div className="space-y-1.5">
            <Label htmlFor="dow">Day</Label>
            <Select value={String(value.day_of_week ?? 2)} onValueChange={(v) => patch({ day_of_week: Number(v) })}>
              <SelectTrigger id="dow" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DAYS.map((d, i) => (
                  <SelectItem key={d} value={String(i)}>
                    {d}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="month">Month</Label>
            <Select value={String(value.month ?? 6)} onValueChange={(v) => patch({ month: Number(v) })}>
              <SelectTrigger id="month" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {MONTHS.map((m, i) => (
                  <SelectItem key={m} value={String(i + 1)}>
                    {m}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </Section>

      {/* Road context */}
      <Section title="Nearby road features">
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {ROAD_TOGGLES.map((t) => {
            const on = Boolean(value[t.key]);
            return (
              <label
                key={t.key}
                className={cn(
                  "flex cursor-pointer items-center justify-between gap-2 rounded-md border px-2.5 py-2 text-xs transition-colors",
                  on ? "border-accent/60 bg-accent/10 text-foreground" : "border-border-subtle text-muted-foreground hover:border-border"
                )}
              >
                {t.label}
                <Switch checked={on} onCheckedChange={(checked) => patch({ [t.key]: checked })} />
              </label>
            );
          })}
        </div>
      </Section>

      <p className="flex items-start gap-1.5 text-xs text-muted-foreground">
        <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden />
        Traffic density and vehicle speed aren&apos;t in the training dataset, so they can&apos;t be used as inputs.
      </p>

      <div className="sticky bottom-0 -mx-6 -mb-6 flex gap-2 rounded-b-lg border-t border-border-subtle bg-card/95 px-6 py-4 backdrop-blur">
        <Button type="button" variant="outline" size="lg" className="px-4" onClick={onReset} aria-label="Reset all inputs">
          <RotateCcw />
        </Button>
        <motion.div whileTap={{ scale: 0.98 }} className="flex-1">
          <Button type="submit" size="lg" variant="accent" className="w-full font-semibold" disabled={loading}>
            {loading ? <Loader2 className="animate-spin" /> : null}
            {loading ? "Assessing..." : "Assess risk"}
          </Button>
        </motion.div>
      </div>
    </form>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <fieldset className="space-y-3">
      <legend className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{title}</legend>
      {children}
    </fieldset>
  );
}

interface SliderFieldProps {
  label: string;
  unit?: string;
  value: number;
  min: number;
  max: number;
  step: number;
  decimals?: number;
  format?: (n: number) => string;
  onChange: (n: number) => void;
  className?: string;
  action?: React.ReactNode;
}

function SliderField({ label, unit = "", value, min, max, step, decimals = 0, format, onChange, className, action }: SliderFieldProps) {
  const clamped = Math.min(max, Math.max(min, value));
  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between">
        <Label className="flex items-center gap-1">
          {label}
          {action}
        </Label>
        <span className="text-sm font-medium tabular-nums text-accent">{format ? format(value) : `${value.toFixed(decimals)} ${unit}`}</span>
      </div>
      <Slider aria-label={label} value={[clamped]} min={min} max={max} step={step} onValueChange={([n]) => onChange(n)} />
    </div>
  );
}

/** Optional input: unset means the model imputes the training median, which is what most users want. */
function OptionalSliderField({
  value,
  fallback,
  onClear,
  ...rest
}: Omit<SliderFieldProps, "value"> & { value: number | undefined; fallback: number; onClear: () => void }) {
  if (value === undefined) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label className="text-muted-foreground">{rest.label}</Label>
          <button type="button" onClick={() => rest.onChange(fallback)} className="text-xs font-medium text-accent hover:underline">
            Set value
          </button>
        </div>
        <p className="flex h-4 items-center text-xs text-muted-foreground">Auto (typical value)</p>
      </div>
    );
  }
  return (
    <SliderField
      {...rest}
      value={value}
      action={
        <button
          type="button"
          aria-label={`Clear ${rest.label}`}
          onClick={onClear}
          className="rounded p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <X className="size-3.5" />
        </button>
      }
    />
  );
}
