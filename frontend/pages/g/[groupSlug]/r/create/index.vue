<template>
  <div />
</template>

<script lang="ts">
export default defineNuxtComponent({
  setup() {
    const route = useRoute();
    const router = useRouter();
    onMounted(() => {
      router.replace({
        path: `/g/${route.params.groupSlug}/r/create/url`,
        query: route.query,
      });
    });
    return {};
  },
});
</script>
