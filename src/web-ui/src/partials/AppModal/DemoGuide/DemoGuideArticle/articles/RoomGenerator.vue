<template>
    <ArticleLayout>
      <template #heading>Room Makeover</template>
      <p>
        Imagine being able to instantly re-imagine a room in different decor styles. 
        This demo combines Stable Diffusion, Amazon Sagemaker, Amazon Bedrock and Amazon Rekognition to enable an innovative approach to generating re-styled rooms from an initial user uploaded image.
      </p>
      <div class="architecture">
        <img src="/room-generator-architecture.png" alt="room makeover architecture" class="img-fluid" />
      </div>
      <ol>
        <li>The user authenticates with Amazon Cognito and obtains an identity token.  This is passed through to all subsequent API requests to the API Gateway.</li>
        <li>User selects a room image through the browser and the Web UI uses AWS Amplify Storage module to upload to S3.</li>
        <li>The Web UI calls the API Gateway, passing in the S3 location of the uploaded image and the selected room style, to create a room generation request.  A unique id is returned that can be used to retrieve the results.</li>
        <li>The API Gateway uses a Lambda authorizer to validate the supplied identity token.  It then proxies the request through to a Lambda function that validates and then persists the request into DynamoDB.</li>
        <li>DynamoDB streams captures the newly inserted room request.</li>
        <li>A lambda function triggers on each new record in the stream and starts an AWS Step Function to process the request.</li>
        <li>The first step of the step function performs image analysis on the uploaded room image.  The output of the step is a prompt that can passed to the Stable Diffusion model.
          <ol type="i">
            <li>Amazon Rekognition is used to detect objects in the image – such as sofa’s, chairs, and tables.  It returns a list of objects, together with their associated bounding boxes.</li>
            <li>For each object detected, a cropped image is created using the bounding box coordinates.</li>
            <li>Each image is then converted into a base64 string and sent as a request to Amazon Bedrock to use the Titan Multimodal Embeddings G1 model to obtain an embedding representation of the image.</li>
            <li>For each embedding, a K-NN request is made to the Amazon OpenSearch service to obtain the closest product matches.  The product match will also contain a caption – pre-generated by Anthropic’s Claude 3 Haiku model.  The caption was generated by passing the product and prompting Claude 3 to describe what’s in the picture.</li>
            <li>To create the final prompt, an initial base prompt is looked up using the style selected by the customer, which is then combined with the top matching product’s captions using <a href="https://huggingface.co/docs/diffusers/main/en/using-diffusers/weighted_prompts" target="_blank">prompt weighting</a>.</li>
          </ol>
        </li>
        <li>The uploaded room image and prompt are sent to the SageMaker Asynchronous Inference Endpoint.  The Step Function pauses at this point until the inference process completes – implemented using a callback <a href="https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html#connect-wait-token" target="_blank">task token</a>.</li>
        <li>The SageMaker Endpoint is deployed as a <a href="https://docs.aws.amazon.com/sagemaker/latest/dg/hugging-face.html" target="_blank">HuggingFace Deep Learning Container</a>, which hosts a custom Stable Diffusion model that uses ControlNet to add depth conditioning of the uploaded image to the generation. When the model completes the inference process, it places the result in an S3 bucket and sends a notification to an Amazon SNS topic containing the location of the result payload.</li>
        <li>Amazon SNS invokes the Lambda function that is subscribed to the topic.  The Lambda function calls-back into the Step Function to resume the process.</li>
        <li>The final step of the Step Function loads the inference result, extracts the generated image, and places it in the bucket for the customer to access.  The final image is also re-analyzed following the process in step 7, so that new bounding boxes and similar products are retrieved.</li>
        <li>The Web UI has been polling the API Gateway using the unique ID obtained from the initial request.  The room generation response is updated throughout the process.  A done state is returned, together with a reference to the final room image, which indicates to the frontend to render the results.  The Amplify Storage API is used to generate a signed URL, so that the image can be downloaded from S3.</li>
      </ol>
      <section class="dataloader-container">
        <h2 class="dataloader-heading">Pre-processing the product images</h2>
          The objects detected in the image analysis step described above need to be matched with similar items in the product catalogue, so that they can be recommended to the user.
          Embeddings are generated using the image and product name.
          Captions are generated for each product image for use in the prompt sent to the custom Stable Diffusion model.
          <img src="/room-generator-dataloader-architecture.png" alt="room makeover data loader architecture">
          <ol>
            <li>A S3 Batch Operations Job executes on the product images bucket and triggers a Lambda function for each image.</li>
            <li>Lambda function resizes the product image and places resulting image in separate bucket.</li>
            <li>Lambda function triggers on S3 create event in bucket.</li>
            <li>Lambda function starts execution of express workflow to process image.</li>
            <li>Embedding for image are retrieved using Titan Multimodal Embeddings model through Amazon Bedrock.</li>
            <li>Product captions – descriptions of what the product image contains – are created by calling Anthropic Claude 3 Haiku model through Amazon Bedrock.</li>
            <li>Embedding and caption are published to SQS.</li>
            <li>Lambda function receives batches of captions & embeddings and indexes them into Amazon OpenSearch.</li>
          </ol>
          The prompt used with the Claude 3 Haiku model to generate the product captions was as follows:
          <blockquote class="prompt">
            Identify the {category} product in the image. Then identify the dominant color or colours of the {category} product. Be descriptive. Ignore the background. Name the product and then describe it without any preamble.<br/>
            &lt;example&gt;Sofa, deep, plush green color with a smooth, velvet-like texture. It features a rectangular shape with a modern, streamlined silhouette and two cylindrical cushions at either end, serving as armrests. The sofa has three seat cushions that create a single seating surface without separations, and the back cushion runs the length of the sofa in a single piece as well, contributing to its sleek design. There are no visible patterns or prints on the fabric, which gives it a rich, uniform look. The sofa's legs are short, cylindrical, and appear to be made of light-colored wood&lt;/example&gt;
          </blockquote>
      </section>
    </ArticleLayout>
</template>

<script>
import ArticleLayout from '../ArticleLayout.vue';

export default {
  name: 'RoomGenerator',
  components: { ArticleLayout },
};
</script>
<style scoped>
.dataloader-container {
  margin-bottom: 9rem;
}

.dataloader-heading {
  font-size: 1.5rem;
}

.prompt {
  color: black;
  background: var(--blue-100);
  font-family: "Lucida Console", "Courier New", monospace;
  margin-top: 1rem;
}
</style>