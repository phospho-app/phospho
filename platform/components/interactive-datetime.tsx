import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import moment from "moment";

/**
 * Display a datetime in a human-readable format.
 * - First row is "25 sept. 2021"
 * - Second row is "2 weeks ago" or "2 days ago" or "2 hours ago"
 * - When hovering, display the full human readable datetime: "25 sept. 2021, 14:30 UTC"
 * @param timestamp Unix timestamp in seconds
 * @returns
 * **/
function InteractiveDatetime({
  timestamp,
}: {
  timestamp: number | undefined | null;
}) {
  if (!timestamp) return null;

  const date = moment(timestamp * 1000);
  const timeAgo = moment.duration(moment().diff(date));
  const shortDate = date.format("MMM D, YYYY");
  const longDate = date.format("MMM D, YYYY HH:mm:ss UTC");

  return (
    <HoverCard openDelay={0} closeDelay={0}>
      <HoverCardTrigger>
        <div>{shortDate}</div>
        <div className="text-xs text-muted-foreground">
          {timeAgo.humanize()} ago
        </div>
      </HoverCardTrigger>
      <HoverCardContent className="text-xs">{longDate}</HoverCardContent>
    </HoverCard>
  );
}

export { InteractiveDatetime };
