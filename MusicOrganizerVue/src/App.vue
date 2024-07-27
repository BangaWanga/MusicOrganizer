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

</style>

<template>
  <div id="app">
    <div class="flexbox">
      <div class="navbar">
        <nav class="menu">
          <RouterLink to="/">Go to Home</RouterLink>
          <RouterLink to="/frontview">Go to Frontview</RouterLink>
        </nav>
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