import React, { useState, useEffect, useMemo, useRef } from 'react';
import { getProgress } from '../services/readerAuth.js';
import { getTrackConfig } from '../constants.js';

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export default function CalendarView({ allPosts = [], onSelectPost }) {
  const [loading, setLoading] = useState(true);
  const [progressData, setProgressData] = useState(null);
  const [currentMonthDate, setCurrentMonthDate] = useState(() => new Date());
  const [selectedDateStr, setSelectedDateStr] = useState(null);
  const gridRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    getProgress()
      .then((res) => {
        if (mounted && res && res.progress) {
          setProgressData(res.progress);
        }
      })
      .catch((err) => console.warn('[CalendarView] Failed to load progress:', err))
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => { mounted = false; };
  }, []);

  const tz = progressData?.preferences?.timezone || 'Asia/Kolkata';
  const activityByDate = progressData?.activityByDate || {};

  const year = currentMonthDate.getFullYear();
  const month = currentMonthDate.getMonth(); // 0-indexed

  // Format month name (e.g. "November 2026")
  const monthTitle = useMemo(() => {
    return new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' }).format(currentMonthDate);
  }, [currentMonthDate]);

  // Today string in user tz
  const todayStr = useMemo(() => {
    return new Date().toLocaleDateString('en-CA', { timeZone: tz });
  }, [tz]);

  // Generate calendar days for the current month
  const calendarDays = useMemo(() => {
    const firstDayOfMonth = new Date(year, month, 1);
    const lastDayOfMonth = new Date(year, month + 1, 0);

    const totalDays = lastDayOfMonth.getDate();
    // Monday is index 0 in our week: Sunday (0) becomes 6, Monday (1) becomes 0
    let startDayOfWeek = firstDayOfMonth.getDay() - 1;
    if (startDayOfWeek === -1) startDayOfWeek = 6;

    const days = [];

    // Leading padding days from previous month
    for (let i = 0; i < startDayOfWeek; i++) {
      days.push({ empty: true, key: `empty-${i}` });
    }

    // Days of current month
    for (let day = 1; day <= totalDays; day++) {
      const dayDate = new Date(year, month, day);
      const dateStr = dayDate.toLocaleDateString('en-CA', { timeZone: tz });
      const readCount = activityByDate[dateStr] || 0;

      let level = 0;
      if (readCount >= 3) level = 3;
      else if (readCount >= 1) level = 1;

      days.push({
        empty: false,
        day,
        dateStr,
        readCount,
        level,
        isToday: dateStr === todayStr,
        key: dateStr,
      });
    }

    return days;
  }, [year, month, activityByDate, todayStr, tz]);

  // Posts read on the currently selected day
  const postsOnSelectedDay = useMemo(() => {
    if (!selectedDateStr || !allPosts || allPosts.length === 0) return [];
    // If the post was read and has matching date, show it
    return allPosts.filter((p) => {
      if (!p || !p.date) return false;
      const postDateStr = p.date.slice(0, 10);
      return postDateStr === selectedDateStr;
    });
  }, [selectedDateStr, allPosts]);

  function handlePrevMonth() {
    setCurrentMonthDate(new Date(year, month - 1, 1));
    setSelectedDateStr(null);
  }

  function handleNextMonth() {
    setCurrentMonthDate(new Date(year, month + 1, 1));
    setSelectedDateStr(null);
  }

  function handleTodayShortcut() {
    setCurrentMonthDate(new Date());
    setSelectedDateStr(todayStr);
  }

  // Keyboard navigation for accessible grid
  function handleKeyDown(e, dayObj, index) {
    if (dayObj.empty) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setSelectedDateStr(dayObj.dateStr);
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      focusDay(index + 1);
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      focusDay(index - 1);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      focusDay(index + 7);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      focusDay(index - 7);
    }
  }

  function focusDay(targetIdx) {
    const buttons = gridRef.current?.querySelectorAll('button.calendar-day-btn');
    if (buttons && buttons[targetIdx]) {
      buttons[targetIdx].focus();
    }
  }

  if (loading) {
    return (
      <div className="calendar-loading-skeleton" aria-busy="true" aria-label="Loading reading calendar">
        <div className="skeleton-line skeleton-title" />
        <div className="skeleton-grid" />
      </div>
    );
  }

  return (
    <div className="calendar-feature-root">
      {/* Metrics Banner */}
      <div className="calendar-metrics-strip">
        <div className="metric-box">
          <span className="metric-num">🔥 {progressData?.currentStreak || 0}</span>
          <span className="metric-label">day streak</span>
        </div>
        <div className="metric-box">
          <span className="metric-num">⚡ {progressData?.longestStreak || 0}</span>
          <span className="metric-label">longest streak</span>
        </div>
        <div className="metric-box">
          <span className="metric-num">📚 {progressData?.totalReads || 0}</span>
          <span className="metric-label">bites completed</span>
        </div>
      </div>

      {/* Calendar Card */}
      <div className="calendar-card">
        {/* Month Navigation Header */}
        <div className="calendar-month-header">
          <button
            type="button"
            className="calendar-nav-btn"
            onClick={handlePrevMonth}
            aria-label="Previous month"
          >
            ←
          </button>
          <div className="calendar-month-title-wrap">
            <h3 className="calendar-month-title">{monthTitle}</h3>
            <button
              type="button"
              className="calendar-today-btn"
              onClick={handleTodayShortcut}
            >
              Today
            </button>
          </div>
          <button
            type="button"
            className="calendar-nav-btn"
            onClick={handleNextMonth}
            aria-label="Next month"
          >
            →
          </button>
        </div>

        {/* Days of Week Row */}
        <div className="calendar-weekdays-row" aria-hidden="true">
          {WEEKDAYS.map((w) => (
            <span key={w} className="calendar-weekday-label">
              {w}
            </span>
          ))}
        </div>

        {/* Days Grid */}
        <div
          ref={gridRef}
          className="calendar-days-grid"
          role="grid"
          aria-label={`${monthTitle} Reading Activity`}
        >
          {calendarDays.map((d, idx) => {
            if (d.empty) {
              return <div key={d.key} className="calendar-day-empty" role="gridcell" aria-hidden="true" />;
            }

            const isSelected = selectedDateStr === d.dateStr;
            const intensityClass = `activity-level-${d.level}`;
            const todayClass = d.isToday ? 'is-today' : '';
            const selectedClass = isSelected ? 'is-selected' : '';

            return (
              <button
                key={d.key}
                type="button"
                role="gridcell"
                className={`calendar-day-btn ${intensityClass} ${todayClass} ${selectedClass}`}
                onClick={() => setSelectedDateStr(d.dateStr)}
                onKeyDown={(e) => handleKeyDown(e, d, idx)}
                aria-label={`${d.day} ${monthTitle}, ${d.readCount} post${d.readCount === 1 ? '' : 's'} read`}
                aria-selected={isSelected}
              >
                <span className="day-number">{d.day}</span>
                {d.readCount > 0 && <span className="activity-dot" aria-hidden="true" />}
              </button>
            );
          })}
        </div>

        {/* Legend */}
        <div className="calendar-legend-bar" aria-hidden="true">
          <span className="legend-label">Less</span>
          <span className="legend-cell activity-level-0" />
          <span className="legend-cell activity-level-1" />
          <span className="legend-cell activity-level-3" />
          <span className="legend-label">More</span>
        </div>
      </div>

      {/* Selected Day Details */}
      {selectedDateStr && (
        <div className="calendar-day-detail-drawer" role="region" aria-label="Selected day notes">
          <div className="detail-drawer-header">
            <h4>
              Activity on{' '}
              {new Date(selectedDateStr + 'T12:00:00Z').toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
              })}
            </h4>
            <button
              type="button"
              className="drawer-close-btn"
              onClick={() => setSelectedDateStr(null)}
              aria-label="Close day detail"
            >
              ✕
            </button>
          </div>

          {postsOnSelectedDay.length > 0 ? (
            <div className="drawer-posts-list">
              {postsOnSelectedDay.map((post) => {
                const trackCfg = getTrackConfig(post.track);
                return (
                  <div key={post.id} className="drawer-post-card">
                    <span
                      className="drawer-track-badge"
                      style={{ backgroundColor: trackCfg.bgTint, color: trackCfg.color }}
                    >
                      {trackCfg.shortLabel}
                    </span>
                    <strong className="drawer-post-title">{post.title}</strong>
                    <button
                      type="button"
                      className="drawer-view-btn"
                      onClick={() => onSelectPost && onSelectPost(post.id)}
                    >
                      Open Note →
                    </button>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="drawer-empty-text">
              {activityByDate[selectedDateStr]
                ? `${activityByDate[selectedDateStr]} bite(s) completed on this day.`
                : 'No reading activity recorded for this day.'}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
