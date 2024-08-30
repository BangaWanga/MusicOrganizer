import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import 'bootstrap/dist/css/bootstrap.min.css'
import { createMemoryHistory, createRouter } from 'vue-router'
import Frontview from './components/Frontview.vue'
import Projectview from './components/Projectview.vue'
import AbletonProjectTable from './components/AbletonProjectTable.vue'
//import HomeView from './Front.vue'
import Systemview from "@/components/Systemview.vue";


const routes = [
  { path: '/', component: AbletonProjectTable },
  { path: '/frontview', component: Frontview, prope: true },
  { path: '/project_view', component: Projectview, props: true  },
  { path: '/systemview', component: Systemview, props: true  },
]

const router = createRouter({
  history: createMemoryHistory(),
  routes,
})
//import router from './router/routes.js'
const app = createApp(App);
app.use(router);
app.mount('#app');




import axios from 'axios'
export default{
    data()
    {
        return {
            dataentry:{name:"",department:"",},
        }
	},
    methods:{
        get_projects:function(){
            console.log("Trying to get something")
            const path = 'http://127.0.0.1:5000/get_project_paths'
            axios.get(path,
                      {
                          project_id: 0,
                          //department:this.dataentry.department,
                      }).then(response => {
                          console.log(response)
                      }).catch(err =>{console.log(err)
                      })
        },
    }
}