# Use an official Python image as the base image.
FROM python:3.8

# Set the working directory in the container.
WORKDIR /app

# Copy the model files and dependencies into the container.
COPY . .

# Install the dependencies listed in requirements.txt
RUN pip install -r requirements.txt

# Remove the license and download.sh file from the container
RUN rm LICENSE download.sh

# Set the entrypoint command to run the main() function inside custom_chat_completion.py.
ENTRYPOINT ["python", "custom_chat_completion.py"]
