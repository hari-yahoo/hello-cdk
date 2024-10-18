# Steps
### 1. Create an SQS FIFO Queue
* Go to the Amazon SQS Console.
* Choose Create Queue.
* Select FIFO as the queue type.
* Enter a Queue Name (ensure it ends with .fifo).
* Configure Message Deduplication and Message Group ID as per your requirements.
* Optionally, set up a Dead-Letter Queue (DLQ) for handling message failures.
* Create Queue.
### 2. Create a REST API in API Gateway
* Go to the API Gateway Console.
* Choose Create API, and select REST API.
* Provide a name and description for the API.
* Create a Resource (e.g., /messages) under the API.
* Under this resource, create a POST Method to handle incoming messages.
### 3. Integrate API Gateway with SQS
* In the Method Execution view for the POST method:
* Select AWS Service as the integration type.
* For AWS Region, select the region where your SQS queue is located.
* In AWS Service, choose SQS.
* Select Action Type as SendMessage.
* Specify the Queue ARN (you can find it in the SQS Console under queue details).
* For the Execution Role, create an IAM Role that allows API Gateway to send messages to SQS.
### 4. Set Up IAM Role for API Gateway
* Go to the IAM Console and create a new IAM Role.
* In Trust Relationships, add API Gateway (apigateway.amazonaws.com) as a trusted entity.
* Attach a policy to allow the following permissions:
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sqs:SendMessage",
      "Resource": "arn:aws:sqs:<region>:<account-id>:<queue-name>"
    }
  ]
}
```
This will allow API Gateway to send messages to the SQS queue.
### 5. Configure Method Request and Body Mapping
* In the Method Request of the POST method, you can define the expected request body parameters (such as messageBody, messageGroupId, etc.).
* Set up Body Mapping Templates:
* In the Integration Request, configure the Mapping Template for the incoming request body to map it to the parameters SQS expects.
Example:
```
{
  "Action": "SendMessage",
  "MessageBody": "$input.path('$.messageBody')",
  "MessageGroupId": "$input.path('$.messageGroupId')",
  "QueueUrl": "https://sqs.<region>.amazonaws.com/<account-id>/<queue-name>.fifo"
}
```
### 6. Deploy the API
* Once the method and integration are set up, deploy the API to a Stage (such as dev or prod).
* Go to the Stages section, choose Deploy API, and select a stage.
### 7. Test the API
* After deployment, test the API by sending a POST request to the endpoint (you can use Postman or cURL).
* The body of the request should contain the messageBody and messageGroupId (for FIFO Queue):
```
{
  "messageBody": "Test message",
  "messageGroupId": "group1"
}
```
Verify that the message appears in the SQS Queue.
### 8. Security and Access Control
* Use API Keys or IAM Authorization to secure the API Gateway.
* Ensure that only the external application with proper authentication can invoke the API to push messages to SQS.
### 9. Monitoring
* Use CloudWatch Logs to monitor API Gateway for errors or access logs.
* Check the SQS Queue for any failed or delayed messages, if necessary.
* Set up Alarms in CloudWatch for monitoring message traffic or error rates.