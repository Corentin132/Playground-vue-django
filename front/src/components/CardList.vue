<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  createTask,
  deleteTask,
  listProjects,
  listTasks,
  updateTask,
  type Task as ApiTask,
  type TaskStatus as ApiTaskStatus,
} from '../lib/api'

import Card from './ui/card.vue'

interface Task {
  id: number
  title: string
  company: string
  timeAgo: string
  color: string
  status: TaskStatus
  order: number
  dueDate: string | null
}

type TaskStatus = 'todos' | 'in-progress' | 'done'

interface Column {
  key: TaskStatus
  label: string
}

const route = useRoute()
const router = useRouter()

const projectName = ref('Projet')
const loading = ref(false)
const creating = ref(false)
const error = ref('')

const newTitle = ref('')
const newDescription = ref('')
const newStatus = ref<TaskStatus>('todos')

const projectId = computed(() => Number(route.params.projectId))

const columns: Column[] = [
  { key: 'todos', label: 'Todo' },
  { key: 'in-progress', label: 'In Progress' },
  { key: 'done', label: 'Done' },
]

const tasks = ref<Task[]>([])

const statusColor: Record<TaskStatus, string> = {
  todos: '#0066ff',
  'in-progress': '#ff7a00',
  done: '#19a15f',
}

const apiToBoardStatus = (status: ApiTaskStatus): TaskStatus => {
  if (status === 'in_progress') return 'in-progress'
  if (status === 'done') return 'done'
  return 'todos'
}

const boardToApiStatus = (status: TaskStatus): ApiTaskStatus => {
  if (status === 'in-progress') return 'in_progress'
  if (status === 'done') return 'done'
  return 'todo'
}

const formatTimeAgo = (isoDate: string): string => {
  const now = Date.now()
  const target = new Date(isoDate).getTime()
  const deltaSeconds = Math.max(0, Math.floor((now - target) / 1000))

  if (deltaSeconds < 60) return 'à l\'instant'

  const minutes = Math.floor(deltaSeconds / 60)
  if (minutes < 60) return `il y a ${minutes} min`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `il y a ${hours} h`

  const days = Math.floor(hours / 24)
  return `il y a ${days} j`
}

const fromApiTasks = (apiTasks: ApiTask[]): Task[] => {
  const orderByStatus: Record<TaskStatus, number> = {
    todos: 0,
    'in-progress': 0,
    done: 0,
  }

  return apiTasks.map((apiTask) => {
    const boardStatus = apiToBoardStatus(apiTask.status)
    orderByStatus[boardStatus] += 1

    return {
      id: apiTask.id,
      title: apiTask.title,
      company: apiTask.description || 'Sans description',
      timeAgo: formatTimeAgo(apiTask.created_at),
      color: statusColor[boardStatus],
      status: boardStatus,
      order: orderByStatus[boardStatus],
      dueDate: apiTask.due_date,
    }
  })
}

const activeColumn = ref<TaskStatus | null>(null)
const draggedTaskId = ref<number | null>(null)
const draggedTaskStartStatus = ref<TaskStatus | null>(null)
const dragPreviewEl = ref<HTMLElement | null>(null)
const dragOffset = ref({ x: 0, y: 0 })
const lastPlacementKey = ref<string | null>(null)
const lastPointerX = ref<number | null>(null)
const filteredDeltaX = ref(0)
const currentRotation = ref(0)
const targetRotation = ref(0)

const contextMenuVisible = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
const contextMenuTaskId = ref<number | null>(null)

const orderedTasksByStatus = computed<Record<TaskStatus, Task[]>>(() => ({
  todos: tasks.value.filter((task) => task.status === 'todos').sort((a, b) => a.order - b.order),
  'in-progress': tasks.value.filter((task) => task.status === 'in-progress').sort((a, b) => a.order - b.order),
  done: tasks.value.filter((task) => task.status === 'done').sort((a, b) => a.order - b.order),
}))

const getTaskById = (id: number) => tasks.value.find((task) => task.id === id)

const loadProjectData = async () => {
  if (Number.isNaN(projectId.value) || projectId.value <= 0) {
    error.value = 'Identifiant projet invalide.'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const [allProjects, projectTasks] = await Promise.all([
      listProjects(),
      listTasks(projectId.value),
    ])

    const found = allProjects.find((project) => project.id === projectId.value)
    projectName.value = found?.name || `Projet #${projectId.value}`
    tasks.value = fromApiTasks(projectTasks)
  } catch (caughtError: unknown) {
    error.value = caughtError instanceof Error ? caughtError.message : 'Erreur inconnue'
  } finally {
    loading.value = false
  }
}

const createNewTask = async () => {
  if (!newTitle.value.trim()) {
    error.value = 'Le titre est requis.'
    return
  }

  creating.value = true
  error.value = ''

  try {
    const created = await createTask(projectId.value, {
      title: newTitle.value.trim(),
      description: newDescription.value.trim(),
      status: boardToApiStatus(newStatus.value),
      due_date: null,
    })

    const [newTask] = fromApiTasks([created])
    newTask.order = orderedTasksByStatus.value[newTask.status].length + 1
    tasks.value = [...tasks.value, newTask]

    newTitle.value = ''
    newDescription.value = ''
    newStatus.value = 'todos'
  } catch (caughtError: unknown) {
    error.value = caughtError instanceof Error ? caughtError.message : 'Erreur inconnue'
  } finally {
    creating.value = false
  }
}

const updateTaskStatus = async (taskId: number, previousStatus: TaskStatus, nextStatus: TaskStatus) => {
  const task = getTaskById(taskId)
  if (!task || previousStatus === nextStatus) return

  try {
    await updateTask(projectId.value, taskId, {
      title: task.title,
      description: task.company,
      status: boardToApiStatus(nextStatus),
      due_date: task.dueDate,
    })
  } catch (caughtError: unknown) {
    task.status = previousStatus
    task.color = statusColor[previousStatus]
    normalizeColumnOrder(nextStatus)
    normalizeColumnOrder(previousStatus)
    error.value = caughtError instanceof Error ? caughtError.message : 'Erreur inconnue'
  }
}

const editTask = async (taskId: number) => {
  const task = getTaskById(taskId)
  if (!task) return

  const nextTitle = window.prompt('Titre de la tâche', task.title)
  if (nextTitle === null) return

  const nextDescription = window.prompt('Description', task.company)
  if (nextDescription === null) return

  if (!nextTitle.trim()) {
    error.value = 'Le titre est requis.'
    return
  }

  error.value = ''

  try {
    const updated = await updateTask(projectId.value, task.id, {
      title: nextTitle.trim(),
      description: nextDescription.trim(),
      status: boardToApiStatus(task.status),
      due_date: task.dueDate,
    })

    task.title = updated.title
    task.company = updated.description || 'Sans description'
  } catch (caughtError: unknown) {
    error.value = caughtError instanceof Error ? caughtError.message : 'Erreur inconnue'
  }
}

const removeTask = async (taskId: number) => {
  const task = getTaskById(taskId)
  if (!task) return

  const accepted = window.confirm('Supprimer cette tâche ?')
  if (!accepted) return

  error.value = ''

  try {
    await deleteTask(projectId.value, taskId)
    tasks.value = tasks.value.filter((item) => item.id !== taskId)
    normalizeColumnOrder(task.status)
  } catch (caughtError: unknown) {
    error.value = caughtError instanceof Error ? caughtError.message : 'Erreur inconnue'
  }
}

const closeTaskContextMenu = () => {
  contextMenuVisible.value = false
  contextMenuTaskId.value = null
}

const onTaskContextMenu = (event: MouseEvent, taskId: number) => {
  event.preventDefault()

  const menuWidth = 170
  const menuHeight = 100
  const margin = 8

  contextMenuX.value = Math.min(event.clientX, window.innerWidth - menuWidth - margin)
  contextMenuY.value = Math.min(event.clientY, window.innerHeight - menuHeight - margin)
  contextMenuTaskId.value = taskId
  contextMenuVisible.value = true
}

const onContextAction = (action: 'edit' | 'delete') => {
  const taskId = contextMenuTaskId.value
  closeTaskContextMenu()

  if (taskId === null) return

  if (action === 'edit') {
    void editTask(taskId)
    return
  }

  void removeTask(taskId)
}

const onGlobalPointerDown = () => {
  if (contextMenuVisible.value) {
    closeTaskContextMenu()
  }
}

const onGlobalKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    closeTaskContextMenu()
  }
}

const backToProjects = async () => {
  await router.push('/projects')
}

const normalizeColumnOrder = (status: TaskStatus) => {
  orderedTasksByStatus.value[status].forEach((task, index) => {
    task.order = index + 1
  })
}

const setOrderForColumn = (status: TaskStatus, orderedIds: number[]) => {
  orderedIds.forEach((id, index) => {
    const task = getTaskById(id)
    if (task) {
      task.status = status
      task.order = index + 1
    }
  })
}

const moveDraggedTaskTo = (targetStatus: TaskStatus, targetIndex: number) => {
  if (draggedTaskId.value === null) return

  const draggedTask = getTaskById(draggedTaskId.value)
  if (!draggedTask) return

  const placementKey = `${targetStatus}-${targetIndex}`
  if (lastPlacementKey.value === placementKey) return

  const sourceStatus = draggedTask.status
  const targetIds = orderedTasksByStatus.value[targetStatus]
    .filter((task) => task.id !== draggedTask.id)
    .map((task) => task.id)

  const boundedIndex = Math.max(0, Math.min(targetIndex, targetIds.length))
  targetIds.splice(boundedIndex, 0, draggedTask.id)
  setOrderForColumn(targetStatus, targetIds)

  if (sourceStatus !== targetStatus) {
    normalizeColumnOrder(sourceStatus)
  }

  lastPlacementKey.value = placementKey
}

const getDropIndexInColumn = (columnElement: HTMLElement, pointerY: number) => {
  const cardSlots = Array.from(columnElement.querySelectorAll<HTMLElement>('[data-task-id]'))
    .filter((element) => Number(element.dataset.taskId) !== draggedTaskId.value)

  for (let index = 0; index < cardSlots.length; index += 1) {
    const rect = cardSlots[index].getBoundingClientRect()
    if (pointerY < rect.top + rect.height / 2) {
      return index
    }
  }

  return cardSlots.length
}

const statusFromNode = (node: Element | null): TaskStatus | null => {
  const status = node?.closest('[data-column-status]')?.getAttribute('data-column-status')
  if (status === 'todos' || status === 'in-progress' || status === 'done') return status
  return null
}

const movePreview = (clientX: number, clientY: number, rotation: number) => {
  if (!dragPreviewEl.value) return
  dragPreviewEl.value.style.left = `${clientX - dragOffset.value.x}px`
  dragPreviewEl.value.style.top = `${clientY - dragOffset.value.y}px`
  dragPreviewEl.value.style.transform = `rotate(${rotation}deg)`
}

const onGlobalMouseMove = (event: MouseEvent) => {
  if (draggedTaskId.value === null) return

  let deltaX = 0
  if (lastPointerX.value !== null) {
    deltaX = event.clientX - lastPointerX.value
  }

  filteredDeltaX.value = filteredDeltaX.value * 0.8 + deltaX * 0.2

  if (filteredDeltaX.value > 1.2) {
    targetRotation.value = 10
  } else if (filteredDeltaX.value < -1.2) {
    targetRotation.value = -10
  } else {
    targetRotation.value = 0
  }

  currentRotation.value = currentRotation.value * 0.78 + targetRotation.value * 0.22

  movePreview(event.clientX, event.clientY, currentRotation.value)
  lastPointerX.value = event.clientX

  const hovered = document.elementFromPoint(event.clientX, event.clientY)
  const targetStatus = statusFromNode(hovered)
  if (!targetStatus) return

  activeColumn.value = targetStatus

  const columnElement = hovered?.closest('[data-column-status]') as HTMLElement | null
  if (!columnElement) return

  const targetIndex = getDropIndexInColumn(columnElement, event.clientY)
  moveDraggedTaskTo(targetStatus, targetIndex)
}

const clearPreview = () => {
  if (dragPreviewEl.value) {
    dragPreviewEl.value.remove()
    dragPreviewEl.value = null
  }
}

// clear le drag en cours et les listeners associés
const stopCustomDrag = () => {
  draggedTaskId.value = null
  draggedTaskStartStatus.value = null
  activeColumn.value = null
  lastPlacementKey.value = null
  lastPointerX.value = null
  filteredDeltaX.value = 0
  currentRotation.value = 0
  targetRotation.value = 0
  clearPreview()

  window.removeEventListener('mousemove', onGlobalMouseMove)
  window.removeEventListener('mouseup', onGlobalMouseUp)

  document.body.style.userSelect = ''
  document.body.style.cursor = ''
}

const onGlobalMouseUp = () => {
  const taskId = draggedTaskId.value
  const fromStatus = draggedTaskStartStatus.value
  const currentTask = taskId !== null ? getTaskById(taskId) : undefined

  if (taskId !== null && fromStatus && currentTask && currentTask.status !== fromStatus) {
    void updateTaskStatus(taskId, fromStatus, currentTask.status)
  }

  stopCustomDrag()
}

const onCardMouseDown = (event: MouseEvent, taskId: number) => {
  if (event.button !== 0) return

  closeTaskContextMenu()

  const taskElement = event.currentTarget as HTMLElement
  const rect = taskElement.getBoundingClientRect()

  draggedTaskId.value = taskId
  draggedTaskStartStatus.value = getTaskById(taskId)?.status ?? null
  lastPlacementKey.value = null
  lastPointerX.value = event.clientX
  filteredDeltaX.value = 0
  currentRotation.value = 0
  targetRotation.value = 0
  dragOffset.value = {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top,
  }

  const clone = taskElement.cloneNode(true) as HTMLElement
  Object.assign(clone.style, {
    position: 'fixed',
    width: `${rect.width}px`,
    left: `${rect.left}px`,
    top: `${rect.top}px`,
    pointerEvents: 'none',
    zIndex: '9999',
    transform: 'rotate(0deg)',
    transition: 'transform 0.1s',


  })

  dragPreviewEl.value = clone
  document.body.appendChild(clone)

  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'grabbing'

  window.addEventListener('mousemove', onGlobalMouseMove)
  window.addEventListener('mouseup', onGlobalMouseUp)
}

onBeforeUnmount(() => {
  stopCustomDrag()
  window.removeEventListener('mousedown', onGlobalPointerDown)
  window.removeEventListener('keydown', onGlobalKeyDown)
  window.removeEventListener('resize', closeTaskContextMenu)
  window.removeEventListener('scroll', closeTaskContextMenu, true)
})

onMounted(() => {
  window.addEventListener('mousedown', onGlobalPointerDown)
  window.addEventListener('keydown', onGlobalKeyDown)
  window.addEventListener('resize', closeTaskContextMenu)
  window.addEventListener('scroll', closeTaskContextMenu, true)
  void loadProjectData()
})
</script>

<template>
  <div class="min-h-screen bg-[#f8f9fa] p-6 ">
    <div class="mb-6 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="mb-1 text-3xl font-semibold text-[#172b4d]">{{ projectName }}</h1>
        <p class="m-0 text-sm text-[#5e6c84]">Glisse-dépose pour changer le statut d'une tâche</p>
      </div>
      <q-btn color="primary" outline label="Retour projets" @click="backToProjects" />
    </div>

    <q-banner v-if="error" class="bg-red-1 text-red-8 q-mb-md" dense>
      {{ error }}
    </q-banner>

    <form class="mb-5 grid gap-3 rounded-xl border border-[#dfe1e6] bg-white p-4" @submit.prevent="createNewTask">
      <div class="text-sm font-semibold text-[#172b4d]">Créer une tâche</div>
      <div class="grid gap-3 md:grid-cols-3">
        <input
          v-model="newTitle"
          type="text"
          placeholder="Titre"
          class="h-11 rounded-lg border border-[#d5d9df] px-3"
        />
        <input
          v-model="newDescription"
          type="text"
          placeholder="Description"
          class="h-11 rounded-lg border border-[#d5d9df] px-3"
        />
        <select v-model="newStatus" class="h-11 rounded-lg border border-[#d5d9df] px-3">
          <option value="todos">Todo</option>
          <option value="in-progress">In Progress</option>
          <option value="done">Done</option>
        </select>
      </div>
      <div class="flex justify-end">
        <q-btn :loading="creating" color="primary" type="submit" label="Ajouter" />
      </div>
    </form>

    <div v-if="loading" class="text-sm text-[#5e6c84]">Chargement des tâches...</div>

    <div v-else class="flex gap-5 overflow-x-auto pb-2 flex justify-center">
      <section
        v-for="column in columns"
        :key="column.key"
        :data-column-status="column.key"
        class="w-[350px] min-w-[350px] rounded-xl bg-[#ebecf0] p-3 transition-colors "
        :class="activeColumn === column.key ? 'bg-[#dfe1e6]' : ''"
      >
        <header class="mb-3 flex items-center justify-between px-1">
          <h2 class="text-sm font-semibold text-[#172b4d]">{{ column.label }}</h2>
          <span class="rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-[#5e6c84]">
            {{ orderedTasksByStatus[column.key].length }}
          </span>
        </header>

        <TransitionGroup
          tag="div"
          class="h-[420px] relative overflow-y-auto "
          move-class="transition-transform duration-180 ease-[cubic-bezier(0.2,0,0,1)]"
          enter-active-class="transition-all duration-160 ease-[cubic-bezier(0.2,0,0,1)]"
          leave-active-class="transition-all duration-160 ease-[cubic-bezier(0.2,0,0,1)] absolute left-0 right-0 pointer-events-none"
          enter-from-class="opacity-0 scale-96"
          leave-to-class="opacity-0 scale-96"
        >
          <div
            v-for="task in orderedTasksByStatus[column.key]"
            :key="task.id"
            :data-task-id="task.id"
            class="rounded-lg mb-3"
            :class="draggedTaskId === task.id ? 'opacity-0 ' : ''"
            @mousedown="(event) => onCardMouseDown(event, task.id)"
            @contextmenu="(event) => onTaskContextMenu(event, task.id)"
          >
            <div :class="draggedTaskId === task.id ? 'opacity-0 pointer-events-none' : ''">
              <Card
                :title="task.title"
                :company="task.company"
                :timeAgo="task.timeAgo"
                :color="task.color"
              />
            </div>
          </div>

        </TransitionGroup>
      </section>
    </div>

    <div
      v-if="contextMenuVisible"
      class="fixed z-[10000] min-w-[170px] rounded-lg border border-[#d8dde6] bg-white py-1 shadow-lg"
      :style="{ left: `${contextMenuX}px`, top: `${contextMenuY}px` }"
      @mousedown.stop
      @contextmenu.prevent
    >
      <button
        type="button"
        class="block w-full px-3 py-2 text-left text-sm text-[#1f2f46] hover:bg-[#edf2fb]"
        @click="onContextAction('edit')"
      >
        Modifier
      </button>
      <button
        type="button"
        class="block w-full px-3 py-2 text-left text-sm text-[#c62828] hover:bg-[#fff1f1]"
        @click="onContextAction('delete')"
      >
        Supprimer
      </button>
    </div>
  </div>
</template>
