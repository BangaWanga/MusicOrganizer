<template>

  <table>
      <tr>
        <th
          v-for="(header, i) in headers"
          :key="`${header}${i}`"
          class="header-item"
        >
          {{ header }}
        </th>
      </tr>
      <tbody>
        <tr
          v-for="(trow, i) in project_paths"
          :key="`row-${i}`"
          class="table-rows"
        >
          <td
            v-for="(datapoint, i) in trow"
            :key="`Dataipoint-${i}`"
          >
                <RouterLink to="/project_view">{{ datapoint }}</RouterLink>


          </td>
        </tr>
      </tbody>
    </table>
</template>

<script setup>


  import {onMounted, ref, watch} from "vue";
  import axios from "axios";
  let project_paths = ref(null)
  let headers = ref(["Project Path"])
  let project_check = null
  let resp = null
  let resp_resolved = false



    let set_project_check = function(){
      project_check = setTimeout(()=>{

          if (resp_resolved){
              console.log("Message received in Component", project_paths, headers);
              project_paths.value = resp;
          }
          else{
            set_project_check()
          }

      }, 100)
  }
  onMounted(() => {
      get_projects().then((data)=> {
          resp_resolved = true;
          resp = data.projects;
      })
      //project_paths = resp.projects
      set_project_check()
  })
  let get_projects = function(){

      console.log("Trying to get somethign")
      const path = 'http://127.0.0.1:5000/get_project_paths'
      return axios.get(path,
                {
                    //department:this.dataentry.department,
                }).then(response => response.data).catch(err =>{console.log(err)
                })
        }



</script>

<style scoped>

</style>



