<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import Card from './ui/card.vue'
// A definir dans un fichier type.ts global
interface Task {
  id: number
  title: string
  company: string
  timeAgo: string
  color: string
  status: TaskStatus
  order: number
}
type TaskStatus = 'todos' | 'in-progress' | 'done'

interface Column {
  key: TaskStatus
  label: string
}


/* Place Holders */
const projectName = 'Job Board'

const columns: Column[] = [
  { key: 'todos', label: 'Enregistrée' },
  { key: 'in-progress', label: 'Postulée' },
  { key: 'done', label: 'Entretien' },
]

const tasks = ref<Task[]>([
  { id: 1, title: 'Data Scientist', company: 'Elax Energie', timeAgo: 'il y a 9 minutes', color: '#0066ff', status: 'todos', order: 1 },
  { id: 2, title: 'Senior Frontend Developer (React)', company: 'Papernest', timeAgo: 'il y a environ 16 heures', color: '#6a0dad', status: 'todos', order: 2 },
  { id: 3, title: 'Expert conseil DATA F/H', company: 'Orange', timeAgo: 'il y a 8 minutes', color: '#ff6600', status: 'in-progress', order: 1 },
  { id: 4, title: 'Product Designer, AI Studio', company: 'Mistral AI', timeAgo: 'il y a 43 minutes', color: '#ffcc00', status: 'done', order: 1 },
  { id: 5, title: 'Product Designer, AI Studio', company: 'Mistral AI', timeAgo: 'il y a 43 minutes', color: '#ffcc00', status: 'done', order: 1 },
  { id: 6, title: 'Product Designer, AI Studio', company: 'Mistral AI', timeAgo: 'il y a 43 minutes', color: '#ffcc00', status: 'done', order: 1 },
  { id: 7, title: 'Product Designer, AI Studio', company: 'Mistral AI', timeAgo: 'il y a 43 minutes', color: '#ffcc00', status: 'done', order: 1 },
])
/* Place Holders */


const activeColumn = ref<TaskStatus | null>(null)
const draggedTaskId = ref<number | null>(null)
const dragPreviewEl = ref<HTMLElement | null>(null)
const dragOffset = ref({ x: 0, y: 0 })
const lastPlacementKey = ref<string | null>(null)
const lastPointerX = ref<number | null>(null)
const filteredDeltaX = ref(0)
const currentRotation = ref(0)
const targetRotation = ref(0)

const orderedTasksByStatus = computed<Record<TaskStatus, Task[]>>(() => ({
  todos: tasks.value.filter((task) => task.status === 'todos').sort((a, b) => a.order - b.order),
  'in-progress': tasks.value.filter((task) => task.status === 'in-progress').sort((a, b) => a.order - b.order),
  done: tasks.value.filter((task) => task.status === 'done').sort((a, b) => a.order - b.order),
}))

const getTaskById = (id: number) => tasks.value.find((task) => task.id === id)

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
  stopCustomDrag()
}

const onCardMouseDown = (event: MouseEvent, taskId: number) => {
  if (event.button !== 0) return

  const taskElement = event.currentTarget as HTMLElement
  const rect = taskElement.getBoundingClientRect()

  draggedTaskId.value = taskId
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
})
</script>

<template>
  <div class="min-h-screen bg-[#f8f9fa] p-6 ">
    <h1 class="mb-6 text-3xl font-semibold text-[#172b4d]">{{ projectName }}</h1>

    <div class="flex gap-5 overflow-x-auto pb-2 flex justify-center">
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
  </div>
</template>
