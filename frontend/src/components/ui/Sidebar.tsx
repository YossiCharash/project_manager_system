import React from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useSelector } from 'react-redux'
import type { RootState } from '../../store'
import { selectHasAnyAccess } from '../../store/slices/permissionsSlice'
import { Logo } from './Logo'
import { cn } from '../../lib/utils'
import {
  LayoutDashboard,
  FolderOpen,
  BarChart2,
  FileText,
  Truck,
  Settings,
  Users,
  ShieldCheck,
  ClipboardList,
  Package,
  ChevronRight,
  ChevronLeft,
  X,
} from 'lucide-react'

interface NavItem {
  label: string
  to: string
  icon: React.ReactNode
  resource?: string
  adminOnly?: boolean
}

const NAV_ITEMS: NavItem[] = [
  { label: 'לוח בקרה', to: '/dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
  { label: 'פרויקטים', to: '/projects', icon: <FolderOpen className="w-5 h-5" />, resource: 'project' },
  { label: 'דוחות', to: '/reports', icon: <BarChart2 className="w-5 h-5" />, resource: 'report' },
  { label: 'הצעות מחיר', to: '/price-quotes', icon: <FileText className="w-5 h-5" />, resource: 'quote' },
  { label: 'ספקים', to: '/suppliers', icon: <Truck className="w-5 h-5" />, resource: 'supplier' },
  { label: 'ניהול משימות', to: '/task-management', icon: <ClipboardList className="w-5 h-5" />, resource: 'task' },
  { label: 'מלאי', to: '/inventory', icon: <Package className="w-5 h-5" /> },
  { label: 'משתמשים', to: '/users', icon: <Users className="w-5 h-5" /> },
  { label: 'הרשאות', to: '/admin-management', icon: <ShieldCheck className="w-5 h-5" /> },
  { label: 'הגדרות', to: '/settings', icon: <Settings className="w-5 h-5" /> },
]

function NavItems({ collapsed }: { collapsed: boolean }) {
  const me = useSelector((s: RootState) => s.auth.me)
  const permissions = useSelector((s: RootState) => s.permissions.permissions)
  const location = useLocation()

  const isActive = (to: string) =>
    location.pathname === to || location.pathname.startsWith(to + '/')

  const canSee = (item: NavItem) => {
    if (!item.resource) return true
    if (me?.role === 'Admin') return true
    return permissions.some((p) => p.resource_type === item.resource)
  }

  return (
    <nav className="flex-1 overflow-y-auto py-4 space-y-1 px-2">
      {NAV_ITEMS.filter(canSee).map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={cn(
            'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
            isActive(item.to)
              ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700',
            collapsed && 'justify-center px-2'
          )}
          title={collapsed ? item.label : undefined}
        >
          <span className="flex-shrink-0">{item.icon}</span>
          {!collapsed && <span className="truncate">{item.label}</span>}
        </NavLink>
      ))}
    </nav>
  )
}

interface SidebarProps {
  isCollapsed: boolean
  onToggle: () => void
}

export function Sidebar({ isCollapsed, onToggle }: SidebarProps) {
  return (
    <div
      className={cn(
        'fixed top-0 right-0 h-screen bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col z-30 transition-all duration-300',
        isCollapsed ? 'w-[80px]' : 'w-[280px]'
      )}
      dir="rtl"
    >
      {/* Logo area */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-4 border-b border-gray-200 dark:border-gray-700 h-[60px]">
        {!isCollapsed && <Logo size="md" showText />}
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          title={isCollapsed ? 'הרחב תפריט' : 'כווץ תפריט'}
        >
          {isCollapsed ? (
            <ChevronLeft className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          )}
        </button>
      </div>

      <NavItems collapsed={isCollapsed} />
    </div>
  )
}

interface MobileSidebarProps {
  isOpen: boolean
  onClose: () => void
}

export function MobileSidebar({ isOpen, onClose }: MobileSidebarProps) {
  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <div
        className={cn(
          'fixed top-0 right-0 h-screen w-[280px] bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col z-50 transition-transform duration-300 lg:hidden',
          isOpen ? 'translate-x-0' : 'translate-x-full'
        )}
        dir="rtl"
      >
        {/* Header */}
        <div className="flex-shrink-0 flex items-center justify-between px-4 py-4 border-b border-gray-200 dark:border-gray-700 h-[60px]">
          <Logo size="md" showText />
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title="סגור תפריט"
          >
            <X className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        <NavItems collapsed={false} />
      </div>
    </>
  )
}
