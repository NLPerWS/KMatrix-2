import Vue from 'vue'
import VueRouter from 'vue-router'

Vue.use(VueRouter)

const router = new VueRouter({
	mode: "history",
	base: import.meta.env.BASE_URL,
	routes: [
		{
			path: "/",
			name: "knowledgedb",
			component: () => import("../views/knowledgedb.vue"),
		},

		{
			path: "/knowledgedb",
			name: "knowledgedb",
			component: () => import("../views/knowledgedb.vue"),
		},
		{
			path: "/chat",
			name: "chat",
			component: () => import("../views/chat.vue"),
		},
		{
			path: "/task",
			name: "task",
			component: () => import("../views/task.vue"),
		},
	],
});

export default router
