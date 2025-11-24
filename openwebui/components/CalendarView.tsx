/**
 * Calendar View Component - Shows events and deadlines from emails
 * Monthly/weekly view with event creation
 */

import React, { useState, useEffect } from 'react';

interface CalendarEvent {
  event_id: string;
  title: string;
  description: string;
  start_time: string;
  end_time?: string;
  event_type: 'deadline' | 'meeting' | 'reminder' | 'task';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  email_id?: string;
  created_from_email?: boolean;
  status: 'pending' | 'confirmed' | 'cancelled';
}

interface CalendarViewProps {
  className?: string;
}

export const CalendarView: React.FC<CalendarViewProps> = ({ className = '' }) => {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [viewMode, setViewMode] = useState<'month' | 'week'>('month');
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const fetchEvents = async () => {
    try {
      const startDate = getViewStartDate();
      const endDate = getViewEndDate();

      const response = await fetch(
        `http://localhost:5000/api/calendar/events?start=${startDate.toISOString()}&end=${endDate.toISOString()}`
      );
      const data = await response.json();
      setEvents(data.events || []);
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to fetch calendar events:', error);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [selectedDate, viewMode]);

  const getViewStartDate = (): Date => {
    if (viewMode === 'month') {
      const start = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1);
      start.setDate(start.getDate() - start.getDay()); // Go to Sunday of first week
      return start;
    } else {
      const start = new Date(selectedDate);
      start.setDate(start.getDate() - start.getDay()); // Go to Sunday
      return start;
    }
  };

  const getViewEndDate = (): Date => {
    if (viewMode === 'month') {
      const end = new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 0);
      end.setDate(end.getDate() + (6 - end.getDay())); // Go to Saturday of last week
      return end;
    } else {
      const end = new Date(selectedDate);
      end.setDate(end.getDate() + (6 - end.getDay())); // Go to Saturday
      return end;
    }
  };

  const getDaysInView = (): Date[] => {
    const days: Date[] = [];
    const start = getViewStartDate();
    const end = getViewEndDate();

    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      days.push(new Date(d));
    }
    return days;
  };

  const getEventsForDate = (date: Date): CalendarEvent[] => {
    return events.filter(event => {
      const eventDate = new Date(event.start_time);
      return (
        eventDate.getDate() === date.getDate() &&
        eventDate.getMonth() === date.getMonth() &&
        eventDate.getFullYear() === date.getFullYear()
      );
    });
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    const newDate = new Date(selectedDate);
    newDate.setMonth(newDate.getMonth() + (direction === 'next' ? 1 : -1));
    setSelectedDate(newDate);
  };

  const navigateWeek = (direction: 'prev' | 'next') => {
    const newDate = new Date(selectedDate);
    newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7));
    setSelectedDate(newDate);
  };

  const getEventColor = (event: CalendarEvent) => {
    switch (event.event_type) {
      case 'deadline':
        return 'bg-red-100 text-red-700 border-red-300';
      case 'meeting':
        return 'bg-blue-100 text-blue-700 border-blue-300';
      case 'reminder':
        return 'bg-yellow-100 text-yellow-700 border-yellow-300';
      case 'task':
        return 'bg-green-100 text-green-700 border-green-300';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  const getPriorityIndicator = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return '🔴';
      case 'high':
        return '🟠';
      case 'medium':
        return '🟡';
      case 'low':
        return '🟢';
      default:
        return '⚪';
    }
  };

  const isToday = (date: Date): boolean => {
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  };

  const isCurrentMonth = (date: Date): boolean => {
    return date.getMonth() === selectedDate.getMonth();
  };

  return (
    <div className={`calendar-view ${className} h-full flex flex-col bg-gray-100`}>
      {/* Header */}
      <div className="p-4 bg-white shadow">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-bold text-gray-800">Calendar</h2>
            <div className="flex items-center gap-2">
              <button
                onClick={() => (viewMode === 'month' ? navigateMonth('prev') : navigateWeek('prev'))}
                className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded"
              >
                ‹
              </button>
              <button
                onClick={() => setSelectedDate(new Date())}
                className="px-4 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Today
              </button>
              <button
                onClick={() => (viewMode === 'month' ? navigateMonth('next') : navigateWeek('next'))}
                className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded"
              >
                ›
              </button>
            </div>
            <h3 className="text-xl font-semibold text-gray-700">
              {selectedDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex bg-gray-200 rounded">
              <button
                onClick={() => setViewMode('month')}
                className={`px-4 py-2 rounded ${
                  viewMode === 'month' ? 'bg-blue-600 text-white' : 'text-gray-700'
                }`}
              >
                Month
              </button>
              <button
                onClick={() => setViewMode('week')}
                className={`px-4 py-2 rounded ${
                  viewMode === 'week' ? 'bg-blue-600 text-white' : 'text-gray-700'
                }`}
              >
                Week
              </button>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              + New Event
            </button>
          </div>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="flex-1 p-4 overflow-y-auto">
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {/* Day Headers */}
          <div className="grid grid-cols-7 bg-gray-50 border-b">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="p-3 text-center font-semibold text-gray-700">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar Days */}
          <div className="grid grid-cols-7 auto-rows-fr min-h-[600px]">
            {getDaysInView().map((date, index) => {
              const dayEvents = getEventsForDate(date);
              const isTodayDate = isToday(date);
              const isCurrentMonthDate = isCurrentMonth(date);

              return (
                <div
                  key={index}
                  className={`border-r border-b p-2 min-h-[120px] ${
                    !isCurrentMonthDate ? 'bg-gray-50' : ''
                  } ${isTodayDate ? 'bg-blue-50' : ''}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`text-sm font-medium ${
                        isTodayDate
                          ? 'bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center'
                          : !isCurrentMonthDate
                          ? 'text-gray-400'
                          : 'text-gray-700'
                      }`}
                    >
                      {date.getDate()}
                    </span>
                    {dayEvents.length > 0 && (
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                        {dayEvents.length}
                      </span>
                    )}
                  </div>
                  <div className="space-y-1">
                    {dayEvents.slice(0, 3).map(event => (
                      <button
                        key={event.event_id}
                        onClick={() => setSelectedEvent(event)}
                        className={`w-full text-left text-xs p-1 rounded border truncate ${getEventColor(
                          event
                        )}`}
                      >
                        <span className="mr-1">{getPriorityIndicator(event.priority)}</span>
                        {event.title}
                      </button>
                    ))}
                    {dayEvents.length > 3 && (
                      <div className="text-xs text-gray-500 text-center">
                        +{dayEvents.length - 3} more
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Event Details Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-lg w-full">
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-2xl font-bold text-gray-800">{selectedEvent.title}</h3>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <span className="text-sm text-gray-500">Type:</span>
                <div className="mt-1">
                  <span className={`px-3 py-1 rounded border text-sm ${getEventColor(selectedEvent)}`}>
                    {selectedEvent.event_type}
                  </span>
                </div>
              </div>
              <div>
                <span className="text-sm text-gray-500">Priority:</span>
                <p className="font-medium text-gray-800 mt-1">
                  {getPriorityIndicator(selectedEvent.priority)} {selectedEvent.priority}
                </p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Start Time:</span>
                <p className="font-medium text-gray-800 mt-1">
                  {new Date(selectedEvent.start_time).toLocaleString()}
                </p>
              </div>
              {selectedEvent.end_time && (
                <div>
                  <span className="text-sm text-gray-500">End Time:</span>
                  <p className="font-medium text-gray-800 mt-1">
                    {new Date(selectedEvent.end_time).toLocaleString()}
                  </p>
                </div>
              )}
              <div>
                <span className="text-sm text-gray-500">Description:</span>
                <p className="text-gray-700 mt-1 whitespace-pre-wrap">{selectedEvent.description}</p>
              </div>
              {selectedEvent.created_from_email && (
                <div className="bg-blue-50 border border-blue-200 rounded p-3">
                  <p className="text-sm text-blue-800">
                    Created from email: <code className="font-mono">{selectedEvent.email_id}</code>
                  </p>
                </div>
              )}
              <div className="flex gap-2 pt-4">
                <button className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                  Edit Event
                </button>
                <button className="flex-1 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
                  Delete Event
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
