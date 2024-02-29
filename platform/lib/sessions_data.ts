import { Session, SessionWithTasks } from "@/models/sessions";
import { Task } from "@/models/tasks";

export function getCountsPerDay(
  sessions: Session[]
): { name: string; total: number }[] {
  const currentDate = new Date();
  const countsPerDay: { name: string; total: number }[] = [];
  const days = 7;

  for (let i = 0; i < days; i++) {
    const endDate = new Date(currentDate);
    endDate.setDate(currentDate.getDate() - i);
    endDate.setHours(23, 59, 59, 999); // Set the end time to 23:59:59.999

    const startDate = new Date(currentDate);
    startDate.setDate(currentDate.getDate() - i);
    startDate.setHours(0, 0, 0, 0); // Set the start time to 00:00:00.000

    const filteredSessions = sessions.filter((session) => {
      const createdAt = new Date(Number(session.created_at) * 1000);
      return createdAt >= startDate && createdAt <= endDate;
    });

    const countSessionsForDay = filteredSessions.length;

    const formattedStartDate = startDate.toLocaleDateString("en-US", {
      day: "2-digit",
      month: "short",
    });

    countsPerDay.push({ name: formattedStartDate, total: countSessionsForDay });
  }

  return countsPerDay.reverse();
}

export function getCountsPerMinute(
  sessions: Session[]
): { name: string; total: number }[] {
  const countsPerMinute: { name: string; total: number }[] = [];
  const currentTime = new Date(); // Current time in UTC
  const secondsPerMinute = 60;

  for (let i = 0; i < 30; i++) {
    const startTime = new Date(
      currentTime.getTime() - (i + 1) * secondsPerMinute * 1000
    );
    const endTime = new Date(
      currentTime.getTime() - i * secondsPerMinute * 1000
    );

    const filteredSessions = sessions.filter((session) => {
      const createdAt = new Date(Number(session.created_at) * 1000);
      return createdAt >= startTime && createdAt < endTime;
    });

    const countSessionsForMinute = filteredSessions.length;
    const formattedTime = startTime.toISOString().slice(11, 16); // Format to HH:MM in UTC

    // countsPerMinute.push({ name: formattedTime, total: countSessionsForMinute });
    countsPerMinute.push({
      name: formattedTime,
      total: countSessionsForMinute,
    });
  }

  return countsPerMinute.reverse(); // Reverse to get chronological order
}

export function getTaskCountsPerMinute(
  tasks: Task[]
): { name: string; total: number }[] {
  const countsPerMinute: { name: string; total: number }[] = [];
  const currentTime = new Date(); // Current time in UTC
  const secondsPerMinute = 60;

  for (let i = 0; i < 30; i++) {
    const startTime = new Date(
      currentTime.getTime() - (i + 1) * secondsPerMinute * 1000
    );
    const endTime = new Date(
      currentTime.getTime() - i * secondsPerMinute * 1000
    );

    const filteredTasks = tasks.filter((task) => {
      const createdAt = new Date(Number(task.created_at) * 1000);
      return createdAt >= startTime && createdAt < endTime;
    });

    const countTaskForMinute = filteredTasks?.length;
    const formattedTime = startTime.toISOString().slice(11, 16); // Format to HH:MM in UTC

    // countsPerMinute.push({ name: formattedTime, total: countSessionsForMinute });
    countsPerMinute.push({ name: formattedTime, total: countTaskForMinute });
  }

  return countsPerMinute.reverse(); // Reverse to get chronological order
}

export function getCountOfTasksByStatus(
  tasks: Task[],
  days: number = 7
): { name: string; success: number; failure: number; undefined: number }[] {
  const currentDate = new Date();
  const results: {
    name: string;
    success: number;
    failure: number;
    undefined: number;
  }[] = [];

  for (let i = 0; i < days; i++) {
    const endDate = new Date(currentDate);
    endDate.setDate(currentDate.getDate() - i);
    endDate.setHours(23, 59, 59, 999); // Set the end time to 23:59:59.999

    const startDate = new Date(currentDate);
    startDate.setDate(currentDate.getDate() - i);
    startDate.setHours(0, 0, 0, 0); // Set the start time to 00:00:00.000

    const filteredTasks = tasks.filter((task) => {
      const createdAt = new Date(Number(task.created_at) * 1000);
      return createdAt >= startDate && createdAt <= endDate;
    });

    const dailyResult = {
      name: startDate.toLocaleDateString("en-US", {
        day: "2-digit",
        month: "short",
      }),
      success: filteredTasks.filter((task) => task.flag === "success").length,
      failure: filteredTasks.filter((task) => task.flag === "failure").length,
      undefined: filteredTasks.filter(
        (task) => !task.flag || task.flag === undefined
      ).length,
    };

    results.push(dailyResult);
  }
  return results.reverse();
}

// Obsolete
export function getCountOfSessionsByStatus(
  sessions: Session[],
  days: number = 7
): { name: string; success: number; failure: number; undefined: number }[] {
  const currentDate = new Date();
  const results: {
    name: string;
    success: number;
    failure: number;
    undefined: number;
  }[] = [];

  for (let i = 0; i < days; i++) {
    const endDate = new Date(currentDate);
    endDate.setDate(currentDate.getDate() - i);
    endDate.setHours(23, 59, 59, 999); // Set the end time to 23:59:59.999

    const startDate = new Date(currentDate);
    startDate.setDate(currentDate.getDate() - i);
    startDate.setHours(0, 0, 0, 0); // Set the start time to 00:00:00.000

    const filteredSessions = sessions.filter((session) => {
      const createdAt = new Date(Number(session.created_at) * 1000);
      return createdAt >= startDate && createdAt <= endDate;
    });

    const dailyResult = {
      name: startDate.toLocaleDateString("en-US", {
        day: "2-digit",
        month: "short",
      }),
      success: filteredSessions.filter(
        (session) => session.metadata && session.metadata.flag === "success"
      ).length,
      failure: filteredSessions.filter(
        (session) => session.metadata && session.metadata.flag === "failure"
      ).length,
      undefined: filteredSessions.filter(
        (session) =>
          !session.metadata ||
          !session.metadata.flag ||
          (session.metadata &&
            session.metadata.flag !== "success" &&
            session.metadata.flag !== "failure")
      ).length,
    };

    results.push(dailyResult);
  }
  return results.reverse();
}
