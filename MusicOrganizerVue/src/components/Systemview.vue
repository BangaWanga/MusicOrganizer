


<style>

.GroupTrack {
    background-color: chocolate;
    margin: 1px;

}

.ExpandedGroupTrack {
    background-color: #ffaa69;
}

.MidiTrack {
    background-color: #4e4e43;
}

.AudioTrack {
    background-color: firebrick;
}

.Track:hover {
    opacity: 0.5;
//: 5px 5px lightblue inset; margin: 50px;
}
.inactiveComponent{
    opacity: .05;
}
.inactiveComponent:hover{
    opacity: .1;
}
.activeComponent{
}
.activeComponent{
    //margin: 6em;
    opacity: .8;
    scale: 1;
    transition:  2s ease-in-out;
}
.selectedComponent:hover{
    background-color: #b8b8b8;
    transition: background-color .2s ease-in-out;
}
.selectedComponent{
    //margin: 6em;
    opacity: 1;
    scale: 3;
    background-color: #554949;
    transition:  2s ease-in-out;
}
.selectedComponentName{
    //margin: 6em;
    transition:  2s ease-in-out;
}
.selectedComponent{
    transition:  2s ease-in-out;
}
.name-insert{
    scale: .5;
    min-width: 100px;
    transition:  2s ease-in-out;
}

</style>

<template>

    <table>
        <tbody>
            <tr v-for="(_, idx_y) in 3" :key="idx_y" v-on:click="" class="justify-content-between d-flex flex-row bd-highlight mb-3">
                <td v-for="(_, idx_x) in 3" :key="idx_x" class="justify-content-between d-flex flex-column bd-highlight mb-3 ">
                    <button
                        @click="component_click(idx_x, idx_y)"
                        class="btn btn-secondary rounded-circle p-3 lh-1"
                        v-bind:class="{
                        'mb-3':true,
                        'activeComponent': states[(idx_y * 3) + idx_x].active,
                        'inactiveComponent': !states[(idx_y * 3) + idx_x].active,
                        'shadow-lg selectedComponent': selected_idx === (idx_y * 3) + idx_x
                    }"
                            type="button">
                        <svg class="bi" width="24" height="24"><use xlink:href="#x-lg"></use></svg>
                        <span class="visually-hidden">Dismiss</span>
                        <input type="text" placeholder="Neue Komponente..." class="w-75 name-insert selectedComponentName" >
                    </button>
                    <!--
                    <div  class="flex-container">
                    </div>
                    <div class="grid-item"  style="float: right">Say What</div>
                    -->

                </td>
            </tr>
        </tbody>
    </table>
</template>

<script setup>


import {onMounted, ref} from "vue";
import axios from "axios";

let create_init_states = function(){
    let _states = []
    for (let y=0; y<3; y++){
        for (let x=0; x<3; x++) {
            _states.push({
                active: false,
                id: String(x)+String(y)
            })
        }
    }
    return _states
}
let states = ref(create_init_states())
let selected_idx = ref(null)
let project_check = null
let resp = null
let resp_resolved = false
let expanded_groups = []
const project_id = 0 // defineProps(['project_id'])

onMounted(() => {
    resp = get_projects().then((data) => {
        resp_resolved = true;
        resp = data;
    })
    //project_paths = resp.projects
    //set_project_check()
    init_canvas();

})
let component_click = function (idx_x, idx_y){
    const component_idx = (idx_y * 3) + idx_x
    states.value[component_idx].active = true;
    if (selected_idx.value === component_idx){
        // selected_idx.value = null;
    }else{
        selected_idx.value = component_idx;
    }
}

let init_canvas = function(nrows=3, ncols=3){
    let canvas = document.getElementById("system_canvas");
    let context = canvas.getContext("2d");
    const bw = nrows * 200; //Calculating Border Width
    const bh = ncols * 40; // Calculating Border Height
    const p = 10; //margin
    console.log("Init canvas ", bw, bh, p);

    context.clearRect(0, 0, canvas.width, canvas.height);
    for (let x = 0; x <= bw; x += 200) {
        context.moveTo(0.5 + x + p, p);
        context.lineTo(0.5 + x + p, bh + p);
    }

    for (let x = 0; x <= bh; x += 40) {
        context.moveTo(p, 0.5 + x + p);
        context.lineTo(bw + p, 0.5 + x + p);
    }
    context.strokeStyle = "black";
    context.stroke();
}


let get_projects = function () {

    console.log("Trying to get somethign")
    const path = 'http://127.0.0.1:5000/get_project'
    return axios.post(path,
                      {
                          project_id: project_id
                          //department:this.dataentry.department,
                      }).then(response => response.data).catch(err => {
        console.log(err)
    })
}


</script>

<style scoped>

</style>



