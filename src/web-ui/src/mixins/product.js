// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { mapState } from 'vuex';

import { RepositoryFactory } from '@/repositories/RepositoryFactory';
import { AnalyticsHandler } from '@/analytics/AnalyticsHandler';
import { capitalize } from '@/util/capitalize';
import { getProductImageUrl } from '../util/getProductImageUrl';

const ProductsRepository = RepositoryFactory.get('products');

export const product = {
  data() {
    return {
      product: null,
    };
  },
  computed: {
    ...mapState(['user']),
    productImageUrl() {
      if (!this.product) return null;

      return getProductImageUrl(this.product);
    },
    readableProductCategory() {
      if (!this.product) return null;

      return capitalize(this.product.category);
    },
    outOfStock() {
      if (!this.product) return false;

      return this.product.current_stock === 0;
    },
  },
  methods: {
    async getProductByID(product_id, personalized, userId, behaviorType) {
      this.product = await ProductsRepository.getProduct(product_id, personalized, userId, behaviorType);
    },
    async getPersonalizedProduct(product_id) {
      this.product.description = (await ProductsRepository.getProduct(product_id, true)).description;
    },
    async addPersonalizeEvent(product_id, userId, behaviorType) {
      await ProductsRepository.addToCartPersonalizedEvent(product_id, userId, behaviorType);
    },
    recordProductViewed(feature, exp, discount) {
      AnalyticsHandler.productViewed(this.user, this.product, feature, exp, discount);
    },
  },
};
