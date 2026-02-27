import { createContext, useContext, useState, ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchFilters } from '../api/sessions'

interface ProjectContextType {
  allProjects: string[]
  selectedProjects: string[]
  setSelectedProjects: (projects: string[]) => void
  isAllSelected: boolean
  toggleProject: (project: string) => void
  selectAll: () => void
  clearAll: () => void
  projectsParam: string[] | undefined // For API calls
}

const ProjectContext = createContext<ProjectContextType | null>(null)

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [selectedProjects, setSelectedProjects] = useState<string[]>([])

  const { data: filters } = useQuery({
    queryKey: ['filters'],
    queryFn: fetchFilters,
  })

  const allProjects = filters?.projects ?? []
  const isAllSelected = selectedProjects.length === 0 || selectedProjects.length === allProjects.length

  const toggleProject = (project: string) => {
    setSelectedProjects((prev) => {
      if (prev.includes(project)) {
        return prev.filter((p) => p !== project)
      } else {
        return [...prev, project]
      }
    })
  }

  const selectAll = () => {
    setSelectedProjects([])
  }

  const clearAll = () => {
    setSelectedProjects([])
  }

  // For API calls: undefined means "all", otherwise pass the selected projects
  const projectsParam = isAllSelected ? undefined : selectedProjects

  return (
    <ProjectContext.Provider
      value={{
        allProjects,
        selectedProjects,
        setSelectedProjects,
        isAllSelected,
        toggleProject,
        selectAll,
        clearAll,
        projectsParam,
      }}
    >
      {children}
    </ProjectContext.Provider>
  )
}

export function useProjectFilter() {
  const context = useContext(ProjectContext)
  if (!context) {
    throw new Error('useProjectFilter must be used within a ProjectProvider')
  }
  return context
}
