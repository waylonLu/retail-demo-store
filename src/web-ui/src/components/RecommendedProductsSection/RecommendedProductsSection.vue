<template>
  <section class="mb-5">
    <div class="mb-3 text-left">
      <h2 class="recommendations-heading"><slot name="heading"></slot></h2>
      <div v-if="experiment" class="recommendation-explanation text-muted small">
        <i class="fa fa-balance-scale px-1"></i>
        {{ experiment }}
      </div>
    </div>

    <div class="row">
      <LoadingFallback v-if="isLoading" class="col my-4 text-center"></LoadingFallback>

      <ProductCarousel
        v-else
        :recommendedProducts="recommendedProducts"
        :feature="feature"
        :eventAttributionSource="eventAttributionSource"
        class="col"
      ></ProductCarousel>
    </div>
  </section>
</template>

<script>
import LoadingFallback from '@/components/LoadingFallback/LoadingFallback.vue';
import ProductCarousel from './ProductCarousel/ProductCarousel.vue';

export default {
  name: 'RecommendedProductsSection',
  props: {
    experiment: {
      type: String,
      required: false,
    },
    recommendedProducts: {
      type: Array,
      required: false,
    },
    feature: {
      type: String,
      required: false,
    },
    eventAttributionSource: {
        type: String,
        required: false,
      },
  },
  components: {
    LoadingFallback,
    ProductCarousel,
  },
  computed: {
    isLoading() {
      console.log(this.eventAttributionSource)

      return !this.recommendedProducts;
    },
  },
};
</script>

<style scoped>
.recommendations-heading {
  font-size: 1rem;
}

.recommendation-explanation {
  font-style: italic;
}

@media (min-width: 768px) {
  .recommendations-heading {
    font-size: 1.4rem;
  }
}
</style>
