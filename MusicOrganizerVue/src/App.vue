<style>

.navbar {
  overflow: hidden;
  background-color: #333;
  position: fixed; /* Set the navbar to fixed position */
  top: 0; /* Position the navbar at the top of the page */
  left: 0;
  width: 100%; /* Full width */
}
.routerView{
    margin-top: 5%;
}
.flexbox{
    display: flex;
   flex-direction: column;
    left: 0
}
#app {
  min-height: 100vh;
}
.routerView{
    margin-top: 8em;
    margin-left: 3em;
}
</style>

<template>
  <div id="app">
    <div  class="d-flex flex-nowrap">
      <div class="navbar d-flex flex-column flex-shrink-0 p-3 text-bg-dark" style="width: 280px">
        <ul class="nav nav-pills nav-flush flex-column mb-auto text-center">

          <li class="nav-item">
              <RouterLink to="/" class='nav-link active py-3 border-bottom rounded-0" aria-current="page" data-bs-toggle="tooltip" data-bs-placement="right" aria-label="Home" data-bs-original-title="Home"'>Go to Home</RouterLink>
          </li>
          <li class="nav-item">
            <RouterLink to="/frontview" class='nav-link active py-3 border-bottom rounded-0" aria-current="page" data-bs-toggle="tooltip" data-bs-placement="right" aria-label="Home" data-bs-original-title="Home"'>Go to Frontview</RouterLink>
          </li>

          <li class="nav-item">
            <RouterLink to="/systemview" class='nav-link active py-3 border-bottom rounded-0" aria-current="page" data-bs-toggle="tooltip" data-bs-placement="right" aria-label="Home" data-bs-original-title="Home"'>Go to Systemview</RouterLink>
          </li>

        </ul>
      </div>
<!--
<router-view />
-->
      <div class="routerView">
        <router-view></router-view>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>