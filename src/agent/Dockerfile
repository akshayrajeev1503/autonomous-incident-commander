FROM public.ecr.aws/lambda/python:3.11

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# Copy source code
COPY agents ${LAMBDA_TASK_ROOT}/agents
COPY data ${LAMBDA_TASK_ROOT}/data
COPY graph.py ${LAMBDA_TASK_ROOT}
COPY secrets_manager.py ${LAMBDA_TASK_ROOT}
COPY app.py ${LAMBDA_TASK_ROOT}

CMD [ "app.handler" ]
