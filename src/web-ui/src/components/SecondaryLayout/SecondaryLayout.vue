<template>
  <div>
    <div class="banner mb-5 py-2">
      <div class="container d-flex align-items-center">
        <img src="/cherrypicks_logo_TC_portrait.png" alt="logo" class="logo" />
        <!-- <PoweredByAWS class="powered-by-logo"></PoweredByAWS> -->
      </div>
    </div>

    <slot></slot>

    <footer class="mt-5 container">
      <TermsAndConditions></TermsAndConditions>
    </footer>
  </div>
</template>

<script>
// import PoweredByAWS from '@/components/PoweredByAWS/PoweredByAWS.vue';
import TermsAndConditions from '@/partials/TermsAndConditions/TermsAndConditions.vue';

export default {
  name: 'SecondaryLayout',
  components: { TermsAndConditions },
};
</script>

<style scoped>
.banner {
  background: var(--aws-deep-squid-ink);
}

.logo {
  width: 120px;
}

.powered-by-logo {
  /* fine-tune spacing to make logo appear more centered */
  margin-top: 15px;
  height: 45px;
  fill: var(--white);
}
</style>
