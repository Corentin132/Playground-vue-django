import { createRouter, createWebHistory } from 'vue-router'

import Auth from '../Auth.vue'
import Projects from '../Projects.vue'
import Project from '../Project.vue'
import { hydrateSession, isAuthenticated } from '../lib/api'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Auth, meta: { guestOnly: true } },
  { path: '/register', component: Auth, meta: { guestOnly: true } },
  { path: '/projects', component: Projects, meta: { requiresAuth: true } },
  { path: '/projects/:projectId', component: Project, meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', redirect: '/login' },
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach(async (to) => {
  const loggedIn = isAuthenticated() || Boolean(await hydrateSession())

  if (to.meta.requiresAuth && !loggedIn) {
    return '/login'
  }

  if (to.meta.guestOnly && loggedIn) {
    return '/projects'
  }

  return true
})