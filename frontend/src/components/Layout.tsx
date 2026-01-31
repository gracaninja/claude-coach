import { useState, useRef, useEffect } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { useProjectFilter } from '../context/ProjectContext'

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/sessions', label: 'Sessions' },
  { path: '/analytics', label: 'Analytics' },
  { path: '/errors', label: 'Errors' },
  { path: '/insights', label: 'Insights' },
]

function getProjectName(projectPath: string): string {
  if (!projectPath) return '-'
  const parts = projectPath.split('/')
  return parts[parts.length - 1] || projectPath
}

function ProjectSelector() {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const {
    allProjects,
    selectedProjects,
    isAllSelected,
    toggleProject,
    selectAll,
  } = useProjectFilter()

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const displayText = isAllSelected
    ? 'All Projects'
    : selectedProjects.length === 1
    ? getProjectName(selectedProjects[0])
    : `${selectedProjects.length} projects`

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
      >
        <span className="max-w-[200px] truncate">{displayText}</span>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 bg-white border border-gray-200 rounded-md shadow-lg z-50 max-h-96 overflow-auto">
          <div className="p-2 border-b">
            <button
              onClick={selectAll}
              className={`w-full text-left px-3 py-2 text-sm rounded hover:bg-gray-100 ${
                isAllSelected ? 'bg-indigo-50 text-indigo-700 font-medium' : ''
              }`}
            >
              All Projects
            </button>
          </div>
          <div className="p-2">
            {allProjects.map((project) => {
              const isSelected = selectedProjects.includes(project)
              return (
                <label
                  key={project}
                  className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-100 rounded cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleProject(project)}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="truncate" title={project}>
                    {getProjectName(project)}
                  </span>
                </label>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

function Layout() {
  const location = useLocation()

  return (
    <div className="min-h-screen">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <span className="text-xl font-bold text-indigo-600">Claude-Coach</span>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                {navItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      location.pathname === item.path
                        ? 'border-indigo-500 text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>
            <div className="flex items-center">
              <ProjectSelector />
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout
