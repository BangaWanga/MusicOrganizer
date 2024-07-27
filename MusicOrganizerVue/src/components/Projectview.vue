<style>
    .GroupTrack{
        background-color: chocolate;
        margin: 1px;

    }
    .ExpandedGroupTrack{
        background-color: #ffaa69;
    }
    .MidiTrack{
        background-color: #4e4e43;
    }
    .AudioTrack{
        background-color: firebrick;
    }
    .Track:hover{
      opacity: 0.5; //: 5px 5px lightblue inset;
      margin: 50px;
    }



</style>

<template>

  <table>
      <tr>
        <th
          v-for="(header, i) in headers"
          :key="`${header}${i}`"
          class="header-item"
        > {{ header }}
        </th>
      </tr>
      <tbody>
        <tr
          v-for="(trow, i) in data"
          v-show="trow['is_toggled']"
          :key="`row-${i}`"
          v-bind:class="{GroupTrack: trow['type']==='GroupTrack', Track: true,              AudioTrack: trow['type']==='AudioTrack',
              MidiTrack: trow['type']==='MidiTrack',              ExpandedGroupTrack: is_expanded(trow['track_id']),}"
          v-on:click="expand(trow['track_id'])"
        >
          <td
            v-for="(header, i) in headers"
            :key="`Dataipoint-${i}`">

               <div v-if="header==='name'"  class="flex-container" v-bind:style="{'display': 'flex', 'flex-direction': 'row',   'align-content': 'stretch'}">
                    <div class="flex-item depth-placeholder" v-for="i in trow['depth']" v-bind:style="{background: 'aliceblue', 'min-width': '10px', 'min-height': '5px'}"></div>
                    <div class="flex-item-data" style="margin-left: 10px">  {{trow['name']}}</div>
               </div>
              <div class="grid-item" v-else style="float: right">{{ trow[header] }}</div>


          </td>
        </tr>
      </tbody>
    </table>
</template>

<script setup>


  import {onMounted, ref } from "vue";
  import axios from "axios";
  let headers = ref([])
  let data = ref([])
  let project_check = null
  let resp = null
  let resp_resolved = false
  let expanded_groups = []
  const project_id = 0 // defineProps(['project_id'])

  let get_template_areas = function(depth){
      let areas = ""
      for (let i=0; i<depth; i++){
          areas += "placeholder "
      }
      areas += "trackname"
      return areas
  }
  let is_expanded = function (track_id){
      return expanded_groups.includes(track_id)
  }
  let expand = function (track_id){
      console.log("EXPAND ", track_id)
      let is_expanded = false;
      data.value.forEach((x)=>
                            {
          if (x["group_id"] === track_id) {
              x["is_toggled"] = !x["is_toggled"];
              if (x["is_toggled"]) {
                  is_expanded = true;
              }
          }
          if (is_expanded){
                expanded_groups.push(track_id)
          }else {
                  if (expanded_groups.includes(track_id)){
                      const index = expanded_groups.indexOf(track_id);
                      if (index !== -1) {
                        expanded_groups.splice(index, 1);
                      }
                  }
              }

      })
  }
    let set_project_check = function(){
      project_check = setTimeout(()=>{
          if (resp_resolved){
            headers.value = resp.headers;
            data.value = resp.data;
            console.log("Received Data: ", headers.value, data.value)

          }else{
            set_project_check()

          }

      }, 200)
  }
  onMounted(() => {
      resp = get_projects().then((data)=> {
          resp_resolved = true;
          resp = data;
      })
      //project_paths = resp.projects
      set_project_check()
  })
  let get_projects = function(){

      console.log("Trying to get somethign")
      const path = 'http://127.0.0.1:5000/get_project'
      return axios.post(path,
                {
                    project_id: project_id
                    //department:this.dataentry.department,
                }).then(response => response.data).catch(err =>{console.log(err)
                })
        }



</script>

<style scoped>

</style>



