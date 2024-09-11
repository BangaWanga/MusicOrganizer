<style>
    .GroupTrack {
        //background-color: chocolate;
        //margin: 1px;

    }
    .ExpandedGroupTrack {
        //background-color: #ffaa69;
    }
    .MidiTrack {
        //background-color: #4e4e43;
    }
    .AudioTrack {
        //background-color: firebrick;
    }
    .Leaf{
        background-color: #b8b8b8 !important;
    }
    .Expanded{
        background-color: #a29628 !important;
    }
    .Expandable:hover{
      opacity: 0.5;
        //: 5px 5px lightblue inset;
        background-color: #7fbd75 !important;
    }


    .bd-example{
        width: 80%;
        height: 50%;
        //position: relative;
        overflow: auto;
        padding: 3rem;
        margin: 1rem -.75rem 0;
        border: solid #dee2e6;
        border-width: 1px 0 0;

    }

    .bd-highlight{
            background-color: rgba(86, 61, 124, 0.15);
            border: 1px solid rgba(86, 61, 124, 0.15);
    }

</style>

<template>
    <div class="d-flex">
        <div class="bd-example flex-row">
            <input type="text" placeholder="Suchbegriff" v-model="search_word">
            <div class="d-flex justify-content-start bd-highlight mb-3" v-for="(path, idx) in project_paths">
                <button class="btn btn-dark" @click="picked_project=idx">{{ path }}</button>
            </div>
            <div>
                <span v-if="search_word !== ''">Suchwort {{ search_word }}</span>
            </div>
            <button class="btn btn-dark" @click="update_projects()">Update </button>

        </div>

        <div class="" style="overflow: auto; flex-direction: row; height: 80%">
            <div v-for="(row, row_idx) in rows">
                <div class="p-2" v-if="is_visible(row_idx)">
                    <button @click="toggle_expand(row_idx);"
                            :class="{'btn-light': isLeaf(row_idx), 'Expanded btn-info': is_expanded(row_idx),
                        'Expandable': !isLeaf(row_idx) && !is_expanded(row_idx)}" :disabled="isLeaf(row_idx)"
                    >{{ row_idx }} {{ row }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>



<script setup>

  // ToDo (Bug): Make row invisible if parent is folded as well
  import {onBeforeUpdate, onMounted, onUpdated, ref} from "vue";
  import axios from "axios";
  //import 'bootstrap/dist/css/bootstrap.min.css'

  let rows = ref([])
  let project_paths = ref([])
  let picked_project = 0;
  let project_check = null
  let resp = null
  let project_search_response = null
  let project_names_response = null
  let expanded_rows = ref([])
  let visible_rows = ref([0])
  let search_word = "";
  const project_id = 0 // defineProps(['project_id'])
  let break_points = new Map()

  let is_expanded = function (row_idx) {
      return expanded_rows.value.includes(row_idx)
  }
  let is_visible = function (row_idx) {
      return visible_rows.value.includes(row_idx)
  }
  let isLeaf = function (row_idx){
      return rows.value[row_idx].depth >= rows.value[row_idx + 1].depth
  }

  const get_breakpoint = function (id){
      return break_points.get(id) ?? null;
  }
  let toggle_expand = function (row_idx) {
      if (isLeaf(row_idx)){
          return;
      }
      if (is_expanded(row_idx)) { //collapse
          expanded_rows.value.splice(expanded_rows.value.indexOf(row_idx), 1)

          let remove_idx = [];
          for (let i = visible_rows.value.indexOf(row_idx + 1); i < visible_rows.value.length; i++) {
              let check_row_idx = visible_rows.value[i];
              if (rows.value[check_row_idx].depth > rows.value[row_idx].depth) {
                  //console.log("Is bigger ", check_row_idx, i);
                  if (is_expanded(check_row_idx)){
                      console.log("Is Expanded: ", check_row_idx);
                      toggle_expand(check_row_idx);
                  }
                  if (visible_rows.value.includes(check_row_idx)){
                      console.log("Will be removed ", check_row_idx);
                      remove_idx.push(i)
                  }
              } else {
                  console.log(Array.from(expanded_rows.value), Array.from(visible_rows.value))

              }
          }
          console.log("remove_idx: ", remove_idx);
          for (let i=1; i <=remove_idx.length; i++){
              //console.log("Before removing ", remove_idx[remove_idx.length-i], Array.from(visible_rows.value));
              visible_rows.value.splice(remove_idx[remove_idx.length-i], 1);
              //console.log("After removing ", remove_idx[remove_idx.length-i], Array.from(visible_rows.value));

          }
          console.log(Array.from(expanded_rows.value), Array.from(visible_rows.value))

      } else {
          console.log("Expand ", row_idx)
          expanded_rows.value.push(row_idx);
          let expansion_steps = 0;

          const break_point = get_breakpoint(get_depth(row_idx));
          if (break_point){
            console.log("break_point: ", break_point);
          }
          for (let i = row_idx + 1; i < rows.value.length - row_idx; i++) {
              // console.log("i ", i);
              if (get_depth(i) === get_depth(row_idx + 1)) {
                  visible_rows.value.push(i);
              } else if (get_depth(i) <= get_depth(row_idx)) {
                  //console.log(Array.from(expanded_rows.value), Array.from(visible_rows.value))
                  if (expansion_steps > 100) {
                      //const info_arr = [row_idx, expansion_steps];
                      if (get_breakpoint(get_depth(row_idx)) === null) {
                          break_points.set(get_depth(row_idx), [row_idx]);
                      } else {
                          get_breakpoint(get_depth(row_idx)).push(row_idx);
                      }
                  }
                  console.log("Returning at ", i, " for ", row_idx)
                  return;
              }else{
                  //console.log("Depths ", i, get_depth(i), row_idx, get_depth(row_idx))
              }
              expansion_steps ++;

          }
      }
  }
  let get_template_areas = function(depth){
      let areas = ""
      for (let i=0; i<depth; i++){
          areas += "placeholder "
      }
      areas += "trackname";
      return areas
  }

  let get_depth = function (row_idx){
    return rows.value[row_idx].depth
  }


  let update_projects = function () {
      get_project_search(picked_project).then((data) => {
          //project_search_response = data;
          //rows = ref([]);
          rows.value = data.rows;
          console.log("Data: ", data)
      })
      //set_project_check(project_search_response, (resp)=>{alert("Got Rows"); rows.value = resp.rows;});

  }

  onMounted(() => {
      get_project_names().then((data) => {
          project_paths.value = data.projects
      })

      //set_project_check(project_names_response, (resp)=>{alert("YEAH"); project_paths.value = resp.projects;});
  })

    let get_project_search = function(project_id) {
        const path = 'http://127.0.0.1:5000/get_project_search?project_id='+project_id.toString()+'&search_word='+search_word;
              return axios.get(path).then(response => response.data).catch(err =>{console.log(err)
                })
    }
  let get_project_names = function(){

      console.log("Trying to get somethign")
      const path = 'http://127.0.0.1:5000/get_project_paths'
      return axios.get(path).then(response => response.data).catch(err =>{console.log(err)
                })
        }



</script>

<style scoped>

</style>



