import React from 'react'
import { Navigate } from 'react-router-dom'

// Route /task-calendar redirects to /task-management — this component is
// never rendered.  The file exists only to satisfy the static import in
// App.tsx so Vite can resolve it at build time.
export default function TaskCalendar() {
  return <Navigate to="/task-management" replace />
}
