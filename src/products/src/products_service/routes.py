# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from decimal import Decimal
from flask import jsonify, request, Response, current_app, Blueprint
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, UnsupportedMediaType, NotFound, Unauthorized
from botocore.exceptions import BotoCoreError
from http import HTTPStatus
from datetime import datetime
import json
import boto3
import os
import uuid
import time

import products_service.products as product_service
from products_service import auth

personalize_event = boto3.Session(aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                           aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'), 
                           region_name=os.environ.get('AWS_DEFAULT_REGION')).client('personalize-events')

cognito_idp = boto3.client('cognito-idp')

api = Blueprint('api', __name__)
CORS(api)

@api.route('/')
def welcome():
    return jsonify("Welcome to the Products Web Service"), 200

@api.route('/init', methods=['POST'])
def init():
    products_loaded, categories_loaded = product_service.init()
    return {
        "products": products_loaded,
        "categories": categories_loaded
    }

@api.route('/products/all', methods=['GET'])
def get_all_products():
    products = product_service.get_all_products(should_fully_qualify_image_urls())
    
    return Response(json.dumps(products, default=custom_serializer), mimetype='application/json'), 200

@api.route('/products/id/<product_ids>', methods=['GET'])
def get_products_by_id(product_ids):
    product_ids = product_ids.split(",")
    if len(product_ids) > product_service.MAX_BATCH_GET_ITEM:
        return jsonify({"error": f"Maximum number of product IDs per request is {product_service.MAX_BATCH_GET_ITEM}"}), HTTPStatus.UNPROCESSABLE_ENTITY
    if len(product_ids) > 1:
        products = product_service.get_products_by_ids(product_ids, should_fully_qualify_image_urls())
        return jsonify(products), 200

    user = None
    user_id = request.args.get('userId')
    event_type = request.args.get('behaviorType')
    recommendation_id = request.args.get('recommendationId')
    event_attribution_source = request.args.get('eventAttributionSource')
    # If the personalization parameter is passed in then Bedrock is called for personalised product descriptions       
    if request.args.get('personalized') == 'true':
        cognito_authentication_provider = request.headers.get('cognitoAuthenticationProvider')
        user = auth.auth_user(cognito_authentication_provider)
    
    product = product_service.get_product_by_id(product_ids[0], should_fully_qualify_image_urls(), user)
    if product and event_type:
        event_param = {
            'eventType': event_type,
            'itemId': product.get('id'),
            'sentAt': int(time.time()),
            'properties': json.dumps({
                'DISCOUNT': 'No'
            })
        }
        if recommendation_id:
            event_param['recommendationId'] = recommendation_id
            
        if event_attribution_source:
            event_param['metricAttribution'] = {
                'eventAttributionSource': event_attribution_source
            }
            
        temp_id = str(uuid.uuid4())
        personalize_event.put_events(
            trackingId=os.environ.get('AWS_PERSONALIZE_TRACKING_ID'),
            userId=user_id if user_id else temp_id,
            sessionId=str(uuid.uuid5(uuid.NAMESPACE_DNS, str(user_id))) if user_id else temp_id,
            eventList=[
                event_param
            ]
        )
    if not product:
        raise NotFound

    return jsonify(product), 200

@api.route('/products/id/<product_id>', methods=['PUT'])
def update_products_by_id(product_id):
    product = request.get_json(force=True)
    existing_product = product_service.get_product_by_id(product_id)
    
    if not existing_product:
        raise NotFound
    
    product_service.update_product(existing_product, product)
    
    return jsonify(product), 200

@api.route('/products/id/<product_id>/add_to_cart_event', methods=['GET'])
def add_to_cart_event_products_by_id(product_id):
    user_id = request.args.get('userId')
    event_type = request.args.get('behaviorType')
    recommendation_id = request.args.get('recommendationId')
    event_attribution_source = request.args.get('eventAttributionSource')
    
    product = product_service.get_product_by_id(product_id, should_fully_qualify_image_urls(), None)
    if product and event_type:
        event_param = {
            'eventType': event_type,
            'itemId': product.get('id'),
            'sentAt': int(time.time()),
            'properties': json.dumps({
                'DISCOUNT': 'No'
            })
        }
        if recommendation_id:
            event_param['recommendationId'] = recommendation_id
            
        if event_attribution_source:
            event_param['metricAttribution'] = {
                'eventAttributionSource': event_attribution_source
            }
            
        temp_id = str(uuid.uuid4())
        personalize_event.put_events(
            trackingId=os.environ.get('AWS_PERSONALIZE_TRACKING_ID'),
            userId=user_id if user_id else temp_id,
            sessionId=str(uuid.uuid5(uuid.NAMESPACE_DNS, str(user_id))) if user_id else temp_id,
            eventList=[
                event_param
            ]
        )

    return jsonify("Success"), 200

@api.route('/products/id/<product_ids>', methods=['DELETE'])
def delete_products_by_id(product_ids):
    
    if product := product_service.get_product_by_id(product_ids):
        product_service.delete_product(product)
    else:
        raise NotFound

    return {"Success"}
        
@api.route('/products/featured', methods=['GET'])
def get_featured_products():
    products = product_service.get_featured_products(should_fully_qualify_image_urls())
    
    return jsonify(products), 200

@api.route('/products/category/<category_name>', methods=['GET'])
def get_products_by_category(category_name):
    products = product_service.get_products_by_category(category_name, should_fully_qualify_image_urls())
    return jsonify(products), 200

@api.route('/products', methods=['POST'])
def create_product():
    product = request.get_json()
    
    product_service.add_product(product)

    return jsonify(product), 201

@api.route('/products/id/<product_id>/inventory', methods=['PUT'])
def update_product_inventory(product_id):
       
    if product := product_service.get_product_by_id(product_id):
        inventory = request.get_json()
        product_service.update_inventory_delta(product, inventory['stock_delta'])
    else:
        raise NotFound
    
    return jsonify(product), 200
    
@api.route('/categories/all', methods=['GET'])
def get_all_categories():
    categories = product_service.get_all_categories(should_fully_qualify_image_urls())
    
    return jsonify(categories), 200

@api.route('/categories/id/<category_id>', methods=['GET'])
def get_categories_by_id(category_id):
    category = product_service.get_category_by_id(category_id, should_fully_qualify_image_urls())    
    
    return jsonify(category), 200

def should_fully_qualify_image_urls() -> bool:
    param = request.args.get("fullyQualifyimageUrls", "1")
    return param.lower() in ["1", "true"]
        
def custom_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError("Type not serializable") 

# Errors

@api.errorhandler(BadRequest)
def handle_bad_request(e):
    current_app.logger.error(f'BadRequest: {str(e)}')
    return jsonify({"error": "Bad request, please check your input"}), 400

@api.errorhandler(BotoCoreError)
def handle_boto_core_error(e):
    current_app.logger.error(f'BotoCoreError: {str(e)}')
    return jsonify({"error": "Internal server error"}), 500

#error for user not found
@api.errorhandler(NotFound)
def handle_not_found(e):
    current_app.logger.error(f'NotFound: {str(e)}')
    return jsonify({"error": "Not found"}), 404

@api.errorhandler(KeyError)
def handle_key_error(e):
    current_app.logger.error(f'KeyError: {str(e)}')
    return jsonify({"error": "Not found"}), 404

@api.errorhandler(UnsupportedMediaType)
def handle_unsupported_media_type(e):
    current_app.logger.error(f'UnsupportedMediaType: {str(e)}')
    return jsonify({"error": "Unsupported media type"}), 415

@api.errorhandler(Unauthorized)
def handle_unauthorized(e):
    current_app.logger.error(f'Unauthorized: {str(e)}')
    return jsonify({"error": "Unauthorized"}), 401

@api.errorhandler(500)
def handle_internal_error(e):
    current_app.logger.error(f'InternalServerError: {str(e)}')
    return jsonify({"error": "Internal server error"}), 500
