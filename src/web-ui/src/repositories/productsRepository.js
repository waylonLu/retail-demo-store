// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { get } from 'aws-amplify/api';

const resource = "/products";
const apiName = 'productsService';

export default {
    async get() {
        const restOperation = get({
            apiName: apiName,
            path: `${resource}/all`
        });
        const { body } = await restOperation.response;
        return body.json();
    },
    async getFeatured() {
        const restOperation = get({
            apiName: apiName,
            path: `${resource}/featured`
        });
        const { body } = await restOperation.response;
        return body.json();
    },
    async getProduct(productID, personalized, userId, behaviorType) {
        if (!productID || productID.length == 0)
            throw "productID required"
        if (Array.isArray(productID))
            productID = productID.join()

        const params = {};
        if (personalized) {
            params['personalized'] = true;            
        } 
        if (userId) {
            params['userId'] = userId;
        }
        if (behaviorType) {
            params['behaviorType'] = behaviorType;
        }
        const restOperation = get({
            apiName: apiName,
            path: `${resource}/id/${productID}`,
            options: {
                queryParams: params
              }
        });
        const { body } = await restOperation.response;
        return body.json();
    },
    async getProductsByCategory(categoryName) {
        if (!categoryName || categoryName.length == 0)
            throw "categoryName required"
        const restOperation = get({
            apiName: apiName,
            path: `${resource}/category/${categoryName}`
        });
        const { body } = await restOperation.response;
        return body.json();
    },
    async getCategories() {
        const restOperation = get({
            apiName: apiName,
            path: "/categories/all"
        });
        const { body } = await restOperation.response;
        return body.json();
    },
    async addToCartPersonalizedEvent(productId, userId, behaviorType) {
        if (!productId) throw "productID required";
        const params = {};
        if (userId) params['userId'] = userId;
        if (behaviorType) params['behaviorType'] = behaviorType;
        const restOperation = get({
            apiName: apiName,
            path: `/products/id/${productId}/add_to_cart_event`,
            options: {
                queryParams: params
            }
        });
        const { body } = await restOperation.response;
        return body.json();
    }
}