<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { createProject, deleteProject, fetchMe, listProjects, logout as logoutRequest, type Project } from './lib/api'

const router = useRouter()

const userName = ref('')
const projects = ref<Project[]>([])
const loading = ref(false)
const creating = ref(false)
const error = ref('')

const newProjectName = ref('')
const newProjectDescription = ref('')

const loadProjects = async () => {
  loading.value = true
  error.value = ''

  try {
    const [user, userProjects] = await Promise.all([fetchMe(), listProjects()])
    userName.value = user.username
    projects.value = userProjects
  } catch (caughtError: unknown) {
    error.value = caughtError instanceof Error ? caughtError.message : 'Erreur inconnue'
  } finally {
    loading.value = false
  }
}

const submitProject = async () => {
  if (!newProjectName.value.trim()) {
    error.value = 'Le nom du projet est requis.'
    return
  }

  creating.value = true
  error.value = ''

  try {
    const created = await createProject({
      name: newProjectName.value.trim(),
      description: newProjectDescription.value.trim(),
    })

    projects.value = [created, ...projects.value]
    newProjectName.value = ''
    newProjectDescription.value = ''
  } catch (caughtError: unknown) {
    error.value = caughtError instanceof Error ? caughtError.message : 'Erreur inconnue'
  } finally {
    creating.value = false
  }
}

const openProject = async (projectId: number) => {
  await router.push(`/projects/${projectId}`)
}

const removeProject = async (projectId: number) => {
  const accepted = window.confirm('Supprimer ce projet ? Toutes les tâches seront supprimées.')
  if (!accepted) {
    return
  }

  error.value = ''

  try {
    await deleteProject(projectId)
    projects.value = projects.value.filter((project) => project.id !== projectId)
  } catch (caughtError: unknown) {
    error.value = caughtError instanceof Error ? caughtError.message : 'Erreur inconnue'
  }
}

const logout = async () => {
  await logoutRequest()
  await router.push('/login')
}

onMounted(() => {
  void loadProjects()
})
</script>

<template>
  <div class="projects-screen q-pa-md">
    <div class="projects-shell">
      <q-card class="q-pa-lg projects-card">
        <div class="row items-center justify-between q-mb-md gap-2">
          <div>
            <div class="text-overline text-blue-grey-7">Tableau de bord</div>
            <div class="text-h6">Mes projets</div>
            <div class="text-caption text-blue-grey-8">Connecté en tant que {{ userName || '...' }}</div>
          </div>
          <q-btn flat color="primary" label="Déconnexion" @click="logout" />
        </div>

        <q-banner v-if="error" class="bg-red-1 text-red-8 q-mb-md" dense>
          {{ error }}
        </q-banner>

        <q-form class="q-gutter-sm q-mb-md" @submit.prevent="submitProject">
          <q-input
            v-model="newProjectName"
            type="text"
            label="Nom du projet"
            filled
            :rules="[(val) => !!val || 'Nom requis']"
          />
          <q-input v-model="newProjectDescription" type="text" label="Description" filled />
          <q-btn label="Créer un projet" type="submit" color="primary" :loading="creating" />
        </q-form>

        <div v-if="loading" class="text-blue-grey-8">Chargement des projets...</div>

        <div v-else-if="projects.length === 0" class="empty-state">
          Aucun projet pour le moment. Crée ton premier projet ci-dessus.
        </div>

        <div v-else class="projects-grid">
          <article v-for="project in projects" :key="project.id" class="project-item">
            <div>
              <h3 class="project-title">{{ project.name }}</h3>
              <p class="project-description">{{ project.description || 'Sans description' }}</p>
              <p class="project-role">
                {{ project.is_owner ? 'Propriétaire' : `Membre · Propriétaire: ${project.owner.username}` }}
              </p>
            </div>

            <div class="project-actions">
              <q-btn color="primary" label="Ouvrir" @click="openProject(project.id)" />
              <q-btn
                v-if="project.is_owner"
                flat
                color="negative"
                label="Supprimer"
                @click="removeProject(project.id)"
              />
            </div>
          </article>
        </div>
      </q-card>
    </div>
  </div>
</template>

<style scoped>
.projects-screen {
  min-height: 100vh;
  background: linear-gradient(120deg, #ecf2ff 0%, #f7fafc 42%, #fef7ed 100%);
}

.projects-shell {
  max-width: 960px;
  margin: 0 auto;
}

.projects-card {
  border: 1px solid #dde6f3;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.9rem;
}

.project-item {
  border: 1px solid #dde6f3;
  border-radius: 12px;
  padding: 0.85rem;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  justify-content: space-between;
}

.project-title {
  margin: 0;
  font-size: 1.02rem;
  color: #12233f;
}

.project-description {
  margin: 0.25rem 0 0;
  color: #465771;
}

.project-role {
  margin: 0.4rem 0 0;
  color: #6a798f;
  font-size: 0.85rem;
}

.project-actions {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
}

.empty-state {
  border: 1px dashed #b8c4da;
  border-radius: 10px;
  padding: 1rem;
  color: #42506b;
  background: #f8fbff;
}
</style>
