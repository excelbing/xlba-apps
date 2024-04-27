# Use an official Python runtime as the parent image
FROM python:3.9-slim

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install required packages
RUN pip install --no-cache-dir fastapi[all]==0.108 uvicorn==0.25 pandas==1.5 numpy==1.26 requests==2.31.0

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable for Uvicorn to know where the app lives
ENV APP_MODULE=main:app

# Command to run on container start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
