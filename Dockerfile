FROM python:2.7-alpine

# Install required Python Modules
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    slackclient \
    requests

COPY foaas_bot.py /opt/foaas_bot.py
CMD ["python", "/opt/foaas_bot.py"]