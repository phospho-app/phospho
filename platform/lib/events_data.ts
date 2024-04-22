import { Event } from "@/models/models";

interface DayCount {
  date: string;
  total: number;
  eventCounts: { [eventName: string]: number };
}

export function getCountsPerDay(
  events: Event[],
  event_names: string[],
): DayCount[] {
  const currentDate = new Date();
  const countsPerDay: DayCount[] = [];
  const days = 7;

  for (let i = 0; i < days; i++) {
    const endDate = new Date(currentDate);
    endDate.setDate(currentDate.getDate() - i);
    endDate.setHours(23, 59, 59, 999);

    const startDate = new Date(currentDate);
    startDate.setDate(currentDate.getDate() - i);
    startDate.setHours(0, 0, 0, 0);

    if (events) {
      const filteredEvents = events.filter((event) => {
        const createdAt = new Date(Number(event.created_at) * 1000);
        return createdAt >= startDate && createdAt <= endDate;
      });

      const eventCounts: { [eventName: string]: number } = {};

      // Initialize counts for each event name
      event_names?.forEach((event_name) => {
        eventCounts[event_name] = filteredEvents.filter(
          (event) => event.event_name === event_name,
        ).length;
      });

      // Get the total count of events for the day
      const totalEventsForDay = filteredEvents.length;

      const formattedStartDate = startDate.toLocaleDateString("en-US", {
        day: "2-digit",
        month: "short",
      });

      countsPerDay.push({
        date: formattedStartDate,
        total: totalEventsForDay,
        eventCounts,
      });
    } else {
      countsPerDay.push({
        date: "No Data",
        total: 0,
        eventCounts: {},
      });
    }
  }

  return countsPerDay.reverse();
}

export function getCountsPerMinute(
  events: Event[],
  event_names: string[],
): DayCount[] {
  const countsPerMinute: DayCount[] = [];
  const currentTime = new Date(); // Current time in UTC
  const secondsPerMinute = 60;

  for (let i = 0; i < 30; i++) {
    const startTime = new Date(
      currentTime.getTime() - (i + 1) * secondsPerMinute * 1000,
    );
    const endTime = new Date(
      currentTime.getTime() - i * secondsPerMinute * 1000,
    );

    const filteredEvents = events.filter((event) => {
      const createdAt = new Date(Number(event.created_at) * 1000);
      return createdAt >= startTime && createdAt < endTime;
    });

    const eventCounts: { [eventName: string]: number } = {};

    // Initialize counts for each event name
    event_names?.forEach((event_name) => {
      eventCounts[event_name] = filteredEvents.filter(
        (event) => event.event_name === event_name,
      ).length;
    });

    // Get the total count of events for the day
    const totalEventsForDay = filteredEvents.length;

    const formattedTime = startTime.toISOString().slice(11, 16); // Format to HH:MM in UTC

    countsPerMinute.push({
      date: formattedTime,
      total: totalEventsForDay,
      eventCounts,
    });
  }

  return countsPerMinute.reverse();
}

// Get the count for each event name during the last 30 minutes
export function getCountsPerEvent(
  events: Event[],
  event_names: string[],
): { event_name: string; total: number }[] {
  const countsPerEvent: { event_name: string; total: number }[] = [];

  if (!events || !event_names) {
    return countsPerEvent;
  }

  // Counting occurrences of each event
  event_names?.forEach((eventName) => {
    if (!events?.filter) return;
    const filteredEvents = events.filter(
      (event) => event.event_name === eventName,
    );
    countsPerEvent.push({
      event_name: eventName,
      total: filteredEvents.length,
    });
  });

  // Sorting the countsPerEvent array by total in descending order
  countsPerEvent.sort((a, b) => b.total - a.total);

  return countsPerEvent;
}
