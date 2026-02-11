import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import AdminLayout from '@/layouts/AdminLayout.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
  },
  {
    path: '/',
    component: AdminLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘', icon: 'Odometer' },
      },
      {
        path: 'accounts',
        name: 'Accounts',
        component: () => import('@/views/Accounts.vue'),
        meta: { title: '账号管理', icon: 'User' },
      },
      {
        path: 'keys',
        name: 'Keys',
        component: () => import('@/views/Keys.vue'),
        meta: { title: '密钥管理', icon: 'Key' },
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/Logs.vue'),
        meta: { title: '任务日志', icon: 'Document' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '系统设置', icon: 'Setting' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫 — 检查 adminKey
router.beforeEach((to, _from, next) => {
  const adminKey = localStorage.getItem('adminKey')
  if (to.name !== 'Login' && !adminKey) {
    next({ name: 'Login' })
  } else {
    next()
  }
})

export default router
