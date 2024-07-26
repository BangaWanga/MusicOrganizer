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
          v-for="(trow, i) in data"
          :key="`row-${i}`"
          class="table-rows"
        >
          <td
            v-for="(header, i) in headers"
            :key="`${header}-${i}`"
          >
            <slot :name="`column${i}`"> {{ trow[i] }} </slot>
          </td>
        </tr>
      </tbody>
    </table>
</template>

<script>
export default {
    name: "AbletonProjectTable",
    props: {
        headers: {
            type: Array,
            required: true,
        },
        data: {
            type: Array,
            required: true,
        }
    }
}
</script>

<style scoped>

</style>



