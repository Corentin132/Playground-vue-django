import { createApp } from 'vue'
import './style.css'
import 'virtual:uno.css'
import App from './App.vue'
import { Quasar, QPage, QCard, QBanner, QForm, QInput, QBtn } from 'quasar'
import 'quasar/src/css/index.sass'
import '@quasar/extras/material-icons/material-icons.css'
import { router } from './router'
const app = createApp(App)

app.use(router)
app.use(Quasar, {
	plugins: {},
	components: {
		QPage,
		QCard,
		QBanner,
		QForm,
		QInput,
		QBtn,
	},
})
.mount('#app')
