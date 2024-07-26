<template>
<div id="app">
    <h3>Enter your Data</h3>
    <form @submit="submit">

        <button pill v-on:Click="submit" id="button-1" type="submit" variant="dark">Submit</button>
    </form>
</div>
</template>

<script>



import './../assets/main.css'

//import { createApp } from 'vue'
//import App from './../App.vue'

//createApp(App).mount('#app')




import axios from 'axios'
export default{
    data()
    {
        return {
            dataentry:{name:"",department:"",},
        }
	},
    methods:{
        submit:function(){
            const path = 'http://localhost:5000/get_project';
            console.log("SUBMIT");
            // axios.defaults.headers.common['Authorization'] = 'AUTH TOKEN';
            // axios.defaults.headers.post['Content-Type'] = 'application/json';
            // axios.defaults.headers.post['crossDomain'] = true;
            // axios.defaults.headers.post['dataType'] = "json";
            // axios.defaults.headers.post['xhrFields'] = {"withCredentials": true};
            axios.get(path, {
                headers: {
                    type: "GET",
                    xhrFields: {
                        withCredentials: true
                    },
                    crossDomain: true,
                    contentType: 'application/json; charset=utf-8'
                }
                      }).then(response => {
                                      console.log(response)
                                  }).catch(err =>{console.log(err)
                                  })
        },
    }
}


/* for get-request:

$.ajaxSetup({
    type: "POST",
    data: {},
    dataType: 'json',
    xhrFields: {
       withCredentials: true
    },
    crossDomain: true,
    contentType: 'application/json; charset=utf-8'
});
 */
</script>



<style>
  @import url('https://fonts.googleapis.com/css2?family=Lato&display=swap');
  @import url('https://fonts.googleapis.com/css2?family=Castoro&display=swap');
  #app {font-family: 'Lato', sans-serif;-webkit-font-smoothing: antialiased;-moz-osx-font-smoothing: grayscale;color: #2c3e50;}
  #input-group-1 {margin-left:25%;margin-bottom: 20px;width: 50%;padding-left: 80px;margin-top: 50px;font-weight:bold;}
  h3{margin-left:40%;margin-top:20px;font-family: 'Castoro', serif;}
  #input-group-2{margin-left:25%;margin-bottom: 20px;width:50%;padding-left:80px;font-weight:bold;}
  #button-1{margin-left:50%;}.nav-bar{padding-left: 50px;;}.link{padding-right:100px;font-size: 20px;color:white;}
</style>