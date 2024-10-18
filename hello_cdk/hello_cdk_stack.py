from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_lambda as lmda,
    aws_lambda_event_sources as lambda_event_source,
    aws_sqs as sqs,
)
from constructs import Construct

AWS_ACCOUNT_ID = 730335563531
name_prefix = "CourseStatusUpdate"
name_suffix = "-Staging"

class HelloCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        api_role, lambda_role = self.createRoles()

        dlq = self.createDeadLetterQueue(name_prefix + "DLQ" + name_suffix + ".fifo")

        queue = self.createFifoQueue(name_prefix + "Queue" + name_suffix + ".fifo", dlq)

        func = self.createLambdaFunction(name_prefix + "Function" + name_suffix, queue)

        # api = self.createApiGateway(name_prefix + "Gateway" + name_suffix, api_role, queue)



    def createApiGateway(self, name, role, queue):
        #Create an API GW Rest API
        base_api = apigw.RestApi(self, 'ApiGW',rest_api_name='TestAPI')
        base_api.root.add_method("ANY")

        #Create a resource named "example" on the base API
        api_resource = base_api.root.add_resource('update')
       
        integration_response = apigw.IntegrationResponse(
            status_code = "200",
            response_templates={"application/json": ""},

        )
       
        api_integration_options = apigw.IntegrationOptions(
            credentials_role = role,
            integration_responses = [integration_response],
            request_templates={"application/json": "Action=SendMessage&MessageBody=$input.body"},
            passthrough_behavior=apigw.PassthroughBehavior.NEVER,
            request_parameters={"integration.request.header.Content-Type": "'application/x-www-form-urlencoded'"},
        )
        
        api_resource_sqs_integration = apigw.AwsIntegration(
            service="sqs",
            integration_http_method="POST",
            path="{}/{}".format(AWS_ACCOUNT_ID, queue.queue_name),
            options=api_integration_options
        )
        
        method_response = apigw.MethodResponse(status_code="200")

        #Add the API GW Integration to the "example" API GW Resource
        api_resource.add_method(
            "POST",
            api_resource_sqs_integration,
            method_responses=[method_response]
        )


    def createDeadLetterQueue(self, name):
        dlq = sqs.Queue(
            self, "DLQ",
            queue_name = name,
            fifo = True, 
            content_based_deduplication = True
        )
        return dlq

    def createFifoQueue(self, name, dlq):
        #Creating FIFO SQS Queue with Dead Letter Queue
        fifo_queue = sqs.Queue (
            self, "MyFifoQueue",
            queue_name = name,
            fifo = True,
            content_based_deduplication = True,
            dead_letter_queue = sqs.DeadLetterQueue(
                max_receive_count = 3,  # Number of retries before moving to DLQ
                queue = dlq
            )
        )   

        return fifo_queue

    def createLambdaFunction(self, name, queue):
        #Creating Lambda function that will be triggered by the SQS Queue
        sqs_lambda = lmda.Function(self, name,
                                   
            handler = 'process_messages.handler',
            runtime = lmda.Runtime.PYTHON_3_10,
            code = lmda.Code.from_asset('lambda'),
        )

        #Create an SQS event source for Lambda
        sqs_event_source = lambda_event_source.SqsEventSource(queue)

        #Add SQS event source to the Lambda function
        sqs_lambda.add_event_source(sqs_event_source)

    def createRoles(self):
        #Create the API GW service role with permissions to call SQS
        rest_api_role = iam.Role(
            self,
            "RestApiSqsRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSQSFullAccess")]
        )
        # sqs:ReceiveMessage, sqs:DeleteMessage, sqs:GetQueueAttributes
        # logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents
        # Modify the SQS Queue Policy to allow Lambda to poll messages from the queue

        return (rest_api_role, None)
