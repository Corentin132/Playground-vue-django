import { createRouter, createWebHistory } from 'vue-router'

import Auth from '../Auth.vue'
import Project from '../Project.vue'

const routes = [
  { path: '/', component: Auth },
  { path: '/project', component: Project },
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})