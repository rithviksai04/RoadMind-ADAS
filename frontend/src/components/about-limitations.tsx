import { BookMarked, ExternalLink, ShieldAlert } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function AboutLimitations() {
  return (
    <div className="space-y-6">
      <Card className="border-l-4 border-l-risk-medium">
        <CardHeader>
          <div className="flex items-center gap-2">
            <ShieldAlert className="size-5 text-risk-medium" aria-hidden />
            <CardTitle>Research prototype - not a certified safety system</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground">
          <p>
            RoadMind is a technical project proposal and decision-support demo, grounded in a verified public dataset
            and standard machine-learning / explainability techniques. It <strong className="text-foreground">does not control the vehicle</strong>,
            has not been experimentally validated on live traffic, and no claim is made that it prevents accidents.
          </p>
          <p>
            The target variable (<code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">Severity</code>) measures{" "}
            <strong className="text-foreground">traffic-flow delay impact</strong>, not injury severity. The dataset contains only
            accidents that occurred, so predictions estimate the probability of a high-impact outcome{" "}
            <em>given that an accident occurs</em> under these conditions - not the probability that an accident happens at all.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <BookMarked className="size-5 text-accent" aria-hidden />
            <CardTitle>Dataset & attribution</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>
            <strong className="text-foreground">US Accidents (2016-2023)</strong> by Sobhan Moosavi et al. - ~7.7M rows, 46 columns,
            Feb 2016-Mar 2023, 49 US states.
          </p>
          <p>
            Licensed <strong className="text-foreground">CC BY-NC-SA 4.0</strong> - research / non-commercial use only.
          </p>
          <a
            href="https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-accent hover:underline"
          >
            kaggle.com/datasets/sobhanmoosavi/us-accidents <ExternalLink className="size-3.5" aria-hidden />
          </a>
          <p className="pt-2">
            Moosavi, S., Samavatian, M. H., Parthasarathy, S., Ramnath, R. (2019).{" "}
            <em>A Countrywide Traffic Accident Dataset.</em> arXiv:1906.05409.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Known limitations</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-disc space-y-1.5 pl-5 text-sm text-muted-foreground">
            <li>No driver-behavior fields (speed, braking, steering) and no real-time traffic-density field in this dataset.</li>
            <li>Road-surface condition is derived from weather + precipitation, not measured directly.</li>
            <li>Severity labeling drifts across data providers and years - see the primary vs. time-based split comparison.</li>
            <li>Modest predictive signal: ROC-AUC ≈ 0.75, High-tier precision ≈ 37% - most of the signal is location and road annotations, not weather.</li>
            <li>Only US, 2016-2023 data; performance elsewhere is unknown.</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
