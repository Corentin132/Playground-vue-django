<script setup>
import { ref } from 'vue'

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  error.value = ''
  loading.value = true

  try {
    // 👉 Simule une requête API
    await new Promise((resolve) => setTimeout(resolve, 1000))

    if (email.value !== 'test@test.com') {
      throw new Error('Identifiants invalides')
    }

    console.log('Login success', {
      email: email.value,
      password: password.value
    })

  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex flex-center bg-grey-2" style="min-height: 100vh;">
    <q-card class="q-pa-lg shadow-2 rounded-borders" style="width: 400px; max-width: 90vw;">
      
      <!-- Title -->
      <div class="text-h5 text-center q-mb-md">
        Connexion
      </div>

      <!-- Error -->
      <q-banner
        v-if="error"
        class="bg-red-1 text-red-8 q-mb-md"
        dense
      >
        {{ error }}
      </q-banner>

      <!-- Form -->
      <q-form @submit.prevent="handleLogin" class="q-gutter-md">

        <q-input
          v-model="email"
          type="email"
          label="Email"
          filled
          lazy-rules
          :rules="[val => !!val || 'Email requis']"
        />

        <q-input
          v-model="password"
          type="password"
          label="Mot de passe"
          filled
          lazy-rules
          :rules="[val => !!val || 'Mot de passe requis']"
        />

        <q-btn
          label="Se connecter"
          type="submit"
          color="primary"
          class="full-width"
          :loading="loading"
        />

      </q-form>

      <!-- Footer -->
      <div class="text-center q-mt-md text-grey-7">
        Pas de compte ?
        <q-btn flat dense color="primary" label="S’inscrire" />
      </div>

    </q-card>
  </div>
</template>