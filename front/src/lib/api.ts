export type TaskStatus = "todo" | "in_progress" | "done"

export interface User {
  id: number
  username: string
  email: string
}

export interface AuthResponse {
  user: User
  detail?: string
}

export interface Project {
  id: number
  name: string
  description: string
  owner: User
  members: User[]
  is_owner: boolean
  created_at: string
  updated_at: string
}

export interface Task {
  id: number
  project_id: number
  title: string
  description: string
  status: TaskStatus
  assigned_to: User | null
  due_date: string | null
  created_at: string
  updated_at: string
}

interface ApiErrorPayload {
  detail?: string
  [key: string]: unknown
}

const API_BASE_URL = ((import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000/api").replace(/\/$/, "")
const CSRF_COOKIE_NAME = "csrftoken"
const CSRF_HEADER_NAME = "X-CSRFToken"
const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"])

let currentUser: User | null = null
let refreshPromise: Promise<boolean> | null = null
let sessionProbePromise: Promise<User | null> | null = null
let csrfBootstrapPromise: Promise<void> | null = null

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
}

function getCookie(name: string): string | null {
  const pattern = new RegExp(`(?:^|; )${escapeRegExp(name)}=([^;]*)`)
  const match = document.cookie.match(pattern)
  return match ? decodeURIComponent(match[1]) : null
}

async function ensureCsrfCookie(): Promise<void> {
  if (getCookie(CSRF_COOKIE_NAME)) {
    return
  }

  if (!csrfBootstrapPromise) {
    csrfBootstrapPromise = fetch(`${API_BASE_URL}/auth/csrf/`, {
      method: "GET",
      credentials: "include",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Impossible d'initialiser la protection CSRF.")
        }
      })
      .finally(() => {
        csrfBootstrapPromise = null
      })
  }

  await csrfBootstrapPromise
}

async function refreshSession(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      await ensureCsrfCookie()

      const headers = new Headers()
      const csrfToken = getCookie(CSRF_COOKIE_NAME)
      if (csrfToken) {
        headers.set(CSRF_HEADER_NAME, csrfToken)
      }

      const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
        method: "POST",
        headers,
        credentials: "include",
      })

      return response.ok
    })().finally(() => {
      refreshPromise = null
    })
  }

  return refreshPromise
}

export function getCurrentUser(): User | null {
  return currentUser
}

export function isAuthenticated(): boolean {
  return currentUser !== null
}

export function clearAuth(): void {
  currentUser = null
}

async function toErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload
    if (payload.detail && typeof payload.detail === "string") {
      return payload.detail
    }

    const firstEntry = Object.entries(payload)[0]
    if (!firstEntry) {
      return `Erreur ${response.status}`
    }

    const entryValue = firstEntry[1]
    if (Array.isArray(entryValue) && typeof entryValue[0] === "string") {
      return entryValue[0]
    }

    if (typeof entryValue === "string") {
      return entryValue
    }
  } catch {
    return `Erreur ${response.status}`
  }

  return `Erreur ${response.status}`
}

async function request<T>(path: string, init: RequestInit = {}, authenticated = true): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase()
  const headers = new Headers(init.headers)

  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json")
  }

  if (UNSAFE_METHODS.has(method)) {
    await ensureCsrfCookie()
    const csrfToken = getCookie(CSRF_COOKIE_NAME)
    if (csrfToken) {
      headers.set(CSRF_HEADER_NAME, csrfToken)
    }
  }

  const doFetch = async () =>
    fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers,
      credentials: "include",
    })

  let response = await doFetch()

  if (response.status === 401 && authenticated) {
    const refreshed = await refreshSession()
    if (refreshed) {
      response = await doFetch()
    }
  }

  if (!response.ok) {
    if (response.status === 401) {
      clearAuth()
    }
    throw new Error(await toErrorMessage(response))
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export async function register(payload: { username: string; email: string; password: string }): Promise<AuthResponse> {
  const authData = await request<AuthResponse>(
    "/auth/register/",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    false,
  )
  currentUser = authData.user
  return authData
}

export async function login(payload: { identifier: string; password: string }): Promise<AuthResponse> {
  const body = payload.identifier.includes("@")
    ? { email: payload.identifier, password: payload.password }
    : { username: payload.identifier, password: payload.password }

  const authData = await request<AuthResponse>(
    "/auth/login/",
    {
      method: "POST",
      body: JSON.stringify(body),
    },
    false,
  )
  currentUser = authData.user
  return authData
}

export async function fetchMe(): Promise<User> {
  const me = await request<User>("/auth/me/")
  currentUser = me
  return me
}

export async function hydrateSession(): Promise<User | null> {
  if (currentUser) {
    return currentUser
  }

  if (!sessionProbePromise) {
    sessionProbePromise = fetchMe()
      .then((user) => user)
      .catch(() => {
        clearAuth()
        return null
      })
      .finally(() => {
        sessionProbePromise = null
      })
  }

  return sessionProbePromise
}

export async function logout(): Promise<void> {
  try {
    await request<void>(
      "/auth/logout/",
      {
        method: "POST",
      },
      false,
    )
  } finally {
    clearAuth()
  }
}

export async function listProjects(): Promise<Project[]> {
  return request<Project[]>("/projects/")
}

export async function createProject(payload: { name: string; description: string }): Promise<Project> {
  return request<Project>("/projects/", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function deleteProject(projectId: number): Promise<void> {
  await request<void>(`/projects/${projectId}/`, {
    method: "DELETE",
  })
}

export async function listProjectMembers(projectId: number): Promise<User[]> {
  return request<User[]>(`/projects/${projectId}/members/`)
}

export async function addProjectMember(projectId: number, payload: { email: string }): Promise<User> {
  return request<User>(`/projects/${projectId}/members/`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function removeProjectMember(projectId: number, userId: number): Promise<void> {
  await request<void>(`/projects/${projectId}/members/${userId}/`, {
    method: "DELETE",
  })
}

export async function listTasks(projectId: number): Promise<Task[]> {
  return request<Task[]>(`/projects/${projectId}/tasks/`)
}

export async function createTask(
  projectId: number,
  payload: {
    title: string
    description: string
    status: TaskStatus
    due_date: string | null
    assigned_to_id?: number | null
  },
): Promise<Task> {
  return request<Task>(`/projects/${projectId}/tasks/`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function updateTask(
  projectId: number,
  taskId: number,
  payload: {
    title: string
    description: string
    status: TaskStatus
    due_date: string | null
    assigned_to_id?: number | null
  },
): Promise<Task> {
  return request<Task>(`/projects/${projectId}/tasks/${taskId}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
}

export async function deleteTask(projectId: number, taskId: number): Promise<void> {
  await request<void>(`/projects/${projectId}/tasks/${taskId}/`, {
    method: "DELETE",
  })
}
