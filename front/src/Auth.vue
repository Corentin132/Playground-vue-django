<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { isAuthenticated, login, register } from './lib/api'

const route = useRoute()
const router = useRouter()

const username = ref('')
const emailOrUsername = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const isRegisterMode = computed(() => route.path === '/register')
const title = computed(() => (isRegisterMode.value ? 'Créer un compte' : 'Connexion'))

onMounted(() => {
  if (isAuthenticated()) {
    void router.replace('/projects')
  }
})

const submit = async () => {
  error.value = ''
  loading.value = true

  try {
    if (isRegisterMode.value) {
      await register({
        username: username.value.trim(),
        email: email.value.trim(),
        password: password.value,
      })
    } else {
      await login({
        identifier: emailOrUsername.value.trim(),
        password: password.value,
      })
    }

    await router.push('/projects')
  } catch (caughtError: unknown) {
    error.value = caughtError instanceof Error ? caughtError.message : 'Erreur inconnue'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-screen">
    <q-card class="auth-card q-pa-lg shadow-2 rounded-borders">
      <div class="text-h5 text-center q-mb-md">{{ title }}</div>

      <q-banner v-if="error" class="bg-red-1 text-red-8 q-mb-md" dense>
        {{ error }}
      </q-banner>

      <q-form @submit.prevent="submit" class="q-gutter-md">
        <q-input
          v-if="isRegisterMode"
          v-model="username"
          type="text"
          label="Nom d'utilisateur"
          filled
          lazy-rules
          :rules="[(val) => !!val || 'Nom utilisateur requis']"
        />

        <q-input
          v-if="isRegisterMode"
          v-model="email"
          type="email"
          label="Email"
          filled
          lazy-rules
          :rules="[(val) => !!val || 'Email requis']"
        />

        <q-input
          v-if="!isRegisterMode"
          v-model="emailOrUsername"
          type="text"
          label="Username"
          filled
          lazy-rules
          :rules="[(val) => !!val || 'Identifiant requis']"
        />

        <q-input
          v-model="password"
          type="password"
          label="Mot de passe"
          filled
          lazy-rules
          :rules="[(val) => !!val || 'Mot de passe requis']"
        />

        <q-btn
          :label="isRegisterMode ? 'Créer mon compte' : 'Se connecter'"
          type="submit"
          color="primary"
          class="full-width"
          :loading="loading"
        />
      </q-form>

      <div class="text-center q-mt-md text-grey-7">
        <span v-if="isRegisterMode">
          Déjà un compte ?
          <RouterLink class="text-primary" to="/login">Se connecter</RouterLink>
        </span>
        <span v-else>
          Pas de compte ?
          <RouterLink class="text-primary" to="/register">S'inscrire</RouterLink>
        </span>
      </div>
    </q-card>
  </div>
</template>

<style scoped>
.auth-screen {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 1rem;
  background: radial-gradient(circle at top left, #d9e4ff 0%, #f4f6fb 42%, #f7fafc 100%);
}

.auth-card {
  width: 420px;
  max-width: 92vw;
  border: 1px solid #e2e8f0;
}
</style>