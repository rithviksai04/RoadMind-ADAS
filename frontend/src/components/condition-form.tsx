"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CloudFog, CloudRain, Loader2, MapPin, Satellite, Snowflake, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";
import { getLiveWeather, getStates } from "@/lib/api";
import type { ConditionInput } from "@/lib/types";

const WEATHER_OPTIONS = [
  "Fair", "Clear", "Mostly Cloudy", "Partly Cloudy", "Cloudy", "Overcast", "Light Rain", "Rain", "Heavy Rain",
  "Thunderstorm", "Light Snow", "Snow", "Freezing Rain", "Fog", "Haze",
];
const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const PRESETS: { label: string; icon: typeof Sun; patch: ConditionInput }[] = [
  { label: "Clear day", icon: Sun, patch: { weather_condition: "Fair", temperature_f: 72, visibility_mi: 10, wind_speed_mph: 5, precipitation_in: 0, hour: 14, day_of_week: 2 } },
  { label: "Rainy rush hour", icon: CloudRain, patch: { weather_condition: "Heavy Rain", temperature_f: 58, visibility_mi: 2, wind_speed_mph: 18, precipitation_in: 0.3, hour: 17, day_of_week: 4 } },
  { label: "Foggy night", icon: CloudFog, patch: { weather_condition: "Fog", temperature_f: 45, visibility_mi: 0.5, wind_speed_mph: 3, precipitation_in: 0.02, hour: 23, day_of_week: 5 } },
  { label: "Winter storm", icon: Snowflake, patch: { weather_condition: "Snow", temperature_f: 26, visibility_mi: 1.5, wind_speed_mph: 22, precipitation_in: 0.1, hour: 7, day_of_week: 0 } },
];

const ROAD_TOGGLES: { key: keyof ConditionInput; label: string }[] = [
  { key: "junction", label: "Junction nearby" },
  { key: "traffic_signal", label: "Traffic signal nearby" },
  { key: "crossing", label: "Pedestrian crossing" },
  { key: "stop", label: "Stop sign" },
  { key: "railway", label: "Railway crossing" },
  { key: "roundabout", label: "Roundabout" },
];

interface ConditionFormProps {
  value: ConditionInput;
  onChange: (v: ConditionInput) => void;
  onAssess: () => void;
  loading: boolean;
}

export function ConditionForm({ value, onChange, onAssess, loading }: ConditionFormProps) {
  const [states, setStates] = useState<string[]>([]);
  const [fetchingWeather, setFetchingWeather] = useState(false);
  const [weatherError, setWeatherError] = useState<string | null>(null);
  const [stateFullName, setStateFullName] = useState("California");

  useEffect(() => {
    getStates().then((r) => setStates(r.states)).catch(() => setStates([]));
  }, []);

  function patch(p: ConditionInput) {
    onChange({ ...value, ...p });
  }

  async function useLiveWeather() {
    setFetchingWeather(true);
    setWeatherError(null);
    try {
      const w = await getLiveWeather(stateFullName);
      onChange({ ...value, ...w });
    } catch (e) {
      setWeatherError(e instanceof Error ? e.message : "Could not fetch live weather.");
    } finally {
      setFetchingWeather(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Preset scenarios */}
      <div>
        <Label className="mb-2 text-muted-foreground">Quick scenarios</Label>
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p) => {
            const Icon = p.icon;
            return (
              <button
                key={p.label}
                type="button"
                onClick={() => patch(p.patch)}
                className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:border-accent hover:bg-accent/10"
              >
                <Icon className="size-3.5 text-accent" aria-hidden />
                {p.label}
              </button>
            );
          })}
        </div>
      </div>

      <Separator />

      {/* Live weather */}
      <div className="space-y-2 rounded-lg border border-border-subtle bg-muted/40 p-3">
        <div className="flex items-center gap-2 text-sm font-medium text-foreground">
          <Satellite className="size-4 text-accent" aria-hidden />
          Live US weather
        </div>
        <div className="flex gap-2">
          <Select value={stateFullName} onValueChange={setStateFullName}>
            <SelectTrigger className="flex-1">
              <SelectValue placeholder="Select a state" />
            </SelectTrigger>
            <SelectContent>
              {states.map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button type="button" variant="secondary" size="sm" onClick={useLiveWeather} disabled={fetchingWeather}>
            {fetchingWeather ? <Loader2 className="size-4 animate-spin" /> : <MapPin className="size-4" />}
            Fetch
          </Button>
        </div>
        {weatherError && <p className="text-xs text-risk-high">{weatherError}</p>}
        {value.state && <p className="text-xs text-muted-foreground">Using conditions for state: {value.state}</p>}
      </div>

      <Separator />

      {/* Core weather inputs */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <div className="space-y-1.5 sm:col-span-2">
          <Label htmlFor="weather">Weather condition</Label>
          <Select value={value.weather_condition ?? "Fair"} onValueChange={(v) => patch({ weather_condition: v })}>
            <SelectTrigger id="weather" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {WEATHER_OPTIONS.map((w) => (
                <SelectItem key={w} value={w}>
                  {w}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <SliderField
          label="Visibility"
          unit="mi"
          value={value.visibility_mi ?? 10}
          min={0}
          max={10}
          step={0.5}
          onChange={(n) => patch({ visibility_mi: n })}
        />
        <SliderField
          label="Temperature"
          unit="°F"
          value={value.temperature_f ?? 65}
          min={-20}
          max={120}
          step={1}
          onChange={(n) => patch({ temperature_f: n })}
        />
        <SliderField
          label="Wind speed"
          unit="mph"
          value={value.wind_speed_mph ?? 5}
          min={0}
          max={60}
          step={1}
          onChange={(n) => patch({ wind_speed_mph: n })}
        />
        <SliderField
          label="Precipitation"
          unit="in/hr"
          value={value.precipitation_in ?? 0}
          min={0}
          max={1}
          step={0.01}
          decimals={2}
          onChange={(n) => patch({ precipitation_in: n })}
        />
      </div>

      <Separator />

      {/* Time */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <SliderField
          label="Hour of day (local)"
          unit=":00"
          value={value.hour ?? 12}
          min={0}
          max={23}
          step={1}
          suffixFirst
          onChange={(n) => patch({ hour: n })}
        />
        <div className="space-y-1.5">
          <Label>Day of week</Label>
          <Select value={String(value.day_of_week ?? 2)} onValueChange={(v) => patch({ day_of_week: Number(v) })}>
            <SelectTrigger className="w-full">
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
      </div>

      <Separator />

      {/* Road context */}
      <div>
        <Label className="mb-3 text-muted-foreground">Road context</Label>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {ROAD_TOGGLES.map((t) => (
            <label key={t.key} className="flex items-center justify-between gap-2 rounded-md border border-border-subtle px-3 py-2 text-sm">
              {t.label}
              <Switch
                checked={Boolean(value[t.key])}
                onCheckedChange={(checked) => patch({ [t.key]: checked })}
              />
            </label>
          ))}
        </div>
      </div>

      <Separator />

      {/* Documented dataset limitation fields - shown, disabled, never sent to the model */}
      <div className="space-y-3 rounded-lg border border-dashed border-border p-3">
        <p className="text-xs font-medium text-muted-foreground">Not available in this dataset (documented limitation)</p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 opacity-60">
          <DisabledField label="Traffic density" tooltip="US-Accidents (2016-2023) has no real-time traffic-density field. Simulating one would fabricate a feature the model was never trained on - see README limitations." />
          <DisabledField label="Vehicle speed" tooltip="This dataset has no driver-behavior fields (speed, braking, steering). A production version would need vehicle telematics - see README's 'what a production version would need'." />
        </div>
      </div>

      <motion.div whileTap={{ scale: 0.98 }}>
        <Button size="lg" className="w-full" onClick={onAssess} disabled={loading}>
          {loading ? <Loader2 className="size-4 animate-spin" /> : null}
          {loading ? "Assessing..." : "Assess Risk"}
        </Button>
      </motion.div>
    </div>
  );
}

function SliderField({
  label,
  unit,
  value,
  min,
  max,
  step,
  decimals = 0,
  suffixFirst = false,
  onChange,
}: {
  label: string;
  unit: string;
  value: number;
  min: number;
  max: number;
  step: number;
  decimals?: number;
  suffixFirst?: boolean;
  onChange: (n: number) => void;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label>{label}</Label>
        <span className="text-sm font-medium tabular-nums text-accent">
          {suffixFirst ? `${value.toString().padStart(2, "0")}${unit}` : `${value.toFixed(decimals)} ${unit}`}
        </span>
      </div>
      <Slider value={[value]} min={min} max={max} step={step} onValueChange={([n]) => onChange(n)} />
    </div>
  );
}

function DisabledField({ label, tooltip }: { label: string; tooltip: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className="space-y-1.5">
          <Label className="text-muted-foreground">{label}</Label>
          <div className="flex h-10 items-center rounded-md border border-border bg-muted px-3 text-sm text-muted-foreground">
            Not in dataset
          </div>
        </div>
      </TooltipTrigger>
      <TooltipContent>{tooltip}</TooltipContent>
    </Tooltip>
  );
}
