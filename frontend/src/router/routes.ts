import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('../modules/front-facing/hero/HeroPage.vue'),
  },
  {
    path: '/login',
    component: () => import('../modules/auth/pages/LoginPage.vue'),
  },
  {
    path: '/seleccionar',
    component: () => import('../modules/auth/pages/SelectOrgPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/dashboard',
    component: () => import('layouts/DashboardLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', component: () => import('../modules/home/HomePage.vue') },
      { path: 'periodo', component: () => import('../modules/periodo/PeriodoPage.vue') },
      { path: 'inscripciones', component: () => import('../modules/inscripcion/InscripcionPage.vue') },
      { path: 'mis-inscripciones', component: () => import('../modules/inscripcion/MisInscripcionesPage.vue') },
      { path: 'evaluacion', component: () => import('../modules/evaluacion/CargaNotasPage.vue') },
      { path: 'boletines/:inscripcionId', component: () => import('../modules/evaluacion/BoletinPage.vue') },
      { path: 'asistencia', component: () => import('../modules/asistencia/ListaPage.vue') },
      { path: 'mis-faltas', component: () => import('../modules/asistencia/MisFaltasPage.vue') },
    ],
  },
  {
    path: '/plataforma',
    component: () => import('layouts/DashboardLayout.vue'),
    meta: { requiresAuth: true, plataforma: true },
    children: [
      { path: '', component: () => import('../modules/home/HomePage.vue') },
    ],
  },
  {
    path: '/:catchAll(.*)*',
    component: () => import('../modules/error/NotFoundPage.vue'),
  },
];

export default routes;
