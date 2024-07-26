/*
import Vue from 'vue';
import VueRouter from 'vue-router';
//Vue.use(VueRouter);
export default new VueRouter(
    {
        mode:'history',
        routes:[
            {path:'/', name: 'Frontview', component: Frontview,},
            {path:'/dummy',name:'HelloWorld',component: HelloWorld,},
        ],}
)
*/
import { createMemoryHistory, createRouter } from 'vue-router'
import Frontview from './../components/Frontview.vue'
import HelloWorld from './../components/HelloWorld.vue'
//import HomeView from './Front.vue'


const routes = [
  { path: '/', component: HelloWorld },
  { path: '/frontview', component: Frontview },
]

const router = createRouter({
  history: createMemoryHistory(),
  routes,
})